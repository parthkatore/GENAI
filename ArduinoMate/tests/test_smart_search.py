"""
ArduinoMate - Machine Learning Smart Search Test Suite
------------------------------------------------------
Tests the TF-IDF Vectorizer and Cosine Similarity ranking logic,
edge case handling, and caching behavior in app/smart_search.py.
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
        """Prepare sample test dataset."""
        self.sample_records = [
            {
                "id": 1,
                "title": "Blinking LED with Resistor",
                "description": "Basic digital output tutorial to flash a 5mm LED.",
                "category": "LED projects",
                "tags": ["LED", "resistor", "digitalWrite"]
            },
            {
                "id": 2,
                "title": "Ultrasonic Distance Sensor HC-SR04",
                "description": "Echo and trigger pin measurement for obstacle detection.",
                "category": "Ultrasonic sensors",
                "tags": ["ultrasonic", "distance", "HC-SR04"]
            },
            {
                "id": 3,
                "title": "Servo Motor Angle Controller",
                "description": "Rotate a micro servo horn between 0 and 180 degrees using PWM.",
                "category": "Servo motors",
                "tags": ["servo", "motor", "PWM"]
            }
        ]
        self.engine = SmartSearchEngine()

    def test_search_ranks_correctly(self):
        """Searching for 'ultrasonic' must rank the ultrasonic record first."""
        results = self.engine.search("ultrasonic distance", records=self.sample_records)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 2)
        self.assertIn("similarity_score", results[0])
        self.assertGreater(results[0]["similarity_score"], 0.0)

    def test_similarity_scores_are_descending(self):
        """Results must be ordered strictly from highest similarity to lowest."""
        results = self.engine.search("motor led", records=self.sample_records, top_k=3)
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
        results = engine.search("servo", records=[])
        self.assertEqual(results, [])

    def test_missing_or_corrupt_fields_handled(self):
        """Records with missing keys or None values must not cause exceptions."""
        dirty_records = [
            {"id": 10, "title": None, "description": None, "category": None, "tags": None},
            {"id": 11, "title": "Buzzer Melody"}  # missing description and tags
        ]
        results = self.engine.search("buzzer melody", records=dirty_records)
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
        initial_hash = self.engine._dataset_hash

        # Fit again with the exact same records
        self.engine.fit(self.sample_records)
        self.assertIs(self.engine.tfidf_matrix, initial_matrix)
        self.assertEqual(self.engine._dataset_hash, initial_hash)

    def test_convenience_function(self):
        """smart_search() helper function works as expected."""
        results = smart_search("LED", records=self.sample_records, top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

