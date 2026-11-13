"""
Day 6 — Pydantic Schemas for ArduinoMate Chat API
---------------------------------------------------
Request and response models for the POST /chat endpoint.

Response shape (JSON):
    {
        "answer":     "<AI explanation>",
        "confidence": 0.95,
        "follow_up":  "<suggested next question>"
    }
"""

from pydantic import BaseModel, Field
from typing import Optional


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    """
    Payload sent by the client to POST /chat.

    Fields:
        message  : The user's Arduino question (required).
        task     : Prompt template to use — 'explain' (default) or 'debug'.
    """
    message: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The user's Arduino question or problem.",
        json_schema_extra={"example": "What does pinMode() do in Arduino?"}
    )
    task: Optional[str] = Field(
        default="explain",
        description="Task type: 'explain' for function explanations, 'debug' for debugging help.",
        json_schema_extra={"example": "explain"}
    )


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------
class ChatResponse(BaseModel):
    """
    Response returned by POST /chat.

    Fields:
        answer     : The AI-generated explanation or debug help.
        confidence : Model's self-reported confidence (0.0–1.0).
        follow_up  : One suggested follow-up question.
        model      : LLM model name used for this response.
        status     : 'success' or 'error'.
    """
    answer: str = Field(description="The AI-generated answer.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0."
    )
    follow_up: str = Field(description="Suggested follow-up question.")
    model: str = Field(description="LLM model used for generation.")
    status: str = Field(description="'success' or 'error'.")
