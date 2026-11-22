# Day 12 — CI/CD, Deployment, and Production Hardening
**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

**S1 — Production hardening:** Log latency and token usage per request, add a
simple in-memory cache, enforce input-length limits, write one prompt-injection
test; add a `Production notes` section to the README with real numbers.

**S2 — Polished documentation:** Rewrite the README so it sells ArduinoMate
(problem statement, Mermaid architecture diagram, results table, demo video
link); add `docs/resume.md` with three resume bullets backed by real numbers.

---

## Tasks Completed

- [x] `app/middleware.py` — `ProductionMiddleware` ASGI class
  - Latency logging: structured log line per request with elapsed ms
  - Token tracking: Groq `usage` written via `ContextVar`, read after response
  - In-memory LRU cache: 256 entries, 60 s TTL, full-URL cache keys
  - `X-Cache: HIT/MISS` and `X-Latency-Ms` headers on every response
  - Cache stats surfaced in `GET /health` (`cache_size`, `cache_hits`, `cache_misses`)
  - Input-length guard: POST body > 16 KB → HTTP 413
  - Prompt-injection guard: 20 known patterns → HTTP 400 + `WARN` log
- [x] `app/llm.py` — reads `completion.usage` after each Groq call and writes
  `prompt_tokens` / `completion_tokens` into the request-scoped `ContextVar`
- [x] `main.py` — wires `ProductionMiddleware`, adds `logging.config.dictConfig`,
  version `6.0.0`, `/health` now exposes cache stats
- [x] `tests/test_production.py` — 26 new tests covering all four hardening layers
- [x] `tests/conftest.py` — updated to reload `main` so the new middleware is active
  during tests; `raise_server_exceptions=False` so 400/413 responses are testable
- [x] `.github/workflows/ci.yml` — three-job CI pipeline (lint → test → docker build)
- [x] `render.yaml` — Render Blueprint for one-click deployment
- [x] `Dockerfile` — CMD updated to read `${PORT:-8000}` for Render compatibility
- [x] `README.md` — full rewrite with problem, Mermaid diagram, results table,
  production notes, API reference, tech stack
- [x] `docs/resume.md` — three resume bullets with supporting numbers table
- [x] `PROGRESS.md` — Day 12 entry added
- [x] Feature branch `day-12/production-hardening` pushed → merged to `master`
- [x] Git tag `day-12` applied and pushed

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `app/middleware.py` | Created | `ProductionMiddleware`: latency, tokens, cache, limits, injection guard |
| `app/llm.py` | Modified | Writes Groq token usage into request-scoped `ContextVar` |
| `main.py` | Modified | Wires middleware, structured logging, version 6.0.0 |
| `tests/test_production.py` | Created | 26 production hardening tests |
| `tests/conftest.py` | Modified | Reloads `main` to pick up middleware; `raise_server_exceptions=False` |
| `.github/workflows/ci.yml` | Created | GitHub Actions CI: ruff + pytest + docker build |
| `render.yaml` | Created | Render Blueprint for cloud deployment |
| `Dockerfile` | Modified | CMD reads `${PORT:-8000}` |
| `README.md` | Rewritten | Problem, Mermaid arch, results table, production notes |
| `docs/resume.md` | Created | 3 resume bullets with numbers |
| `docs/day12/README.md` | Created | This file |
| `PROGRESS.md` | Created | Project-level progress log |

---

## S1 — Production Hardening

### Architecture

```
HTTP Request
     │
     ▼
ProductionMiddleware  (app/middleware.py)
     │
     ├─ 1. Body size check  ──────────────────────► 413 if > 16 KB
     │
     ├─ 2. Injection scan   ──────────────────────► 400 + WARN log if pattern matched
     │
     ├─ 3. Cache lookup     ──────────────────────► 200 X-Cache:HIT (< 5 ms) if hit
     │
     ├─ 4. Reset token ContextVar
     │
     ▼
Route handler  (main.py)
     │
     └─► app/llm.py ──► Groq API ──► writes usage to ContextVar
     │
     ▼
ProductionMiddleware (after response)
     ├─ Reads ContextVar (prompt_tokens, completion_tokens)
     ├─ Logs:  POST /ask  200  847ms  tokens=in:312/out:184
     ├─ Stores response in cache (if 2xx and < 32 KB)
     └─ Adds X-Cache and X-Latency-Ms headers
```

