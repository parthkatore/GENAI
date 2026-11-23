"""
app/embed.py — Embedding Engine
---------------------------------
Generates dense vector embeddings through the Gemini API, avoiding a local
transformer model and its memory overhead.

Public API
----------
    embed_texts(texts)       -> np.ndarray  shape (N, 3072)
    embed_query(query)       -> np.ndarray  shape (3072,)
    semantic_search(query, chunks, top_k) -> list[SearchResult]
"""

import os
from dataclasses import dataclass
from typing import Any

import numpy as np

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 3072
EMBEDDING_BATCH_SIZE = 50
_client: Any | None = None


def _get_client() -> Any:
    """Return the shared Gemini API client, creating it on first use."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for document embeddings.")
        from google import genai

        _client = genai.Client(api_key=api_key)
    return _client


def embed_texts(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> np.ndarray:
    """
    Embed strings in bounded API batches and return unit-normalised vectors.

    Args:
        texts     : List of strings to embed.
        task_type : Gemini embedding task type for documents or queries.

    Returns:
        numpy array of shape (len(texts), 3072), dtype float32.
    """
    if not texts:
        return np.empty((0, EMBEDDING_DIMENSIONS), dtype=np.float32)

    client = _get_client()
    from google.genai import types

    config = types.EmbedContentConfig(task_type=task_type)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[start : start + EMBEDDING_BATCH_SIZE]
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=config,
        )
        embeddings = response.embeddings
        if embeddings is None or len(embeddings) != len(batch):
            raise RuntimeError("Gemini returned an unexpected number of embeddings.")
        for embedding in embeddings:
            if embedding.values is None or len(embedding.values) != EMBEDDING_DIMENSIONS:
                raise ValueError(
                    f"Gemini returned an embedding with an unexpected size; "
                    f"expected {EMBEDDING_DIMENSIONS} dimensions."
                )
            vectors.append(embedding.values)

    vectors_array = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(vectors_array, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return (vectors_array / norms).astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.

    Returns:
        numpy array of shape (3072,), normalised.
    """
    return embed_texts([query], task_type="RETRIEVAL_QUERY")[0]


# ---------------------------------------------------------------------------
# SearchResult dataclass
# ---------------------------------------------------------------------------
@dataclass
class SearchResult:
    """One ranked result from semantic_search()."""
    chunk_id:  str
    title:     str
    source:    str
    page:      int
    category:  str
    text:      str
    score:     float   # cosine similarity 0.0 – 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id":  self.chunk_id,
            "title":     self.title,
            "source":    self.source,
            "page":      self.page,
            "category":  self.category,
            "text":      self.text[:300] + ("..." if len(self.text) > 300 else ""),
            "score":     round(self.score, 4),
        }


# ---------------------------------------------------------------------------
# Semantic search over a list of Chunk objects
# ---------------------------------------------------------------------------
def semantic_search(
    query:   str,
    chunks,          # list[Chunk]
    top_k:   int = 5,
    min_score: float = 0.15,
) -> list[SearchResult]:
    """
    Search a list of Chunk objects by semantic similarity.

    Args:
        query     : User query string.
        chunks    : list[Chunk] from app.chunking.
        top_k     : Maximum results to return.
        min_score : Minimum cosine similarity to include.

    Returns:
        List of SearchResult sorted by score descending.
    """
    if not chunks:
        return []

    texts       = [c.text for c in chunks]
    doc_vecs    = embed_texts(texts)          # (N, 3072)
    query_vec   = embed_query(query)          # (3072,)

    scores      = doc_vecs @ query_vec        # cosine sim (unit vectors)

    # Rank
    ranked_idx  = np.argsort(scores)[::-1]

    results: list[SearchResult] = []
    for i in ranked_idx[:top_k]:
        s = float(scores[i])
        if s < min_score:
            break
        c = chunks[i]
        results.append(
            SearchResult(
                chunk_id=c.chunk_id,
                title=c.title,
                source=c.source,
                page=c.page,
                category=c.category,
                text=c.text,
                score=s,
            )
        )

    return results


if __name__ == "__main__":
    from app.chunking import load_all_chunks

    chunks = load_all_chunks()
    print(f"Chunks loaded: {len(chunks)}")

    test_queries = [
        "What does pinMode do?",
        "how to read analog sensor value",
        "delay vs millis non-blocking",
        "serial monitor baud rate mismatch",
        "interrupt ISR volatile variable",
    ]

    for q in test_queries:
        print(f"\nQuery: {q!r}")
        for r in semantic_search(q, chunks, top_k=3):
            print(f"  [{r.score:.3f}] {r.title:25s} (page {r.page}) {r.text[:60]}...")
