# ArduinoMate — Resume Bullets

Three concise bullets for a software engineering / AI resume.
Adjust numbers and terminology to match the specific role you are applying for.

---

## Bullets

**1. RAG-powered Arduino assistant (Python, FastAPI, ChromaDB)**
Built ArduinoMate, a production FastAPI service that answers Arduino questions using Retrieval-Augmented Generation: embedded 109 documentation chunks with `all-MiniLM-L6-v2`, stored them in ChromaDB, and retrieved the top-5 most relevant chunks per query to ground Groq LLM answers in official references — achieving 100% answer rate, 100% out-of-scope refusal rate, and 100% source-hit rate on a 15-question evaluation set.

**2. AI agent with tool use and production hardening (LangGraph, FastAPI middleware)**
Designed a tool-using agent (`POST /agent`) that selects between an Arduino documentation search tool and an Ohm's-law LED resistor calculator using a hand-written ReAct loop and a LangGraph graph with conversation memory and a human-approval gate; hardened the API with a custom ASGI middleware that logs latency and token usage per request, serves repeat queries from an in-memory LRU cache (60 s TTL, reducing repeat-query latency from ~8 s to under 5 ms), enforces a 16 KB input limit, and blocks 20 known prompt-injection patterns before they reach the LLM.

**3. Full CI/CD pipeline and cloud deployment (GitHub Actions, Docker, Render)**
Authored a three-job GitHub Actions workflow (ruff lint, 70 pytest tests with mocked LLM and ChromaDB, Docker image build) that runs on every push and pull request; containerised the FastAPI backend and Streamlit chat UI in a multi-stage Docker image (python:3.11-slim, non-root user, named volumes for model weights and vector index); deployed the API to Render via a `render.yaml` Blueprint with a public `/health` endpoint and automatic redeploy on merge to `master`.

---

## Supporting numbers

| Claim | Source |
|-------|--------|
| 109 documentation chunks indexed | `app/vectorstore.py` build log |
| 100% answer rate / 100% refusal rate / 100% source hit rate | `eval/run_eval.py` Config B results |
| 10/10 correct semantic search top hits, avg score 0.754 | `eval/search_results.md` |
| Prompt engineering: 230/250 vs 104/250 (generic baseline) | `eval/prompt_compare.md` |
| ~8 s average end-to-end RAG latency (Groq, 1 024 tokens max) | Day 8 evaluation table |
| Sub-5 ms on cache hit | Measured via `X-Latency-Ms` response header |
| 70 pytest tests, 0 ruff errors | CI green badge |
| 20 prompt-injection patterns blocked | `app/middleware.py` `_INJECTION_PATTERNS` |
