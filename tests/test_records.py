"""
tests/test_records.py — Arduino records data integrity tests.
-------------------------------------------------------------
Loads data/records.json (the 20-function knowledge base) and asserts
that every record has the required schema fields with non-empty values.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RECORDS_PATH = ROOT / "ArduinoMate" / "data" / "records.json"

REQUIRED_FIELDS = [
    "function_name",
    "category",
    "syntax",
    "returns",
    "common_gotcha",
    "source_url",
]

KNOWN_CATEGORIES = {
    "Digital I/O",
    "Analog I/O",
    "Time",
    "Math",
    "Advanced I/O",
    "Serial",
    "Interrupts",
}


@pytest.fixture(scope="module")
def records() -> list[dict]:
    """Load records.json once for the whole module."""
    assert RECORDS_PATH.exists(), f"records.json not found at {RECORDS_PATH}"
    data = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, list), "records.json must be a JSON array"
    return data


class TestRecordsSchema:
    """Records must conform to the ArduinoMate data schema."""

    def test_minimum_record_count(self, records):
        """Knowledge base must contain at least 20 Arduino function records."""
        assert len(records) >= 20, f"Expected >= 20 records, got {len(records)}"

    def test_all_required_fields_present(self, records):
        """Every record must have all six required schema fields."""
        for rec in records:
            for field in REQUIRED_FIELDS:
                assert field in rec, f"Record missing field '{field}': {rec}"

    def test_no_empty_function_names(self, records):
        """Every record must have a non-empty function_name."""
        for rec in records:
            assert rec["function_name"], f"Empty function_name in record: {rec}"

    def test_all_categories_are_known(self, records):
        """Every record's category must be one of the documented categories."""
        for rec in records:
            assert rec["category"] in KNOWN_CATEGORIES, (
                f"Unknown category '{rec['category']}' in record '{rec['function_name']}'"
            )

    def test_source_urls_are_strings(self, records):
        """source_url must be a non-empty string in every record."""
        for rec in records:
            assert isinstance(rec["source_url"], str) and rec["source_url"].strip(), (
                f"Invalid source_url in record '{rec['function_name']}'"
            )

    def test_function_names_are_unique(self, records):
        """No two records may share the same function_name."""
        names = [r["function_name"] for r in records]
        duplicates = {n for n in names if names.count(n) > 1}
        assert not duplicates, f"Duplicate function names found: {duplicates}"

    def test_category_distribution(self, records):
        """At least three different categories must be represented."""
        categories = {r["category"] for r in records}
        assert len(categories) >= 3, (
            f"Expected >= 3 categories, found {len(categories)}: {categories}"
        )
