"""
app/rag.py — RAG Pipeline
--------------------------
Retrieval-Augmented Generation for ArduinoMate.

Retrieves the top-k most relevant chunks from ChromaDB, injects them as
grounded context into the LLM prompt, and returns a structured answer with
citations.

If no chunk scores above MIN_SCORE (i.e. the question is out of scope),
the LLM is instructed — and the prompt enforces — an "I don't know" reply
so the system never fabricates out-of-scope answers.

Public API
----------
    rag_answer(question, top_k, min_score, chunk_size) -> RagResponse
"""

from __future__ import annotations

import os
import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.llm import chat, active_model
from app.vectorstore import query_collection

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_TOP_K     = 5       # number of chunks to retrieve
DEFAULT_MIN_SCORE = 0.20    # below this → treat as out-of-scope
OUT_OF_SCOPE_MARKER = "I don't know"


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------
@dataclass
class Citation:
    """One source reference attached to a RAG answer."""
    title:  str
    source: str
    page:   int
    score:  float

    def to_dict(self) -> dict[str, Any]:
        return {
            "title":  self.title,
            "source": self.source,
            "page":   self.page,
            "score":  self.score,
        }


@dataclass
class RagResponse:
    """Full RAG answer returned by rag_answer()."""
    question:    str
    answer:      str
    citations:   list[Citation]
    model:       str
    top_k:       int
    chunk_size:  int        # max_chars used for chunking (config parameter)
    retrieved:   int        # number of chunks actually retrieved
    out_of_scope: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "question":    self.question,
            "answer":      self.answer,
            "citations":   [c.to_dict() for c in self.citations],
            "model":       self.model,
            "top_k":       self.top_k,
            "chunk_size":  self.chunk_size,
            "retrieved":   self.retrieved,
            "out_of_scope": self.out_of_scope,
        }


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------
_SYSTEM_RAG = """\
You are ArduinoMate, an expert AI assistant dedicated to helping beginners
learn Arduino programming.

Your knowledge covers Arduino language reference functions: pinMode,
digitalRead, digitalWrite, analogRead, analogWrite, delay, millis,
Serial.begin, Serial.print, attachInterrupt, map, constrain, random,
and closely related functions.

RULES:
1. Answer ONLY using information found in the CONTEXT block below.
2. If the CONTEXT is empty OR does not contain relevant information for
   the question, reply with EXACTLY:
   {"answer": "I don't know based on the available Arduino documentation.", "confidence": 0.0, "follow_up": ""}
3. Never fabricate hardware wiring, sensor libraries, or facts not in CONTEXT.
4. Be concise and beginner-friendly. Include a short code snippet when helpful.
5. Cite the sources you used in your answer (function name and page number).

Response format (strict JSON):
{
  "answer": "<your full explanation here>",
  "confidence": <float 0.0 – 1.0>,
  "follow_up": "<one suggested follow-up question, or empty string>"
}
"""


def _build_user_prompt(question: str, chunks: list[dict]) -> str:
    """Assemble the user message with retrieved context."""
    if not chunks:
        context_block = "(no relevant documentation found)"
    else:
        lines = []
        for i, c in enumerate(chunks, 1):
            lines.append(
                f"[{i}] {c['title']} (page {c['page']}, score {c['score']:.3f})\n"
                f"Source: {c['source']}\n"
                f"{c['text']}\n"
            )
        context_block = "\n".join(lines)

    return (
        f"CONTEXT:\n{context_block}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using ONLY the context above. Return strict JSON."
    )


# ---------------------------------------------------------------------------
# JSON extractor
# ---------------------------------------------------------------------------
def _extract_json(raw: str) -> dict[str, Any]:
    """
    Extract the first JSON object from a raw LLM reply.
    Handles markdown code fences, thinking tags, and stray text.
    """
    # Strip <think>...</think> tags (some models emit these)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    # Hard fallback
    return {
        "answer":     raw.strip() or OUT_OF_SCOPE_MARKER,
        "confidence": 0.5,
        "follow_up":  "",
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def rag_answer(
    question:   str,
    top_k:      int   = DEFAULT_TOP_K,
    min_score:  float = DEFAULT_MIN_SCORE,
    chunk_size: int   = 500,          # recorded in response for eval comparison
) -> RagResponse:
    """
    Full RAG pipeline: retrieve → augment → generate.

    Args:
        question   : The user's Arduino question.
        top_k      : How many chunks to retrieve from ChromaDB.
        min_score  : Minimum cosine similarity; chunks below this are dropped.
        chunk_size : The MAX_CHARS value the chunker was built with (metadata
                     only — rag_answer does not re-chunk; it's used for eval
                     logging so two configs can be compared).

    Returns:
        RagResponse with answer, citations, and metadata.
    """
    model_name = active_model()

    # 1. Retrieve
    chunks = query_collection(query=question, n_results=top_k, min_score=min_score)
    out_of_scope = len(chunks) == 0

    # 2. Build prompt
    messages = [
        {"role": "system", "content": _SYSTEM_RAG},
        {"role": "user",   "content": _build_user_prompt(question, chunks)},
    ]

    # 3. Call LLM
    try:
        raw = chat(messages, temperature=0.2)
        parsed = _extract_json(raw)
    except Exception as exc:
        parsed = {
            "answer":     f"ArduinoMate encountered an error: {exc}",
            "confidence": 0.0,
            "follow_up":  "",
        }

    answer = str(parsed.get("answer", OUT_OF_SCOPE_MARKER)).strip()

    # Enforce "I don't know" if no chunks were retrieved regardless of LLM output
    if out_of_scope and OUT_OF_SCOPE_MARKER.lower() not in answer.lower():
        answer = "I don't know based on the available Arduino documentation."

    # 4. Build citations
    citations = [
        Citation(
            title=c["title"],
            source=c["source"],
            page=c["page"],
            score=c["score"],
        )
        for c in chunks
    ]

    return RagResponse(
        question=question,
        answer=answer,
        citations=citations,
        model=model_name,
        top_k=top_k,
        chunk_size=chunk_size,
        retrieved=len(chunks),
        out_of_scope=out_of_scope,
    )
