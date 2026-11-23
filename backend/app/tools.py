"""
app/tools.py — ArduinoMate Agent Tools
----------------------------------------
Two callable tools the agent can invoke:

  1. rag_search(question)              → str
     Retrieves and answers an Arduino question from the ChromaDB knowledge base.
     Returns the LLM-generated answer plus a short citation list.

  2. led_resistor_calculator(supply_voltage, led_forward_voltage, led_current_ma)
     → str
     Ohm's law LED resistor calculator.
     Formula:  R_exact = (Vs - Vf) / I
     Result rounded UP to the next standard E12 value.

E12 series
----------
The E12 series has 12 values per decade:
    10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82
repeated for each power of 10 (10 Ω … 10 MΩ).

Public API
----------
    TOOLS          : list[dict]   — OpenAI-style tool schemas
    call_tool(name, args) -> str  — dispatcher used by agent_loop
    led_resistor_calculator(...)  — direct access for tests
    rag_search(...)               — direct access for tests
"""

from __future__ import annotations

import math
from typing import Any

# ---------------------------------------------------------------------------
# E12 resistor series
# ---------------------------------------------------------------------------
_E12_MANTISSAS = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]


def _next_e12(ohms: float) -> int:
    """
    Return the smallest standard E12 resistor value >= ohms.

    The E12 mantissas are in the range [10, 82] (two-digit values).
    We scale `ohms` so the mantissa falls in [10, 100), compare against
    the E12 list, then multiply back by the decade.

    Args:
        ohms : Exact calculated resistance (positive float).

    Returns:
        Nearest E12 value at or above `ohms`, as an integer.
    """
    if ohms <= 0:
        return 10  # floor at 10 Ω

    # Express ohms as mantissa × decade where mantissa ∈ [10, 100)
    # e.g. 150 Ω → decade=10, mantissa=15.0
    #      47  Ω → decade=1,  mantissa=47.0
    #      330 Ω → decade=10, mantissa=33.0
    exponent = math.floor(math.log10(ohms))
    decade   = 10 ** (exponent - 1)       # keeps mantissa in [10, 100)
    mantissa = ohms / decade               # e.g. 15.0, 47.0, 33.0

    for m in _E12_MANTISSAS:
        if m >= round(mantissa, 6):
            return int(m * decade)

    # Rolled past 82 → next decade's first value: 100 × decade
    return int(100 * decade)


# ---------------------------------------------------------------------------
# Tool 1: LED resistor calculator
# ---------------------------------------------------------------------------
def led_resistor_calculator(
    supply_voltage: float,
    led_forward_voltage: float,
    led_current_ma: float,
) -> str:
    """
    Calculate the minimum safe series resistor for an LED.

    Formula:   R = (Vs - Vf) / I

    Args:
        supply_voltage      : Arduino supply voltage in volts (e.g. 5.0).
        led_forward_voltage : LED forward voltage in volts (e.g. 2.0 for red).
        led_current_ma      : Desired LED current in milliamps (e.g. 20).

    Returns:
        A human-readable string with the exact and E12-rounded resistance.
    """
    if led_current_ma <= 0:
        return "Error: LED current must be greater than 0 mA."
    if supply_voltage <= led_forward_voltage:
        return (
            f"Error: supply voltage ({supply_voltage} V) must be greater than "
            f"LED forward voltage ({led_forward_voltage} V)."
        )

    current_a  = led_current_ma / 1000.0
    r_exact    = (supply_voltage - led_forward_voltage) / current_a
    r_e12      = _next_e12(r_exact)

    return (
        f"LED Resistor Calculation\n"
        f"  Supply voltage      : {supply_voltage} V\n"
        f"  LED forward voltage : {led_forward_voltage} V\n"
        f"  LED current         : {led_current_ma} mA\n"
        f"  Exact resistance    : {r_exact:.1f} Ω\n"
        f"  Standard E12 value  : {r_e12} Ω  ← use this resistor\n"
        f"\n"
        f"Formula: R = (Vs - Vf) / I = "
        f"({supply_voltage} - {led_forward_voltage}) / {current_a:.4f} = {r_exact:.1f} Ω"
    )


# ---------------------------------------------------------------------------
# Tool 2: RAG search
# ---------------------------------------------------------------------------
def rag_search(question: str) -> str:
    """
    Answer an Arduino question using the RAG pipeline (ChromaDB + LLM).

    Args:
        question : Free-text Arduino question.

    Returns:
        Answer string with inline citation titles; or "I don't know …" if
        the question is out of scope.
    """
    from backend.app.rag import rag_answer

    resp = rag_answer(question, top_k=5, min_score=0.20)
    if resp.out_of_scope or not resp.citations:
        return resp.answer

    # Append compact citation list
    citation_lines = [
        f"  [{i+1}] {c.title} — {c.source} (p{c.page}, score {c.score:.3f})"
        for i, c in enumerate(resp.citations)
    ]
    return resp.answer + "\n\nSources:\n" + "\n".join(citation_lines)


# ---------------------------------------------------------------------------
# OpenAI-style tool schemas  (used by the agent to announce capabilities)
# ---------------------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": (
                "Search the ArduinoMate documentation knowledge base and return "
                "a grounded answer with citations. Use this for Arduino programming "
                "questions: functions, syntax, gotchas, timing, serial, interrupts, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The Arduino question to look up.",
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "led_resistor_calculator",
            "description": (
                "Calculate the correct series resistor for an LED using Ohm's law. "
                "Returns the exact resistance and the nearest standard E12 value. "
                "Use this whenever the user asks about LED resistors, current limiting, "
                "or which resistor to use with an LED."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "supply_voltage": {
                        "type": "number",
                        "description": "Arduino supply voltage in volts (typically 3.3 or 5.0).",
                    },
                    "led_forward_voltage": {
                        "type": "number",
                        "description": (
                            "LED forward voltage in volts. "
                            "Common values: red≈2.0 V, green≈2.1 V, blue/white≈3.3 V."
                        ),
                    },
                    "led_current_ma": {
                        "type": "number",
                        "description": "Desired LED current in milliamps (typical: 10–20 mA).",
                    },
                },
                "required": ["supply_voltage", "led_forward_voltage", "led_current_ma"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Central dispatcher
# ---------------------------------------------------------------------------
def call_tool(name: str, args: dict[str, Any]) -> str:
    """
    Dispatch a tool call by name.

    Args:
        name : Tool name — 'rag_search' or 'led_resistor_calculator'.
        args : Keyword arguments matching the tool's parameter schema.

    Returns:
        Tool result as a string.

    Raises:
        ValueError if the tool name is unknown.
    """
    if name == "rag_search":
        return rag_search(question=args["question"])

    if name == "led_resistor_calculator":
        return led_resistor_calculator(
            supply_voltage=float(args["supply_voltage"]),
            led_forward_voltage=float(args["led_forward_voltage"]),
            led_current_ma=float(args["led_current_ma"]),
        )

    raise ValueError(f"Unknown tool: {name!r}. Available: rag_search, led_resistor_calculator")