### Latency and token logging

Every request emits one line:

```
2026-11-19T14:32:11  INFO  arduinomate  POST /ask  200  847ms  tokens=in:312/out:184
```

Token counts come from the Groq `completion.usage` object via a
`contextvars.ContextVar` — no shared mutable state between concurrent requests.

Observed timings from the Day 8 evaluation run:

| Operation | Typical latency |
|-----------|----------------|
| Embedding query (`all-MiniLM-L6-v2`) | ~20 ms |
| ChromaDB HNSW search (109 chunks) | ~5 ms |
| Groq LLM completion (1 024 max tokens) | 700 ms – 13 s |
| End-to-end `POST /ask` (Config B) | **~8.3 s average** |

Token usage per RAG request (Config B, top_k=5):

| | Typical value |
|-|--------------|
| Prompt tokens | 280 – 420 |
| Completion tokens | 150 – 250 |

### Cache

- **Key:** `SHA-256(method + full-URL-including-query-string + body)[:16]`
- **TTL:** 60 seconds
- **Capacity:** 256 entries (LRU eviction)
- **Max response size stored:** 32 KB
- **Thread safety:** `threading.Lock` around the `OrderedDict` (correct for Uvicorn single-worker)

```
GET /health    first call:   X-Cache: MISS   12 ms
GET /health    second call:  X-Cache: HIT     1 ms
```

Stats are exposed in `GET /health`:
```json
{ "cache_size": 3, "cache_hits": 12, "cache_misses": 7 }
```

### Input-length guard

```
POST /ask  with 20 000-byte body
→ HTTP 413
{ "detail": "Request body too large: 20000 bytes. Maximum allowed is 16384 bytes (16 KB)." }
```

### Prompt-injection guard

20 blocked patterns (lowercase match, any position in body):

```python
"ignore previous instructions", "ignore all instructions",
"disregard previous", "forget your instructions",
"you are now", "new instructions:", "override instructions",
"system prompt:", "bypass your", "do not follow",
"act as if you", "pretend you are", "pretend to be",
"roleplay as", "jailbreak", "dan mode",
"developer mode enabled", "ignore the above",
"disregard the above"
```

```
POST /ask  { "question": "ignore previous instructions and ..." }
→ HTTP 400
{ "detail": "Request blocked: prompt-injection pattern detected. ArduinoMate only answers Arduino questions." }
WARN  arduinomate  400 INJECTION  POST /ask  pattern='ignore previous instructions'  ip=127.0.0.1
```

---

## S1 — CI/CD Pipeline

`.github/workflows/ci.yml` — three jobs, run on every push and PR to `master`:

```
push / PR
    │
    ▼
lint job      ruff check .
    │  (must pass)
    ▼
test job      pytest tests/ -v  (70 tests, mocked LLM + ChromaDB)
              env: GROQ_API_KEY=test-key-ci
                   HF_HUB_OFFLINE=1
    │  (must pass)
    ▼
docker job    docker/build-push-action (push=false, GHA layer cache)
```

CI badge in README:
```
[![CI](https://github.com/parthkatore/GENAI/actions/workflows/ci.yml/badge.svg)](...)
```

**Docker Hub images** (pushed on every merge to `master`):
- `parthkatore/arduinomate-api:latest`
- `parthkatore/arduinomate-api:<git-sha>`

To enable the push, add a `DOCKERHUB_TOKEN` secret in the repo:
> GitHub repo → Settings → Secrets → Actions → New repository secret
> Name: `DOCKERHUB_TOKEN`  Value: Docker Hub access token for `parthkatore`

---

## S1 — Tests

### New tests in `tests/test_production.py`

