"""
eval/run_eval.py — RAG Evaluation Runner
-----------------------------------------
Runs the RAG pipeline over eval/eval_set.json under two configurations
and prints a comparison table.

Configurations
--------------
  Config A — small chunks / narrow retrieval
      chunk_size = 300  (MAX_CHARS in chunking)
      top_k      = 3

  Config B — standard chunks / wider retrieval  (Day 7 defaults)
      chunk_size = 500
      top_k      = 5

Metrics per question
--------------------
  answered        : bool  — did the LLM produce a non-"I don't know" answer?
  correct_refusal : bool  — for out-of-scope Qs, did it correctly say I don't know?
  source_hit      : bool  — did at least one expected source appear in citations?
  retrieved       : int   — number of chunks retrieved

Aggregate metrics per config
-----------------------------
  answer_rate     : fraction of in-scope Qs that received a real answer
  refusal_rate    : fraction of out-of-scope Qs that correctly refused
  source_hit_rate : fraction of in-scope Qs where ≥1 expected source was cited
  avg_retrieved   : mean chunks retrieved across all questions

Usage
-----
    python eval/run_eval.py

    # Force a full vector-index rebuild before running (slow, one-time):
    python eval/run_eval.py --rebuild
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Add project root to path so app imports work when run from eval/ or root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.app.rag import OUT_OF_SCOPE_MARKER, rag_answer  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration pairs to compare
# ---------------------------------------------------------------------------
CONFIGS: list[dict] = [
    {
        "name":       "Config A — chunk=300 / top_k=3",
        "top_k":      3,
        "min_score":  0.20,
        "chunk_size": 300,   # informational; actual chunking uses live index
    },
    {
        "name":       "Config B — chunk=500 / top_k=5",
        "top_k":      5,
        "min_score":  0.20,
        "chunk_size": 500,   # Day 7 defaults
    },
]

EVAL_PATH = ROOT / "eval" / "eval_set.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_refusal(answer: str) -> bool:
    return OUT_OF_SCOPE_MARKER.lower() in answer.lower()


def _source_hit(citations: list, expected_sources: list[str]) -> bool:
    """Return True if any citation title fuzzy-matches an expected source."""
    if not expected_sources:
        return True  # out-of-scope Qs have no expected source
    for c in citations:
        title = c.title.lower()
        for exp in expected_sources:
            if exp.lower() in title or title in exp.lower():
                return True
    return False


# ---------------------------------------------------------------------------
# Run one config over all questions
# ---------------------------------------------------------------------------
def run_config(questions: list[dict], cfg: dict) -> list[dict]:
    """
    Run rag_answer() for every question in questions using cfg parameters.
    Returns a list of per-question result dicts.
    """
    results = []
    for q in questions:
        t0 = time.time()
        resp = rag_answer(
            question=q["question"],
            top_k=cfg["top_k"],
            min_score=cfg["min_score"],
            chunk_size=cfg["chunk_size"],
        )
        elapsed = round(time.time() - t0, 2)

        is_refusal      = _is_refusal(resp.answer)
        expect_answer   = q["expect_answer"]
        answered        = not is_refusal
        correct_refusal = (not expect_answer) and is_refusal
        source_hit      = _source_hit(resp.citations, q["expected_sources"]) if expect_answer else None

        results.append({
            "id":              q["id"],
            "question":        q["question"][:70] + ("…" if len(q["question"]) > 70 else ""),
            "expect_answer":   expect_answer,
            "answered":        answered,
            "correct_refusal": correct_refusal,
            "source_hit":      source_hit,
            "retrieved":       resp.retrieved,
            "elapsed_s":       elapsed,
            "answer_preview":  resp.answer[:120].replace("\n", " "),
        })

        status_icon = "✅" if (answered if expect_answer else correct_refusal) else "❌"
        print(f"  {status_icon} {q['id']} [{elapsed:.1f}s] {q['question'][:55]}…")

    return results


# ---------------------------------------------------------------------------
# Aggregate metrics
# ---------------------------------------------------------------------------
def aggregate(results: list[dict]) -> dict:
    in_scope   = [r for r in results if r["expect_answer"]]
    out_scope  = [r for r in results if not r["expect_answer"]]

    answer_rate   = sum(r["answered"] for r in in_scope) / len(in_scope) if in_scope else 0.0
    refusal_rate  = sum(r["correct_refusal"] for r in out_scope) / len(out_scope) if out_scope else 0.0
    source_hits   = [r for r in in_scope if r["source_hit"]]
    source_rate   = len(source_hits) / len(in_scope) if in_scope else 0.0
    avg_retrieved = sum(r["retrieved"] for r in results) / len(results) if results else 0.0
    avg_elapsed   = sum(r["elapsed_s"] for r in results) / len(results) if results else 0.0

    return {
        "answer_rate":    round(answer_rate,   3),
        "refusal_rate":   round(refusal_rate,  3),
        "source_hit_rate": round(source_rate,  3),
        "avg_retrieved":  round(avg_retrieved, 2),
        "avg_elapsed_s":  round(avg_elapsed,   2),
    }


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------
def print_table(all_results: list[tuple[str, list[dict], dict]]) -> None:
    """Print a markdown-style comparison table."""
    print("\n" + "=" * 80)
    print("RAG EVALUATION RESULTS")
    print("=" * 80)

    # Per-question detail
    for cfg_name, results, _ in all_results:
        print(f"\n── {cfg_name} ──")
        header = f"{'ID':>4}  {'Ans?':5}  {'Ref?':5}  {'SrcHit':7}  {'Ret':3}  {'s':5}  Question"
        print(header)
        print("-" * 90)
        for r in results:
            ans_ok  = "✅" if r["answered"]        else "❌"  if r["expect_answer"]  else "—"
            ref_ok  = "✅" if r["correct_refusal"] else "—"  if r["expect_answer"]   else "❌"
            src_ok  = "✅" if r["source_hit"]      else "❌"  if r["source_hit"] is not None else "—"
            print(
                f"{r['id']:>4}  {ans_ok:5}  {ref_ok:5}  {src_ok:7}  "
                f"{r['retrieved']:3}  {r['elapsed_s']:5.1f}  {r['question'][:55]}"
            )

    # Aggregate summary
    print("\n" + "=" * 80)
    print(f"{'Metric':<22}", end="")
    for cfg_name, _, _ in all_results:
        short = cfg_name.split("—")[1].strip() if "—" in cfg_name else cfg_name
        print(f"  {short:<28}", end="")
    print()
    print("-" * 80)

    metric_labels = {
        "answer_rate":     "Answer rate (in-scope)",
        "refusal_rate":    "Refusal rate (out-scope)",
        "source_hit_rate": "Source hit rate",
        "avg_retrieved":   "Avg chunks retrieved",
        "avg_elapsed_s":   "Avg latency (s)",
    }

    for key, label in metric_labels.items():
        print(f"{label:<22}", end="")
        for _, _, agg in all_results:
            val = agg[key]
            fmt = f"{val:.0%}" if key.endswith("rate") else f"{val:.2f}"
            print(f"  {fmt:<28}", end="")
        print()

    # Determine winner
    scores = []
    for cfg_name, _, agg in all_results:
        composite = (
            agg["answer_rate"]    * 0.35 +
            agg["refusal_rate"]   * 0.35 +
            agg["source_hit_rate"]* 0.30
        )
        scores.append((cfg_name, composite))

    scores.sort(key=lambda x: x[1], reverse=True)
    winner_name, winner_score = scores[0]
    print("\n" + "=" * 80)
    print(f"🏆 WINNER: {winner_name}  (composite score: {winner_score:.3f})")
    print("=" * 80 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    rebuild = "--rebuild" in sys.argv

    if rebuild:
        print("[eval] Rebuilding vector index …")
        from backend.app.vectorstore import build_index
        build_index(force_rebuild=True)
    else:
        # Ensure index is built
        from backend.app.vectorstore import build_index
        build_index(force_rebuild=False)

    questions = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    print(f"\n[eval] Loaded {len(questions)} questions from eval_set.json\n")

    all_results: list[tuple[str, list[dict], dict]] = []

    for cfg in CONFIGS:
        print(f"\n[eval] Running: {cfg['name']}")
        results = run_config(questions, cfg)
        agg     = aggregate(results)
        all_results.append((cfg["name"], results, agg))
        print(f"       → answer={agg['answer_rate']:.0%}  refusal={agg['refusal_rate']:.0%}  "
              f"src_hit={agg['source_hit_rate']:.0%}  avg_ret={agg['avg_retrieved']:.1f}")

    print_table(all_results)


if __name__ == "__main__":
    main()
