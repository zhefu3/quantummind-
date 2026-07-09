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
from .paths import outputs_root

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


def run_all(n_runs: int, client: LLMClient | None = None,
            fresh: bool = False) -> list[dict]:
    client = client or LLMClient()
    summaries = []
    for name in EXPLORATION_ALGORITHMS:
        print(f"=== {name} ===")
        summaries.append(check_consistency(name, n_runs, client, fresh=fresh))
        print()
    return summaries


def _ok_runs(s: dict) -> list[dict]:
    return [r for r in s["runs"] if "error" not in r]


def _print_table(summaries: list[dict]) -> None:
    n = summaries[0]["n_runs"]
    print(f"\nExploration consistency table (N={n} runs each, "
          f"backend: {summaries[0]['backend']} / {summaries[0]['model']} / "
          f"temperature={summaries[0]['temperature']})\n")
    print(f"{'algorithm':<52}{'runs (got)':<50}{'confidence':<25}{'review':<20}{'rounds'}")
    for s in summaries:
        gots = ", ".join(r.get("got", "FAILED") for r in s["runs"])
        confs = ", ".join(r.get("overall_confidence") or "?" for r in s["runs"])
        reviews = ", ".join(r.get("review_verdict") or "?" for r in s["runs"])
        rounds = ", ".join(str(r.get("rounds_used", "?")) for r in s["runs"])
        print(f"{s['algorithm'][:50]:<52}{gots:<50}{confs:<25}{reviews:<20}{rounds}")

    swayed = [s for s in summaries
              if len(set(r["got"] for r in _ok_runs(s))) > 1]
    non_none_consistent = [
        s for s in summaries
        if _ok_runs(s) and len(set(r["got"] for r in _ok_runs(s))) == 1
        and _ok_runs(s)[0]["got"] != "none"
    ]
    failed_total = sum(s.get("failed_runs", 0) for s in summaries)

    print("\n--- Runs that disagreed on speedup (SWAYED) ---")
    if swayed:
        for s in swayed:
            print(f"  {s['algorithm']}: {[r['got'] for r in _ok_runs(s)]}")
    else:
        print("  (none)")

    print("\n--- Runs that agreed on a NON-none answer every time ('has speedup') ---")
    if non_none_consistent:
        for s in non_none_consistent:
            ok = _ok_runs(s)
            print(f"  {s['algorithm']}: {ok[0]['got']} "
                  f"({len(ok)}/{n} runs, confidence: "
                  f"{', '.join(r['overall_confidence'] or '?' for r in ok)})")
    else:
        print("  (none)")

    if failed_total:
        print(f"\nWARNING: {failed_total} run(s) failed after retries -- re-run the "
              f"same command to fill them in (completed runs are cached).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2, help="independent runs per algorithm")
    ap.add_argument("--fresh", action="store_true",
                     help="re-run everything, ignoring existing run_<i>.json files")
    args = ap.parse_args()

    client = LLMClient()
    print(f"Backend: {client.backend} / model: {client.model} / "
          f"temperature: {client.temperature}\n")
    summaries = run_all(args.n, client, fresh=args.fresh)
    _print_table(summaries)

    out_dir = outputs_root(client.backend)
    summary_path = os.path.join(out_dir, "exploration_consistency_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summaries, f, indent=2)
    print(f"\nWrote {summary_path}")
    print(f"Per-run full reasoning saved under {out_dir}/consistency_<algorithm>/run_<i>.json")


if __name__ == "__main__":
    main()
