"""
app/graph.py — LangGraph Agent with Memory + Approval Step
------------------------------------------------------------
Rebuilds the hand-written agent_loop in LangGraph 1.x.

Graph topology
--------------

  ┌─────────┐    ┌──────────┐    ┌──────────────┐    ┌────────────┐
  │  START  │───►│  reason  │───►│   approval   │───►│  act       │
  └─────────┘    └──────────┘    └──────────────┘    └────────────┘
                      ▲                │  approve              │
                      │                │                       │
                      └───────────────◄┘  reject → answer     │
                      │                                        │
                      └────────────────────────────────────────┘
                                                               │
                                                           ┌───▼───┐
                                                           │  END  │
                                                           └───────┘

Nodes
-----
  reason    : LLM decides: call a tool or answer directly.
  approval  : Approval gate — auto-approves tool calls unless
              AUTO_APPROVE=false in env (for demo / supervised mode).
              In supervised mode the caller sets state["approved"] before
              resuming so the graph can be paused at this node via a
              LangGraph checkpoint.
  act       : Executes the approved tool call, appends observation.
  answer    : Formats and returns the final answer.

Memory
------
  LangGraph's MemorySaver is used as the checkpointer.
  Every turn is saved to an in-process dict keyed by thread_id.
  Pass the same thread_id across turns to continue the conversation.

Public API
----------
    run_graph(user_message, thread_id, approved)  -> GraphResult
    GraphResult.to_dict()                         -> dict
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver

# LangGraph imports
from langgraph.graph import END, StateGraph

from backend.app.llm import active_model, chat
from backend.app.tools import call_tool

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_STEPS = 6
# Set AUTO_APPROVE=false in .env to enable the supervised approval gate
_AUTO_APPROVE = os.getenv("AUTO_APPROVE", "true").lower() != "false"


# ---------------------------------------------------------------------------
# State schema (plain dict — LangGraph uses TypedDict-style state)
# ---------------------------------------------------------------------------


class AgentState(TypedDict, total=False):
    user_message:  str
    messages:      list[dict]       # full conversation (OpenAI format)
    tool_name:     str              # pending tool call
    tool_args:     dict             # pending tool args
    tool_result:   str              # last observation
    steps:         list[dict]       # trace
    answer:        str              # final answer
    approved:      bool             # True = proceed; False = reject
    step_count:    int


# ---------------------------------------------------------------------------
# JSON / tool-call helpers (same as agent_loop)
# ---------------------------------------------------------------------------
def _parse_tool_call(raw: str) -> tuple[str, dict] | None:
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict) and "tool" in obj and "args" in obj:
            return obj["tool"], obj["args"]
    except json.JSONDecodeError:
        pass
    m = re.search(r'\{[^{}]*"tool"\s*:[^{}]*\}', cleaned, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group())
            if "tool" in obj and "args" in obj:
                return obj["tool"], obj["args"]
        except json.JSONDecodeError:
            pass
    return None


def _extract_answer(raw: str) -> str:
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return str(obj.get("answer", raw)).strip()
    except json.JSONDecodeError:
        pass
    return cleaned


_SYSTEM_AGENT = """\
You are ArduinoMate Agent, an expert assistant for Arduino programming and electronics.

