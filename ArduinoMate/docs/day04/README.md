# Day 4 — FastAPI Backend and Data Analysis

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Build a fully working FastAPI REST service with five endpoints, implement smart TF-IDF search, and analyse the dataset with Pandas to produce meaningful statistical insights.

---

## Tasks Completed

- [x] `app/main.py` — FastAPI app with 5 documented endpoints
- [x] `app/smart_search.py` — TF-IDF + Cosine Similarity engine with caching
- [x] `analysis/explore.py` — Pandas data exploration with 4 dynamic facts
- [x] All 5 endpoints tested and working
- [x] 404 handling on missing records
- [x] 400 handling on invalid limit parameter
- [x] Pydantic validation on POST /questions
- [x] 25 automated tests — all passing

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `app/main.py` | Complete | FastAPI app — 5 endpoints, CORS, lifespan |
| `app/smart_search.py` | Updated | TF-IDF engine updated for new record schema |
| `analysis/explore.py` | Updated | Pandas analysis updated for Arduino-function schema |
| `tests/test_api.py` | Updated | 14 endpoint tests updated for new schema |
| `tests/test_smart_search.py` | Updated | 8 search engine tests |
| `tests/test_explore.py` | Updated | 3 Pandas analysis tests |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health + record count |
| GET | `/records?limit=N` | All records, optional limit |
| GET | `/records/{id}` | Single record by ID, 404 if missing |
| GET | `/search?q=query&limit=N` | TF-IDF smart search |
| POST | `/questions` | Submit & validate a user question |

---

## How to Start the FastAPI Server

```bash
cd ArduinoMate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **API base URL:** http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc UI:** http://127.0.0.1:8000/redoc

---

## Example API Calls

### GET /health
```bash
curl http://127.0.0.1:8000/health
```
```json
{
  "status": "healthy",
  "service": "ArduinoMate API",
  "version": "1.0.0",
  "total_records": 20,
  "timestamp": "2026-11-12T10:00:00+00:00"
}
```

### GET /records?limit=2
```bash
curl "http://127.0.0.1:8000/records?limit=2"
```
```json
[
  {
    "function_name": "analogRead",
    "category": "Analog I/O",
    "syntax": "analogRead(pin)",
    "returns": "Integer 0-1023",
    "id": 1
  },
  {
    "function_name": "analogReference",
    "category": "Analog I/O",
    "syntax": "analogReference(type)",
    "id": 2
  }
]
```

### GET /search?q=digital pin read
```bash
curl "http://127.0.0.1:8000/search?q=digital+pin+read&limit=3"
```
```json
{
  "query": "digital pin read",
  "total_matches": 3,
  "results": [
    {
      "function_name": "digitalRead",
      "category": "Digital I/O",
      "similarity_score": 0.7823
    }
  ]
}
```

### POST /questions
```bash
curl -X POST http://127.0.0.1:8000/questions \
  -H "Content-Type: application/json" \
  -d '{"user_name":"Parth","question":"What does pinMode do?","category":"Digital I/O"}'
```
```json
{
  "message": "Question submitted successfully.",
  "question_id": 1,
  "data": {
    "id": 1,
    "user_name": "Parth",
    "question": "What does pinMode do?",
    "category": "Digital I/O",
    "created_at": "2026-11-12T10:05:00+00:00"
  }
}
```

---

## TF-IDF Smart Search — How It Works

1. All 20 Arduino records are vectorised using `TfidfVectorizer` (scikit-learn)
2. The vectoriser uses `ngram_range=(1,2)` to capture both single words and bigrams
3. When a query arrives, it is transformed using the **same** fitted vocabulary
4. Cosine similarity is computed between the query vector and all document vectors
5. Results are ranked highest-to-lowest and returned with `similarity_score`
6. The TF-IDF matrix is **cached** using an MD5 hash — recomputed only when records change

---

## Pandas Data Analysis Facts

Run `python analysis/explore.py` to see:

- **Fact 1:** Total records (20)
- **Fact 2:** Category distribution with bar chart
- **Fact 3:** Keyword coverage across function names, syntax, gotchas
- **Fact 4:** Gotcha/warning length statistics (avg, max, which function)

---

## Running Tests

```bash
# Run all 25 tests
python tests/run_tests.py

# Or with pytest
pytest tests/ -v
```

Expected result: **25 passed, 0 failed**

---

## Completion Status

Day 4 is fully complete. FastAPI starts successfully, all 5 endpoints work, TF-IDF search is live, Pandas analysis runs, all 25 tests pass.
