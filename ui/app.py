"""
ui/app.py — ArduinoMate Streamlit Chat Interface
-------------------------------------------------
Day 10: Streamlit frontend for the ArduinoMate FastAPI backend.

Features
--------
1. Dual-mode chat  — toggle between /ask (RAG) and /agent (tool-using).
2. Citations panel — expandable source list for every RAG answer.
3. Thumbs up / down — saves user feedback to data/feedback.json.
4. SIGNATURE: Pin Map panel — Arduino Uno diagram that lights up every
   pin mentioned in the answer (digital D0-D13, PWM ~, analog A0-A5,
   power 5V/GND/3.3V).
5. Sidebar controls — API URL, mode selector, top_k, min_score sliders.
6. Agent trace — expandable reasoning steps for /agent mode.

Run
---
    # Start the FastAPI backend first:
    uvicorn main:app --reload --host 127.0.0.1 --port 8000

    # Then launch Streamlit:
    streamlit run ui/app.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Path setup — allow imports from project root
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ui.pin_map import extract_pins, render_pin_map  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_API_URL = os.getenv("ARDUINOMATE_API_URL", "http://127.0.0.1:8000")
FEEDBACK_FILE   = ROOT / "data" / "feedback.json"
REQUEST_TIMEOUT = 60

MODES = {
    "RAG Answer (/ask)":  "ask",
    "AI Agent (/agent)":  "agent",
}

# ---------------------------------------------------------------------------
# Page config — MUST be the first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ArduinoMate",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.msg-user {
    background: #1565C0;
    color: #E3F2FD;
    border-radius: 16px 16px 4px 16px;
    padding: 10px 16px;
    margin: 6px 0;
    max-width: 80%;
    margin-left: auto;
    font-size: 15px;
    line-height: 1.5;
}
.msg-bot {
    background: #1A237E;
    color: #E8EAF6;
    border-radius: 16px 16px 16px 4px;
    padding: 10px 16px;
    margin: 6px 0;
    max-width: 90%;
    font-size: 15px;
    line-height: 1.5;
    border-left: 3px solid #3F51B5;
}
.citation-chip {
    display: inline-block;
    background: #263238;
    color: #80DEEA;
    border: 1px solid #37474F;
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 12px;
    margin: 2px 4px 2px 0;
    font-family: monospace;
}
.score-badge {
    display: inline-block;
    background: #1B5E20;
    color: #A5D6A7;
    border-radius: 8px;
    padding: 1px 7px;
    font-size: 11px;
    margin-left: 4px;
}
.oos-badge {
    display: inline-block;
    background: #B71C1C;
    color: #FFCDD2;
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 12px;
    margin-top: 4px;
}
.pin-active-label {
    color: #FFB300;
    font-weight: bold;
    font-family: monospace;
    font-size: 13px;
    margin-right: 6px;
}
[data-testid="stSidebar"] {
    background-color: #0D1B2A;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults: dict[str, Any] = {
        "messages":  [],
        "feedback":  {},
        "api_url":   DEFAULT_API_URL,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ---------------------------------------------------------------------------
# Feedback persistence
# ---------------------------------------------------------------------------
def _load_feedback() -> list[dict]:
    if FEEDBACK_FILE.exists():
        try:
            return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_feedback(question: str, answer: str, thumb: str) -> None:
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    records = _load_feedback()
    records.append({
        "timestamp": datetime.utcnow().isoformat(),
        "question":  question,
        "answer":    answer[:300],
        "thumb":     thumb,
    })
    FEEDBACK_FILE.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------
def _call_ask(question: str, top_k: int, min_score: float, api_url: str) -> dict:
    payload = {"question": question, "top_k": top_k, "min_score": min_score}
    resp = requests.post(f"{api_url}/ask", json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _call_agent(message: str, thread_id: str, use_graph: bool, api_url: str) -> dict:
    payload = {
        "message":   message,
        "thread_id": thread_id,
        "use_graph": use_graph,
        "approved":  True,
    }
    resp = requests.post(f"{api_url}/agent", json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _health_check(api_url: str) -> dict | None:
    try:
        r = requests.get(f"{api_url}/health", timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def _render_sidebar() -> dict[str, Any]:
    with st.sidebar:
        st.markdown("## 🤖 ArduinoMate")
        st.caption("AI-Powered Arduino Learning Assistant")
        st.divider()

        st.subheader("API Settings")
        api_url = st.text_input(
            "FastAPI URL",
            value=st.session_state.api_url,
            help="Base URL of the running FastAPI backend.",
        )
        st.session_state.api_url = api_url.rstrip("/")

        health = _health_check(st.session_state.api_url)
        if health:
            st.success(
                f"Online  {health.get('indexed_chunks', '?')} chunks\n\n"
                f"Model: `{health.get('model', '?')}`"
            )
        else:
            st.warning("Backend is starting or waking up. Retry shortly if it stays offline.")

        st.divider()

        st.subheader("Mode")
        mode_label = st.radio(
            "Query mode",
            options=list(MODES.keys()),
            index=0,
            label_visibility="collapsed",
        )
        mode = MODES[mode_label]

        st.divider()

        cfg: dict[str, Any] = {"mode": mode}

        if mode == "ask":
            st.subheader("RAG Config")
            cfg["top_k"] = st.slider("Top K chunks", 1, 10, 5)
            cfg["min_score"] = st.slider("Min similarity", 0.0, 1.0, 0.20, 0.01)
        else:
            st.subheader("Agent Config")
            cfg["use_graph"] = st.toggle("Use LangGraph", value=True)
            cfg["thread_id"] = st.text_input("Thread ID", value="default")

        st.divider()

        st.subheader("Feedback")
        fb   = _load_feedback()
        up   = sum(1 for r in fb if r.get("thumb") == "up")
        down = sum(1 for r in fb if r.get("thumb") == "down")
        c1, c2 = st.columns(2)
        c1.metric("Thumbs up",   up)
        c2.metric("Thumbs down", down)
        if fb:
            st.caption(f"Last: {fb[-1]['timestamp'][:16]}")

        st.divider()
        st.caption("v1.0 · Day 10 · ArduinoMate")

    return cfg


# ---------------------------------------------------------------------------
# Pin Map panel
# ---------------------------------------------------------------------------
def _render_pin_map(answer_text: str) -> None:
    active = extract_pins(answer_text)
    st.markdown("#### Arduino Uno Pin Map")
    if active:
        chips = "  ".join(
            f'<span class="pin-active-label">{p}</span>' for p in sorted(active)
        )
        st.markdown(
            f'<div style="margin-bottom:8px;">Highlighted: {chips}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("No specific pins detected in this answer.")
    svg_html = render_pin_map(active)
    components.html(svg_html, height=680, scrolling=False)


# ---------------------------------------------------------------------------
# Message rendering helpers
# ---------------------------------------------------------------------------
def _render_citations(citations: list[dict]) -> None:
    if not citations:
        return
    with st.expander(f"Sources ({len(citations)})", expanded=False):
        for i, c in enumerate(citations, 1):
            score_pct = f"{c.get('score', 0) * 100:.0f}%"
            src_name  = Path(c.get("source", "unknown")).name
            st.markdown(
                f'<span class="citation-chip">[{i}] {c.get("title", "")}</span>'
                f'<span class="score-badge">{score_pct}</span>  '
                f'`{src_name}` chunk {c.get("page", "?")}',
                unsafe_allow_html=True,
            )


def _render_agent_steps(steps: list[dict]) -> None:
    if not steps:
        return
    with st.expander(f"Agent trace ({len(steps)} steps)", expanded=False):
        for s in steps:
            stype = s.get("type", "")
            step  = s.get("step", "?")
            if stype == "tool_call":
                st.markdown(f"**Step {step} · Tool call** `{s.get('tool', '?')}`")
                st.json(s.get("args", {}))
            elif stype == "observation":
                st.markdown(f"**Step {step} · Observation** (`{s.get('tool', '?')}`)")
                st.code(s.get("result", ""), language="text")
            elif stype == "final_answer":
                st.markdown(f"**Step {step} · Final answer**")


def _render_feedback_buttons(msg_idx: int, question: str, answer: str) -> None:
    existing  = st.session_state.feedback.get(msg_idx)
    up_type   = "primary"   if existing == "up"   else "secondary"
    down_type = "primary"   if existing == "down" else "secondary"
    col_up, col_dn, _ = st.columns([1, 1, 8])

    if col_up.button("👍", key=f"up_{msg_idx}", type=up_type):
        if existing != "up":
            st.session_state.feedback[msg_idx] = "up"
            _save_feedback(question, answer, "up")
            st.toast("Thanks for the feedback!", icon="✅")

    if col_dn.button("👎", key=f"dn_{msg_idx}", type=down_type):
        if existing != "down":
            st.session_state.feedback[msg_idx] = "down"
            _save_feedback(question, answer, "down")
            st.toast("Feedback noted — we will improve!", icon="📝")


# ---------------------------------------------------------------------------
# Chat history renderer
# ---------------------------------------------------------------------------
def _render_chat_history() -> None:
    for i, msg in enumerate(st.session_state.messages):
        role    = msg["role"]
        content = msg["content"]
        meta    = msg.get("meta", {})

        if role == "user":
            st.markdown(
                f'<div class="msg-user">You: {content}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="msg-bot">ArduinoMate: {content}</div>',
                unsafe_allow_html=True,
            )

            if meta.get("out_of_scope"):
                st.markdown(
                    '<span class="oos-badge">Out of scope — no matching docs found</span>',
                    unsafe_allow_html=True,
                )

            if meta.get("citations"):
                _render_citations(meta["citations"])

            if meta.get("steps"):
                _render_agent_steps(meta["steps"])

            if meta.get("model"):
                lat = meta.get("latency_s")
                lat_str = f" · {lat:.1f}s" if lat else ""
                st.caption(f"`{meta['model']}`{lat_str}")

            user_q = ""
            if i > 0 and st.session_state.messages[i - 1]["role"] == "user":
                user_q = st.session_state.messages[i - 1]["content"]
            _render_feedback_buttons(i, user_q, content)
            st.divider()


# ---------------------------------------------------------------------------
# Send a message
# ---------------------------------------------------------------------------
def _send_message(question: str, cfg: dict[str, Any]) -> None:
    api_url = st.session_state.api_url
    mode    = cfg["mode"]

    st.session_state.messages.append({
        "role":    "user",
        "content": question,
        "meta":    {},
    })

    with st.spinner("ArduinoMate is thinking..."):
        t0 = time.perf_counter()
        try:
            if mode == "ask":
                data   = _call_ask(
                    question,
                    top_k=cfg.get("top_k", 5),
                    min_score=cfg.get("min_score", 0.20),
                    api_url=api_url,
                )
                answer = data.get("answer", "No answer returned.")
                meta   = {
                    "citations":    data.get("citations", []),
                    "out_of_scope": data.get("out_of_scope", False),
                    "model":        data.get("model", ""),
                    "latency_s":    round(time.perf_counter() - t0, 2),
                    "steps":        [],
                }
            else:
                data   = _call_agent(
                    question,
                    thread_id=cfg.get("thread_id", "default"),
                    use_graph=cfg.get("use_graph", True),
                    api_url=api_url,
                )
                answer = data.get("answer", "No answer returned.")
                meta   = {
                    "citations":    [],
                    "out_of_scope": False,
                    "model":        data.get("model", ""),
                    "latency_s":    round(time.perf_counter() - t0, 2),
                    "steps":        data.get("steps", []),
                }

        except requests.exceptions.ConnectionError:
            answer = "Could not connect to the ArduinoMate API. Check that the backend is running and try again."
            meta = {}
        except requests.exceptions.Timeout:
            answer = "The API request timed out. Try again."
            meta   = {}
        except requests.exceptions.HTTPError as exc:
            answer = f"API error {exc.response.status_code}: {exc.response.text[:200]}"
            meta   = {}
        except Exception as exc:
            answer = f"Unexpected error: {exc}"
            meta   = {}

    st.session_state.messages.append({
        "role":    "assistant",
        "content": answer,
        "meta":    meta,
    })


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------
def main() -> None:
    cfg = _render_sidebar()

    # Two-column layout: chat on left, pin map on right
    col_chat, col_map = st.columns([3, 2], gap="large")

    with col_chat:
        st.markdown("## ArduinoMate Chat")

        mode_display = "RAG (/ask)" if cfg["mode"] == "ask" else "Agent (/agent)"
        st.caption(f"Mode: **{mode_display}**")

        # Render conversation history
        _render_chat_history()

        # Input row
        with st.form("chat_form", clear_on_submit=True):
            question = st.text_input(
                "Ask an Arduino question",
                placeholder="e.g. How do I blink an LED on pin 13?",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Send", use_container_width=True)

        if submitted and question.strip():
            _send_message(question.strip(), cfg)
            st.rerun()

        # Quick example buttons
        st.markdown("**Try an example:**")
        examples = [
            "What does pinMode() do?",
            "How do I fade an LED with analogWrite() on pin 9?",
            "What resistor for a red LED on 5V at 20mA?",
            "Explain the difference between delay() and millis()",
        ]
        ex_cols = st.columns(len(examples))
        for col, ex in zip(ex_cols, examples):
            if col.button(ex[:30] + ("..." if len(ex) > 30 else ""), use_container_width=True):
                _send_message(ex, cfg)
                st.rerun()

        # Clear chat
        st.divider()
        if st.button("Clear chat", use_container_width=False):
            st.session_state.messages = []
            st.session_state.feedback = {}
            st.rerun()

    # ---------------------------------------------------------------------------
    # Right panel: Arduino Uno Pin Map
    # ---------------------------------------------------------------------------
    with col_map:
        # Find the last assistant answer to drive pin highlights
        last_answer = ""
        for m in reversed(st.session_state.messages):
            if m["role"] == "assistant":
                last_answer = m["content"]
                break

        _render_pin_map(last_answer)

        # Pin legend
        with st.expander("Pin legend", expanded=False):
            st.markdown("""
| Colour | Meaning |
|--------|---------|
| 🟡 Amber | Active pin (mentioned in answer) |
| 🔵 Blue | PWM-capable digital pin |
| 🟣 Purple | Analog input (A0–A5) |
| 🔴 Red | Power pin (5V / 3.3V / GND / VIN) |
| ⬜ Grey | Idle digital pin |
""")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