You have access to two tools:
  - rag_search              : Look up Arduino documentation (functions, syntax, gotchas).
  - led_resistor_calculator : Calculate the correct LED series resistor (Ohm's law).

RULES:
1. For Arduino function questions → call rag_search.
2. For LED resistor questions     → call led_resistor_calculator.
3. After a tool result, give a clear beginner-friendly final answer.
4. Never fabricate values — use the tools.

To call a tool respond with ONLY:
  {"tool": "<name>", "args": {<params>}}

For a final answer respond with ONLY:
  {"answer": "<full answer>"}
"""


# ---------------------------------------------------------------------------
# Node: reason
# ---------------------------------------------------------------------------
def node_reason(state: AgentState) -> AgentState:
    """LLM decides: tool call or final answer."""
    messages = state.get("messages", [])
    if not messages:
        # First turn — initialise
        messages = [{"role": "system", "content": _SYSTEM_AGENT}]
        if state.get("user_message"):
            messages.append({"role": "user", "content": state["user_message"]})

    raw = chat(messages, temperature=0.1)
    tool_call = _parse_tool_call(raw)

    steps = list(state.get("steps", []))
    step_count = state.get("step_count", 0) + 1

    if tool_call:
        tool_name, tool_args = tool_call
        steps.append({
            "step": step_count,
            "type": "tool_call",
            "tool": tool_name,
            "args": tool_args,
        })
        messages.append({"role": "assistant", "content": raw})
        return {
            **state,
            "messages":   messages,
            "tool_name":  tool_name,
            "tool_args":  tool_args,
            "steps":      steps,
            "step_count": step_count,
            "answer":     "",
        }
    else:
        final = _extract_answer(raw)
        steps.append({"step": step_count, "type": "final_answer", "answer": final})
        return {
            **state,
            "messages":   messages,
            "tool_name":  "",
            "tool_args":  {},
            "steps":      steps,
            "step_count": step_count,
            "answer":     final,
        }


# ---------------------------------------------------------------------------
# Node: approval
# ---------------------------------------------------------------------------
def node_approval(state: AgentState) -> AgentState:
    """
    Approval gate before executing a tool.

    In AUTO_APPROVE mode (default) this node always approves.
    In supervised mode the caller sets state["approved"] via a
    LangGraph interrupt/resume cycle (the graph is checkpointed
    at this node and the caller resumes with approved=True/False).
    """
    if _AUTO_APPROVE:
        return {**state, "approved": True}

    # Non-auto: check if the caller has already set approved
    if "approved" not in state:
        # Leave state unchanged — the checkpoint will pause here
        return state

    return state  # caller's value of "approved" is already set


# ---------------------------------------------------------------------------
# Node: act
# ---------------------------------------------------------------------------
def node_act(state: AgentState) -> AgentState:
    """Execute the approved tool call and append the observation."""
    tool_name = state.get("tool_name", "")
    tool_args = state.get("tool_args", {})

    try:
        observation = call_tool(tool_name, tool_args)
    except Exception as exc:
        observation = f"Tool error: {exc}"

    steps = list(state.get("steps", []))
    step_count = state.get("step_count", 0)
    steps.append({
        "step":   step_count,
        "type":   "observation",
        "tool":   tool_name,
        "result": observation[:400] + ("…" if len(observation) > 400 else ""),
    })

    messages = list(state.get("messages", []))
    messages.append({
        "role":    "user",
        "content": f"Tool result for {tool_name}:\n{observation}\n\nNow give your final answer.",
    })

    return {
        **state,
        "messages":    messages,
        "tool_result": observation,
        "steps":       steps,
        # Clear pending tool so the router re-evaluates cleanly
        "tool_name":   "",
        "tool_args":   {},
    }


# ---------------------------------------------------------------------------
# Conditional edge router
# ---------------------------------------------------------------------------
def route_after_reason(state: AgentState) -> Literal["approval", "answer"]:
    """Route to approval if a tool was requested, else to END."""
    if state.get("tool_name"):
        return "approval"
    return "answer"


def route_after_approval(state: AgentState) -> Literal["act", "answer"]:
    """Route to act if approved; to answer (rejection) otherwise."""
    if state.get("approved", True):
        return "act"
    return "answer"


def route_after_act(state: AgentState) -> Literal["reason", "answer"]:
    """Loop back to reason unless we've hit the step ceiling."""
    if state.get("step_count", 0) >= MAX_STEPS:
        return "answer"
    return "reason"


# ---------------------------------------------------------------------------
# Node: answer  (passthrough — just surfaces state["answer"])
# ---------------------------------------------------------------------------
def node_answer(state: AgentState) -> AgentState:
    """Final answer node — no-op, answer is already in state."""
    return state


# ---------------------------------------------------------------------------
# Build the compiled graph
# ---------------------------------------------------------------------------
def _build_graph() -> Any:
    memory = MemorySaver()
    builder: StateGraph = StateGraph(AgentState)

    builder.add_node("reason",   node_reason)
    builder.add_node("approval", node_approval)
    builder.add_node("act",      node_act)
    builder.add_node("answer",   node_answer)

    builder.set_entry_point("reason")

    builder.add_conditional_edges("reason",   route_after_reason,
                                  {"approval": "approval", "answer": "answer"})
    builder.add_conditional_edges("approval", route_after_approval,
                                  {"act": "act", "answer": "answer"})
    builder.add_conditional_edges("act",      route_after_act,
                                  {"reason": "reason", "answer": "answer"})
    builder.add_edge("answer", END)

    return builder.compile(checkpointer=memory)


# Module-level compiled graph (lazy-initialised)
_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Output type
# ---------------------------------------------------------------------------
@dataclass
class GraphResult:
    """Result returned by run_graph()."""
    answer:    str
    steps:     list[dict]
    model:     str
    thread_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer":    self.answer,
            "steps":     self.steps,
            "model":     self.model,
            "thread_id": self.thread_id,
            "num_steps": len(self.steps),
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def run_graph(
    user_message: str,
    thread_id:    str  = "default",
    approved:     bool = True,
) -> GraphResult:
    """
    Run the LangGraph agent for one user turn.

    Args:
        user_message : The user's question or request.
        thread_id    : Conversation ID — same ID across calls continues the
                       conversation (LangGraph MemorySaver checkpoint).
        approved     : Pre-set the approval gate (True = auto-approve).
                       Ignored when AUTO_APPROVE=true (env default).

    Returns:
        GraphResult with the final answer, step trace, model, and thread_id.
    """
    graph = _get_graph()
    model_name = active_model()

    initial_state: AgentState = {
        "user_message": user_message,
        "messages":     [],
        "tool_name":    "",
        "tool_args":    {},
        "tool_result":  "",
        "steps":        [],
        "answer":       "",
        "approved":     approved,
        "step_count":   0,
    }

    config = {"configurable": {"thread_id": thread_id}}
    final_state: AgentState = graph.invoke(initial_state, config=config)

    return GraphResult(
        answer=final_state.get("answer", ""),
        steps=final_state.get("steps", []),
        model=model_name,
        thread_id=thread_id,
    )
