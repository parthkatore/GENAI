"""
ArduinoMate - Day 4: Data Analysis Module  (analysis/explore.py)
-----------------------------------------------------------------
Student  : Parth Dasharath Katore
Enroll   : 2124UCEM2079
Roll No  : 53

Uses Pandas to analyse the ArduinoMate Arduino-function dataset
(data/records.json) and surface at least four meaningful facts:

  Fact 1 – Total number of records
  Fact 2 – Category distribution (most common / bar chart)
  Fact 3 – Keyword coverage across function names, syntax, and gotchas
  Fact 4 – Average gotcha length & longest gotcha
  Bonus   – Data quality check (nulls / missing values)

The module is importable (used by test suite) AND runnable directly:
    python analysis/explore.py
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import pandas as pd


# ── Path helpers ──────────────────────────────────────────────────────────────

def get_default_data_path() -> Path:
    """
    Locate data/records.json reliably regardless of current working directory.
    """
    script_dir = Path(__file__).resolve().parent
    candidate_1 = script_dir.parent / "data" / "records.json"
    if candidate_1.exists():
        return candidate_1
    candidate_2 = Path.cwd() / "data" / "records.json"
    if candidate_2.exists():
        return candidate_2
    candidate_3 = Path.cwd() / "ArduinoMate" / "data" / "records.json"
    if candidate_3.exists():
        return candidate_3
    return candidate_1


# ── Dataset loader ────────────────────────────────────────────────────────────

def load_dataset(file_path: Optional[Path | str] = None) -> pd.DataFrame:
    """
    Load JSON records into a clean Pandas DataFrame.

    Parameters
    ----------
    file_path : optional path override.  Defaults to data/records.json.

    Returns
    -------
    pd.DataFrame with columns:
        id, function_name, category, syntax, returns,
        common_gotcha, source_url, description
    """
    target_path = Path(file_path) if file_path else get_default_data_path()

    if not target_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    if not records:
        return pd.DataFrame(
            columns=["id", "function_name", "category", "syntax",
                     "returns", "common_gotcha", "source_url", "description"]
        )

    df = pd.DataFrame(records)

    # Ensure required text columns exist and have no NaN
    for col in ["id", "function_name", "category", "syntax",
                "returns", "common_gotcha", "source_url"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    if "description" not in df.columns:
        df["description"] = ""
    df["description"] = df["description"].fillna("")

    return df


# ── Fact calculator ───────────────────────────────────────────────────────────

def calculate_dataset_facts(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Derive dynamic facts from the records DataFrame.
    Nothing is hard-coded — all values come directly from the data.

    Returns
    -------
    dict with keys:
        total_records, category_counts, top_category, top_category_count,
        top_category_percentage, keyword_counts, avg_gotcha_length,
        max_gotcha_length, longest_gotcha_function, missing_values
    """
    if df.empty:
        return {
            "total_records"          : 0,
            "category_counts"        : {},
            "top_category"           : None,
            "top_category_count"     : 0,
            "top_category_percentage": 0.0,
            "keyword_counts"         : {},
            "avg_gotcha_length"      : 0.0,
            "max_gotcha_length"      : 0,
            "longest_gotcha_function": None,
            "missing_values"         : {}
        }

    total_records = int(len(df))

    # Fact 2: Category distribution
    category_counts   = df["category"].value_counts().to_dict()
    top_category      = df["category"].value_counts().index[0]
    top_category_cnt  = int(category_counts[top_category])
    top_category_pct  = round(top_category_cnt / total_records * 100, 2)

    # Fact 3: Keyword coverage across function_name + syntax + common_gotcha
    combined_text = (
        df["function_name"] + " " +
        df["syntax"]        + " " +
        df["common_gotcha"] + " " +
        df["description"]
    ).str.lower()

    keywords = ["digital", "analog", "serial", "interrupt",
                "delay", "timer", "pwm", "pin", "read", "write"]
    keyword_counts = {
        kw: int(combined_text.str.contains(kw, case=False, na=False).sum())
        for kw in keywords
    }

    # Fact 4: Gotcha length statistics
    gotcha_lengths        = df["common_gotcha"].str.len().fillna(0)
    avg_gotcha_length     = round(float(gotcha_lengths.mean()), 1)
    max_gotcha_length     = int(gotcha_lengths.max())
    longest_idx           = int(gotcha_lengths.idxmax())
    longest_gotcha_func   = df.loc[longest_idx, "function_name"]

    # Data quality
    missing_values = df.isnull().sum().to_dict()

    return {
        "total_records"          : total_records,
        "category_counts"        : category_counts,
        "top_category"           : top_category,
        "top_category_count"     : top_category_cnt,
        "top_category_percentage": top_category_pct,
        "keyword_counts"         : keyword_counts,
        "avg_gotcha_length"      : avg_gotcha_length,
        "max_gotcha_length"      : max_gotcha_length,
        "longest_gotcha_function": longest_gotcha_func,
        "missing_values"         : missing_values
    }


# ── Pretty printer ────────────────────────────────────────────────────────────

def print_facts(facts: Dict[str, Any]) -> None:
    """Print the computed facts in a clean, human-readable terminal report."""
    SEP = "=" * 65

    print(SEP)
    print("     ARDUINOMATE DATA EXPLORATION REPORT (Pandas)")
    print(SEP)

    # Fact 1
    print(f"\n[Fact 1]  Total Records in Dataset")
    print(f"          → {facts['total_records']} Arduino function records loaded.")

    # Fact 2
    print(f"\n[Fact 2]  Category Distribution")
    print(f"          Most common: '{facts['top_category']}' "
          f"({facts['top_category_count']} records, "
          f"{facts['top_category_percentage']}% of total)")
    print("          Full breakdown:")
    max_count = max(facts["category_counts"].values(), default=1)
    for cat, cnt in sorted(facts["category_counts"].items(),
                           key=lambda x: -x[1]):
        bar = "█" * cnt
        pct = round(cnt / max(facts["total_records"], 1) * 100, 1)
        print(f"            {cat:<22}: {cnt:>2}  ({pct:4.1f}%)  {bar}")

    # Fact 3
    print(f"\n[Fact 3]  Keyword Coverage Across Records")
    print(f"          (searched in function_name + syntax + common_gotcha + description)")
    for kw, cnt in sorted(facts["keyword_counts"].items(), key=lambda x: -x[1]):
        pct = round(cnt / max(facts["total_records"], 1) * 100, 1)
        bar = "▪" * cnt
        print(f"            '{kw:<12}' : {cnt:>2} record(s) ({pct:4.1f}%)  {bar}")

    # Fact 4
    print(f"\n[Fact 4]  Gotcha / Warning Length Statistics")
    print(f"          Average gotcha length : {facts['avg_gotcha_length']} characters")
    print(f"          Longest gotcha        : {facts['max_gotcha_length']} chars "
          f"→ '{facts['longest_gotcha_function']}'")

    # Data quality
    print("\n[Data Quality Check]")
    missing = {k: v for k, v in facts["missing_values"].items() if v > 0}
    if not missing:
        print("          ✓ Clean dataset — no null/missing values detected.")
    else:
        print(f"          ⚠ Missing values found: {missing}")

    print(SEP)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    """Execute the full exploration pipeline and print the report."""
    try:
        path = get_default_data_path()
        print(f"Loading dataset from: {path}\n")
        df    = load_dataset(path)
        facts = calculate_dataset_facts(df)
        print_facts(facts)
    except Exception as exc:
        print(f"[explore] Error: {exc}")


if __name__ == "__main__":
    main()
