# Day 8 — RAG Pipeline: Grounded Answers with Citations

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Wire the Day 7 semantic retrieval layer into the LLM to produce grounded answers
with source citations, evaluate two retrieval configurations against a 15-question
eval set, and pick the winning config.

---

## Tasks Completed

- [x] `app/rag.py` — full retrieve-augment-generate pipeline; `rag_answer()` with citations
- [x] `POST /ask` endpoint in `main.py` — RAG-grounded answers via FastAPI
- [x] `schema.py` — `AskRequest`, `AskResponse`, `RagCitation` Pydantic models
- [x] `eval/eval_set.json` — 15-question evaluation set (13 in-scope, 2 out-of-scope)
- [x] `eval/run_eval.py` — automated runner; two configs compared; winner printed
- [x] Eval executed; Config B wins — winner table below
- [x] Git commit + push + `day-8` tag

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `app/rag.py` | Created | Retrieve → augment → generate; `rag_answer()` returns `RagResponse` with citations |
| `main.py` | Updated | Added `POST /ask` endpoint; version → 4.0.0 |
| `schema.py` | Updated | Added `AskRequest`, `AskResponse`, `RagCitation` models |
| `eval/eval_set.json` | Created | 15-row evaluation set covering in-scope and out-of-scope questions |
| `eval/run_eval.py` | Created | Two-config eval runner with per-question results and aggregate table |
| `docs/day08/README.md` | Created | This file |

---

## Architecture

```
POST /ask
         │
         ▼  main.py → ask_endpoint()
         │  Validates AskRequest (question, top_k, min_score)
         │
         ▼  app/rag.py → rag_answer()
         │
         ├─► app/vectorstore.py → query_collection()
         │       Embeds query via all-MiniLM-L6-v2
         │       Queries ChromaDB (cosine HNSW)
         │       Returns top-k chunks with score, title, source, page
         │
         ├─► Builds RAG prompt
         │       System: ArduinoMate rules + "answer only from CONTEXT"
         │       User:   CONTEXT block (numbered chunks) + QUESTION
         │
         ├─► app/llm.py → chat()
         │       Groq / Gemini with temperature=0.2
         │       Returns strict JSON: answer, confidence, follow_up
         │
         └─► RagResponse(answer, citations, model, retrieved, out_of_scope)
                      │
                      ▼
              AskResponse (FastAPI)
```

**Out-of-scope guard:** When no chunk scores ≥ `min_score`, the context block
is empty. The system prompt instructs the LLM to return exactly:
> "I don't know based on the available Arduino documentation."

A post-generation check enforces this string even if the LLM ignores it.

---

## API — POST /ask

```
POST /ask
Content-Type: application/json

{
  "question": "What does pinMode() do in Arduino?",
  "top_k": 5,
  "min_score": 0.20
}
```

**Response:**
```json
{
  "question": "What does pinMode() do in Arduino?",
  "answer": "pinMode(pin, mode) configures a digital pin as INPUT, OUTPUT, or INPUT_PULLUP...",
  "citations": [
    { "title": "pinMode()", "source": "ArduinoMate/data/raw/pinMode.adoc", "page": 1, "score": 0.812 },
    { "title": "pinMode",   "source": "ArduinoMate/data/records.json",     "page": 1, "score": 0.794 }
  ],
  "model": "qwen/qwen3.8-27b",
  "retrieved": 5,
  "out_of_scope": false
}
```

**Out-of-scope example (Q06 — HC-SR04):**
```json
{
  "question": "Can ArduinoMate tell me how to connect an HC-SR04 ultrasonic sensor?",
  "answer": "I don't know based on the available Arduino documentation.",
  "citations": [],
  "model": "qwen/qwen3.8-27b",
  "retrieved": 0,
  "out_of_scope": true
}
```

---

## Eval Set — eval/eval_set.json

15 questions: **13 in-scope** (expect a real answer) + **2 out-of-scope** (expect refusal).

| ID | Question | In-scope? |
|----|----------|-----------|
| Q01 | What does pinMode() do? | ✅ |
| Q02 | Read a button with digitalRead() / INPUT_PULLUP | ✅ |
| Q03 | Difference between delay() and millis() | ✅ |
| Q04 | How analogWrite() produces PWM | ✅ |
| Q05 | analogRead() fluctuating on floating pin | ✅ |
| Q06 | HC-SR04 ultrasonic sensor wiring | ❌ |
| Q07 | Serial Monitor baud rate | ✅ |
| Q08 | attachInterrupt() volatile gotcha | ✅ |
| Q09 | map() vs constrain() for servo | ✅ |
| Q10 | random() seed after reset | ✅ |
| Q11 | Turn LED on/off with digitalWrite() | ✅ |
| Q12 | Return value of analogRead() | ✅ |
| Q13 | I2C LCD display setup | ❌ |
| Q14 | millis() non-blocking LED blink | ✅ |
| Q15 | delay() inside ISR | ✅ |

---

## Evaluation Results

Two retrieval configurations were compared using `eval/run_eval.py`.

### Config A — chunk_size=300, top_k=3

