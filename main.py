"""
ArduinoMate Chat API — main.py
--------------------------------
Day 6: POST /chat  — LLM-powered Arduino Q&A
Day 7: GET  /search/semantic?q=  — ChromaDB semantic search

Endpoints:
    GET  /                      Welcome + provider info
    GET  /health                Health check
    POST /chat                  LLM answer (answer, confidence, follow_up)
    GET  /search/semantic?q=    Vector-store semantic search over all docs
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from schema import ChatRequest, ChatResponse, SemanticSearchResponse, SemanticHit
from services import generate_response
from app.llm import active_model, _get_provider

load_dotenv()


# ---------------------------------------------------------------------------
# Lifespan — build vector index on startup (skip if already indexed)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.vectorstore import build_index
    build_index(force_rebuild=False)
    yield


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ArduinoMate Chat API",
    description=(
        "Day 7 — Semantic search over ArduinoMate docs (ChromaDB + sentence-transformers) "
        "plus LLM-powered Q&A (Groq / Gemini)."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["System"], summary="Welcome")
def home():
    return {
        "message":  "Welcome to ArduinoMate API",
        "version":  "3.0.0",
        "docs":     "/docs",
        "provider": _get_provider(),
        "model":    active_model(),
    }


@app.get("/health", tags=["System"], summary="Health Check")
def health():
    from app.vectorstore import get_collection
    try:
        count = get_collection().count()
    except Exception:
        count = -1
    return {
        "status":        "healthy",
        "service":       "ArduinoMate API",
        "version":       "3.0.0",
        "provider":      _get_provider(),
        "model":         active_model(),
        "indexed_chunks": count,
    }


@app.post(
    "/chat",
    tags=["Chat"],
    status_code=status.HTTP_200_OK,
    response_model=ChatResponse,
    summary="Ask ArduinoMate a question",
    description=(
        "Send an Arduino question. Returns a structured JSON response "
        "with an answer, confidence score, and follow-up suggestion."
    ),
)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
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


@app.get(
    "/search/semantic",
    tags=["Search"],
    response_model=SemanticSearchResponse,
    summary="Semantic search over ArduinoMate documents",
    description=(
        "Query the ChromaDB vector store with a natural-language question. "
        "Returns ranked chunks from real Arduino documentation."
    ),
)
def semantic_search_endpoint(
    q: str = Query(
        ...,
        min_length=2,
        description="Natural-language search query.",
        json_schema_extra={"example": "how to read a button press"},
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results to return.",
    ),
) -> SemanticSearchResponse:
    from app.vectorstore import query_collection

    if not q.strip():
        return SemanticSearchResponse(query=q, total_results=0, results=[])

    hits = query_collection(query=q, n_results=limit, min_score=0.15)

    return SemanticSearchResponse(
        query=q,
        total_results=len(hits),
        results=[SemanticHit(**h) for h in hits],
    )
