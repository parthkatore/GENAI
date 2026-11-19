"""
tests/test_search.py — Semantic search and chunking unit tests.
---------------------------------------------------------------
Tests app.vectorstore.query_collection (mocked) and
app.chunking.load_all_chunks to validate the retrieval pipeline
without requiring a live ChromaDB index or network calls.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


class TestChunking:
    """Chunk loading from the ArduinoMate data sources."""

    def test_load_all_chunks_returns_list(self):
        """load_all_chunks() must return a non-empty list."""
        from app.chunking import load_all_chunks

        chunks = load_all_chunks()
        assert isinstance(chunks, list)
        assert len(chunks) > 0, "Expected at least one chunk from records.json or .adoc files"

    def test_chunks_have_required_attributes(self):
        """Every Chunk must expose text, source, title, page, category, chunk_id."""
        from app.chunking import Chunk, load_all_chunks

        chunks = load_all_chunks()
        for chunk in chunks[:10]:  # spot-check the first 10
            assert isinstance(chunk, Chunk)
            assert chunk.text.strip(), f"Empty text in chunk {chunk.chunk_id}"
            assert chunk.source, f"Empty source in chunk {chunk.chunk_id}"
            assert chunk.title, f"Empty title in chunk {chunk.chunk_id}"
            assert chunk.page >= 1, f"Page must be >= 1 in chunk {chunk.chunk_id}"
            assert chunk.chunk_id, "chunk_id must be non-empty"

    def test_chunk_ids_are_unique(self):
        """All chunk IDs in the loaded set must be unique."""
        from app.chunking import load_all_chunks

        chunks = load_all_chunks()
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "Duplicate chunk_ids found"

    def test_chunk_text_minimum_length(self):
        """No chunk should be shorter than MIN_CHARS (60 characters)."""
        from app.chunking import MIN_CHARS, load_all_chunks

        chunks = load_all_chunks()
        short = [c for c in chunks if len(c.text) < MIN_CHARS]
        assert not short, (
            f"{len(short)} chunks are shorter than MIN_CHARS={MIN_CHARS}: "
            f"{[c.chunk_id for c in short[:3]]}"
        )


class TestSemanticSearch:
    """query_collection returns ranked, schema-valid results."""

    _MOCK_HITS = [
        {
            "title": "pinMode()",
            "source": "ArduinoMate/data/raw/pinMode.adoc",
            "page": 1,
            "category": "Digital I/O",
            "text": "pinMode(pin, mode) configures the specified pin as INPUT or OUTPUT.",
            "score": 0.87,
        },
        {
            "title": "digitalWrite()",
            "source": "ArduinoMate/data/raw/digitalWrite.adoc",
            "page": 1,
            "category": "Digital I/O",
            "text": "digitalWrite(pin, value) writes a HIGH or LOW value to a digital pin.",
            "score": 0.72,
        },
    ]

    def test_query_returns_list_of_dicts(self):
        """query_collection must return a list of dicts with required keys."""
        with patch("app.vectorstore.query_collection", return_value=self._MOCK_HITS):
            from app.vectorstore import query_collection

            results = query_collection("What does pinMode do?", n_results=5)
            assert isinstance(results, list)
            assert len(results) == 2

    def test_query_results_have_required_keys(self):
        """Each result dict must have title, source, page, text, score."""
        with patch("app.vectorstore.query_collection", return_value=self._MOCK_HITS):
            from app.vectorstore import query_collection

            results = query_collection("digital pin")
            for hit in results:
                for key in ("title", "source", "page", "text", "score"):
                    assert key in hit, f"Missing key '{key}' in result: {hit}"

    def test_scores_are_in_valid_range(self):
        """All returned scores must be between 0.0 and 1.0."""
        with patch("app.vectorstore.query_collection", return_value=self._MOCK_HITS):
            from app.vectorstore import query_collection

            results = query_collection("pin mode")
            for hit in results:
                assert 0.0 <= hit["score"] <= 1.0, (
                    f"Score {hit['score']} out of range for '{hit['title']}'"
                )

    def test_empty_collection_returns_empty_list(self):
        """When the collection is empty, query_collection returns []."""
        with patch("app.vectorstore.query_collection", return_value=[]):
            from app.vectorstore import query_collection

            results = query_collection("anything")
            assert results == []
