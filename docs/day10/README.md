# Day 10 — Streamlit Chat UI + Arduino Pin Map

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Build a polished Streamlit web interface that wraps the Day 6–9 FastAPI backend.  
The signature feature is an **interactive Arduino Uno pin diagram** that highlights
every pin mentioned in the LLM's answer — digital (D0–D13), PWM-capable (~3, ~5,
~6, ~9, ~10, ~11), analog (A0–A5), and power (5V / 3.3V / GND / VIN).

---

## Tasks Completed

- [x] `ui/app.py` — full Streamlit chat interface calling `/ask` or `/agent`
- [x] `ui/pin_map.py` — Arduino Uno SVG renderer + `extract_pins()` parser
- [x] Citations panel — expandable source list for every RAG answer
- [x] Thumbs up / down — saves feedback records to `data/feedback.json`
- [x] **Pin Map panel** — Arduino Uno diagram with animated amber highlights
- [x] Agent trace expander — step-by-step reasoning for `/agent` mode
- [x] Sidebar controls — API URL, mode toggle, top_k, min_score, thread ID
- [x] Quick-example buttons — four one-click starter questions
- [x] `requirements.txt` updated — added `streamlit>=1.35.0`
- [x] `docs/screenshots/` directory created for README screenshots
- [x] Git commit + push + `checkpoint-2` tag

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `ui/app.py` | Created | Streamlit chat UI — calls `/ask` and `/agent`, shows citations, pin map, feedback |
| `ui/pin_map.py` | Created | Arduino Uno SVG renderer; `extract_pins()` regex parser; `render_pin_map()` |
| `ui/__init__.py` | Created | Package marker |
| `data/feedback.json` | Created | Persistent feedback store (initially empty list) |
| `requirements.txt` | Updated | Added `streamlit>=1.35.0` |
| `docs/day10/README.md` | Created | This file |

---

## Signature Feature — Arduino Uno Pin Map

The pin map is a pixel-accurate SVG of the Arduino Uno R3 rendered entirely in
Python. It lives permanently in the right panel of the chat interface.

### How it works

1. After every answer, `extract_pins(answer_text)` scans the text with a set of
   targeted regular expressions and returns a set of pin IDs like
   `{"D13", "D9", "A0"}`.

2. `render_pin_map(active_pins)` builds an inline SVG where:
   - **Amber circles + pulse animation** mark every active pin.
   - **Blue circles** mark PWM-capable pins (D3, D5, D6, D9, D10, D11).
   - **Purple circles** mark analog inputs A0–A5.
   - **Red circles** mark power pins (5V, 3.3V, GND, VIN).
   - **Grey circles** mark idle digital pins.

3. The SVG is served to Streamlit via `st.components.v1.html()` so it renders
   as a live interactive element, not a static image.

### Pin recognition patterns

| Pattern | Example text | Detected pin(s) |
|---------|-------------|-----------------|
| `A0`–`A5` | "read on A0" | A0 |
| `pin 13`, `D13` | "turn pin 13 HIGH" | D13 |
| `~3`, `~9` | "PWM on ~9" | D9 |
| Digital context | "digital pin 2" | D2 |
| PWM context | "PWM output 6" | D6 |
| `5V`, `GND`, `3.3V`, `VIN` | "connect to 5V" | 5V |

### SVG components

| Element | Description |
|---------|-------------|
| Board outline | Dark-blue rounded rectangle representing the Uno PCB |
| ATmega328P chip | Black rectangle with green label in the board centre |
| USB + power jack | Left-side connectors |
| Pin circles | Colour-coded filled circles for all 28 annotated pins |
| Pulse animation | Amber rings expand and fade on active pins |
| Legend | Four colour swatches at the bottom of the SVG |
| Header labels | DIGITAL/PWM and ANALOG IN column headers |

---

## Screenshot

> Replace the placeholder below with an actual screenshot once the app is running.

```
docs/screenshots/day10_ui.png
docs/screenshots/day10_pin_map.png
```

---

## UI Layout

