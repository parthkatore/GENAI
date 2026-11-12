# Day 2 — Arduino Reference Records

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Build the ArduinoMate knowledge base by storing 20 official Arduino functions as structured Python dictionaries, and implement four reusable functions to work with the data. Refactor the code into a proper `app/` package with `records.py` and `cli.py`.

---

## Tasks Completed

- [x] Created `data/sample_records.py` with **20 Arduino functions** as list of dicts
- [x] Each record contains: `function_name`, `category`, `syntax`, `returns`, `common_gotcha`, `source_url`
- [x] Created `app/records.py` with `load_records()`, `search()`, `count_by()`, `get_by_id()`
- [x] Created `app/cli.py` with a full 4-option interactive command-line interface
- [x] Created Python virtual environment (`.venv`)
- [x] Created/updated `requirements.txt` and `.gitignore`

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `data/sample_records.py` | Created | 20 Arduino function records as list of dicts |
| `app/records.py` | Created | `load_records`, `search`, `count_by`, `get_by_id` |
| `app/cli.py` | Created | Interactive CLI using the records module |
| `requirements.txt` | Updated | All project dependencies pinned |
| `.gitignore` | Updated | Excludes `.venv`, `__pycache__`, `.env` |

---

## 20 Arduino Functions Stored

| # | Function | Category |
|---|----------|----------|
| 1 | `pinMode` | Digital I/O |
| 2 | `digitalRead` | Digital I/O |
| 3 | `digitalWrite` | Digital I/O |
| 4 | `analogRead` | Analog I/O |
| 5 | `analogWrite` | Analog I/O |
| 6 | `analogReference` | Analog I/O |
| 7 | `delay` | Time |
| 8 | `delayMicroseconds` | Time |
| 9 | `millis` | Time |
| 10 | `micros` | Time |
| 11 | `map` | Math |
| 12 | `constrain` | Math |
| 13 | `tone` | Advanced I/O |
| 14 | `noTone` | Advanced I/O |
| 15 | `pulseIn` | Advanced I/O |
| 16 | `Serial.begin` | Serial |
| 17 | `Serial.print` | Serial |
| 18 | `Serial.read` | Serial |
| 19 | `attachInterrupt` | Interrupts |
| 20 | `random` | Math |

---

## Concepts Learned

- Structuring data as a list of dictionaries
- Writing reusable functions with clear parameters and return types
- Separating data (`sample_records.py`) from logic (`records.py`) from UI (`cli.py`)
- Python package layout with `__init__.py`
- Virtual environments and `requirements.txt`

---

## Technologies Used

- Python 3.13 (built-in only for Day 2)

---

## Commands to Run

```bash
# Run the CLI directly
python -m app.cli

# Or run the sample records script standalone
python data/sample_records.py
```

---

## Sample Output — CLI Option 3 (Count by Category)

```
  Category Distribution:
    Advanced I/O          :  3  ███
    Analog I/O            :  3  ███
    Digital I/O           :  3  ███
    Interrupts            :  1  █
    Math                  :  3  ███
    Serial                :  3  ███
    Time                  :  4  ████
```

---

## Sample Output — CLI Option 2 (Search)

```
  Enter search keyword: delay
  Found 3 result(s) for 'delay':
    → delay  [Time]
      delay(ms)
    → delayMicroseconds  [Time]
      delayMicroseconds(us)
    → millis  [Time]
      millis()
```

---

## Completion Status

Day 2 is fully complete. All 20 records present, all 4 functions verified, CLI runs without errors.
