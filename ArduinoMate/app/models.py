"""
ArduinoMate - Day 3: Record Dataclass (app/models.py)
------------------------------------------------------
Student  : Parth Dasharath Katore
Enroll   : 2124UCEM2079
Roll No  : 53

Defines the Record dataclass used throughout the pipeline:
  fetch.py  → ingest.py  → records.json  → main.py
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Record:
    """
    Represents a single Arduino reference record.

    Fields
    ------
    id            : Unique integer identifier (auto-assigned during ingest).
    function_name : Official Arduino function name, e.g. "digitalRead".
    category      : Functional category, e.g. "Digital I/O".
    syntax        : Full function signature string.
    returns       : Description of the return value.
    common_gotcha : Common mistake or important caveat to remember.
    source_url    : URL of the official Arduino documentation page.
    description   : Optional longer description parsed from the .adoc file.
    """

    function_name : str
    category      : str
    syntax        : str
    returns       : str
    common_gotcha : str
    source_url    : str
    id            : int            = 0
    description   : Optional[str] = field(default=None)

    # ── Convenience helpers ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Convert this record to a plain Python dictionary."""
        return asdict(self)

    def is_valid(self) -> bool:
        """
        Return True when all required text fields are non-empty.
        Used by ingest.py to skip incomplete records.
        """
        required = [self.function_name, self.category, self.syntax,
                    self.returns, self.common_gotcha, self.source_url]
        return all(isinstance(f, str) and f.strip() for f in required)

    @classmethod
    def from_dict(cls, data: dict) -> "Record":
        """
        Build a Record from a dictionary.
        Unknown keys are silently ignored.
        """
        return cls(
            id            = int(data.get("id", 0)),
            function_name = str(data.get("function_name", "")).strip(),
            category      = str(data.get("category", "")).strip(),
            syntax        = str(data.get("syntax", "")).strip(),
            returns       = str(data.get("returns", "")).strip(),
            common_gotcha = str(data.get("common_gotcha", "")).strip(),
            source_url    = str(data.get("source_url", "")).strip(),
            description   = data.get("description"),
        )
