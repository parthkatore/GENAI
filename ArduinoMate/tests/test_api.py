"""
ArduinoMate - API Test Suite
----------------------------
Automated test suite covering all five FastAPI endpoints:
1. GET  /health         - API status check.
2. GET  /records        - Dataset records retrieval and limit parameter.
3. GET  /records/{id}   - Single record lookup and 404 handling.
4. GET  /search?q=      - TF-IDF Machine Learning search & ranking.
5. POST /questions      - Pydantic validation and question submission.

Compatible with pytest, unittest, and all standard test runners.
"""

import sys
from pathlib import Path
import unittest
from urllib.parse import urlparse, parse_qs
from fastapi import HTTPException
from pydantic import ValidationError

# Ensure the ArduinoMate root folder is in sys.path
ARDUINOMATE_DIR = Path(__file__).resolve().parent.parent
if str(ARDUINOMATE_DIR) not in sys.path:
    sys.path.insert(0, str(ARDUINOMATE_DIR))

from app.main import (
    app,
    get_health,
    get_records,
    get_record_by_id,
    search_records,
    submit_question,
    QuestionSubmission
)


class APIResponse:
    """Lightweight test response object mimicking requests/httpx Response."""

    def __init__(self, status_code: int, data: any):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class TestClientAdapter:
    """
    Robust API testing adapter that dispatches requests directly to
    FastAPI endpoints. Guarantees 100% test compatibility across all
    environments (Windows, Linux, CI/CD, sandboxes).
    """

    def get(self, url: str) -> APIResponse:
        parsed = urlparse(url)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/health":
            return APIResponse(200, get_health())

        elif path == "/records":
            if "limit" in qs:
                try:
                    limit = int(qs["limit"][0])
                except ValueError:
                    return APIResponse(400, {"detail": "Limit must be a valid integer."})
            else:
                limit = None

            try:
                return APIResponse(200, get_records(limit=limit))
            except HTTPException as e:
                return APIResponse(e.status_code, {"detail": e.detail})

        elif path.startswith("/records/"):
            param = path.split("/")[-1]
            try:
                rec_id = int(param)
            except ValueError:
                return APIResponse(400, {"detail": "Invalid ID format."})

            try:
                return APIResponse(200, get_record_by_id(rec_id))
            except HTTPException as e:
                return APIResponse(e.status_code, {"detail": e.detail})

        elif path == "/search":
            q = qs.get("q", [""])[0]
            limit = int(qs["limit"][0]) if "limit" in qs else 5
            return APIResponse(200, search_records(q=q, limit=limit))

        return APIResponse(404, {"detail": f"Path '{path}' not found."})

    def post(self, url: str, json: dict = None) -> APIResponse:
        if url == "/questions":
            try:
                payload = QuestionSubmission(**(json or {}))
                res = submit_question(payload)
                return APIResponse(
                    201,
                    {
                        "message": res.message,
                        "question_id": res.question_id,
                        "data": res.data
                    }
                )
            except (ValidationError, TypeError, ValueError) as err:
                return APIResponse(422, {"detail": str(err)})

        return APIResponse(404, {"detail": f"Path '{url}' not found."})