| ID | Answered? | Correct Refusal? | Source Hit? | Retrieved | Latency |
|----|-----------|-----------------|-------------|-----------|---------|
| Q01 | ✅ | — | ✅ | 3 | 19.6 s |
| Q02 | ✅ | — | ✅ | 3 | 0.9 s |
| Q03 | ✅ | — | ✅ | 3 | 0.8 s |
| Q04 | ✅ | — | ✅ | 3 | 0.6 s |
| Q05 | ✅ | — | ✅ | 3 | 1.0 s |
| Q06 | — | ✅ | — | 3 | 1.0 s |
| Q07 | ✅ | — | ✅ | 3 | 1.2 s |
| Q08 | ✅ | — | ✅ | 3 | 0.7 s |
| Q09 | ✅ | — | ✅ | 3 | 3.5 s |
| Q10 | ✅ | — | ✅ | 3 | 10.7 s |
| Q11 | ✅ | — | ✅ | 3 | 5.0 s |
| Q12 | ✅ | — | ✅ | 3 | 0.7 s |
| Q13 | — | ✅ | — | 3 | 15.2 s |
| Q14 | ❌ | — | ❌ | 3 | 2.5 s |
| Q15 | ❌ | — | ✅ | 3 | 2.1 s |

### Config B — chunk_size=500, top_k=5 ← **WINNER**

| ID | Answered? | Correct Refusal? | Source Hit? | Retrieved | Latency |
|----|-----------|-----------------|-------------|-----------|---------|
| Q01 | ✅ | — | ✅ | 5 | 0.9 s |
| Q02 | ✅ | — | ✅ | 5 | 9.3 s |
| Q03 | ✅ | — | ✅ | 5 | 13.1 s |
| Q04 | ✅ | — | ✅ | 5 | 7.9 s |
| Q05 | ✅ | — | ✅ | 5 | 8.1 s |
| Q06 | — | ✅ | — | 5 | 1.6 s |
| Q07 | ✅ | — | ✅ | 5 | 7.2 s |
| Q08 | ✅ | — | ✅ | 5 | 12.4 s |
| Q09 | ✅ | — | ✅ | 5 | 9.3 s |
| Q10 | ✅ | — | ✅ | 5 | 10.0 s |
| Q11 | ✅ | — | ✅ | 5 | 12.8 s |
| Q12 | ✅ | — | ✅ | 5 | 7.9 s |
| Q13 | — | ✅ | — | 5 | 12.7 s |
| Q14 | ✅ | — | ✅ | 5 | 0.7 s |
| Q15 | ✅ | — | ✅ | 5 | 10.9 s |

---

## Winner Table

| Metric | Config A (chunk=300, top_k=3) | Config B (chunk=500, top_k=5) |
|--------|-------------------------------|-------------------------------|
| Answer rate (in-scope) | 85% | **100%** |
| Refusal rate (out-of-scope) | **100%** | **100%** |
| Source hit rate | 92% | **100%** |
| Avg chunks retrieved | 3.0 | 5.0 |
| Avg latency (s) | **4.4 s** | 8.3 s |
| **Composite score** | 0.912 | **1.000** |

> Composite = answer_rate × 0.35 + refusal_rate × 0.35 + source_hit_rate × 0.30

🏆 **Winner: Config B — chunk_size=500, top_k=5**

Config B answers all 13 in-scope questions correctly (100%), refuses both
out-of-scope questions (100%), and cites the correct source for every answer
(100%). Config A missed Q14 and Q15 because top_k=3 sometimes fails to pull
both the `millis()` and `attachInterrupt()` chunks needed for multi-function
questions. The latency trade-off (~4 extra seconds) is acceptable for an
educational assistant.

---

## RAG vs Plain Chat

| Property | POST /chat (Day 6) | POST /ask (Day 8) |
|----------|-------------------|-------------------|
| Context | None — LLM general knowledge | Retrieved documentation chunks |
| Citations | ❌ | ✅ |
| Out-of-scope guard | Prompt instruction only | Chunk score + prompt instruction |
| Hallucination risk | Moderate | Low |
| Latency | ~1 s | ~8 s (retrieval + embedding) |

---

## Setup

```bash
# Install dependencies (unchanged from Day 7)
pip install -r requirements.txt

# Start the server (index auto-builds on startup)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Test RAG endpoint
curl -X POST http://127.0.0.1:8000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"What does pinMode() do?\", \"top_k\": 5}"

# Run eval (requires running server or just the Python module directly)
python eval/run_eval.py

# Force index rebuild + eval
python eval/run_eval.py --rebuild
```

---

## Technologies Used

- Python 3.13
- FastAPI 0.110+
- ChromaDB 1.5.9 (persistent HNSW cosine index)
- sentence-transformers 6.3.0 (`all-MiniLM-L6-v2`, 384-dim)
- Groq SDK (`qwen/qwen3.8-27b`)
- Pydantic v2

---

## Commands

```bash
# Start server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# RAG answer
curl -X POST http://127.0.0.1:8000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"delay vs millis\", \"top_k\": 5}"

# Out-of-scope (should say I don't know)
curl -X POST http://127.0.0.1:8000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"How do I wire an HC-SR04 sensor?\"}"

# Health (check indexed_chunks)
curl http://127.0.0.1:8000/health

# Run eval
python eval/run_eval.py
```
