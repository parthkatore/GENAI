# Day 6 — LLM Integration: Provider Wrapper + Structured Chat API

**Student:** Parth Dasharath Katore | Enroll: 2124UCEM2079 | Roll: 53  
**Status:** ✅ Complete

---

## Objective

Integrate a real LLM (Groq / Gemini) into the ArduinoMate FastAPI backend.  
Implement a provider wrapper (`app/llm.py`), a structured `POST /chat` endpoint,  
a `prompts/` folder with a system prompt and two task prompts, and an evaluation  
document comparing two prompt versions across all 10 user questions.

---

## Tasks Completed

- [x] `app/llm.py` — provider wrapper supporting Groq (primary) and Gemini (optional)
- [x] `schema.py` — updated `ChatRequest` and `ChatResponse` (answer, confidence, follow_up)
- [x] `services.py` — `generate_response()` loads prompts, calls LLM, parses JSON
- [x] `main.py` — clean FastAPI with `GET /`, `GET /health`, `POST /chat`
- [x] `prompts/system_prompt.txt` — ArduinoMate domain system prompt with JSON output rule
- [x] `prompts/task_explain.txt` — task prompt for function explanations
- [x] `prompts/task_debug.txt` — task prompt for debugging help
- [x] `eval/prompt_compare.md` — compares Version A (generic) vs Version B (ArduinoMate) on 10 questions
- [x] `.env.example` — committed (safe template, no real keys)
- [x] `.env` — NOT committed (in .gitignore)
- [x] `requirements.txt` — updated with groq, python-dotenv
- [x] Git commit + push to GitHub

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `app/llm.py` | Created | Groq + Gemini provider wrapper with single `chat()` interface |
| `schema.py` | Updated | ChatRequest + ChatResponse (answer, confidence, follow_up) |
| `services.py` | Created | Business logic: prompt loading, LLM call, JSON parsing |
| `main.py` | Rewritten | Clean FastAPI — /health, POST /chat with ArduinoMate prompt |
| `prompts/system_prompt.txt` | Created | ArduinoMate system prompt — domain rules + JSON output format |
| `prompts/task_explain.txt` | Created | Task prompt for explaining Arduino functions |
| `prompts/task_debug.txt` | Created | Task prompt for debugging Arduino problems |
| `eval/prompt_compare.md` | Created | Prompt A vs B evaluation on 10 questions |
| `.env.example` | Created | Safe template for environment variables |
| `.gitignore` | Updated | Ensures .env is never committed |
| `requirements.txt` | Updated | Added groq, python-dotenv |

---

## Architecture

```
POST /chat
    │
    ▼  main.py (FastAPI route)
    │  Validates ChatRequest via Pydantic
    │
    ▼  services.py → generate_response()
    │  Loads prompts/system_prompt.txt
    │  Loads prompts/task_explain.txt or task_debug.txt
    │  Builds messages list
    │
    ▼  app/llm.py → chat()
    │  Reads PROVIDER from .env (default: groq)
    │  Calls Groq API (or Gemini if configured)
    │
    ▼  services.py → _extract_json()
    │  Parses JSON from LLM response
    │  Fallback if JSON is malformed
    │
    ▼  ChatResponse (answer, confidence, follow_up, model, status)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome + active provider info |
| GET | `/health` | Health check with model/provider details |
| POST | `/chat` | LLM-powered Arduino Q&A |

### POST /chat Request
```json
{
  "message": "What does pinMode() do in Arduino?",
  "task": "explain"
}
```

### POST /chat Response
```json
{
  "answer": "pinMode(pin, mode) configures a digital pin as INPUT, OUTPUT, or INPUT_PULLUP. Always call it in setup() before any digitalRead() or digitalWrite()...",
  "confidence": 0.97,
  "follow_up": "What is the difference between INPUT and INPUT_PULLUP?",
  "model": "llama3-8b-8192",
  "status": "success"
}
```

### Task Types

| Task | Prompt File | Use Case |
|------|-------------|----------|
| `explain` (default) | `prompts/task_explain.txt` | Explain an Arduino function |
| `debug` | `prompts/task_debug.txt` | Debug an Arduino problem |

---

## Prompt Design

### System Prompt (`prompts/system_prompt.txt`)
- Establishes ArduinoMate persona
- Lists 5 response rules (relevance, beginner-friendly, code examples, honesty, follow-ups)
- Enforces strict JSON output format with `answer`, `confidence`, `follow_up`

### Task Prompt — Explain (`prompts/task_explain.txt`)
- One plain-English sentence about the function
- Correct syntax with types
- Minimal working code snippet
- Most common gotcha
- 200-word limit

### Task Prompt — Debug (`prompts/task_debug.txt`)
- Identify most likely root cause
- Explain why it causes the symptom
- Corrected code snippet
- Quick verification test
- 200-word limit

---

## Prompt Evaluation Summary

See `eval/prompt_compare.md` for full results.

| Metric | Version A (Generic) | Version B (ArduinoMate) |
|--------|--------------------|-----------------------|
| Avg relevance | 3.1 / 5 | 5.0 / 5 |
| Avg code quality | 1.7 / 5 | 4.9 / 5 |
| Avg clarity | 2.7 / 5 | 5.0 / 5 |
| Structured JSON | 0 / 10 | 10 / 10 |
| Gotcha coverage | 0 / 10 | 10 / 10 |
| **Total score** | **104 / 250** | **230 / 250** |

Version B wins 10/10 questions.

---

## Setup and Running

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
# Copy the example file
copy .env.example .env

# Edit .env — add your Groq API key
# GROQ_API_KEY=your_key_from_https://console.groq.com/keys
```

### 3. Start the API
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Test the chat endpoint
```bash
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"What does pinMode do?\", \"task\": \"explain\"}"
```

---

## Switching Providers

To use Gemini instead of Groq, update `.env`:
```
PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key_here
```
Then: `pip install google-generativeai`

No code changes needed — `app/llm.py` handles both.

---

## Security Notes

- `.env` is in `.gitignore` and is **never committed**
- `.env.example` is committed as a safe template with placeholder values
- API keys are read exclusively via `os.getenv()` — never hardcoded
- `services.py` catches all LLM exceptions and returns a graceful error response

---

## Technologies Used

- Python 3.13
- FastAPI 0.110+
- Pydantic v2
- Groq Python SDK 0.9+
- python-dotenv 1.0+
- uvicorn

---

## Git Tags

```bash
git tag day-6
git push origin day-6
```
