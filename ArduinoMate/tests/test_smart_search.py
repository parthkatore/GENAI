"""
ArduinoMate - Machine Learning Smart Search Test Suite
------------------------------------------------------
Tests the TF-IDF Vectorizer and Cosine Similarity ranking logic,
edge case handling, and caching behaviour in app/smart_search.py.
Uses the Arduino-function record schema.
"""

import sys
from pathlib import Path
import unittest

ARDUINOMATE_DIR = Path(__file__).resolve().parent.parent
if str(ARDUINOMATE_DIR) not in sys.path:
    sys.path.insert(0, str(ARDUINOMATE_DIR))

from app.smart_search import SmartSearchEngine, smart_search


class TestSmartSearch(unittest.TestCase):
    """Test suite for TF-IDF Vectorizer & Cosine Similarity search engine."""

    def setUp(self):
        """Prepare sample test dataset using Arduino-function schema."""
        self.sample_records = [
            {
                "id": 1,
                "function_name": "digitalRead",
                "category": "Digital I/O",
                "syntax": "digitalRead(pin)",
                "returns": "HIGH or LOW",
                "common_gotcha": "Pin must be configured as INPUT or INPUT_PULLUP first.",
                "source_url": "https://docs.arduino.cc/language-reference/en/functions/digital-io/digitalread/"
            },
            {
                "id": 2,
                "function_name": "analogRead",
                "category": "Analog I/O",
                "syntax": "analogRead(pin)",
                "returns": "Integer 0-1023",
                "common_gotcha": "Only works on analog pins A0-A5 on Uno.",
                "source_url": "https://docs.arduino.cc/language-reference/en/functions/analog-io/analogread/"
            },
            {
                "id": 3,
                "function_name": "Serial.begin",
                "category": "Serial",
                "syntax": "Serial.begin(speed)",
                "returns": "None",
                "common_gotcha": "Baud rate in Serial Monitor must match.",
                "source_url": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/begin/"
            }
        ]
        self.engine = SmartSearchEngine()

    def test_search_ranks_correctly(self):
        """Searching for 'analogRead' must rank the analog record first."""
        results = self.engine.search("analogRead analog pin", records=self.sample_records)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 2)
        self.assertIn("similarity_score", results[0])
        self.assertGreater(results[0]["similarity_score"], 0.0)

    def test_similarity_scores_are_descending(self):
        """Results must be ordered strictly from highest similarity to lowest."""
        results = self.engine.search("pin read", records=self.sample_records, top_k=3)
        scores = [r["similarity_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_empty_query_returns_empty_list(self):
        """Empty or whitespace queries must return an empty list."""
        self.assertEqual(self.engine.search("", records=self.sample_records), [])
        self.assertEqual(self.engine.search("   ", records=self.sample_records), [])
        self.assertEqual(self.engine.search(None, records=self.sample_records), [])

    def test_empty_dataset_returns_empty_list(self):
        """Searching an empty dataset must return an empty list gracefully."""
        engine = SmartSearchEngine()
        results = engine.search("serial", records=[])
        self.assertEqual(results, [])

    def test_missing_or_corrupt_fields_handled(self):
        """Records with missing keys or None values must not cause exceptions."""
        dirty_records = [
            {"id": 10, "function_name": None, "category": None,
             "syntax": None, "returns": None, "common_gotcha": None},
            {"id": 11, "function_name": "tone"}   # most fields missing
        ]
        results = self.engine.search("tone", records=dirty_records)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 11)

    def test_out_of_vocabulary_query(self):
        """Words not present in any document must return an empty list, not crash."""
        results = self.engine.search("quantum teleportation xkcd", records=self.sample_records)
        self.assertEqual(results, [])

    def test_caching_avoids_unnecessary_recalculation(self):
        """Vectorizer and matrix should be cached if records are identical."""
        self.engine.fit(self.sample_records)
        initial_matrix = self.engine.tfidf_matrix
        initial_hash   = self.engine._dataset_hash

        # Fit again with the exact same records — should reuse
        self.engine.fit(self.sample_records)
        self.assertIs(self.engine.tfidf_matrix, initial_matrix)
        self.assertEqual(self.engine._dataset_hash, initial_hash)

    def test_convenience_function(self):
        """smart_search() helper function works as expected."""
        results = smart_search("digital", records=self.sample_records, top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
