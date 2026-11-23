"""
tests/conftest.py -- Shared pytest fixtures for ArduinoMate Day 11/12 tests.

Strategy
--------
Heavy optional deps (chromadb, langgraph, langchain*)
are stubbed into sys.modules BEFORE any backend module is imported.  This lets
tests run in a plain Python 3.11 environment with only the packages listed
in requirements.txt that are already available (fastapi, pydantic, groq ...).

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
# Stub heavy / unavailable packages so backend.app.* modules can be imported without
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
    mock_mod = MagicMock(name=name)
    sys.modules[name] = mock_mod  # type: ignore[assignment]
    return mock_mod


# Stub chromadb
for _pkg in ["chromadb", "chromadb.config", "chromadb.errors", "chromadb.utils"]:
    _stub(_pkg)

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
# Fake LLM responses
# ---------------------------------------------------------------------------
FAKE_RAG_ANSWER = json.dumps({
    "answer": "pinMode(pin, mode) configures a digital pin as INPUT, OUTPUT, or INPUT_PULLUP.",
    "confidence": 0.95,
    "follow_up": "How do I use digitalRead() after setting pinMode?",
})

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
# Session fixture: patch backend.app.llm.chat
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def fake_llm_patch():
    """Replace backend.app.llm.chat with a stub — no Groq API key needed."""
    import backend.app.llm  # noqa: F401
    with patch("backend.app.llm.chat", return_value=FAKE_RAG_ANSWER) as mock_chat:
        yield mock_chat


# ---------------------------------------------------------------------------
# Session fixture: FastAPI TestClient
# ---------------------------------------------------------------------------
@pytest.fixture
def api_client(fake_llm_patch):
    """
    Session-scoped TestClient.  All heavy deps and I/O are mocked.
    ProductionMiddleware runs for real so test_production.py can verify
    injection blocking, caching, and latency headers.
    """
    import backend.app.rag  # noqa: F401
    import backend.app.vectorstore  # noqa: F401

    with (
        patch("backend.app.vectorstore.query_collection", return_value=MOCK_HITS),
        patch("backend.app.vectorstore.build_index", return_value=1),
        patch("backend.app.rag.query_collection", return_value=MOCK_HITS),
    ):
        # Remove cached backend imports so the patches above apply to a fresh app.
        sys.modules.pop("backend.main", None)
        from backend.main import app as fastapi_app  # noqa: PLC0415
        with TestClient(fastapi_app, raise_server_exceptions=False) as client:
            yield client
