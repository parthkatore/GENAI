# ArduinoMate — Project Progress

## Day 14 — Interview and Demo Day

- [x] Added `docs/interview.md` with a 60-second pitch, ten likely questions, and an honest board-specific engineering story.
- [x] Added `docs/day14/README.md` with the five-minute demo run-of-show and readiness checklist.
- [x] Verified the automated suite: 75 tests pass; Ruff passes.
- **Blocked:** Two live demo rehearsals remain undone because the public Render API is suspended, the local ChromaDB index has zero chunks, and local `.env` is missing `GEMINI_API_KEY`. The `final` tag will identify this tested repository snapshot, not claim the live demo was rehearsed. See `docs/day14/README.md`.

## Day 13 — Production Hardening

- Added latency/token logging, a response cache, request limits, and prompt-injection checks.
- Empty or unavailable ChromaDB now reports RAG readiness and returns a service error rather than a misleading out-of-scope answer.

## Day 12 — CI/CD Pipeline & Deployment (S1 + S2)

### S1 — GitHub Actions CI
- Added `.github/workflows/ci.yml` with three jobs:
  - **lint**: `ruff check .` — style and import order
  - **test**: `pytest tests/ -v` — 44 tests, LLM + ChromaDB mocked (no API key needed at that milestone)
  - **docker**: `docker build` smoke-test via `docker/build-push-action`
- CI runs on every push and PR to `master`.
- Green badge added to README.

### S2 — Render Deployment
- Added `render.yaml` Blueprint for one-click Render deployment.
- FastAPI backend deployed as a Docker web service.
- `GET /health` exposes API and RAG-index health.
- Render URL: https://arduinomate-api.onrender.com (currently suspended; not demo-ready).
- Live URL added to README (Deploy badge).

---

## Day 11 — Testing & Docker

- 44 pytest tests across records, search, API, and tools at that milestone
- Ruff lint clean
- Multi-stage Dockerfile + docker-compose with a named ChromaDB volume

## Day 10 — Streamlit Chat UI

- Streamlit interface (`frontend/app.py`) with citations, thumbs feedback, and agent trace
- Arduino Uno interactive pin map (`frontend/pin_map.py`)
- checkpoint-2 tag

## Day 9 — AI Agent & LangGraph

- `backend/app/tools.py`: `led_resistor_calculator`, `rag_search`, `call_tool`
- `backend/app/agent_loop.py`: hand-written ReAct loop
- `backend/app/graph.py`: LangGraph agent with memory and approval gate
- `POST /agent` endpoint

## Day 8 — RAG Pipeline

- `backend/app/rag.py` + `POST /ask`
- 15-question eval set, `eval/run_eval.py`
- Config B wins: 100/100/100

## Day 7 — Semantic Search

- Semantic chunking, Gemini API embeddings, ChromaDB vector store
- `GET /search/semantic`

## Day 6 — LLM Integration

- LLM provider wrapper (Groq / Gemini), `POST /chat`
- ArduinoMate system and QA prompts, prompt evaluation

## Week 1 (Days 1–5) — Arduino Records & Ingestion

- 20 Arduino function records, keyword + TF-IDF search
- FastAPI skeleton, checkpoint-1
