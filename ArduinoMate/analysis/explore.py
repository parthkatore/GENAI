"""
ArduinoMate - Data Analysis Module
----------------------------------
Uses Pandas to analyze the ArduinoMate dataset and uncover key statistics.

Key Features:
- Loads records from data/records.json.
- Converts records into a Pandas DataFrame.
- Calculates and displays real dataset facts dynamically (not hardcoded).
- Handles missing or null values gracefully.
- Reusable as both an executable script and an importable module.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import pandas as pd


def get_default_data_path() -> Path:
    """
    Locate data/records.json reliably regardless of current working directory.
    """
    script_dir = Path(__file__).resolve().parent
    # Check parent directory (ArduinoMate/data/records.json)
    candidate_1 = script_dir.parent / "data" / "records.json"
    if candidate_1.exists():
        return candidate_1
    # Check current working directory
    candidate_2 = Path.cwd() / "data" / "records.json"
    if candidate_2.exists():
        return candidate_2
    # Check ArduinoMate subfolder from workspace root
    candidate_3 = Path.cwd() / "ArduinoMate" / "data" / "records.json"
    if candidate_3.exists():
        return candidate_3
    return candidate_1


def load_dataset(file_path: Optional[Path | str] = None) -> pd.DataFrame:
    """
    Load JSON records into a clean Pandas DataFrame.
    Handles missing files and validates required columns.
    """
    target_path = Path(file_path) if file_path else get_default_data_path()

    if not target_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    if not records:
        return pd.DataFrame(columns=["id", "title", "description", "category", "tags"])

    df = pd.DataFrame(records)

    # Ensure required columns exist and handle missing or NaN values
    for col in ["id", "title", "description", "category"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    if "tags" not in df.columns:
        df["tags"] = [[] for _ in range(len(df))]
    else:
        # Guarantee every tags entry is a list
        df["tags"] = df["tags"].apply(lambda t: t if isinstance(t, list) else [])

    return df


def calculate_dataset_facts(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate dynamic facts from the records DataFrame.
    None of these values are hardcoded - all are derived from data.
    """
    if df.empty:
        return {
            "total_records": 0,
            "category_counts": {},
            "top_category": None,
            "top_category_count": 0,
            "top_category_percentage": 0.0,
            "keyword_counts": {},
            "total_unique_tags": 0,
            "top_tags": [],
            "missing_values": {}
        }

    # Fact 1: Total number of records
    total_records = int(len(df))

    # Fact 2: Category distribution & most common category
    category_counts = df["category"].value_counts().to_dict()
    top_category = df["category"].value_counts().index[0] if not df["category"].empty else "N/A"
    top_category_count = int(category_counts.get(top_category, 0))
    top_category_pct = round((top_category_count / total_records) * 100, 2)

    # Fact 3: Keyword occurrences across title and description
    # Combines title and description text into lowercase strings
    combined_texts = (df["title"] + " " + df["description"]).str.lower()
    keywords_to_check = ["sensor", "led", "motor", "i2c", "display", "bluetooth", "robotics"]
    keyword_counts = {
        kw: int(combined_texts.str.contains(kw, case=False, na=False).sum())
        for kw in keywords_to_check
    }

    # Fact 4: Tag statistics (flattening tags list)
    all_tags = [tag.lower() for tags_list in df["tags"] for tag in tags_list if tag]
    tag_series = pd.Series(all_tags)
    total_unique_tags = int(tag_series.nunique())
    top_5_tags = tag_series.value_counts().head(5).to_dict()

    # Data Quality: Missing values check
    missing_summary = df.isnull().sum().to_dict()

    return {
        "total_records": total_records,
        "category_counts": category_counts,
        "top_category": top_category,
        "top_category_count": top_category_count,
        "top_category_percentage": top_category_pct,
        "keyword_counts": keyword_counts,
        "total_unique_tags": total_unique_tags,
        "top_tags": top_5_tags,
        "missing_values": missing_summary
    }


def print_facts(facts: Dict[str, Any]) -> None:
    """Print the calculated facts in a clean, human-readable terminal format."""
    print("=" * 65)
    print("         ARDUINOMATE DATA EXPLORATION REPORT (Pandas)        ")
    print("=" * 65)
    print(f"\n[Fact 1] Total Number of Records:")
    print(f"         -> {facts['total_records']} verified Arduino records in dataset.")

    print(f"\n[Fact 2] Most Common Category:")
    print(f"         -> '{facts['top_category']}' with {facts['top_category_count']} records "
          f"({facts['top_category_percentage']}% of total).")
    print("         Category breakdown:")
    for cat, count in facts["category_counts"].items():
        print(f"           * {cat:22s} : {count} record(s)")

    print(f"\n[Fact 3] Keyword Presence Across Titles & Descriptions:")
    for kw, count in facts["keyword_counts"].items():
        pct = round((count / max(facts['total_records'], 1)) * 100, 1)
        bar = "#" * count
        print(f"           * '{kw:10s}' : {count:2d} record(s) ({pct:4.1f}%) {bar}")

    print(f"\n[Fact 4] Tag Statistics:")
    print(f"         -> Total unique tags: {facts['total_unique_tags']}")
    print("         Top 5 most frequent tags:")
    for tag, freq in facts["top_tags"].items():
        print(f"           * #{tag:18s} : {freq} time(s)")

    print("\n[Data Quality Check]:")
    has_missing = any(v > 0 for v in facts["missing_values"].values())
    if not has_missing:
        print("         -> Clean dataset! No missing/null values detected.")
    else:
        print(f"         -> Missing values detected: {facts['missing_values']}")

    print("=" * 65)


def main():
    """Main execution function when running explore.py directly."""
    try:
        data_path = get_default_data_path()
        print(f"Loading dataset from: {data_path}")
        df = load_dataset(data_path)
        facts = calculate_dataset_facts(df)
        print_facts(facts)
    except Exception as e:
        print(f"Error during data analysis: {e}")


if __name__ == "__main__":
    main()

