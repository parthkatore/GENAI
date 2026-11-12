"""
ArduinoMate - Pandas Data Analysis Test Suite
---------------------------------------------
Tests dataset loading, fact extraction, and empty data handling
in analysis/explore.py against the Arduino-function record schema.
"""

import sys
from pathlib import Path
import unittest
import pandas as pd

ARDUINOMATE_DIR = Path(__file__).resolve().parent.parent
if str(ARDUINOMATE_DIR) not in sys.path:
    sys.path.insert(0, str(ARDUINOMATE_DIR))

from analysis.explore import load_dataset, calculate_dataset_facts, get_default_data_path


class TestExploreAnalysis(unittest.TestCase):
    """Test suite for Pandas dataset exploration module."""

    def test_load_dataset_success(self):
        """Dataset must load into a non-empty DataFrame with expected columns."""
        path = get_default_data_path()
        df = load_dataset(path)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreaterEqual(len(df), 20)
        for col in ["id", "function_name", "category", "syntax",
                    "returns", "common_gotcha", "source_url"]:
            self.assertIn(col, df.columns)

    def test_calculate_dataset_facts(self):
        """Calculated facts must match dataset content dynamically."""
        path = get_default_data_path()
        df   = load_dataset(path)
        facts = calculate_dataset_facts(df)

        # Fact 1: total records
        self.assertEqual(facts["total_records"], len(df))
        self.assertGreaterEqual(facts["total_records"], 20)

        # Fact 2: category info present
        self.assertIn("category_counts", facts)
        self.assertIn(facts["top_category"], facts["category_counts"])
        self.assertGreater(facts["top_category_percentage"], 0)

        # Fact 3: keyword counts present and sensible
        self.assertIn("keyword_counts", facts)
        self.assertIn("pin", facts["keyword_counts"])
        self.assertGreater(facts["keyword_counts"]["pin"], 0)

        # Fact 4: gotcha length stats
        self.assertGreater(facts["avg_gotcha_length"], 0)
        self.assertGreater(facts["max_gotcha_length"], 0)
        self.assertIsNotNone(facts["longest_gotcha_function"])

    def test_empty_dataframe_handled(self):
        """Empty DataFrame must not raise an error and return zeroed facts."""
        empty_df = pd.DataFrame()
        facts = calculate_dataset_facts(empty_df)
        self.assertEqual(facts["total_records"], 0)
        self.assertEqual(facts["category_counts"], {})
        self.assertEqual(facts["avg_gotcha_length"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