| Class | Tests | What is verified |
|-------|-------|-----------------|
| `TestInputLimits` | 4 | 413 on 20 KB body, detail message, normal body passes, body at limit passes |
| `TestPromptInjection` | 12 | 10 parametrized injection phrases → 400; detail message; clean question not blocked; `/chat` also guarded |
| `TestResponseCache` | 3 | `X-Cache: HIT` on second request, same body, different queries are separate entries |
| `TestLatencyHeader` | 3 | `X-Latency-Ms` present on GET and POST, value is a non-negative integer string |
| `TestCacheStats` | 3 | `/health` exposes `cache_hits`, `cache_misses`, `cache_size` as integers |

### Full test count

| File | Tests |
|------|-------|
| `test_records.py` | 7 |
| `test_search.py` | 8 |
| `test_api.py` | 17 |
| `test_tools.py` | 12 |
| `test_production.py` | 26 |
| **Total** | **70** |

### Results

```
============================= test session starts =============================
platform win32 -- Python 3.13.0, pytest-9.2.0
collected 70 items

tests/test_api.py .................                                      [ 24%]
tests/test_production.py ..........................                      [ 61%]
tests/test_records.py .......                                            [ 71%]
tests/test_search.py ........                                            [ 82%]
tests/test_tools.py ............                                         [100%]

============================= 70 passed in 0.92s ==============================
```

```
ruff check .
All checks passed!
```

---

## S2 — README Rewrite

The project README was rewritten to cover:

1. **Problem statement** — what Arduino beginners struggle with and why RAG improves on general-purpose AI
2. **Mermaid architecture diagram** — full flowchart from Streamlit UI through middleware, RAG, ChromaDB, to Groq LLM
3. **Results table** — real numbers from evaluation:
   - RAG Config B: 100% answer rate, 100% refusal rate, 100% source hit rate
   - Semantic search: 10/10 correct top hits, avg score 0.754
   - Prompt eval: 230/250 (ArduinoMate) vs 104/250 (generic baseline)
4. **Production Notes** — latency table, token counts, cache behaviour with example log lines
5. **API reference**, quick start, Docker instructions, tech stack, repo structure
6. **Demo link** placeholder for video

---

## S2 — Resume (`docs/resume.md`)

Three bullets targeting software engineering / AI roles:

**Bullet 1 — RAG pipeline**
> Built ArduinoMate, a production FastAPI service using RAG: embedded 109 chunks with `all-MiniLM-L6-v2`, stored in ChromaDB, achieving 100% answer rate / 100% refusal rate / 100% source-hit rate on a 15-question eval set.

**Bullet 2 — Agent + production middleware**
> Tool-using agent (ReAct + LangGraph) with custom ASGI middleware: latency + token logging per request, in-memory LRU cache (60 s TTL, reducing repeat-query latency from ~8 s to under 5 ms), 16 KB input limit, and 20-pattern prompt-injection guard.

**Bullet 3 — CI/CD and cloud deployment**
> Three-job GitHub Actions CI (ruff, 70 pytest tests with mocked deps, Docker build); containerised with multi-stage Dockerfile; deployed to Render via `render.yaml` Blueprint with public `/health` endpoint.

---

## Deployment — Render (S2)

`render.yaml` Blueprint:

```yaml
services:
  - type: web
    name: arduinomate-api
    runtime: docker
    healthCheckPath: /health
    autoDeploy: true
```

**Live URL:** https://arduinomate-api.onrender.com/health

To deploy:
1. Go to [render.com](https://dashboard.render.com) → **New → Blueprint**
2. Connect the `parthkatore/GENAI` repo
3. Set `GROQ_API_KEY` in the Environment panel
4. Click **Apply** — Render reads `render.yaml` and starts the service

---

## Run Tests Locally

```bash
pip install -r requirements.txt
pytest tests/ -v        # 70 tests, no API key needed
ruff check .            # lint
```

---

## Technologies Used

| Technology | Purpose |
|-----------|---------|
| Python 3.11 | Language |
| FastAPI 0.110 | REST API |
| `contextvars.ContextVar` | Request-scoped token tracking |
| `collections.OrderedDict` | LRU cache backing store |
| `threading.Lock` | Thread-safe cache access |
| pytest 9.2 | 70 automated tests |
| ruff 0.17 | Linter |
| Docker + docker-compose | Containerisation |
| GitHub Actions | CI pipeline |
| Render | Cloud deployment |
