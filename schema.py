"""
Day 6 / Day 7 — Pydantic Schemas for ArduinoMate Chat API
-----------------------------------------------------------
Request and response models for POST /chat and GET /search/semantic.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any


# ---------------------------------------------------------------------------
# Chat schemas (Day 6)
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    """
    Payload sent by the client to POST /chat.

    Fields:
        message : The user's Arduino question (required).
        task    : Prompt template — 'explain' (default) or 'debug'.
    """
    message: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The user's Arduino question or problem.",
        json_schema_extra={"example": "What does pinMode() do in Arduino?"},
    )
    task: Optional[str] = Field(
        default="explain",
        description="'explain' for function explanations, 'debug' for debugging help.",
        json_schema_extra={"example": "explain"},
    )


class ChatResponse(BaseModel):
    """
    Response returned by POST /chat.

    Fields:
        answer     : The AI-generated explanation or debug help.
        confidence : Model self-reported confidence (0.0 – 1.0).
        follow_up  : One suggested follow-up question.
        model      : LLM model name.
        status     : 'success' or 'error'.
    """
    answer:     str   = Field(description="The AI-generated answer.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0 – 1.0.")
    follow_up:  str   = Field(description="Suggested follow-up question.")
    model:      str   = Field(description="LLM model used for generation.")
    status:     str   = Field(description="'success' or 'error'.")


# ---------------------------------------------------------------------------
# Semantic search schemas (Day 7)
# ---------------------------------------------------------------------------
class SemanticHit(BaseModel):
    """One result from the vector-store semantic search."""
    title:    str   = Field(description="Arduino function name.")
    source:   str   = Field(description="Source file path.")
    page:     int   = Field(description="Section / chunk index within the document.")
    category: str   = Field(description="Arduino category (e.g. 'Digital I/O').")
    text:     str   = Field(description="Chunk text (truncated to 300 chars).")
    score:    float = Field(description="Cosine similarity score 0.0 – 1.0.")


class SemanticSearchResponse(BaseModel):
    """Response returned by GET /search/semantic."""
    query:         str               = Field(description="The original search query.")
    total_results: int               = Field(description="Number of hits returned.")
    results:       List[SemanticHit] = Field(description="Ranked list of matching chunks.")


# ---------------------------------------------------------------------------
# RAG schemas (Day 8)
# ---------------------------------------------------------------------------
class AskRequest(BaseModel):
    """
    Payload sent by the client to POST /ask.

    Fields:
        question   : The user's Arduino question (required).
        top_k      : How many chunks to retrieve (default 5).
        min_score  : Minimum cosine similarity threshold (default 0.20).
    """
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The user's Arduino question.",
        json_schema_extra={"example": "What does pinMode() do in Arduino?"},
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of chunks to retrieve from the vector store.",
    )
    min_score: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity to include a chunk.",
    )


class RagCitation(BaseModel):
    """One source reference attached to a RAG answer."""
    title:  str   = Field(description="Arduino function name.")
    source: str   = Field(description="Source file path.")
    page:   int   = Field(description="Chunk / section index within the document.")
    score:  float = Field(description="Cosine similarity score 0.0 – 1.0.")


class AskResponse(BaseModel):
    """Response returned by POST /ask."""
    question:     str             = Field(description="The original question.")
    answer:       str             = Field(description="RAG-grounded answer from the LLM.")
    citations:    List[RagCitation] = Field(description="Source chunks used to generate the answer.")
    model:        str             = Field(description="LLM model name used.")
    retrieved:    int             = Field(description="Number of chunks retrieved.")
    out_of_scope: bool            = Field(description="True when no relevant chunks were found.")
