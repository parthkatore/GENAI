"""
ArduinoMate Chat API -- main.py
--------------------------------
Day  6: POST /chat            -- LLM-powered Arduino Q&A
Day  7: GET  /search/semantic -- ChromaDB semantic search
Day  8: POST /ask             -- RAG-grounded answer with citations
Day  9: POST /agent           -- Tool-using agent (ReAct loop or LangGraph)
Day 12: Production middleware -- latency logging, token tracking, cache, injection guard

Endpoints:
    GET  /                   Welcome + provider info
    GET  /health             Health check
    POST /chat               LLM answer (answer, confidence, follow_up)
    GET  /search/semantic    Vector-store semantic search over all docs
    POST /ask                RAG answer with citations
    POST /agent              Agent with tools (rag_search + led_resistor_calculator)
"""

import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.llm import _get_provider, active_model
from backend.app.middleware import ProductionMiddleware
from backend.app.vectorstore import VectorIndexNotReadyError
from backend.schema import (
    AgentRequest,
    AgentResponse,
    AgentStepOut,
    AskRequest,
    AskResponse,
    ChatRequest,
    ChatResponse,
    RagCitation,
    SemanticHit,
    SemanticSearchResponse,
)
from backend.services import generate_response

# ---------------------------------------------------------------------------
# Logging -- structured single-line format, INFO level
# ---------------------------------------------------------------------------
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
})


# ---------------------------------------------------------------------------
# Lifespan -- build vector index in a background thread so the port binds
# immediately (Render's port scanner won't time out waiting for embeddings)
# ---------------------------------------------------------------------------
_index_status = "not_started"


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    import logging as _logging

    _log = _logging.getLogger("arduinomate")

    async def _build():
        global _index_status
        from backend.app.vectorstore import build_index

        _index_status = "building"
        _log.info("[startup] building vector index in background thread")
        try:
            count = await asyncio.to_thread(build_index, False)
            if count == 0:
                raise RuntimeError("No Arduino documentation chunks were indexed.")
        except Exception:
            _index_status = "failed"
            _log.exception("[startup] vector index build failed")
        else:
            _index_status = "ready"
            _log.info("[startup] vector index ready with %s chunks", count)

    asyncio.create_task(_build())
    yield


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ArduinoMate Chat API",
    description=(
        "Day 12 -- Production-hardened ArduinoMate API. "
        "Includes latency/token logging, response caching, input-length limits, "
        "and prompt-injection detection. "
        "POST /agent: ReAct loop + LangGraph with memory and approval. "
        "POST /ask: RAG-grounded answers. POST /chat: direct LLM chat."
    ),
    version="6.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware -- order matters: add ProductionMiddleware first so it wraps
# everything, then CORSMiddleware for browser preflight handling.
# ---------------------------------------------------------------------------
app.add_middleware(ProductionMiddleware)
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


@app.exception_handler(VectorIndexNotReadyError)
async def vector_index_not_ready_handler(
    request: Request,
    exc: VectorIndexNotReadyError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", tags=["System"], summary="Welcome")
def home():
    return {
        "message":  "Welcome to ArduinoMate API",
        "version":  "6.0.0",
        "docs":     "/docs",
        "provider": _get_provider(),
        "model":    active_model(),
    }


@app.get("/health", tags=["System"], summary="Health Check")
def health():
    from backend.app.middleware import get_cache
    from backend.app.vectorstore import get_collection
    try:
        count = get_collection().count()
    except Exception:
        count = -1
    cache = get_cache()
    rag_status = (
        "ready"
        if isinstance(count, int) and count > 0
        else _index_status
    )
    return {
        "status":          "healthy",
        "service":         "ArduinoMate API",
        "version":         "6.0.0",
        "provider":        _get_provider(),
        "model":           active_model(),
        "indexed_chunks":  count,
        "rag_status":      rag_status,
        "cache_size":      cache.size,
        "cache_hits":      cache.hits,
        "cache_misses":    cache.misses,
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
    from backend.app.vectorstore import query_collection
    if not q.strip():
        return SemanticSearchResponse(query=q, total_results=0, results=[])
    hits = query_collection(query=q, n_results=limit, min_score=0.15)
    return SemanticSearchResponse(
        query=q,
        total_results=len(hits),
        results=[SemanticHit(**h) for h in hits],
    )


@app.post(
    "/ask",
    tags=["RAG"],
    status_code=status.HTTP_200_OK,
    response_model=AskResponse,
    summary="RAG-grounded answer with citations",
    description=(
        "Retrieves the most relevant Arduino documentation chunks from ChromaDB, "
        "injects them as context into the LLM prompt, and returns a grounded answer "
        "with source citations. Replies 'I don't know' for out-of-scope questions "
        "(e.g. HC-SR04 sensor wiring)."
    ),
)
def ask_endpoint(payload: AskRequest) -> AskResponse:
    from backend.app.rag import rag_answer
    result = rag_answer(
        question=payload.question,
        top_k=payload.top_k,
        min_score=payload.min_score,
    )
    return AskResponse(
        question=result.question,
        answer=result.answer,
        citations=[RagCitation(**c.to_dict()) for c in result.citations],
        model=result.model,
        retrieved=result.retrieved,
        out_of_scope=result.out_of_scope,
    )


@app.post(
    "/agent",
    tags=["Agent"],
    status_code=status.HTTP_200_OK,
    response_model=AgentResponse,
    summary="Tool-using agent (ReAct loop or LangGraph)",
    description=(
        "Runs an agent that can call two tools: "
        "`rag_search` (Arduino documentation Q&A) and "
        "`led_resistor_calculator` (Ohm's law E12 resistor calculator). "
        "Set `use_graph=true` (default) for the LangGraph agent with memory and "
        "an approval gate. Set `use_graph=false` for the hand-written ReAct loop. "
        "Pass the same `thread_id` across requests to continue a conversation."
    ),
)
def agent_endpoint(payload: AgentRequest) -> AgentResponse:
    if payload.use_graph:
        from backend.app.graph import run_graph
        result = run_graph(
            user_message=payload.message,
            thread_id=payload.thread_id or "default",
            approved=payload.approved,
        )
        steps = [AgentStepOut(**s) for s in result.steps]
        return AgentResponse(
            answer=result.answer,
            steps=steps,
            model=result.model,
            thread_id=result.thread_id,
            num_steps=len(steps),
        )
    else:
        from backend.app.agent_loop import run_agent
        result = run_agent(
            user_message=payload.message,
            session_id=payload.thread_id or "default",
        )
        steps = [AgentStepOut(**s) for s in result.to_dict()["steps"]]
        return AgentResponse(
            answer=result.answer,
            steps=steps,
            model=result.model,
            thread_id=payload.thread_id or "default",
            num_steps=len(steps),
        )
