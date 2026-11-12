# Day 5 — LLM Fundamentals, Documentation, and Checkpoint 1

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Write clear LLM conceptual documentation, prepare 10 realistic user questions for ArduinoMate, verify all Checkpoint 1 requirements, and create the `checkpoint-1` and `week-1` Git tags.

---

## Tasks Completed

- [x] Created `docs/how_llms_work.md` — explains 9 LLM concepts + Mermaid diagram
- [x] Created `docs/user_questions.md` — 10 realistic user questions including one intentionally unanswerable
- [x] FastAPI verified: starts, `/health` works, `/docs` opens, `/records` returns 20 records, `/search` ranks results
- [x] Checkpoint 1 function explanation prepared (`digitalRead`)
- [x] Git tag `checkpoint-1` created
- [x] Git tag `week-1` created

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `docs/how_llms_work.md` | Created | 9 LLM concepts + Mermaid workflow diagram |
| `docs/user_questions.md` | Created | 10 user questions, Q6 intentionally unanswerable |
| `docs/day01/README.md` | Created | Day 1 documentation |
| `docs/day02/README.md` | Created | Day 2 documentation |
| `docs/day03/README.md` | Created | Day 3 documentation |
| `docs/day04/README.md` | Created | Day 4 documentation |
| `docs/day05/README.md` | Created | This file |

---

## LLM Concepts Documented (`docs/how_llms_work.md`)

1. What is an LLM?
2. How does an LLM work (pre-training + inference)?
3. What are tokens?
4. What are embeddings?
5. What is a prompt?
6. What is context (context window)?
7. What is an AI hallucination?
8. Traditional search vs. semantic search
9. How LLMs will be used in ArduinoMate (RAG pipeline)
10. Mermaid diagram of the full LLM workflow

---

## Checkpoint 1 — Arduino Function Explanation

### `digitalRead()` — Ready to Explain

**What it does:**  
`digitalRead(pin)` reads the electrical state of a digital pin and returns either `HIGH` (1) or `LOW` (0).

**Syntax:**  
```cpp
int value = digitalRead(7);  // Read pin 7
```

**Common gotcha:**  
If the pin is not configured with `pinMode()` beforehand, or if the pin is left physically unconnected, `digitalRead()` can return a random `HIGH` or `LOW` because the pin is "floating" — it picks up electrical noise from the environment.

**Fix:**  
Always call `pinMode(pin, INPUT)` or `pinMode(pin, INPUT_PULLUP)` in `setup()` before reading.

**Data source:**  
`data/raw/digitalRead.adoc` — downloaded from https://github.com/arduino/reference-en

---

## Checkpoint 1 Verification

| Check | Status |
|-------|--------|
| FastAPI starts | ✅ `uvicorn app.main:app --reload` |
| `GET /health` returns 200 | ✅ `{"status":"healthy","total_records":20}` |
| `GET /docs` opens Swagger UI | ✅ http://127.0.0.1:8000/docs |
| `GET /records` returns 20 records | ✅ All Arduino function records |
| `GET /search?q=digitalRead` ranks correctly | ✅ `digitalRead` score > 0.7 |
| Arduino function explained from stored data | ✅ `digitalRead()` above |
| 25 tests passing | ✅ `python tests/run_tests.py` |
| Git tag `checkpoint-1` | ✅ Created |
| Git tag `week-1` | ✅ Created |

---

## Technologies Used

- Python 3.13
- FastAPI 0.162+
- scikit-learn (TF-IDF + Cosine Similarity)
- pandas 3.1+
- Mermaid (diagram in Markdown)
- Git (tags)

---

## Commands to Run Day 5 Deliverables

```bash
# Verify FastAPI is healthy (server must be running first)
curl http://127.0.0.1:8000/health

# View LLM documentation
# Open docs/how_llms_work.md in any Markdown viewer

# View user questions
# Open docs/user_questions.md

# Start server for Checkpoint 1 demo
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run all tests
python tests/run_tests.py

# Check git tags
git tag -l
```

---

## Completion Status

Day 5 is fully complete. All documentation written, all checkpoint requirements verified, Git tags created, full Week 1 implementation committed and pushed.
