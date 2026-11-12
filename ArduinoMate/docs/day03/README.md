# Day 3 — Real Arduino Documentation Ingestion

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Download real Arduino reference documentation from the official GitHub repository, parse the AsciiDoc format, extract structured data, and save it as `data/records.json`. Build a production-quality ingest pipeline with error handling.

---

## Tasks Completed

- [x] Created `app/fetch.py` — downloads 10 `.adoc` files from `github.com/arduino/reference-en`
- [x] Created `app/ingest.py` — parses AsciiDoc, cleans markup, merges with `sample_records.py`
- [x] Created `app/models.py` — `Record` dataclass with `to_dict()`, `from_dict()`, `is_valid()`
- [x] Downloaded 10 real Arduino documentation files into `data/raw/`
- [x] Generated `data/records.json` with **20 clean records**
- [x] All fetching includes: request timeouts, HTTP error handling, connection error handling, 3-attempt retry logic

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `app/fetch.py` | Created | Downloads 10 `.adoc` files with retry & error handling |
| `app/ingest.py` | Created | Parses AsciiDoc → Record objects → `records.json` |
| `app/models.py` | Updated | `Record` dataclass with validation helpers |
| `data/records.json` | Generated | 20 structured Arduino function records |
| `data/raw/*.adoc` | Downloaded | 10 official Arduino documentation files |

---

## Documentation Files Downloaded

| File | Arduino Function | URL |
|------|-----------------|-----|
| `digitalRead.adoc` | `digitalRead()` | Language/Functions/Digital IO/ |
| `digitalWrite.adoc` | `digitalWrite()` | Language/Functions/Digital IO/ |
| `pinMode.adoc` | `pinMode()` | Language/Functions/Digital IO/ |
| `analogRead.adoc` | `analogRead()` | Language/Functions/Analog IO/ |
| `analogWrite.adoc` | `analogWrite()` | Language/Functions/Analog IO/ |
| `delay.adoc` | `delay()` | Language/Functions/Time/ |
| `millis.adoc` | `millis()` | Language/Functions/Time/ |
| `Serial_begin.adoc` | `Serial.begin()` | Language/Functions/Communication/Serial/ |
| `Serial_print.adoc` | `Serial.print()` | Language/Functions/Communication/Serial/ |
| `attachInterrupt.adoc` | `attachInterrupt()` | Language/Functions/External Interrupts/ |

---

## Record Schema (JSON)

```json
{
  "function_name": "digitalRead",
  "category": "Digital I/O",
  "syntax": "digitalRead(pin)",
  "returns": "HIGH or LOW",
  "common_gotcha": "If the pin isn't connected to anything, digitalRead() can return either HIGH or LOW randomly.",
  "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/digitalread/",
  "id": 7,
  "description": "Reads the value from a specified digital pin, either HIGH or LOW."
}
```

---

## Ingest Pipeline Architecture

```
data/raw/*.adoc
      │
      ▼  parse_adoc()   — extract title, syntax, returns, description, notes
      │  _clean_adoc()  — strip AsciiDoc markup artifacts
      ▼
list[Record]  (from docs)
      +  sample_records.py  (fills gaps for un-downloaded functions)
      ▼  merge_with_samples() — deduplicate, sort, assign IDs
      ▼  _sanitize_record()  — final cleanup pass
      ▼
data/records.json  (20 clean records)
```

---

## Error Handling Implemented

| Scenario | Handling |
|----------|----------|
| Network timeout (>20s) | Logs error, retries up to 3 times |
| HTTP 4xx / 5xx | Logs and skips that file (no retry) |
| Connection refused | Retries with 2-second delay between attempts |
| Malformed / empty `.adoc` | `try/except` in parser, record skipped if invalid |
| Missing required fields | `Record.is_valid()` check before saving |

---

## Concepts Learned

- HTTP requests with `requests` library (timeouts, raise_for_status)
- Retry logic with exponential-style back-off
- Parsing structured text formats with `re` (regex)
- Python `dataclass` for clean, typed data structures
- JSON serialisation with `json.dump` / `json.load`
- Separation of download, parse, and persist responsibilities

---

## Technologies Used

- `requests` — HTTP downloads
- `re` (built-in) — AsciiDoc parsing
- `dataclasses` (built-in) — `Record` model
- `json` (built-in) — persistence
- `pathlib` (built-in) — file paths

---

## Commands to Run

```bash
# Step 1: Download all documentation files
python app/fetch.py

# Step 2: Parse docs and generate records.json
python app/ingest.py
```

---

## Sample Ingest Output

```
=======================================================
  ARDUINOMATE INGEST PIPELINE
=======================================================
  Found 10 .adoc file(s) in data/raw
  ✓  Parsed: analogRead  (Analog I/O)
  ✓  Parsed: analogWrite  (Analog I/O)
  ✓  Parsed: attachInterrupt  (Interrupts)
  ✓  Parsed: delay  (Time)
  ✓  Parsed: digitalRead  (Digital I/O)
  ✓  Parsed: digitalWrite  (Digital I/O)
  ✓  Parsed: millis  (Time)
  ✓  Parsed: pinMode  (Digital I/O)
  ✓  Parsed: Serial.begin  (Serial)
  ✓  Parsed: Serial.print  (Serial)

  ✓  Saved 20 records → data/records.json

  Pipeline complete — 20 total records ready.
=======================================================
```

---

## Completion Status

Day 3 is fully complete. 10 real Arduino documents downloaded, 20 records generated, full error handling in place.
