"""
tests/conftest.py — Shared pytest fixtures for ArduinoMate Day 11/12 tests.

Strategy
--------
Heavy optional deps (chromadb, sentence-transformers, langgraph, langchain*)
are stubbed into sys.modules BEFORE any app module is imported.  This lets
tests run in a plain Python 3.11 environment with only the packages listed
in requirements.txt that are already available (fastapi, pydantic, groq …).

All LLM and vector-store calls are replaced with unittest.mock stubs so no
API key, no network, and no GPU are required.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Stub heavy / unavailable packages so app.* modules can be imported without
# them being installed.
# ---------------------------------------------------------------------------
def _stub(name: str) -> MagicMock:
    """Return a MagicMock module stub and register it (and its dotted parents)."""
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        key = ".".join(parts[:i])
        if key not in sys.modules:
            mod = types.ModuleType(key)
            mod.__spec__ = None  # type: ignore[attr-defined]
            sys.modules[key] = mod  # type: ignore[assignment]
    # Replace the leaf with a MagicMock so attribute access always works
    mock_mod = MagicMock(name=name)
    sys.modules[name] = mock_mod  # type: ignore[assignment]
    return mock_mod


# Stub chromadb (and its sub-packages used in app/vectorstore.py)
for _pkg in [
    "chromadb",
    "chromadb.config",
    "chromadb.errors",
    "chromadb.utils",
]:
    _stub(_pkg)

# Stub sentence_transformers
_stub("sentence_transformers")

# Stub langgraph / langchain
for _pkg in [
    "langgraph",
    "langgraph.graph",
    "langgraph.checkpoint",
    "langgraph.checkpoint.memory",
    "langchain_core",
    "langchain_core.messages",
    "langchain_core.tools",
    "langchain_groq",
]:
    _stub(_pkg)

# ---------------------------------------------------------------------------
# Fake LLM chat response
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

# ---------------------------------------------------------------------------
# Mock hits returned by the stubbed vector store
# ---------------------------------------------------------------------------
MOCK_HITS = [
    {
        "title": "pinMode()",
        "source": "ArduinoMate/data/raw/pinMode.adoc",
        "page": 1,
        "category": "Digital I/O",
        "text": "pinMode(pin, mode) configures the specified pin.",
        "score": 0.85,
    }
]


# ---------------------------------------------------------------------------
# Session fixture: patch app.llm.chat
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def fake_llm_patch():
    """
    Session-scoped patch that replaces app.llm.chat with a stub.
    Returns the canned JSON string so no network call is made.
    The same patch works for /chat, /ask, and /agent endpoints.
    """
    import app.llm  # noqa: F401 — ensure module is loaded before patching
    with patch("app.llm.chat", return_value=FAKE_RAG_ANSWER) as mock_chat:
        yield mock_chat


# ---------------------------------------------------------------------------
# Session fixture: FastAPI TestClient with fully-mocked dependencies
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def api_client(fake_llm_patch):
    """
    Session-scoped FastAPI TestClient.
    LLM and ChromaDB are stubbed; no live server or API key is required.
    """
    import app.vectorstore  # noqa: F401 — load module so patch target exists
    import app.rag          # noqa: F401

    with (
        patch("app.vectorstore.query_collection", return_value=MOCK_HITS),
        patch("app.vectorstore.build_index", return_value=1),
        # app.rag imports query_collection directly, so patch its local reference too
        patch("app.rag.query_collection", return_value=MOCK_HITS),
    ):
        from main import app as fastapi_app  # import after patching
        client = TestClient(fastapi_app, raise_server_exceptions=True)
        yield client
