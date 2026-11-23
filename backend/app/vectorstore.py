"""
app/vectorstore.py — Persistent ChromaDB Vector Store
-------------------------------------------------------
Indexes all ArduinoMate chunks into a persistent ChromaDB collection
stored at data/chroma_db/.

The collection is created once; subsequent imports reuse the persisted
data without re-indexing (unless force_rebuild=True is passed).

Public API
----------
    get_collection()   -> chromadb.Collection  (the live Chroma collection)
    build_index(force_rebuild=False)            index all chunks
    query_collection(query, n_results, min_score) -> list[dict]

GET /search/semantic?q=  calls query_collection() directly.
"""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from backend.app.chunking import load_all_chunks
from backend.app.embed import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, embed_texts

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
COLLECTION_NAME = "arduinomate_docs"
COLLECTION_METADATA = {
    "hnsw:space": "cosine",
    "embedding_model": EMBEDDING_MODEL,
    "embedding_dimensions": EMBEDDING_DIMENSIONS,
}


class VectorIndexNotReadyError(RuntimeError):
    """Raised when semantic search is requested before documents are indexed."""


# ---------------------------------------------------------------------------
# ChromaDB client (persistent)
# ---------------------------------------------------------------------------
_client:     chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection() -> chromadb.Collection:
    """
    Return the ArduinoMate ChromaDB collection.
    Creates it if it doesn't exist yet.
    """
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata=COLLECTION_METADATA,
        )
    return _collection


# ---------------------------------------------------------------------------
# Build / rebuild the index
# ---------------------------------------------------------------------------
def build_index(force_rebuild: bool = False) -> int:
    """
    Index all ArduinoMate chunks into the Chroma collection.

    Args:
        force_rebuild : If True, delete and recreate the collection first.

    Returns:
        Total number of chunks indexed.
    """
    global _collection
    client = _get_client()
    collection = get_collection()

    if force_rebuild:
        client.delete_collection(COLLECTION_NAME)
        _collection = None
        collection = get_collection()
    elif collection.count() > 0:
        metadata = collection.metadata or {}
        if (
            metadata.get("embedding_model") != EMBEDDING_MODEL
            or metadata.get("embedding_dimensions") != EMBEDDING_DIMENSIONS
        ):
            print("[vectorstore] Existing index uses incompatible embeddings; rebuilding.")
            client.delete_collection(COLLECTION_NAME)
            _collection = None
            collection = get_collection()

    # Skip if already indexed
    if not force_rebuild and collection.count() > 0:
        print(f"[vectorstore] Collection already has {collection.count()} chunks. Skipping rebuild.")
        return collection.count()

    chunks  = load_all_chunks()
    if not chunks:
        print("[vectorstore] No chunks found — nothing to index.")
        return 0

    # Embed all chunks
    print(f"[vectorstore] Embedding {len(chunks)} chunks …")
    texts    = [c.text for c in chunks]
    vectors  = embed_texts(texts)             # (N, 768) float32, unit-normalised

    # ChromaDB add in batches of 100 (API limit)
    BATCH = 100
    total  = 0
    for i in range(0, len(chunks), BATCH):
        batch_chunks  = chunks[i : i + BATCH]
        batch_vectors = vectors[i : i + BATCH]

        collection.add(
            ids         = [c.chunk_id for c in batch_chunks],
            embeddings  = batch_vectors.tolist(),
            documents   = [c.text for c in batch_chunks],
            metadatas   = [
                {
                    "source":   c.source,
                    "title":    c.title,
                    "page":     c.page,
                    "category": c.category,
                }
                for c in batch_chunks
            ],
        )
        total += len(batch_chunks)

    print(f"[vectorstore] Indexed {total} chunks into '{COLLECTION_NAME}'.")
    return total


# ---------------------------------------------------------------------------
# Query the collection
# ---------------------------------------------------------------------------
def query_collection(
    query:      str,
    n_results:  int   = 5,
    min_score:  float = 0.20,
) -> list[dict[str, Any]]:
    """
    Semantic search over the Chroma collection.

    Args:
        query     : Free-text query string.
        n_results : Maximum results to return.
        min_score : Minimum cosine similarity to include (0.0 – 1.0).
                    Chroma returns *distance* (lower = more similar when
                    using cosine space).  We convert: score = 1 - distance.

    Returns:
        List of dicts with keys: chunk_id, title, source, page, category,
        text (truncated to 300 chars), score.
    """
    from backend.app.embed import embed_query

    collection = get_collection()
    collection_count = collection.count()
    if collection_count == 0:
        raise VectorIndexNotReadyError(
            "The Arduino documentation index is empty. Check GEMINI_API_KEY and backend startup logs."
        )

    query_vec   = embed_query(query).tolist()

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=min(n_results, collection_count),
        include=["documents", "metadatas", "distances"],
    )

    hits: list[dict[str, Any]] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # Chroma cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity: 1 - (dist / 2)  → range [0, 1]
        score = round(1.0 - dist / 2.0, 4)
        if score < min_score:
            continue
        hits.append(
            {
                "title":    meta.get("title", ""),
                "source":   meta.get("source", ""),
                "page":     meta.get("page", 1),
                "category": meta.get("category", ""),
                "text":     doc[:300] + ("..." if len(doc) > 300 else ""),
                "score":    score,
            }
        )

    return hits


# ---------------------------------------------------------------------------
# CLI usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    build_index(force_rebuild=True)

    test_queries = [
        "What does pinMode do?",
        "how to use analogRead with floating pin",
        "delay vs millis non-blocking timing",
        "serial monitor baud rate",
        "attachInterrupt ISR volatile",
    ]

    print("\n--- Semantic Search Test ---")
    for q in test_queries:
        print(f"\nQuery: {q!r}")
        for h in query_collection(q, n_results=3):
            print(f"  [{h['score']:.3f}] {h['title']:25s} p{h['page']} | {h['text'][:60]}...")
