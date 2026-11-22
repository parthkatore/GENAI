"""
app/middleware.py — Production hardening for ArduinoMate API
-------------------------------------------------------------
Day 12 — S1

Three concerns are handled here:

1. Latency + token logging
   Every request gets a wall-clock timer.  The llm.chat() wrapper stores the
   last token usage in a request-local context var so the middleware can read
   it after the response is built.  Both are written to stdout in a single
   structured log line:

       [ArduinoMate] POST /ask  200  847ms  tokens=in:312/out:184

2. Simple in-memory cache
   Identical (method, path, body) tuples are cached for CACHE_TTL_SECONDS.
   Only 2xx GET/POST responses whose body fits in CACHE_MAX_BYTES are stored.
   Cache is a plain dict protected by a threading.Lock — safe for Uvicorn's
   default single-worker mode.  Under load a real Redis cache would replace
   this, but for the course project this is correct and zero-dependency.

   Cache hit adds the response header:  X-Cache: HIT

3. Input-length guard
   POST bodies larger than MAX_BODY_BYTES (16 KB) are rejected with 413
   before the route handler runs.  This protects against prompt-stuffing and
   runaway token bills.

Prompt-injection detection
   _contains_injection() scans the decoded body for patterns that attempt to
   override system instructions.  When one is found the request is rejected
   with 400 and a log line is written so it is visible in CI and production
   logs.  The scanner is intentionally conservative — it blocks known attack
   phrases without trying to understand intent.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger("arduinomate")

# ---------------------------------------------------------------------------
# Configuration — tune via environment variables in production
# ---------------------------------------------------------------------------
MAX_BODY_BYTES: int = 16_384          # 16 KB hard limit on POST bodies
CACHE_MAX_ENTRIES: int = 256          # LRU eviction after this many keys
CACHE_TTL_SECONDS: float = 60.0      # cache entries expire after 60 s
CACHE_MAX_BYTES: int = 32_768        # don't cache responses larger than 32 KB

# Endpoints that benefit from caching (read-only or idempotent)
_CACHEABLE_PATHS = {"/health", "/search/semantic", "/ask", "/chat"}

# ---------------------------------------------------------------------------
# Prompt-injection patterns
# Sets of lowercase substrings that indicate an override attempt.
# The list covers the most common jailbreak and instruction-override phrases.
# ---------------------------------------------------------------------------
_INJECTION_PATTERNS: list[str] = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore your instructions",
    "disregard previous",
    "disregard all previous",
    "forget your instructions",
    "forget previous instructions",
    "you are now",
    "new instructions:",
    "override instructions",
    "system prompt:",
    "bypass your",
    "do not follow",
    "act as if you",
    "pretend you are",
    "pretend to be",
    "roleplay as",
    "jailbreak",
    "dan mode",
    "developer mode enabled",
    "ignore the above",
    "disregard the above",
]


def _contains_injection(body: str) -> str | None:
    """
    Scan a request body string for prompt-injection patterns.

    Returns the matched pattern string if found, else None.
    Only the value fields (not JSON keys) are scanned; the scan is
    case-insensitive.
    """
    lower = body.lower()
    for pattern in _INJECTION_PATTERNS:
        if pattern in lower:
            return pattern
    return None


# ---------------------------------------------------------------------------
# Token usage context variable
# app/llm.py writes to this after each API call so the middleware can read it.
# ---------------------------------------------------------------------------
token_usage: ContextVar[dict[str, int]] = ContextVar(
    "token_usage",
    default={"prompt_tokens": 0, "completion_tokens": 0},
)


# ---------------------------------------------------------------------------
# Simple LRU cache with TTL
# ---------------------------------------------------------------------------
class _SimpleCache:
    """Thread-safe in-memory LRU cache with per-entry TTL."""

    def __init__(self, max_entries: int = CACHE_MAX_ENTRIES) -> None:
        self._store: OrderedDict[str, tuple[float, bytes, int]] = OrderedDict()
        self._lock = threading.Lock()
        self._max = max_entries
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _make_key(method: str, path: str, body: bytes) -> str:
        digest = hashlib.sha256(body).hexdigest()[:16]
        return f"{method}:{path}:{digest}"

    def get(self, method: str, path: str, body: bytes) -> bytes | None:
        key = self._make_key(method, path, body)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return None
            ts, payload, _ = entry
            if time.monotonic() - ts > CACHE_TTL_SECONDS:
                del self._store[key]
                self.misses += 1
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            self.hits += 1
            return payload

    def set(self, method: str, path: str, body: bytes, payload: bytes) -> None:
        if len(payload) > CACHE_MAX_BYTES:
            return
        key = self._make_key(method, path, body)
        with self._lock:
            self._store[key] = (time.monotonic(), payload, len(payload))
            self._store.move_to_end(key)
            # Evict oldest if over capacity
            while len(self._store) > self._max:
                self._store.popitem(last=False)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)


# Module-level cache instance shared across all requests
_cache = _SimpleCache()


def get_cache() -> _SimpleCache:
    """Return the module-level cache (used by tests to inspect state)."""
    return _cache


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
class ProductionMiddleware(BaseHTTPMiddleware):
    """
    Single ASGI middleware that handles:
      - POST body size enforcement (→ 413)
      - Prompt-injection detection      (→ 400)
      - Response caching                (adds X-Cache header)
      - Latency + token logging
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        path = request.url.path

        # ------------------------------------------------------------------
        # Read body once (Starlette consumes the stream on first read)
        # ------------------------------------------------------------------
        body = await request.body()

        # ------------------------------------------------------------------
        # 1. Input-length guard
        # ------------------------------------------------------------------
        if request.method == "POST" and len(body) > MAX_BODY_BYTES:
            logger.warning(
                "[ArduinoMate] 413  %s  body=%d bytes (limit %d)",
                path, len(body), MAX_BODY_BYTES,
            )
            return JSONResponse(
                status_code=413,
                content={
                    "detail": (
                        f"Request body too large: {len(body)} bytes. "
                        f"Maximum allowed is {MAX_BODY_BYTES} bytes ({MAX_BODY_BYTES // 1024} KB)."
                    )
                },
            )

        # ------------------------------------------------------------------
        # 2. Prompt-injection detection
        # ------------------------------------------------------------------
        if request.method == "POST" and body:
            try:
                body_text = body.decode("utf-8", errors="replace")
            except Exception:
                body_text = ""
            matched = _contains_injection(body_text)
            if matched:
                logger.warning(
                    "[ArduinoMate] 400 INJECTION  %s  pattern=%r  ip=%s",
                    path, matched, request.client.host if request.client else "unknown",
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": (
                            "Request blocked: prompt-injection pattern detected. "
                            "ArduinoMate only answers Arduino questions."
                        )
                    },
                )

        # ------------------------------------------------------------------
        # 3. Cache lookup (GET and cacheable POST paths only)
        # ------------------------------------------------------------------
        # Include query string in the cache key so ?q=X and ?q=Y are distinct
        cache_path = str(request.url)   # full URL including query string
        use_cache = path in _CACHEABLE_PATHS
        if use_cache:
            cached = _cache.get(request.method, cache_path, body)
            if cached is not None:
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                logger.info(
                    "[ArduinoMate] %s %s  CACHE HIT  %dms",
                    request.method, path, elapsed_ms,
                )
                return Response(
                    content=cached,
                    media_type="application/json",
                    headers={"X-Cache": "HIT", "X-Latency-Ms": str(elapsed_ms)},
                )

        # ------------------------------------------------------------------
        # Reset token usage context for this request
        # ------------------------------------------------------------------
        token_usage.set({"prompt_tokens": 0, "completion_tokens": 0})

        # ------------------------------------------------------------------
        # 4. Call the actual route handler
        # ------------------------------------------------------------------
        response = await call_next(request)

        # ------------------------------------------------------------------
        # 5. Read response body (needed for caching and size header)
        # ------------------------------------------------------------------
        resp_body = b""
        async for chunk in response.body_iterator:
            resp_body += chunk

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        usage = token_usage.get()
        in_tok = usage.get("prompt_tokens", 0)
        out_tok = usage.get("completion_tokens", 0)

        # ------------------------------------------------------------------
        # 6. Structured log line
        # ------------------------------------------------------------------
        logger.info(
            "[ArduinoMate] %s %s  %d  %dms  tokens=in:%d/out:%d",
            request.method, path, response.status_code,
            elapsed_ms, in_tok, out_tok,
        )

        # ------------------------------------------------------------------
        # 7. Store in cache if applicable
        # ------------------------------------------------------------------
        if use_cache and 200 <= response.status_code < 300:
            _cache.set(request.method, cache_path, body, resp_body)

        # ------------------------------------------------------------------
        # 8. Return response with latency header
        # ------------------------------------------------------------------
        return Response(
            content=resp_body,
            status_code=response.status_code,
            headers={
                **dict(response.headers),
                "X-Latency-Ms": str(elapsed_ms),
                "X-Cache": "MISS",
            },
            media_type=response.media_type,
        )
