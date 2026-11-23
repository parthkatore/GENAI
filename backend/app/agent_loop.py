"""
app/agent_loop.py — Hand-Written ReAct Agent Loop
---------------------------------------------------
A minimal ReAct (Reason → Act → Observe) loop that:

  1. Sends the user message + tool schemas to the LLM.
  2. If the LLM calls a tool → dispatch it, append the observation,
     and loop back (up to MAX_STEPS).
  3. If the LLM returns a final answer (no tool call) → return it.

No external agent framework is used here — the loop is hand-written so
the mechanics are fully transparent.

Public API
----------
    run_agent(user_message, session_id, history) -> AgentResult
    AgentResult.to_dict()                        -> dict
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from backend.app.llm import active_model, chat
from backend.app.tools import TOOLS, call_tool

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_STEPS = 6     # safety ceiling — prevents runaway loops

_SYSTEM_AGENT = """\
You are ArduinoMate Agent, an expert assistant for Arduino programming and electronics.

You have access to two tools:
  - rag_search          : Look up Arduino documentation and get a grounded answer.
  - led_resistor_calculator : Calculate the correct LED series resistor (Ohm's law).

RULES:
1. Think step-by-step. For each user message decide: do I need a tool, or can I answer directly?
2. If the question is about an Arduino function, timing, serial, interrupts, PWM, etc.
   — always call rag_search first.
3. If the user asks about an LED resistor or current-limiting resistor
   — always call led_resistor_calculator.
4. After receiving a tool result, synthesise it into a clear, beginner-friendly answer.
5. Never make up resistor values or Arduino facts — use the tools.
6. If neither tool can help, say so honestly.
"""


# ---------------------------------------------------------------------------
# Output type
# ---------------------------------------------------------------------------
@dataclass
class StepRecord:
    """One reasoning/tool step in the agent trace."""
    step:        int
    type:        str   # "tool_call" | "observation" | "final_answer"
    tool_name:   str   = ""
    tool_args:   dict  = field(default_factory=dict)
    content:     str   = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"step": self.step, "type": self.type}
        if self.type == "tool_call":
            d["tool"]  = self.tool_name
            d["args"]  = self.tool_args
        elif self.type == "observation":
            d["tool"]   = self.tool_name
            d["result"] = self.content[:400] + ("…" if len(self.content) > 400 else "")
        else:
            d["answer"] = self.content
        return d


@dataclass
class AgentResult:
    """Full result of one agent run."""
    answer:  str
    steps:   list[StepRecord]
    model:   str
    session_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer":     self.answer,
            "steps":      [s.to_dict() for s in self.steps],
            "model":      self.model,
            "session_id": self.session_id,
            "num_steps":  len(self.steps),
        }


# ---------------------------------------------------------------------------
# JSON / tool-call extractor
# ---------------------------------------------------------------------------
def _parse_tool_call(raw: str) -> tuple[str, dict] | None:
    """
    Extract a tool call from the LLM reply.

    The LLM is prompted to respond with either:
      {"tool": "<name>", "args": {...}}
    or a plain answer.

    Returns (tool_name, args) if a tool call is found, else None.
    """
    # Strip <think>…</think> blocks
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()

    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict) and "tool" in obj and "args" in obj:
            return obj["tool"], obj["args"]
    except json.JSONDecodeError:
        pass

    # Try extracting a JSON block that contains "tool"
    m = re.search(r'\{[^{}]*"tool"\s*:[^{}]*\}', cleaned, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group())
            if "tool" in obj and "args" in obj:
                return obj["tool"], obj["args"]
        except json.JSONDecodeError:
            pass

    return None


def _extract_final_answer(raw: str) -> str:
    """Pull the answer text from the LLM final-answer response."""
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return str(obj.get("answer", raw)).strip()
    except json.JSONDecodeError:
        pass
    return cleaned


# ---------------------------------------------------------------------------
# Agent system prompt builder
# ---------------------------------------------------------------------------
def _tool_instruction() -> str:
    """Return the JSON response format instructions for the LLM."""
    names = [t["function"]["name"] for t in TOOLS]
    return (
        f"Available tools: {names}\n\n"
        "To call a tool, respond with ONLY this JSON (no other text):\n"
        '  {"tool": "<tool_name>", "args": {<arg_key>: <value>, ...}}\n\n'
        "When you have a final answer (no more tools needed), respond with:\n"
        '  {"answer": "<your complete answer here>"}\n'
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run_agent(
    user_message: str,
    session_id:   str = "default",
    history:      list[dict] | None = None,
) -> AgentResult:
    """
    Run the ReAct agent loop for one user turn.

    Args:
        user_message : The user's question or request.
        session_id   : Identifier for this conversation (for logging).
        history      : Previous conversation messages (OpenAI format).
                       Pass [] or None to start a fresh conversation.

    Returns:
        AgentResult with the final answer, step trace, and model name.
    """
    model_name = active_model()
    steps: list[StepRecord] = []

    # Build the full message list
    system_content = _SYSTEM_AGENT + "\n\n" + _tool_instruction()
    messages: list[dict] = [{"role": "system", "content": system_content}]

    # Inject prior history (memory)
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})

    for step_num in range(1, MAX_STEPS + 1):
        # Ask the LLM
        raw = chat(messages, temperature=0.1)

        # Check for tool call
        tool_call = _parse_tool_call(raw)

        if tool_call:
            tool_name, tool_args = tool_call
            steps.append(
                StepRecord(step=step_num, type="tool_call",
                           tool_name=tool_name, tool_args=tool_args)
            )

            # Execute the tool
            try:
                observation = call_tool(tool_name, tool_args)
            except Exception as exc:
                observation = f"Tool error: {exc}"

            steps.append(
                StepRecord(step=step_num, type="observation",
                           tool_name=tool_name, content=observation)
            )

            # Append assistant tool call + observation to messages
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": f"Tool result for {tool_name}:\n{observation}\n\nNow give your final answer.",
            })

        else:
            # Final answer
            final = _extract_final_answer(raw)
            steps.append(
                StepRecord(step=step_num, type="final_answer", content=final)
            )
            return AgentResult(
                answer=final,
                steps=steps,
                model=model_name,
                session_id=session_id,
            )

    # Exceeded MAX_STEPS — use last raw reply as answer
    final = _extract_final_answer(raw)  # type: ignore[possibly-undefined]
    steps.append(StepRecord(step=MAX_STEPS, type="final_answer", content=final))
    return AgentResult(
        answer=final,
        steps=steps,
        model=model_name,
        session_id=session_id,
    )