```
┌─────────────────────────────────────────────────────┐
│  Sidebar                                            │
│  ─────────                                         │
│  API URL input + health status                     │
│  Mode: RAG Answer | AI Agent                       │
│  RAG Config: top_k, min_score                      │
│  Agent Config: LangGraph toggle, thread ID         │
│  Feedback stats: 👍 N  👎 N                        │
└───────────────────────────────────────────────────┘

Main area (2 columns, 3:2)
┌────────────────────────────┬──────────────────────┐
│  Chat panel (left)         │  Pin Map (right)     │
│  ─────────────────────     │  ─────────────────── │
│  [user bubble]             │  Arduino Uno SVG     │
│  [bot bubble]              │  with highlighted    │
│    ↳ Sources (expander)    │  pins                │
│    ↳ Agent trace (expander)│                      │
│    ↳ 👍  👎  feedback      │  Pin legend expander │
│  ─────────────────────     │                      │
│  [text input]  [Send]      │                      │
│  Quick examples            │                      │
│  [Clear chat]              │                      │
└────────────────────────────┴──────────────────────┘
```

---

## Mode Comparison

| Feature | RAG mode (`/ask`) | Agent mode (`/agent`) |
|---------|-------------------|-----------------------|
| Endpoint | `POST /ask` | `POST /agent` |
| Citations | ✅ Expandable source list | ❌ |
| Agent trace | ❌ | ✅ Step-by-step reasoning |
| LED calculator | ❌ | ✅ via `led_resistor_calculator` tool |
| Memory | ❌ | ✅ via `thread_id` |
| Out-of-scope badge | ✅ | — |

---

## Feedback Store — data/feedback.json

Each thumbs-up or thumbs-down click appends one JSON record:

```json
{
  "timestamp": "2025-11-18T10:32:45.123456",
  "question":  "How do I blink an LED on pin 13?",
  "answer":    "To blink an LED on pin 13, use pinMode(13, OUTPUT)...",
  "thumb":     "up"
}
```

The sidebar shows live counts of up/down records.

---

## Checkpoint 2 Deliverables

This commit marks **Checkpoint 2** of the ArduinoMate project.

| Item | Status |
|------|--------|
| FastAPI backend (`/ask`, `/agent`, `/chat`, `/search/semantic`) | ✅ Day 6–9 |
| RAG pipeline (ChromaDB + sentence-transformers + Groq) | ✅ Day 7–8 |
| AI agent (hand-written ReAct + LangGraph) | ✅ Day 9 |
| Streamlit chat UI | ✅ Day 10 |
| Pin Map panel (signature feature) | ✅ Day 10 |
| Citations, feedback, agent trace | ✅ Day 10 |
| `checkpoint-2` git tag | ✅ |

---

## Setup

```bash
# 1. Install new dependency
pip install -r requirements.txt

# 2. Start the FastAPI backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 3. Launch Streamlit (in a second terminal)
streamlit run ui/app.py
```

Open: **http://localhost:8501**

---

## Example Interactions

### RAG mode — pin map lights up

**Question:** "How do I fade an LED using analogWrite() on pin 9?"

**Pin Map result:** Pin `D9` (PWM-capable) highlights in amber. The board
diagram shows D9 glowing with a pulsing ring, confirming that pin 9 is the
correct PWM output.

---

### RAG mode — analog pin

**Question:** "How do I read a potentiometer value with analogRead() on A0?"

**Pin Map result:** Pin `A0` highlights in amber (purple becomes amber).

---

### Agent mode — LED resistor calculator

**Question:** "What resistor do I need for a red LED on 5V at 20mA?"

**Agent trace shows:**
1. Tool call: `led_resistor_calculator` with `supply_voltage=5.0, led_forward_voltage=2.0, led_current_ma=20`
2. Observation: `150.0 Ω exact → 150 Ω E12`
3. Final answer: "Use a 150 Ω resistor..."

**Pin Map:** `5V` power pin highlights in amber (the answer mentions 5V).

---

## Technologies Used

- Python 3.13
- Streamlit 1.35+
- FastAPI 0.110+ (Day 6–9 backend)
- requests (HTTP client for API calls)
- Inline SVG (pin map diagram)
- ChromaDB + sentence-transformers (Day 7 vector store)
- Groq SDK — `qwen/qwen3.8-27b` (LLM)
- LangGraph 1.x (Day 9 agent)
- Pydantic v2
