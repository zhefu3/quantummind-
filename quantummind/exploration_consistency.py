"""
Consistency check across the 8 "explore" algorithms (no fixed ground truth --
see exploration_algorithms.py / the tail of ALGORITHMS in algorithms.py).

Reuses consistency_check.check_consistency() per algorithm -- each run's full
structure/matching/scheme/review is saved to
outputs/consistency_<algorithm>/run_<i>.json, same as a single-algorithm
check. This module just loops over the 8 names and prints/saves one
consolidated table across all of them.
"""

from __future__ import annotations
import argparse
import json
import os

from .consistency_check import check_consistency
from .llm_client import LLMClient

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")

EXPLORATION_ALGORITHMS = [
    "Graph isomorphism",
    "High-dimensional nearest neighbor search",
    "Single-source shortest path to one target",
    "Dense matrix multiplication",
    "Solve a partial differential equation on a grid",
    "Traveling salesman problem (TSP)",
    "Train a small feedforward neural network",
    "Monte Carlo tree search",
]


def run_all(n_runs: int, client: LLMClient | None = None) -> list[dict]:
    client = client or LLMClient()
    summaries = []
    for name in EXPLORATION_ALGORITHMS:
        print(f"=== {name} ===")
        summaries.append(check_consistency(name, n_runs, client))
        print()
    return summaries


def _print_table(summaries: list[dict]) -> None:
    n = summaries[0]["n_runs"]
    print(f"\nExploration consistency table (N={n} runs each, "
          f"backend: {summaries[0]['backend']} / {summaries[0]['model']} / "
          f"temperature={summaries[0]['temperature']})\n")
    print(f"{'algorithm':<52}{'runs (got)':<50}{'confidence':<25}{'review':<20}{'rounds'}")
    for s in summaries:
        gots = ", ".join(r["got"] for r in s["runs"])
        confs = ", ".join(r["overall_confidence"] or "?" for r in s["runs"])
        reviews = ", ".join(r["review_verdict"] or "?" for r in s["runs"])
        rounds = ", ".join(str(r["rounds_used"]) for r in s["runs"])
        print(f"{s['algorithm'][:50]:<52}{gots:<50}{confs:<25}{reviews:<20}{rounds}")

    swayed = [s for s in summaries if len(set(r["got"] for r in s["runs"])) > 1]
    non_none_consistent = [
        s for s in summaries
        if len(set(r["got"] for r in s["runs"])) == 1 and s["runs"][0]["got"] != "none"
    ]

    print("\n--- Runs that disagreed on speedup (SWAYED) ---")
    if swayed:
        for s in swayed:
            print(f"  {s['algorithm']}: {[r['got'] for r in s['runs']]}")
    else:
        print("  (none)")

    print("\n--- Runs that agreed on a NON-none answer every time ('has speedup') ---")
    if non_none_consistent:
        for s in non_none_consistent:
            print(f"  {s['algorithm']}: {s['runs'][0]['got']} "
                  f"({n}/{n} runs, confidence: "
                  f"{', '.join(r['overall_confidence'] or '?' for r in s['runs'])})")
    else:
        print("  (none)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2, help="independent runs per algorithm")
    args = ap.parse_args()

    client = LLMClient()
    print(f"Backend: {client.backend} / model: {client.model} / "
          f"temperature: {client.temperature}\n")
    summaries = run_all(args.n, client)
    _print_table(summaries)

    with open(os.path.join(OUT_DIR, "exploration_consistency_summary.json"), "w") as f:
        json.dump(summaries, f, indent=2)
    print(f"\nWrote {os.path.join(OUT_DIR, 'exploration_consistency_summary.json')}")
    print("Per-run full reasoning saved under outputs/consistency_<algorithm>/run_<i>.json")


if __name__ == "__main__":
    main()
