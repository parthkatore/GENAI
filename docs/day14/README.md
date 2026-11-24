# Day 14 — Interview and Demo-Day Preparation

Day 14 packages the ArduinoMate project for an interview and final demonstration.

## Deliverables

- [Interview pitch and ten likely Q&A](../interview.md)
- A board-specific correctness story that distinguishes implemented behavior from known chunking gaps.
- A demo run-of-show and a checklist for verifying the API, RAG answers, citations, agent, and pin-map UI.

## Five-minute demo run-of-show

1. **Problem and architecture (45 seconds):** explain why Arduino beginners need source-grounded, board-aware answers.
2. **Ask and cite (90 seconds):** ask about `pinMode()` or `analogRead()`, show the answer, citations, and source passage.
3. **Board-specific behavior (60 seconds):** compare the documented `analogRead()` behavior for Uno and Nano ESP32; do not generalize across boards.
4. **Agent tool (60 seconds):** ask for a resistor for a 5 V supply and 2 V LED at 20 mA; show the E12 result and agent trace.
5. **UI signature and close (45 seconds):** show the Uno pin map and summarize the retrieval and safety trade-offs.

Leave three minutes for questions. Keep `/docs` open as a backup to the Streamlit UI.

## Pre-demo checklist

- [ ] Resume the public Render service or start the local API and Streamlit UI.
- [ ] Configure `GROQ_API_KEY` and `GEMINI_API_KEY` without exposing either value.
- [ ] Wait for `/health` to report `rag_status: "ready"` and `indexed_chunks` greater than zero.
- [ ] Verify a supported question returns citations and an unsupported question is handled honestly.
- [ ] Verify the LED resistor tool and the pin-map panel.
- [ ] Rehearse the full five-minute flow twice and record any issues.

## Rehearsal status

The rehearsals are **blocked, not completed**. On 2026-11-24, the public API returned HTTP 503 with “Service Suspended.” The local ChromaDB index has zero chunks, and the local `.env` has no `GEMINI_API_KEY`, so there is no working end-to-end RAG service to rehearse against. Do not mark the demo complete until the service is resumed, the index is built, and both rehearsals have been performed.

## Release status

The interview materials and demo runbook are prepared. The `final` tag labels this tested repository snapshot; it does not mean the live-demo gate has passed. Complete the pre-demo checklist and both rehearsals after the deployment and RAG index are available.
