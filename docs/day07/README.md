# Day 7 — Semantic Chunking, Embeddings, and Vector Store

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Build a full semantic retrieval pipeline on top of the ArduinoMate knowledge base:
chunk all source documents with structured metadata, embed them with
`sentence-transformers`, persist the index in ChromaDB, and expose a
`GET /search/semantic?q=` endpoint on the FastAPI server.

---

## Tasks Completed

- [x] `app/chunking.py` — load + chunk `.adoc` files and `records.json`; every chunk carries `source`, `page`, `title`, `category`
- [x] `app/embed.py` — `all-MiniLM-L6-v2` embedding engine; `semantic_search()` over raw chunk list
- [x] `app/vectorstore.py` — persistent ChromaDB collection; `build_index()` + `query_collection()`
- [x] `main.py` — `GET /search/semantic?q=` endpoint wired to ChromaDB
- [x] `schema.py` — `SemanticHit` + `SemanticSearchResponse` Pydantic models
- [x] `eval/search_results.md` — semantic search results for all 10 user questions
- [x] `app/llm.py` — updated default model from decommissioned `llama3-8b-8192` to `qwen/qwen3.8-27b`
- [x] Git commit + push + `day-7` tag

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `app/chunking.py` | Created | AsciiDoc + JSON chunker; Chunk dataclass with source/page/title/category |
| `app/embed.py` | Created | sentence-transformers embedding; `embed_texts`, `embed_query`, `semantic_search` |
| `app/vectorstore.py` | Created | ChromaDB persistent client; `build_index`, `query_collection` |
| `main.py` | Updated | Added `GET /search/semantic` endpoint + lifespan index build |
| `schema.py` | Updated | Added `SemanticHit`, `SemanticSearchResponse` |
| `app/llm.py` | Updated | Default model → `qwen/qwen3.8-27b` (llama3-8b-8192 decommissioned) |
| `eval/search_results.md` | Created | Search hits for 10 user questions |
| `requirements.txt` | Updated | Added chromadb, sentence-transformers |
| `.env.example` | Updated | Added HF_HOME note |

---

## Architecture

```
GET /search/semantic?q=
         │
         ▼  main.py → semantic_search_endpoint()
         │  Validates query string
         │
         ▼  app/vectorstore.py → query_collection()
         │  Embeds query via embed_query()
         │  Queries persistent ChromaDB collection
         │  Converts distances to cosine scores
         │
         ▼  SemanticSearchResponse (title, source, page, category, text, score)

─────────────────────────────────────────────
Build pipeline (runs once on startup):

data/raw/*.adoc  ──┐
                   ├─► app/chunking.py  ──► 109 Chunk objects
ArduinoMate/        │   (source, page,
data/records.json ──┘    title, category)
                              │
                              ▼
                   app/embed.py (all-MiniLM-L6-v2)
                   embed_texts() → (109, 384) float32
                              │
                              ▼
                   app/vectorstore.py
                   ChromaDB PersistentClient
                   data/chroma_db/ (SQLite + HNSW)
```

---

## Chunking Strategy

Each `.adoc` file is split on `=== Section` boundaries:
- Description
- Syntax / Parameters / Returns
- Example Code
- Notes and Warnings
- See Also

Each `records.json` entry generates 3 chunks:
- `description` field
- `syntax` + `returns` combined
- `common_gotcha` field

**Minimum chunk size:** 60 characters (shorter sections are merged)  
**Maximum chunk size:** 500 characters (longer sections split on sentence boundaries)  
**Total chunks produced:** 109

---

## Embedding Model

| Property | Value |
|----------|-------|
| Model | `all-MiniLM-L6-v2` |
| Dimensions | 384 |
| Normalisation | L2 unit-normalised (cosine similarity via dot product) |
| Cache location | `D:/hf_cache` (redirected from C: to avoid disk space issues) |
| Inference | Local (no API calls needed for embeddings) |

---

## Vector Store

| Property | Value |
|----------|-------|
| Engine | ChromaDB 1.5.9 |
| Collection name | `arduinomate_docs` |
| Index type | HNSW (cosine space) |
| Persistence path | `data/chroma_db/` |
| Rebuild trigger | `build_index(force_rebuild=True)` |
| Auto-build | On FastAPI startup if collection is empty |

---

## API Endpoints (Day 7)

### GET /search/semantic

```
GET /search/semantic?q=delay+vs+millis&limit=5
```

**Response:**
```json
{
  "query": "delay vs millis",
  "total_results": 3,
  "results": [
    {
      "title": "attachInterrupt()",
      "source": "ArduinoMate/data/raw/attachInterrupt.adoc",
      "page": 5,
      "category": "External Interrupts",
      "text": "An ISR cannot have any parameters, and they shouldn't return anything...",
      "score": 0.785
    },
    {
      "title": "delay()",
      "source": "ArduinoMate/data/raw/delay.adoc",
      "page": 5,
      "category": "Time",
      "text": "For alternative approaches to controlling timing see the Blink Without Delay sketch...",
      "score": 0.734
    }
  ]
}
```

---

## Setup

### Install new dependencies
```bash
pip install -r requirements.txt
```

### Set HF_HOME (optional — avoids filling C: drive)
Add to `.env`:
```
HF_HOME=D:/hf_cache
```

### Start server (index builds automatically on first run)
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Force rebuild the vector index
```bash
python -c "from app.vectorstore import build_index; build_index(force_rebuild=True)"
```

---

## Semantic Search Results Summary

See `eval/search_results.md` for full results.

| Q | Top hit | Score | Correct? |
|---|---------|-------|----------|
| Q1 — pinMode | pinMode() | 0.361 | ✅ |
| Q2 — digitalRead button | pinMode (INPUT_PULLUP) | 0.757 | ✅ |
| Q3 — delay vs millis | delay()/millis() | 0.785 | ✅ |
| Q4 — PWM analogWrite | analogWrite() | 0.793 | ✅ |
| Q5 — analogRead floating | analogRead() notes | 0.819 | ✅ |
| Q6 — HC-SR04 (out of scope) | pulseIn (low score) | 0.422 | ✅ |
| Q7 — serial baud rate | Serial.begin() | 0.848 | ✅ |
| Q8 — attachInterrupt ISR | attachInterrupt | 0.754 | ✅ |
| Q9 — map vs constrain | map gotcha | 0.804 | ✅ |
| Q10 — random seed | random gotcha | 0.805 | ✅ |

**10/10 correct | Average score: 0.754**

---

## Technologies Used

- Python 3.13
- sentence-transformers 6.3.0 (`all-MiniLM-L6-v2`)
- ChromaDB 1.5.9 (persistent HNSW index)
- FastAPI 0.110+
- Pydantic v2
- Groq SDK (`qwen/qwen3.8-27b`)

---

## Commands

```bash
# Start the server
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Test semantic search
curl "http://127.0.0.1:8000/search/semantic?q=how+to+read+a+button&limit=3"

# Test chat
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"What does pinMode do?\", \"task\": \"explain\"}"

# Check health (shows indexed_chunks count)
curl http://127.0.0.1:8000/health
```
