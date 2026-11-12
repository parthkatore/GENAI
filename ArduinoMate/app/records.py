"""
ArduinoMate - Day 2: Records Module (app/records.py)
-----------------------------------------------------
Student  : Parth Dasharath Katore
Enroll   : 2124UCEM2079
Roll No  : 53

Provides four reusable functions to work with the Arduino reference
records stored in data/sample_records.py:

    load_records()   – return all 20 records
    search(keyword)  – keyword search across all fields
    count_by(field)  – count records grouped by a field (default: category)
    get_by_id(id)    – fetch one record by 1-based position id
"""

import sys
from pathlib import Path

# ── Ensure ArduinoMate root is importable regardless of CWD ──────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data.sample_records import records as _RAW_RECORDS


# ── Public API ────────────────────────────────────────────────────────────────

def load_records() -> list:
    """
    Return all 20 Arduino function records.

    Returns
    -------
    list[dict]
        A fresh copy of the master records list.
    """
    return list(_RAW_RECORDS)


def search(keyword: str) -> list:
    """
    Search all records for a keyword (case-insensitive).

    Parameters
    ----------
    keyword : str
        Word or phrase to look for across all fields.

    Returns
    -------
    list[dict]
        Records that contain the keyword in any field.
        Returns an empty list if no match or blank keyword.
    """
    if not keyword or not keyword.strip():
        print("  Search keyword cannot be empty.")
        return []

    kw = keyword.strip().lower()
    results = []

    for rec in _RAW_RECORDS:
        combined = " ".join(str(v) for v in rec.values()).lower()
        if kw in combined:
            results.append(rec)

    return results


def count_by(field: str = "category") -> dict:
    """
    Count records grouped by the given field.

    Parameters
    ----------
    field : str
        Dictionary key to group by. Defaults to "category".

    Returns
    -------
    dict  { field_value: count }
    """
    counts: dict = {}

    for rec in _RAW_RECORDS:
        value = rec.get(field, "Unknown")
        counts[value] = counts.get(value, 0) + 1

    return counts


def get_by_id(record_id: int):
    """
    Retrieve a record by its 1-based index ID.

    Parameters
    ----------
    record_id : int
        1-based record ID (1 = first record, 20 = last).

    Returns
    -------
    dict  if found, else None
    """
    if not isinstance(record_id, int) or record_id < 1 or record_id > len(_RAW_RECORDS):
        return None

    return _RAW_RECORDS[record_id - 1]
