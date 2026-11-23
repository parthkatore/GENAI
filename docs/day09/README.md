# Day 9 — Tool-Using Agent: Hand-Written Loop + LangGraph

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Build a tool-using agent in two ways:

1. **S1 — Hand-written ReAct loop** (`app/tools.py` + `app/agent_loop.py`)  
   A transparent Reason → Act → Observe cycle using the existing `app.llm.chat()`.

2. **S2 — LangGraph rebuild** (`app/graph.py` + `POST /agent`)  
   The same agent rebuilt with LangGraph 1.x: stateful memory via `MemorySaver`,
   an explicit approval node, and a compiled `StateGraph`.

---

## Tasks Completed

- [x] `app/tools.py` — `led_resistor_calculator` (Ohm's law + E12 rounding) + `rag_search` + `call_tool` dispatcher + OpenAI-style `TOOLS` schemas
- [x] `app/agent_loop.py` — hand-written ReAct loop; `run_agent()` → `AgentResult`
- [x] `app/graph.py` — LangGraph `StateGraph` with `reason → approval → act → answer`; `MemorySaver` checkpointer; `run_graph()` → `GraphResult`
- [x] `POST /agent` endpoint in `main.py` (supports both backends via `use_graph` flag)
- [x] `schema.py` — `AgentRequest`, `AgentResponse`, `AgentStepOut` Pydantic models
- [x] `requirements.txt` updated — `langgraph`, `langchain-core`, `langchain-groq`
- [x] Git commit + push + `day-9` tag

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `app/tools.py` | Created | `led_resistor_calculator`, `rag_search`, `call_tool`, `TOOLS` schemas |
| `app/agent_loop.py` | Created | Hand-written ReAct loop, `run_agent()` → `AgentResult` |
| `app/graph.py` | Created | LangGraph `StateGraph` with memory + approval; `run_graph()` → `GraphResult` |
| `main.py` | Updated | `POST /agent` endpoint; version → 5.0.0 |
| `schema.py` | Updated | `AgentRequest`, `AgentResponse`, `AgentStepOut` |
| `requirements.txt` | Updated | Added `langgraph`, `langchain-core`, `langchain-groq` |
| `docs/day09/README.md` | Created | This file |

---

## Tool 1 — `led_resistor_calculator`

Calculates the minimum safe series resistor for an LED using Ohm's law, then
rounds the result **up** to the next standard E12 value.

**Formula:**

```
R_exact = (V_supply - V_forward) / I_led
R_e12   = next E12 value ≥ R_exact
```

**E12 series mantissas:** 10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82
(repeated per decade: 10 Ω … 10 MΩ)

**Example:**

```
supply = 5.0 V,  Vf = 2.0 V (red LED),  I = 20 mA
R_exact = (5.0 - 2.0) / 0.020 = 150.0 Ω
R_e12   = 150 Ω  ← standard E12 value
```

| Input | Value |
|-------|-------|
| Supply voltage | 5.0 V |
| LED forward voltage | 2.0 V (red) |
| LED current | 20 mA |
| **Exact R** | **150.0 Ω** |
| **E12 R** | **150 Ω** |

---

## Tool 2 — `rag_search`

Calls `rag_answer()` from Day 8, retrieves top-5 chunks from ChromaDB,
and returns the LLM-generated answer with inline citations.

---

## S1 — Hand-Written ReAct Agent (`app/agent_loop.py`)

```
run_agent(user_message, session_id, history) → AgentResult
```

**Loop:**

```
  User message
      │
      ▼
  LLM (reason) ──► {"tool": "...", "args": {...}}  ──► call_tool() ──► observation
      ▲                                                                        │
      └────────────────────────────────────────────────────────────────────────┘
                             (up to MAX_STEPS = 6)
      │
      ▼  LLM returns {"answer": "..."}
  AgentResult(answer, steps, model, session_id)
```

The LLM is prompted to respond in strict JSON — either a tool call or a
final answer. The loop self-corrects if the LLM uses wrong argument names
(it retries until the tool succeeds or the step limit is reached).

---

## S2 — LangGraph Agent (`app/graph.py`)

```
run_graph(user_message, thread_id, approved) → GraphResult
```

### Graph Topology

```
  START → reason ──► approval ──► act ──► reason (loop)
                │                            │
                └──────────────► answer ◄────┘ (final answer or step limit)
                                    │
                                   END
```

### Nodes

| Node | Description |
|------|-------------|
| `reason` | LLM decides: tool call or final answer |
| `approval` | Gate: auto-approves (default) or pauses for human approval |
| `act` | Executes the approved tool, appends observation to messages |
| `answer` | Surfaces `state["answer"]` → END |

### Memory

`MemorySaver` checkpoints every graph state by `thread_id`.  
Pass the same `thread_id` across API calls to continue a multi-turn conversation.

### Approval Gate

| `AUTO_APPROVE` env | Behaviour |
|-------------------|-----------|
| `true` (default) | Every tool call auto-approved |
| `false` | Graph pauses at `approval` node; caller sets `approved=true/false` and resumes |

---

## API — POST /agent

```
POST /agent
Content-Type: application/json

{
  "message":   "What resistor do I need for a red LED on 5V at 20mA?",
  "thread_id": "session-42",
  "use_graph": true,
  "approved":  true
}
```

**Response:**

```json
{
  "answer": "For a red LED on 5V at 20mA, use a 150 Ω resistor...",
  "steps": [
    { "step": 1, "type": "tool_call",    "tool": "led_resistor_calculator", "args": {...} },
    { "step": 1, "type": "observation",  "tool": "led_resistor_calculator", "result": "LED Resistor Calculation\n..." },
    { "step": 2, "type": "final_answer", "answer": "For a red LED on 5V at 20mA, use a 150 Ω resistor..." }
  ],
  "model":     "qwen/qwen3.8-27b",
  "thread_id": "session-42",
  "num_steps": 3
}
```

**Use hand-written loop:**
```json
{ "message": "What does pinMode() do?", "use_graph": false }
```

---

## Architecture Comparison

| Property | Hand-Written Loop (`agent_loop.py`) | LangGraph (`graph.py`) |
|----------|-------------------------------------|------------------------|
| Framework | None — pure Python | LangGraph 1.x |
| Memory | Caller manages `history` list | `MemorySaver` keyed by `thread_id` |
| Approval gate | ❌ | ✅ (approval node) |
| Transparency | Full — loop logic is explicit | Graph topology visible in code |
| Resumability | ❌ | ✅ (checkpoint resume) |
| Max steps | 6 | 6 |

---

## Setup

```bash
# Install new dependency
pip install -r requirements.txt

# Start the server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# LED resistor question (LangGraph)
curl -X POST http://127.0.0.1:8000/agent ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"What resistor for a red LED on 5V at 20mA?\", \"use_graph\": true}"

# Arduino question (hand-written loop)
curl -X POST http://127.0.0.1:8000/agent ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"What does attachInterrupt() do?\", \"use_graph\": false}"

# Multi-turn memory (same thread_id continues the conversation)
curl -X POST http://127.0.0.1:8000/agent ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"Now what about a green LED?\", \"thread_id\": \"session-1\", \"use_graph\": true}"
```

---

## Technologies Used

- Python 3.13
- LangGraph 1.2.22 (`StateGraph`, `MemorySaver`)
- LangChain Core 1.8.1 / LangChain Groq 1.2.0
- FastAPI 0.110+
- Groq SDK (`qwen/qwen3.8-27b`)
- ChromaDB 1.5.9 + sentence-transformers (Day 7/8 RAG pipeline)
- Pydantic v2
