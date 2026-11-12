"""
ArduinoMate - Smart Search Module
----------------------------------
Implements an intelligent, Machine Learning-based search engine using:
1. TF-IDF (Term Frequency - Inverse Document Frequency) Vectorization
2. Cosine Similarity measurement

This module avoids redundant vectorization by caching fitted vectors
when the underlying dataset has not changed.
"""

from typing import List, Dict, Any, Optional
import hashlib
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SmartSearchEngine:
    """
    Modular TF-IDF + Cosine Similarity search engine for ArduinoMate records.

    Features:
    - Combines multiple text fields (title, description, category, tags).
    - Caches the fitted TF-IDF matrix to avoid expensive recalculation.
    - Gracefully handles empty queries, empty datasets, and missing fields.
    """

    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.records: List[Dict[str, Any]] = []
        self._dataset_hash: Optional[str] = None

    def _extract_record_text(self, record: Dict[str, Any]) -> str:
        """
        Extract and combine all text fields into a single search document.
        Supports both the Arduino-function schema (function_name, syntax, returns,
        common_gotcha) and the legacy project schema (title, description, tags).
        """
        # Arduino function schema fields
        function_name = str(record.get("function_name", "") or "").strip()
        category      = str(record.get("category", "") or "").strip()
        syntax        = str(record.get("syntax", "") or "").strip()
        returns       = str(record.get("returns", "") or "").strip()
        gotcha        = str(record.get("common_gotcha", "") or "").strip()
        description   = str(record.get("description", "") or "").strip()

        # Legacy project schema fields (kept for backward compatibility)
        title   = str(record.get("title", "") or "").strip()
        tags    = record.get("tags", [])
        if isinstance(tags, list):
            tags_text = " ".join(str(t) for t in tags if t)
        else:
            tags_text = str(tags or "").strip()

        combined = f"{function_name} {title} {category} {syntax} {returns} {gotcha} {description} {tags_text}"
        return combined.strip()

    def _compute_hash(self, records: List[Dict[str, Any]]) -> str:
        """Compute an MD5 hash of the records list to detect dataset changes."""
        records_str = json.dumps(records, sort_keys=True, default=str)
        return hashlib.md5(records_str.encode("utf-8")).hexdigest()

    def fit(self, records: List[Dict[str, Any]]) -> "SmartSearchEngine":
        """
        Fit the TF-IDF Vectorizer on the given records.
        Skips recalculation if records have not changed (caching).
        """
        if not records:
            self.records = []
            self.vectorizer = None
            self.tfidf_matrix = None
            self._dataset_hash = None
            return self

        current_hash = self._compute_hash(records)
        # Avoid unnecessary recalculation if dataset is identical
        if self._dataset_hash == current_hash and self.tfidf_matrix is not None:
            return self

        self.records = records
        self._dataset_hash = current_hash

        # Extract text corpus
        corpus = [self._extract_record_text(rec) for rec in records]

        # Initialize TF-IDF Vectorizer:
        # - lowercase=True: makes search case-insensitive
        # - stop_words='english': filters out low-information words like 'the', 'is', 'at'
        # - ngram_range=(1, 2): captures unigrams ("servo") and bigrams ("servo motor")
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2)
        )

        # Fit vectorizer and transform records into a numerical TF-IDF matrix
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        return self

    def search(
        self,
        query: str,
        records: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 5,
        min_score: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Search records using TF-IDF and Cosine Similarity.

        Args:
            query: The search term entered by the user.
            records: Optional dataset (uses pre-fitted dataset if None).
            top_k: Maximum number of ranked results to return.
            min_score: Minimum cosine similarity threshold to consider relevant.

        Returns:
            List of matching records sorted from highest to lowest similarity,
            including a 'similarity_score' field.
        """
        # 1. Handle empty query or whitespace-only query
        if not query or not query.strip():
            return []

        # 2. Update records if provided
        if records is not None:
            self.fit(records)

        # 3. Handle empty dataset or uninitialized vectorizer
        if not self.records or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        cleaned_query = query.strip()

        # 4. Transform query into TF-IDF vector using the SAME fitted vocabulary
        query_vector = self.vectorizer.transform([cleaned_query])

        # 5. If query contains no known vocabulary words, return empty list
        if query_vector.nnz == 0:
            return []

        # 6. Calculate Cosine Similarity between query vector and all document vectors
        # Result is a 1D array of similarity scores between 0.0 and 1.0
        similarity_scores = cosine_similarity(query_vector, self.tfidf_matrix)[0]

        # 7. Collect and rank results
        ranked_results = []
        for index, score in enumerate(similarity_scores):
            if score >= min_score:
                record_copy = dict(self.records[index])
                record_copy["similarity_score"] = round(float(score), 4)
                ranked_results.append((score, record_copy))

        # Sort descending by similarity score
        ranked_results.sort(key=lambda x: x[0], reverse=True)

        # Ensure top_k is an integer
        try:
            top_k_val = int(top_k) if top_k is not None else 5
        except (ValueError, TypeError):
            top_k_val = 5

        # Return top_k records
        return [item[1] for item in ranked_results[:top_k_val]]


# Singleton engine instance for quick re-use across API calls
_global_engine = SmartSearchEngine()


def smart_search(
    query: str,
    records: List[Dict[str, Any]],
    top_k: int = 5,
    min_score: float = 0.01
) -> List[Dict[str, Any]]:
    """
    Convenience function to perform ML search using the cached SmartSearchEngine.
    """
    return _global_engine.search(query=query, records=records, top_k=top_k, min_score=min_score)
