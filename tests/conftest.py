"""
tests/conftest.py — Shared pytest fixtures for ArduinoMate Day 11 tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Project root on sys.path (FastAPI app lives at root, not in a sub-package)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Fake LLM chat — returns a valid JSON RAG answer without hitting Groq/Gemini
# ---------------------------------------------------------------------------
FAKE_RAG_ANSWER = json.dumps({
    "answer": "pinMode(pin, mode) configures a digital pin as INPUT, OUTPUT, or INPUT_PULLUP.",
    "confidence": 0.95,
    "follow_up": "How do I use digitalRead() after setting pinMode?",
})

FAKE_CHAT_RESPONSE = json.dumps({
    "answer": "Use digitalWrite(13, HIGH) to turn on the built-in LED.",
    "confidence": 0.90,
    "follow_up": "How do I add a delay between blinks?",
})


@pytest.fixture(scope="session")
def fake_llm_patch():
    """
    Session-scoped patch that replaces app.llm.chat with a stub.
    Returns the canned JSON string so no network call is made.
    The same patch works for /chat, /ask, and /agent endpoints.
    """
    with patch("app.llm.chat", return_value=FAKE_RAG_ANSWER) as mock_chat:
        yield mock_chat


@pytest.fixture(scope="session")
def api_client(fake_llm_patch):
    """
    Session-scoped FastAPI TestClient.
    The LLM is stubbed out before the app imports so no Groq key is needed.
    The vector store is rebuilt only when the collection is empty (uses the
    cached index from normal runs; forces a mock if the DB is empty).
    """
    # Also patch vectorstore query so tests don't need a live ChromaDB index
    mock_hits = [
        {
            "title": "pinMode()",
            "source": "ArduinoMate/data/raw/pinMode.adoc",
            "page": 1,
            "category": "Digital I/O",
            "text": "pinMode(pin, mode) configures the specified pin.",
            "score": 0.85,
        }
    ]
    with patch("app.vectorstore.query_collection", return_value=mock_hits), \
         patch("app.vectorstore.build_index", return_value=1):
        from main import app  # import after patching to pick up mocks
        client = TestClient(app, raise_server_exceptions=True)
        yield client
