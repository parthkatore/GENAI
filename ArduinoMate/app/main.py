"""
ArduinoMate - FastAPI Application
----------------------------------
Main entrypoint for the ArduinoMate Week-1 backend service.

Endpoints:
1. GET  /health         - Check API status and dataset information.
2. GET  /records        - Retrieve Arduino records with optional limit parameter.
3. GET  /records/{id}   - Retrieve a specific record by ID (or 404 if not found).
4. GET  /search?q=      - Smart search using TF-IDF and Cosine Similarity.
5. POST /questions      - Submit and validate user questions via Pydantic model.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.smart_search import SmartSearchEngine, smart_search

# -----------------------------------------------------------------------------
# Path Configuration
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "records.json"
QUESTIONS_FILE = BASE_DIR / "data" / "questions.json"


# -----------------------------------------------------------------------------
# Data Helper Functions
# -----------------------------------------------------------------------------
def load_records() -> List[Dict[str, Any]]:
    """Load ArduinoMate records from data/records.json."""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def load_saved_questions() -> List[Dict[str, Any]]:
    """Load previously saved user questions if available."""
    if not QUESTIONS_FILE.exists():
        return []
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def persist_questions() -> None:
    """Save submitted questions to data/questions.json."""
    QUESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(questions_db, f, indent=2)


# -----------------------------------------------------------------------------
# Initial State & Pre-training
# -----------------------------------------------------------------------------
# Initialize database and train search engine at module load time
records_db: List[Dict[str, Any]] = load_records()
questions_db: List[Dict[str, Any]] = load_saved_questions()

search_engine = SmartSearchEngine()
if records_db:
    search_engine.fit(records_db)


# -----------------------------------------------------------------------------
# Application Lifespan (Startup / Shutdown)
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown logging."""
    global records_db, questions_db
    if not records_db:
        records_db = load_records()
        if records_db:
            search_engine.fit(records_db)
    if not questions_db:
        questions_db = load_saved_questions()

    print(f"[ArduinoMate] Application started. Loaded {len(records_db)} records.")
    yield
    print("[ArduinoMate] Application shut down.")


# -----------------------------------------------------------------------------
# FastAPI App Initialization
# -----------------------------------------------------------------------------
app = FastAPI(
    title="ArduinoMate API",
    description=(
        "Beginner-friendly backend API for Arduino knowledge base exploration, "
        "data analysis, and Machine Learning TF-IDF smart search."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Pydantic Models for Validation
# -----------------------------------------------------------------------------
class QuestionSubmission(BaseModel):
    """Schema for submitting a question to ArduinoMate."""
    user_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name of the person asking the question.",
        json_schema_extra={"example": "Jane Doe"}
    )
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Arduino question text.",
        json_schema_extra={"example": "How do I measure distance with the HC-SR04 sensor?"}
    )
    category: Optional[str] = Field(
        "General",
        max_length=50,
        description="Topic category (e.g., Sensors, LEDs, Robotics).",
        json_schema_extra={"example": "Ultrasonic sensors"}
    )


class QuestionResponse(BaseModel):
    """Response schema returned after successfully saving a question."""
    message: str
    question_id: int
    data: Dict[str, Any]


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

# A. GET /health
@app.get(
    "/health",
    tags=["System"],
    summary="API Health Check",
    description="Check whether the ArduinoMate API service is running normally."
)
def get_health() -> Dict[str, Any]:
    """Return JSON response indicating healthy status and dataset stats."""
    return {
        "status": "healthy",
        "service": "ArduinoMate API",
        "version": "1.0.0",
        "total_records": len(records_db),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# B. GET /records?limit=
@app.get(
    "/records",
    tags=["Records"],
    summary="Get Arduino Records",
    description="Retrieve all Arduino records, with an optional limit parameter."
)
def get_records(
    limit: Optional[int] = Query(
        default=None,
        description="Optional limit on number of records returned. Must be greater than 0."
    )
) -> List[Dict[str, Any]]:
    """
    Return Arduino records.
    - If limit is provided and valid, returns only the requested number of records.
    - If limit <= 0, returns HTTP 400 Bad Request.
    """
    if limit is not None:
        if limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be a positive integer greater than 0."
            )
        return records_db[:limit]

    return records_db


# C. GET /records/{id}
@app.get(
    "/records/{id}",
    tags=["Records"],
    summary="Get Record by ID",
    description="Retrieve a single ArduinoMate record using its unique ID."
)
def get_record_by_id(id: int) -> Dict[str, Any]:
    """
    Search for a record by its integer ID.
    Returns HTTP 404 if the record does not exist.
    """
    for record in records_db:
        if record.get("id") == id:
            return record

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Record with ID {id} not found."
    )


# D. GET /search?q=
@app.get(
    "/search",
    tags=["Search"],
    summary="Smart Search with TF-IDF and Cosine Similarity",
    description="Search records ranked by relevance using Machine Learning."
)
def search_records(
    q: Optional[str] = Query(
        default="",
        description="Search query string (e.g. 'ultrasonic distance sensor')."
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of search results to return."
    )
) -> Dict[str, Any]:
    """
    Perform ML smart search.
    - Handles empty queries gracefully.
    - Returns ranked records with their similarity scores.
    """
    # Handle empty or whitespace queries
    if not q or not q.strip():
        return {
            "query": q,
            "total_matches": 0,
            "results": [],
            "message": "Search query is empty. Please provide a search term."
        }

    # Extract integer limit
    try:
        limit_val = int(limit) if limit is not None else 5
    except (ValueError, TypeError):
        limit_val = 5

    # Perform TF-IDF Cosine Similarity search
    results = search_engine.search(
        query=q,
        records=records_db,
        top_k=limit_val,
        min_score=0.01
    )

    return {
        "query": q,
        "total_matches": len(results),
        "results": results
    }


# E. POST /questions
@app.post(
    "/questions",
    tags=["Questions"],
    status_code=status.HTTP_201_CREATED,
    response_model=QuestionResponse,
    summary="Submit a User Question",
    description="Accept and validate a new user question about Arduino, then store it."
)
def submit_question(payload: QuestionSubmission) -> QuestionResponse:
    """
    Accept user question via validated Pydantic model.
    Stores the question in memory and persists to data/questions.json.
    """
    new_id = len(questions_db) + 1
    new_question = {
        "id": new_id,
        "user_name": payload.user_name.strip(),
        "question": payload.question.strip(),
        "category": (payload.category or "General").strip(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    questions_db.append(new_question)
    persist_questions()

    return QuestionResponse(
        message="Question submitted successfully.",
        question_id=new_id,
        data=new_question
    )
