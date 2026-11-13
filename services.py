"""
Day 6 — services.py
----------------------
Business logic layer between the FastAPI routes and the LLM provider.

Responsibilities:
- Load the ArduinoMate system prompt from prompts/system_prompt.txt.
- Load the correct task prompt (explain / debug) from prompts/.
- Build the messages list and call app.llm.chat().
- Parse the JSON reply from the LLM into a structured ChatResponse dict.
- Handle JSON parse failures gracefully so the API never returns a 500.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict

from app.llm import chat, active_model

# ---------------------------------------------------------------------------
# Prompt file paths
# ---------------------------------------------------------------------------
BASE_DIR      = Path(__file__).resolve().parent
PROMPTS_DIR   = BASE_DIR / "prompts"
SYSTEM_PROMPT = PROMPTS_DIR / "system_prompt.txt"
TASK_PROMPTS  = {
    "explain": PROMPTS_DIR / "task_explain.txt",
    "debug":   PROMPTS_DIR / "task_debug.txt",
}


def _load_prompt(path: Path) -> str:
    """Read a prompt file and return its content as a string."""
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def _extract_json(raw: str) -> Dict[str, Any]:
    """
    Extract the first JSON object from a raw LLM response string.
    Models sometimes wrap JSON in markdown code fences — this handles that.
    """
    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to extract first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback — wrap the raw text as the answer
    return {
        "answer":     raw.strip(),
        "confidence": 0.5,
        "follow_up":  "Can you explain more about Arduino functions?"
    }


def generate_response(message: str, task: str = "explain") -> Dict[str, Any]:
    """
    Generate an AI response for the given user message.

    Args:
        message : The user's Arduino question or problem description.
        task    : 'explain' or 'debug' — selects the task prompt template.

    Returns:
        A dict with keys: answer, confidence, follow_up, model, status.
    """
    # Resolve task — fall back to 'explain' for unknown task names
    task_key   = task.lower().strip() if task else "explain"
    if task_key not in TASK_PROMPTS:
        task_key = "explain"

    model_name = active_model()

    try:
        # 1. Load prompts
        system_text = _load_prompt(SYSTEM_PROMPT)
        task_text   = _load_prompt(TASK_PROMPTS[task_key]).format(question=message)

        # 2. Build messages in OpenAI-style format
        messages = [
            {"role": "system",    "content": system_text},
            {"role": "user",      "content": task_text},
        ]

        # 3. Call the LLM provider
        raw_reply = chat(messages, temperature=0.3)

        # 4. Parse the structured JSON response
        parsed = _extract_json(raw_reply)

        return {
            "answer":     str(parsed.get("answer",    raw_reply)),
            "confidence": float(parsed.get("confidence", 0.8)),
            "follow_up":  str(parsed.get("follow_up", "")),
            "model":      model_name,
            "status":     "success",
        }

    except Exception as exc:  # noqa: BLE001
        # Return a graceful error — never crash the API
        return {
            "answer":     f"ArduinoMate encountered an error: {exc}",
            "confidence": 0.0,
            "follow_up":  "",
            "model":      model_name,
            "status":     "error",
        }
