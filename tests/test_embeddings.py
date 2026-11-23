from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import app.embed as embed
import app.vectorstore as vectorstore

_build_index = vectorstore.build_index


def test_embed_texts_batches_requests_and_normalizes_vectors():
    client = MagicMock()
    vector = [3.0, 4.0] + [0.0] * (embed.EMBEDDING_DIMENSIONS - 2)
    client.models.embed_content.side_effect = lambda **kwargs: SimpleNamespace(
        embeddings=[
            SimpleNamespace(values=vector)
            for _ in kwargs["contents"]
        ]
    )

    with patch("app.embed._get_client", return_value=client):
        result = embed.embed_texts(["Arduino docs"] * 51)

    assert result.shape == (51, embed.EMBEDDING_DIMENSIONS)
    assert np.allclose(result[0, :2], [0.6, 0.8])
    assert [len(call.kwargs["contents"]) for call in client.models.embed_content.call_args_list] == [
        10,
        10,
        10,
        10,
        10,
        1,
    ]
    assert all(
        call.kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"
        for call in client.models.embed_content.call_args_list
    )
    assert all(
        call.kwargs["config"].output_dimensionality == embed.EMBEDDING_DIMENSIONS
        for call in client.models.embed_content.call_args_list
    )


def test_embed_query_uses_retrieval_query_task_type():
    vectors = np.ones((1, embed.EMBEDDING_DIMENSIONS), dtype=np.float32)
    with patch("app.embed.embed_texts", return_value=vectors) as embed_texts:
        result = embed.embed_query("How does pinMode work?")

    assert result.shape == (embed.EMBEDDING_DIMENSIONS,)
    embed_texts.assert_called_once_with(
        ["How does pinMode work?"],
        task_type="RETRIEVAL_QUERY",
    )


def test_embed_requires_gemini_api_key(monkeypatch):
    monkeypatch.setattr(embed, "_client", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        embed.embed_texts(["Arduino docs"])


def test_build_index_rebuilds_legacy_embedding_collection():
    legacy_collection = MagicMock()
    legacy_collection.count.return_value = 2
    legacy_collection.metadata = {"hnsw:space": "cosine"}
    new_collection = MagicMock()
    new_collection.count.return_value = 0
    client = MagicMock()
    chunk = SimpleNamespace(
        text="Arduino documentation text",
        chunk_id="doc-1",
        source="docs/arduino.adoc",
        title="Arduino",
        page=1,
        category="General",
    )
    vectors = np.zeros((1, embed.EMBEDDING_DIMENSIONS), dtype=np.float32)

    with (
        patch.object(vectorstore, "_collection", None),
        patch.object(vectorstore, "_get_client", return_value=client),
        patch.object(
            vectorstore,
            "get_collection",
            side_effect=[legacy_collection, new_collection],
        ),
        patch.object(vectorstore, "load_all_chunks", return_value=[chunk]),
        patch.object(vectorstore, "embed_texts", return_value=vectors),
    ):
        assert _build_index() == 1

    client.delete_collection.assert_called_once_with(vectorstore.COLLECTION_NAME)
    new_collection.add.assert_called_once()
