"""
tests/test_api.py — FastAPI endpoint tests via TestClient.
-----------------------------------------------------------
Tests GET /health, POST /ask (RAG with fake LLM), POST /agent,
and GET /search/semantic using FastAPI's TestClient so no live
server or real Groq API key is needed.

The LLM and ChromaDB are both stubbed via the fixtures in conftest.py.
"""

from __future__ import annotations

import json


class TestHealth:
    """GET /health — basic liveness and schema validation."""

    def test_health_returns_200(self, api_client):
        """Health endpoint must respond with HTTP 200."""
        resp = api_client.get("/health")
        assert resp.status_code == 200

    def test_health_body_has_status_healthy(self, api_client):
        """Health response must include status == 'healthy'."""
        data = api_client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_body_has_model_field(self, api_client):
        """Health response must include the active model name."""
        data = api_client.get("/health").json()
        assert "model" in data
        assert isinstance(data["model"], str)
        assert data["model"]  # non-empty

    def test_health_body_has_version(self, api_client):
        """Health response must include an API version string."""
        data = api_client.get("/health").json()
        assert "version" in data


class TestAskEndpoint:
    """POST /ask — RAG-grounded answers with a stubbed LLM."""

    def test_ask_returns_200(self, api_client):
        """POST /ask with a valid question must return HTTP 200."""
        resp = api_client.post(
            "/ask",
            json={"question": "What does pinMode() do?", "top_k": 3, "min_score": 0.20},
        )
        assert resp.status_code == 200

    def test_ask_response_has_answer(self, api_client):
        """POST /ask response must contain a non-empty answer string."""
        resp = api_client.post("/ask", json={"question": "How does analogRead work?"})
        data = resp.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

    def test_ask_response_has_citations(self, api_client):
        """POST /ask must return a citations list (may be empty for OOS)."""
        resp = api_client.post("/ask", json={"question": "What does pinMode() do?"})
        data = resp.json()
        assert "citations" in data
        assert isinstance(data["citations"], list)

    def test_ask_response_has_out_of_scope_flag(self, api_client):
        """POST /ask must include the out_of_scope boolean field."""
        resp = api_client.post("/ask", json={"question": "Tell me about pinMode"})
        data = resp.json()
        assert "out_of_scope" in data
        assert isinstance(data["out_of_scope"], bool)

    def test_ask_reports_empty_index_as_service_unavailable(self, api_client):
        """A missing vector index must not be reported as an out-of-scope question."""
        from unittest.mock import patch

        from backend.app.vectorstore import VectorIndexNotReadyError

        with patch(
            "backend.app.rag.query_collection",
            side_effect=VectorIndexNotReadyError("The Arduino documentation index is empty."),
        ):
            resp = api_client.post("/ask", json={"question": "What does pinMode do?"})

        assert resp.status_code == 503
        assert "index is empty" in resp.json()["detail"]

    def test_ask_question_too_short_returns_422(self, api_client):
        """POST /ask with a 2-character question must return HTTP 422."""
        resp = api_client.post("/ask", json={"question": "Hi"})
        assert resp.status_code == 422

    def test_ask_missing_question_returns_422(self, api_client):
        """POST /ask without a question field must return HTTP 422."""
        resp = api_client.post("/ask", json={})
        assert resp.status_code == 422


class TestSemanticSearchEndpoint:
    """GET /search/semantic — vector search over documents."""

    def test_semantic_search_returns_200(self, api_client):
        """GET /search/semantic with a valid query must return HTTP 200."""
        resp = api_client.get("/search/semantic", params={"q": "how to use pinMode"})
        assert resp.status_code == 200

    def test_semantic_search_has_results_key(self, api_client):
        """Response must have a results list and total_results integer."""
        resp = api_client.get("/search/semantic", params={"q": "analog read"})
        data = resp.json()
        assert "results" in data
        assert "total_results" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["total_results"], int)

    def test_semantic_search_short_query_returns_422(self, api_client):
        """Single-character query must be rejected with 422."""
        resp = api_client.get("/search/semantic", params={"q": "a"})
        assert resp.status_code == 422


class TestAgentEndpoint:
    """POST /agent — tool-using agent with stubbed LLM."""

    _FAKE_TOOL_ANSWER = json.dumps({"answer": "Use a 150 Ω resistor."})

    def test_agent_returns_200(self, api_client):
        """POST /agent with a valid message must return HTTP 200."""
        from unittest.mock import patch

        with patch("backend.app.llm.chat", return_value=self._FAKE_TOOL_ANSWER):
            resp = api_client.post(
                "/agent",
                json={
                    "message": "What resistor for a red LED on 5V at 20mA?",
                    "use_graph": False,  # hand-written loop — simpler to stub
                    "thread_id": "test-thread",
                },
            )
        assert resp.status_code == 200

    def test_agent_response_has_answer(self, api_client):
        """POST /agent response must include a non-empty answer string."""
        from unittest.mock import patch

        with patch("backend.app.llm.chat", return_value=self._FAKE_TOOL_ANSWER):
            data = api_client.post(
                "/agent",
                json={"message": "What is analogWrite?", "use_graph": False},
            ).json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert data["answer"]

    def test_agent_response_has_steps(self, api_client):
        """POST /agent response must include a steps list."""
        from unittest.mock import patch

        with patch("backend.app.llm.chat", return_value=self._FAKE_TOOL_ANSWER):
            data = api_client.post(
                "/agent",
                json={"message": "Explain millis()", "use_graph": False},
            ).json()
        assert "steps" in data
        assert isinstance(data["steps"], list)

    def test_agent_message_too_short_returns_422(self, api_client):
        """POST /agent with a 2-character message must return HTTP 422."""
        resp = api_client.post("/agent", json={"message": "Hi"})
        assert resp.status_code == 422
