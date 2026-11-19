# Day 11 — Testing & Docker

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

**S1 — Tests:** Write 8+ pytest tests covering records integrity, semantic
search, all major API endpoints (`/health`, `/ask`, `/agent`,
`/search/semantic`) with a fake LLM, and the agent tools directly.
`ruff check .` must pass with zero errors.

**S2 — Docker:** Containerise the FastAPI backend and Streamlit UI with a
multi-stage `Dockerfile`, a `.dockerignore`, and a `docker-compose.yml` so
`docker compose up --build` starts both services.

---

## Tasks Completed

- [x] `tests/conftest.py` — shared fixtures: fake LLM patch, TestClient, mock vector store
- [x] `tests/test_records.py` — 7 record integrity tests (schema, uniqueness, categories)
- [x] `tests/test_search.py` — 8 chunking + semantic search tests (mocked ChromaDB)
- [x] `tests/test_api.py` — 17 endpoint tests (`/health`, `/ask`, `/agent`, `/search/semantic`)
- [x] `tests/test_tools.py` — 12 agent tool tests (`led_resistor_calculator`, `rag_search`, `call_tool`)
- [x] `pyproject.toml` — ruff config (`select = E,W,F,I,UP`; `ignore = E501`) + pytest config
- [x] `ruff check .` → **All checks passed** (zero errors)
- [x] `pytest tests/ -v` → **44 passed** in 2.5 s
- [x] `Dockerfile` — multi-stage build (builder + runtime); non-root user
- [x] `.dockerignore` — excludes `.env`, `chroma_db/`, `hf_cache/`, venv, pycache
- [x] `docker-compose.yml` — `api` + `ui` services with health check, named volumes, env_file
- [x] `ui/app.py` updated — reads `ARDUINOMATE_API_URL` env var (Docker internal DNS)
- [x] `README.md` updated — **Run with Docker** section added
- [x] Git commit + push + `day-11` tag

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `tests/__init__.py` | Created | Package marker |
| `tests/conftest.py` | Created | Shared fixtures: fake LLM, TestClient, mock vector store |
| `tests/test_records.py` | Created | 7 record schema + integrity tests |
| `tests/test_search.py` | Created | 8 chunking and semantic search unit tests |
| `tests/test_api.py` | Created | 17 FastAPI endpoint tests with fake LLM |
| `tests/test_tools.py` | Created | 12 agent tool unit tests |
| `pyproject.toml` | Created | ruff + pytest configuration |
| `Dockerfile` | Created | Multi-stage image (builder + slim runtime) |
| `.dockerignore` | Created | Excludes secrets, cache, venv from image |
| `docker-compose.yml` | Created | `api` + `ui` services, volumes, health check |
| `ui/app.py` | Updated | `ARDUINOMATE_API_URL` env var support |
| `README.md` | Updated | **Run with Docker** section |
| `docs/day11/README.md` | Created | This file |

---

## S1 — Test Suite

### Test counts by file

| File | Tests | Coverage |
|------|-------|----------|
| `test_records.py` | 7 | records.json schema + integrity |
| `test_search.py` | 8 | chunking pipeline + mocked vector search |
| `test_api.py` | 17 | `/health`, `/ask`, `/agent`, `/search/semantic` |
| `test_tools.py` | 12 | `led_resistor_calculator`, `rag_search`, `call_tool` |
| **Total** | **44** | |

### Test result

```
============================= test session starts =============================
platform win32 -- Python 3.13, pytest-9.2.0
collected 44 items

tests/test_api.py .................                                      [ 38%]
tests/test_records.py .......                                            [ 54%]
tests/test_search.py ........                                            [ 72%]
tests/test_tools.py ............                                         [100%]
============================= 44 passed in 2.56s ==============================
```

### Fake LLM strategy

The LLM and ChromaDB are patched in `conftest.py` before the FastAPI app
imports, so no Groq API key or running server is needed:

```python
# conftest.py (simplified)
@pytest.fixture(scope="session")
def api_client(fake_llm_patch):
    with patch("app.vectorstore.query_collection", return_value=mock_hits), \
         patch("app.vectorstore.build_index", return_value=1):
        from main import app
        yield TestClient(app)
```

### ruff result

```
ruff check .
All checks passed!
```

Config in `pyproject.toml`:

```toml
[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP"]
ignore = ["E501", "UP007", "BLE001"]

exclude = ["ArduinoMate", "GEN_AI", "venv", "data", "docs"]
```

---

## S2 — Docker

### Architecture

```
docker compose up --build
        │
        ├── api  (port 8000)  python:3.11-slim
        │     uvicorn main:app --host 0.0.0.0 --port 8000
        │     volumes: chroma_data → /app/data/chroma_db
        │              hf_cache    → /app/.hf_cache
        │     healthcheck: GET /health every 30 s
        │
        └── ui   (port 8501)  python:3.11-slim
              streamlit run ui/app.py --server.port=8501
              depends_on: api (service_healthy)
              env: ARDUINOMATE_API_URL=http://api:8000
```

### Multi-stage Dockerfile

```
Stage 1 — builder
  python:3.11-slim + gcc/g++
  pip install --prefix=/install -r requirements.txt

Stage 2 — runtime
  python:3.11-slim (no build tools)
  COPY --from=builder /install /usr/local
  Non-root user: arduinomate
  Named volumes for chroma_db + hf_cache
```

### Named volumes

| Volume | Mounted at | Purpose |
|--------|-----------|---------|
| `chroma_data` | `/app/data/chroma_db` | Persist ChromaDB index across restarts |
| `hf_cache` | `/app/.hf_cache` | Persist sentence-transformers model weights |

---

## Run with Docker

See the **Run with Docker** section in the project README.

```bash
# 1. Copy and fill in your API key
cp .env.example .env
# Edit .env: set GROQ_API_KEY=your_key_here

# 2. Build images and start both services
docker compose up --build

# 3. Open in browser
#    API docs  → http://localhost:8000/docs
#    Chat UI   → http://localhost:8501
```

---

## Run Tests Locally

```bash
# Install deps (if not already installed)
pip install -r requirements.txt

# Run all 44 tests
pytest tests/ -v

# Run lint
ruff check .
```

---

## Technologies Used

- Python 3.11 / 3.13
- pytest 9.2 + pytest-anyio
- FastAPI TestClient (httpx-based)
- `unittest.mock.patch` — fake LLM + ChromaDB stubs
- ruff 0.17 — linter (E, W, F, I, UP rules)
- Docker + docker-compose v3.9
- python:3.11-slim base image
- Multi-stage build (builder + runtime)