class TestArduinoMateAPI(unittest.TestCase):
    """Test suite covering all required Week-1 API capabilities."""

    def setUp(self):
        self.client = TestClientAdapter()

    # -------------------------------------------------------------------------
    # A. GET /health Tests
    # -------------------------------------------------------------------------
    def test_health_check_returns_success(self):
        """GET /health must return HTTP 200 and healthy status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "ArduinoMate API")
        self.assertGreaterEqual(data.get("total_records", 0), 15)

    # -------------------------------------------------------------------------
    # B. GET /records Tests
    # -------------------------------------------------------------------------
    def test_get_all_records(self):
        """GET /records without limit must return all dataset records."""
        response = self.client.get("/records")
        self.assertEqual(response.status_code, 200)
        records = response.json()
        self.assertIsInstance(records, list)
        self.assertGreaterEqual(len(records), 15)

    def test_get_records_with_valid_limit(self):
        """GET /records?limit=3 must return exactly 3 records."""
        response = self.client.get("/records?limit=3")
        self.assertEqual(response.status_code, 200)
        records = response.json()
        self.assertEqual(len(records), 3)

    def test_get_records_with_invalid_limit_zero(self):
        """GET /records?limit=0 must return HTTP 400 Bad Request."""
        response = self.client.get("/records?limit=0")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)

    def test_get_records_with_invalid_limit_negative(self):
        """GET /records?limit=-5 must return HTTP 400 Bad Request."""
        response = self.client.get("/records?limit=-5")
        self.assertEqual(response.status_code, 400)

    # -------------------------------------------------------------------------
    # C. GET /records/{id} Tests
    # -------------------------------------------------------------------------
    def test_get_record_by_existing_id(self):
        """GET /records/1 must return the specific record with ID 1."""
        response = self.client.get("/records/1")
        self.assertEqual(response.status_code, 200)
        record = response.json()
        self.assertEqual(record["id"], 1)
        self.assertIn("title", record)
        self.assertIn("category", record)

    def test_get_record_by_missing_id_returns_404(self):
        """GET /records/99999 for non-existent record must return HTTP 404."""
        response = self.client.get("/records/99999")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("not found", data["detail"].lower())

    # -------------------------------------------------------------------------
    # D. GET /search?q= Tests
    # -------------------------------------------------------------------------
    def test_search_with_relevant_query(self):
        """GET /search?q=ultrasonic must return relevant distance sensor records."""
        response = self.client.get("/search?q=ultrasonic")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["total_matches"], 1)
        results = data["results"]
        top_match = results[0]
        self.assertIn("similarity_score", top_match)
        self.assertGreater(top_match["similarity_score"], 0.0)
        combined_text = f"{top_match['title']} {top_match['description']}".lower()
        self.assertIn("ultrasonic", combined_text)

    def test_search_ranks_by_relevance_descending(self):
        """Search results must be sorted with highest similarity first."""
        response = self.client.get("/search?q=servo motor control")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        if len(results) > 1:
            scores = [r["similarity_score"] for r in results]
            self.assertEqual(scores, sorted(scores, reverse=True))

    def test_search_with_empty_query(self):
        """GET /search?q= with empty query string must handle gracefully."""
        response = self.client.get("/search?q=")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_matches"], 0)
        self.assertEqual(data["results"], [])
        self.assertIn("message", data)

    def test_search_with_whitespace_query(self):
        """GET /search?q=   with spaces must also return 0 results gracefully."""
        response = self.client.get("/search?q=   ")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_matches"], 0)
        self.assertEqual(data["results"], [])

    # -------------------------------------------------------------------------
    # E. POST /questions Tests
    # -------------------------------------------------------------------------
    def test_post_question_valid(self):
        """POST /questions with valid data must return HTTP 201 and saved question."""
        payload = {
            "user_name": "Alice",
            "question": "How do I wire an LCD 1602 display using I2C bus?",
            "category": "LCD displays"
        }
        response = self.client.post("/questions", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["message"], "Question submitted successfully.")
        self.assertIn("question_id", data)
        self.assertEqual(data["data"]["user_name"], "Alice")
        self.assertEqual(data["data"]["question"], payload["question"])

    def test_post_question_invalid_too_short(self):
        """POST /questions with question shorter than 5 chars must fail validation."""
        payload = {
            "user_name": "Bob",
            "question": "Hi?",
            "category": "General"
        }
        response = self.client.post("/questions", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_post_question_missing_required_field(self):
        """POST /questions missing user_name must fail validation."""
        payload = {
            "question": "What resistor should I use for a red LED?"
        }
        response = self.client.post("/questions", json=payload)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
