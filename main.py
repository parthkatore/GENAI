"""
Day 6 — ArduinoMate Chat API (main.py)
----------------------------------------
FastAPI application integrating Groq/Gemini LLM with an ArduinoMate
system prompt.  All previous product-demo code has been replaced with the
real ArduinoMate endpoints.

Endpoints:
    GET  /         - Welcome message
    GET  /health   - Health check with active provider info
    POST /chat     - LLM-powered Arduino Q&A (returns answer, confidence, follow_up)
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from schema import ChatRequest, ChatResponse
from services import generate_response
from app.llm import active_model, _get_provider

load_dotenv()

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ArduinoMate Chat API",
    description=(
        "Day 6 — LLM-powered Arduino assistant. "
        "Ask any Arduino question and get a structured answer with confidence "
        "score and follow-up suggestion."
    ),
    version="2.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow frontend dev server on 5500 and any localhost port
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["System"], summary="Welcome")
def home():
    """Return a welcome message."""
    return {
        "message":  "Welcome to ArduinoMate Chat API",
        "version":  "2.0.0",
        "docs":     "/docs",
        "provider": _get_provider(),
        "model":    active_model(),
    }


@app.get("/health", tags=["System"], summary="Health Check")
def health():
    """Check if the API is running and show the active LLM provider."""
    return {
        "status":   "healthy",
        "service":  "ArduinoMate Chat API",
        "version":  "2.0.0",
        "provider": _get_provider(),
        "model":    active_model(),
    }


@app.post(
    "/chat",
    tags=["Chat"],
    status_code=status.HTTP_200_OK,
    response_model=ChatResponse,
    summary="Ask ArduinoMate a question",
    description=(
        "Send an Arduino question and receive a structured JSON response "
        "with an answer, a confidence score (0–1), and a follow-up suggestion."
    ),
)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """
    POST /chat — LLM-powered Arduino Q&A.

    Request body:
        message : The Arduino question (required).
        task    : 'explain' (default) or 'debug'.

    Response:
        answer     : AI-generated answer.
        confidence : Float 0.0–1.0.
        follow_up  : Suggested next question.
        model      : LLM model name.
        status     : 'success' or 'error'.
    """
    result = generate_response(
        message=payload.message,
        task=payload.task or "explain",
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result["answer"],
        )

    return ChatResponse(**result)
