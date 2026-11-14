"""
app/llm.py — LLM Provider Wrapper
-----------------------------------
Supports Groq (primary) with a clean interface for adding Gemini later.

Provider selection is driven by the PROVIDER env var (default: "groq").
The wrapper exposes a single function:

    chat(messages, model, temperature) -> str

Where `messages` is the standard OpenAI-style list:
    [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Provider constants
# ---------------------------------------------------------------------------
PROVIDER_GROQ   = "groq"
PROVIDER_GEMINI = "gemini"

# Default Groq model — qwen/qwen3.8-27b (llama3-8b-8192 is decommissioned)
GROQ_DEFAULT_MODEL   = "qwen/qwen3.8-27b"
GEMINI_DEFAULT_MODEL = "gemini-1.5-flash"


def _get_provider() -> str:
    """Return the active provider from env, defaulting to groq."""
    return os.getenv("PROVIDER", PROVIDER_GROQ).lower().strip()


# ---------------------------------------------------------------------------
# Groq backend
# ---------------------------------------------------------------------------
def _chat_groq(
    messages: list[dict],
    model: str = GROQ_DEFAULT_MODEL,
    temperature: float = 0.3,
) -> str:
    """Call Groq API and return the assistant reply as a string."""
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY") or os.getenv("Gen_AI_API_Key")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to your .env file.")

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=1024,
    )
    return completion.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------
def _chat_gemini(
    messages: list[dict],
    model: str = GEMINI_DEFAULT_MODEL,
    temperature: float = 0.3,
) -> str:
    """Call Google Gemini API and return the assistant reply as a string."""
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise ImportError(
            "google-generativeai is not installed. Run: pip install google-generativeai"
        ) from exc

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gen_AI_API_Key")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")

    genai.configure(api_key=api_key)

    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    user_parts   = [m["content"] for m in messages if m["role"] == "user"]
    system_text  = "\n".join(system_parts)
    user_text    = "\n".join(user_parts)
    full_prompt  = f"{system_text}\n\n{user_text}" if system_text else user_text

    gen_model = genai.GenerativeModel(
        model_name=model,
        generation_config=genai.GenerationConfig(
            temperature=temperature, max_output_tokens=1024,
        ),
    )
    return gen_model.generate_content(full_prompt).text.strip()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def chat(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> str:
    """
    Send messages to the configured LLM provider and return the reply.

    Args:
        messages    : [{"role": "system"|"user"|"assistant", "content": str}]
        model       : Override the default model for the active provider.
        temperature : Sampling temperature (0 = deterministic, 1 = creative).

    Returns:
        The assistant's reply as a plain string.
    """
    provider = _get_provider()

    if provider == PROVIDER_GROQ:
        return _chat_groq(
            messages,
            model=model or os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL),
            temperature=temperature,
        )

    if provider == PROVIDER_GEMINI:
        return _chat_gemini(
            messages,
            model=model or os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL),
            temperature=temperature,
        )

    raise RuntimeError(
        f"Unknown provider '{provider}'. "
        "Set PROVIDER to 'groq' or 'gemini' in your .env file."
    )


def active_model() -> str:
    """Return the model name that will be used for the next call."""
    provider = _get_provider()
    if provider == PROVIDER_GROQ:
        return os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL)
    if provider == PROVIDER_GEMINI:
        return os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
    return "unknown"
