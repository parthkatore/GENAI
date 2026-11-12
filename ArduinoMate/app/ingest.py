"""
ArduinoMate - Day 3: Documentation Ingestor (app/ingest.py)
------------------------------------------------------------
Student  : Parth Dasharath Katore
Enroll   : 2124UCEM2079
Roll No  : 53

Reads every .adoc file from  data/raw/,  parses the structured
AsciiDoc sections (title, description, syntax, returns, notes),
and merges the result with the hand-curated sample_records.py
data to produce a rich  data/records.json  containing all 20
Arduino reference records.

Pipeline:
  data/raw/*.adoc
      ↓  parse_adoc()
  list[Record]  (from docs)
      +  sample_records.py  (fills gaps)
      ↓  merge & deduplicate
  data/records.json
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Optional

# ── Path setup ────────────────────────────────────────────────────────────────
_ROOT   = Path(__file__).resolve().parent.parent
RAW_DIR = _ROOT / "data" / "raw"
OUT_FILE = _ROOT / "data" / "records.json"

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.models import Record
from data.sample_records import records as SAMPLE_RECORDS

# ── ADOC filename  →  metadata mapping ───────────────────────────────────────
# This tells the parser which category and source URL to assign to each file.
ADOC_META = {
    "digitalRead.adoc": {
        "category": "Digital I/O",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/digitalread/",
    },
    "digitalWrite.adoc": {
        "category": "Digital I/O",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/digitalwrite/",
    },
    "pinMode.adoc": {
        "category": "Digital I/O",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/pinmode/",
    },
    "analogRead.adoc": {
        "category": "Analog I/O",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/analog-io/analogread/",
    },
    "analogWrite.adoc": {
        "category": "Analog I/O",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/analog-io/analogwrite/",
    },
    "delay.adoc": {
        "category": "Time",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/delay/",
    },
    "millis.adoc": {
        "category": "Time",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/time/millis/",
    },
    "Serial_begin.adoc": {
        "category": "Serial",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/begin/",
    },
    "Serial_print.adoc": {
        "category": "Serial",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/print/",
    },
    "attachInterrupt.adoc": {
        "category": "Interrupts",
        "source_url": "https://docs.arduino.cc/language-reference/en/functions/external-interrupts/attachinterrupt/",
    },
}


# ── AsciiDoc Parser ───────────────────────────────────────────────────────────

def _clean_adoc(raw: str) -> str:
    """
    Strip common AsciiDoc / markup artifacts from a parsed section body.
    """
    # Remove source-code listing blocks  ---- ... ----
    raw = re.sub(r"----.*?----", "", raw, flags=re.DOTALL)
    # Remove [float], [%hardbreaks], [source,arduino], [options=...], etc.
    raw = re.sub(r"\[.*?\]", "", raw)
    # Remove table syntax lines starting with |
    raw = re.sub(r"^\s*\|.*$", "", raw, flags=re.MULTILINE)
    # Remove AsciiDoc attribute references like link:...[...]
    raw = re.sub(r"link:[^\[]+\[([^\]]*)\]", r"\1", raw)
    # Remove bare link: references without labels
    raw = re.sub(r"link:[^\s,]+", "", raw)
    # Remove http(s) links with label  http://....[label]
    raw = re.sub(r"https?://\S+\[([^\]]*)\]", r"\1", raw)
    # Remove bare http(s) URLs
    raw = re.sub(r"https?://\S+", "", raw)
    # Remove section markers:  // OVERVIEW SECTION STARTS  etc.
    raw = re.sub(r"//.*", "", raw)
    # Remove standalone -- and ++ markers (AsciiDoc block delimiters)
    raw = re.sub(r"\s--\s", " ", raw)
    raw = re.sub(r"^\s*--\s*$", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"^\s*\+\+\s*$", "", raw, flags=re.MULTILINE)
    # Remove section heading lines that leaked in
    raw = re.sub(r"^\s*\[#\w+\]\s*$", "", raw, flags=re.MULTILINE)
    # Remove AsciiDoc markup:  *text*  → text,  `text` → text
    raw = re.sub(r"\*([^*]+)\*", r"\1", raw)
    raw = re.sub(r"`([^`]+)`", r"\1", raw)
    # Collapse multiple spaces / newlines into a single space
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def _extract_section(text: str, section_name: str) -> Optional[str]:
    """
    Extract the content of a named AsciiDoc section.
    Looks for  === <section_name>  followed by body lines.
    """
    # Match  === Description  or  === Syntax  etc. (case-insensitive)
    pattern = re.compile(
        rf"===\s+{re.escape(section_name)}\s*\n(.*?)(?===|\Z)",
        re.IGNORECASE | re.DOTALL
    )
    match = pattern.search(text)
    if not match:
        return None

    raw = match.group(1).strip()
    cleaned = _clean_adoc(raw)
    return cleaned or None


def _extract_title(text: str) -> Optional[str]:
    """Extract the function name from the top-level = Title line."""
    match = re.search(r"^=\s+(.+?)\s*$", text, re.MULTILINE)
    if match:
        name = match.group(1).strip()
        # Remove trailing () — we store just the name token
        return re.sub(r"\(\)$", "", name).strip()
    return None


def parse_adoc(filepath: Path) -> Optional[Record]:
    """
    Parse a single .adoc file and return a Record object.

    Returns None if the file is unreadable or missing required fields.
    Uses the ADOC_META dict for category and source_url.
    """
    try:
        raw_text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ingest] Cannot read {filepath.name}: {e}")
        return None

    meta      = ADOC_META.get(filepath.name, {})
    category  = meta.get("category", "General")
    source_url = meta.get("source_url", "")

    function_name = _extract_title(raw_text)
    description   = _extract_section(raw_text, "Description")
    syntax        = _extract_section(raw_text, "Syntax")
    returns       = _extract_section(raw_text, "Returns")
    notes         = _extract_section(raw_text, "Notes and Warnings")

    # Fallbacks when sections are missing
    if not function_name:
        # Try deriving from filename: "Serial_begin.adoc" → "Serial.begin"
        stem = filepath.stem.replace("_", ".")
        function_name = stem
    else:
        # For Serial sub-functions the title is just "begin()" or "print()"
        # but the filename encodes the full name e.g. "Serial_begin.adoc"
        if filepath.stem.startswith("Serial_"):
            # e.g. Serial_begin → Serial.begin
            full_name = filepath.stem.replace("_", ".", 1)
            function_name = full_name

    if not syntax:
        syntax = f"{function_name}(...)"

    if not returns:
        returns = "See documentation"

    if not description:
        description = f"See official Arduino documentation for {function_name}."

    # Build a plain-English gotcha from notes/warnings section
    if notes:
        cleaned_notes = _clean_adoc(notes)
        # Take first 2 sentences max for a concise gotcha
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned_notes) if s.strip()]
        gotcha = " ".join(sentences[:2])
        if len(gotcha) > 240:
            gotcha = gotcha[:237] + "…"
    else:
        # Fall back to sample_records data if available
        gotcha = _lookup_gotcha_from_samples(function_name)

    rec = Record(
        function_name = function_name,
        category      = category,
        syntax        = syntax,
        returns       = returns,
        common_gotcha = gotcha or "See documentation.",
        source_url    = source_url,
        description   = description,
    )

    if not rec.is_valid():
        print(f"  [ingest] Incomplete record skipped: {filepath.name}")
        return None

    return rec


def _lookup_gotcha_from_samples(function_name: str) -> str:
    """Find a common_gotcha from the hand-curated sample_records data."""
    name_lower = function_name.lower()
    for rec in SAMPLE_RECORDS:
        if rec["function_name"].lower() == name_lower:
            return rec.get("common_gotcha", "")
    return ""


# ── Merge Pipeline ────────────────────────────────────────────────────────────

def build_records_from_adocs(raw_dir: Path = RAW_DIR) -> List[Record]:
    """
    Parse all .adoc files in raw_dir and return a list of Records.
    Files not in ADOC_META are skipped with a warning.
    """
    parsed: List[Record] = []

    adoc_files = sorted(raw_dir.glob("*.adoc"))
    print(f"  Found {len(adoc_files)} .adoc file(s) in {raw_dir}")

    for adoc_path in adoc_files:
        if adoc_path.name not in ADOC_META:
            print(f"  [ingest] No metadata for {adoc_path.name}, skipping.")
            continue
        try:
            rec = parse_adoc(adoc_path)
            if rec:
                parsed.append(rec)
                print(f"  ✓  Parsed: {rec.function_name}  ({rec.category})")
        except Exception as e:
            print(f"  ✗  Error parsing {adoc_path.name}: {e}")

    return parsed


def _sanitize_record(rec: Record) -> Record:
    """Final cleanup pass on a Record — remove any residual adoc artifacts."""
    _junk = re.compile(r"\s*--\s*")
    for attr in ("syntax", "returns", "common_gotcha", "description"):
        val = getattr(rec, attr)
        if val and isinstance(val, str):
            cleaned = _junk.sub(" ", val).strip()
            # Trim trailing punctuation artifacts
            cleaned = re.sub(r"\s+[+]\s*$", "", cleaned).strip()
            setattr(rec, attr, cleaned or None if attr == "description" else cleaned or "See documentation.")
    return rec


def merge_with_samples(adoc_records: List[Record]) -> List[Record]:
    """
    Merge adoc-parsed records with the hand-curated SAMPLE_RECORDS.

    Strategy:
      - adoc records get priority (richer description, real doc source).
      - sample records fill in any functions not covered by downloaded docs.
      - Final list is sorted alphabetically and assigned sequential IDs.
    """
    # Build a lookup of parsed adoc function names (lowercase for comparison)
    parsed_names = {r.function_name.lower() for r in adoc_records}

    # Build enriched versions of adoc records (overwrite gotcha with sample if blank)
    merged: List[Record] = []
    for rec in adoc_records:
        if not rec.common_gotcha or rec.common_gotcha == "See documentation.":
            rec.common_gotcha = _lookup_gotcha_from_samples(rec.function_name) \
                                or rec.common_gotcha
        merged.append(_sanitize_record(rec))

    # Add sample records for functions not in the adoc set
    for sample in SAMPLE_RECORDS:
        fname_lower = sample["function_name"].lower()
        if fname_lower not in parsed_names:
            try:
                rec = Record(
                    function_name = sample["function_name"],
                    category      = sample["category"],
                    syntax        = sample["syntax"],
                    returns       = sample["returns"],
                    common_gotcha = sample["common_gotcha"],
                    source_url    = sample["source_url"],
                )
                merged.append(rec)
            except Exception as e:
                print(f"  [ingest] Skipping sample record '{sample.get('function_name')}': {e}")

    # Sort by function name, then assign sequential IDs
    merged.sort(key=lambda r: r.function_name.lower())
    for idx, rec in enumerate(merged, start=1):
        rec.id = idx

    return merged


def save_records(records: List[Record], out_file: Path = OUT_FILE) -> None:
    """Serialise the records list to JSON and save to disk."""
    out_file.parent.mkdir(parents=True, exist_ok=True)
    data = [r.to_dict() for r in records]
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n  ✓  Saved {len(data)} records → {out_file}")


# ── Entry point ───────────────────────────────────────────────────────────────

def run_ingest(raw_dir: Path = RAW_DIR, out_file: Path = OUT_FILE) -> List[Record]:
    """
    Full ingest pipeline:
      1. Parse .adoc files from raw_dir.
      2. Merge with sample_records.py fallback data.
      3. Save merged list to out_file (data/records.json).

    Returns the final list of Record objects.
    """
    print("\n" + "=" * 55)
    print("  ARDUINOMATE INGEST PIPELINE")
    print("=" * 55)

    adoc_records = build_records_from_adocs(raw_dir)
    all_records  = merge_with_samples(adoc_records)
    save_records(all_records, out_file)

    print(f"\n  Pipeline complete — {len(all_records)} total records ready.")
    print("=" * 55 + "\n")

    return all_records


if __name__ == "__main__":
    run_ingest()
