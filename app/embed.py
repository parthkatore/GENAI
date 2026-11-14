"""
app/embed.py — Embedding Engine
---------------------------------
Generates dense vector embeddings for text using sentence-transformers
(all-MiniLM-L6-v2, 384-dim).

The HF model cache is redirected to D:/hf_cache to avoid filling the
C: drive.  If the model is not cached yet it downloads automatically on
first use (~90 MB).

Public API
----------
    get_embedder()           -> SentenceTransformer (cached singleton)
    embed_texts(texts)       -> np.ndarray  shape (N, 384)
    embed_query(query)       -> np.ndarray  shape (384,)
    semantic_search(query, chunks, top_k) -> list[SearchResult]
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Any

# Redirect HF cache to D drive to avoid filling C:
os.environ.setdefault("HF_HOME", "D:/hf_cache")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

MODEL_NAME = "all-MiniLM-L6-v2"
_embedder  = None   # module-level singleton


def get_embedder():
    """Return the shared SentenceTransformer instance (lazy load)."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Embed a list of strings.

    Args:
        texts : List of strings to embed.

    Returns:
        numpy array of shape (len(texts), 384), dtype float32.
    """
    model = get_embedder()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    # Normalise to unit length for cosine similarity via dot product
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return (vectors / norms).astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.

    Returns:
        numpy array of shape (384,), normalised.
    """
    return embed_texts([query])[0]


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
    doc_vecs    = embed_texts(texts)          # (N, 384)
    query_vec   = embed_query(query)          # (384,)

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
