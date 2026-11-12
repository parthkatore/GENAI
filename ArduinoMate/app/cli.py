"""
ArduinoMate - Day 2: Command-Line Interface (app/cli.py)
---------------------------------------------------------
Student  : Parth Dasharath Katore
Enroll   : 2124UCEM2079
Roll No  : 53

Interactive CLI for the Arduino reference library.
Uses the four functions from app/records.py.

Run:
    python -m app.cli
  or
    python app/cli.py
"""

import sys
from pathlib import Path

# ── Ensure ArduinoMate root is in path ───────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.records import load_records, search, count_by, get_by_id


# ── Helper: pretty-print one record ──────────────────────────────────────────
def _print_record(rec: dict, index: int = None) -> None:
    prefix = f"[{index:02d}] " if index is not None else "    "
    print(f"\n{prefix}{rec['function_name']}  ({rec['category']})")
    print(f"     Syntax  : {rec['syntax']}")
    print(f"     Returns : {rec['returns']}")
    print(f"     Gotcha  : {rec['common_gotcha']}")
    print(f"     Source  : {rec['source_url']}")


# ── Main Menu Loop ────────────────────────────────────────────────────────────
def main() -> None:
    """Run the interactive ArduinoMate reference CLI."""

    while True:
        print()
        print("=" * 48)
        print("     ARDUINOMATE REFERENCE LIBRARY")
        print("=" * 48)
        print("  1. Display all Arduino functions")
        print("  2. Search by keyword")
        print("  3. Count functions by category")
        print("  4. Find function by ID (1–20)")
        print("  0. Exit")
        print("-" * 48)

        choice = input("Enter choice: ").strip()

        # ── 1: Show all ───────────────────────────────────────────────────────
        if choice == "1":
            all_recs = load_records()
            print(f"\n  Showing all {len(all_recs)} Arduino function records:\n")
            for i, rec in enumerate(all_recs, start=1):
                _print_record(rec, index=i)

        # ── 2: Keyword search ─────────────────────────────────────────────────
        elif choice == "2":
            kw = input("  Enter search keyword: ").strip()
            results = search(kw)
            if results:
                print(f"\n  Found {len(results)} result(s) for '{kw}':")
                for rec in results:
                    print(f"    → {rec['function_name']}  [{rec['category']}]")
                    print(f"      {rec['syntax']}")
            else:
                print(f"  No records matched '{kw}'.")

        # ── 3: Count by category ──────────────────────────────────────────────
        elif choice == "3":
            counts = count_by("category")
            print("\n  Category Distribution:")
            for cat, cnt in sorted(counts.items()):
                bar = "█" * cnt
                print(f"    {cat:<22}: {cnt:>2}  {bar}")

        # ── 4: Find by ID ─────────────────────────────────────────────────────
        elif choice == "4":
            id_input = input("  Enter record ID (1–20): ").strip()
            try:
                rec_id = int(id_input)
            except ValueError:
                print("  Please enter a valid integer.")
            else:
                rec = get_by_id(rec_id)
                if rec:
                    _print_record(rec, index=rec_id)
                else:
                    print(f"  Record with ID {rec_id} not found. Valid range: 1–20.")

        # ── 0: Exit ───────────────────────────────────────────────────────────
        elif choice == "0":
            print("\n  Thank you for using ArduinoMate. Happy coding! 🚀")
            break

        else:
            print("  Invalid choice. Please enter 1, 2, 3, 4, or 0.")


if __name__ == "__main__":
    main()
