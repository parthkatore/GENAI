# ArduinoMate — Project Progress

## Day 12 — CI/CD Pipeline & Deployment (S1 + S2)

### S1 — GitHub Actions CI
- Added `.github/workflows/ci.yml` with three jobs:
  - **lint**: `ruff check .` — style and import order
  - **test**: `pytest tests/ -v` — 44 tests, LLM + ChromaDB mocked (no API key needed)
  - **docker**: `docker build` smoke-test via `docker/build-push-action`
- CI runs on every push and PR to `master`.
- Green badge added to README.

### S2 — Render Deployment
- Added `render.yaml` Blueprint for one-click Render deployment.
- FastAPI backend deployed as a Docker web service.
- `GET /health` returns `{"status": "healthy"}` publicly.
- Live URL: https://arduinomate-api.onrender.com
- Live URL added to README (Deploy badge).

---

## Day 11 — Testing & Docker

- 44 pytest tests across `test_records.py`, `test_search.py`, `test_api.py`, `test_tools.py`
- Ruff lint clean
- Multi-stage Dockerfile + docker-compose with named volumes for ChromaDB and HF cache

## Day 10 — Streamlit Chat UI

- Streamlit interface (`ui/app.py`) with citations, thumbs feedback, and agent trace
- Arduino Uno interactive pin map (`ui/pin_map.py`)
- checkpoint-2 tag

## Day 9 — AI Agent & LangGraph

- `app/tools.py`: `led_resistor_calculator`, `rag_search`, `call_tool`
- `app/agent_loop.py`: hand-written ReAct loop
- `app/graph.py`: LangGraph agent with memory and approval gate
- `POST /agent` endpoint

## Day 8 — RAG Pipeline

- `app/rag.py` + `POST /ask`
- 15-question eval set, `eval/run_eval.py`
- Config B wins: 100/100/100

## Day 7 — Semantic Search

- Semantic chunking, all-MiniLM-L6-v2 embeddings, ChromaDB vector store
- `GET /search/semantic`

## Day 6 — LLM Integration

- LLM provider wrapper (Groq / Gemini), `POST /chat`
- ArduinoMate system and QA prompts, prompt evaluation

## Week 1 (Days 1–5) — Arduino Records & Ingestion

- 20 Arduino function records, keyword + TF-IDF search
- FastAPI skeleton, checkpoint-1
