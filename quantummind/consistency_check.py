"""
Consistency check: run one algorithm through the full pipeline N independent
times and report how often the recommendation agrees across runs.

Each run is a fresh, independent set of API calls (same as evaluate.py) --
no state is shared between runs. Useful for borderline cases where the
model's judgement might not be stable across samples.
"""

from __future__ import annotations
import argparse
import json
import os

from .algorithms import ALGORITHMS
from .orchestrator import analyze_algorithm
from .llm_client import LLMClient

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)[:40]


def check_consistency(algorithm_name: str, n_runs: int, client: LLMClient | None = None) -> dict:
    client = client or LLMClient()
    algo = next(a for a in ALGORITHMS if a["name"] == algorithm_name)
    want = algo["known_label"]["primitive"].lower()

    out_dir = os.path.join(OUT_DIR, "consistency_" + _slug(algorithm_name))
    os.makedirs(out_dir, exist_ok=True)

    runs = []
    for i in range(1, n_runs + 1):
        out = analyze_algorithm(algo, client, verbose=False)
        got = (out["matching"].get("recommendation") or "none").lower()
        entry = {
            "run": i,
            "got": got,
            "correct": got == want,
            "overall_confidence": out["matching"].get("overall_confidence"),
            "review_verdict": out["review"].get("verdict"),
            "rounds_used": out["rounds_used"],
        }
        runs.append(entry)

        with open(os.path.join(out_dir, f"run_{i}.json"), "w") as f:
            json.dump(out, f, indent=2)

        print(f"  run {i}/{n_runs}: got={got} confidence={entry['overall_confidence']} "
              f"review={entry['review_verdict']} rounds={entry['rounds_used']}")

    correct_count = sum(r["correct"] for r in runs)
    summary = {
        "algorithm": algorithm_name,
        "expected": want,
        "n_runs": n_runs,
        "correct_count": correct_count,
        "incorrect_count": n_runs - correct_count,
        "runs": runs,
        "backend": client.backend,
        "model": client.model,
        "temperature": client.temperature,
    }

    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def _print_table(summary: dict) -> None:
    print(f"\nAlgorithm: {summary['algorithm']}")
    print(f"Expected: {summary['expected']}  (backend: {summary['backend']} / "
          f"{summary['model']} / temperature={summary['temperature']})\n")
    print(f"{'run':<5}{'got':<20}{'confidence':<12}{'review':<10}{'rounds':<8}{'correct':<8}")
    for r in summary["runs"]:
        print(f"{r['run']:<5}{r['got']:<20}{(r['overall_confidence'] or ''):<12}"
              f"{(r['review_verdict'] or ''):<10}{r['rounds_used']:<8}"
              f"{'yes' if r['correct'] else 'no':<8}")
    print(f"\n{summary['correct_count']}/{summary['n_runs']} correct "
          f"(expected: {summary['expected']}), "
          f"{summary['incorrect_count']}/{summary['n_runs']} incorrect")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo-name", default="Graph connectivity: are two vertices connected?",
                     help="exact 'name' field from algorithms.py")
    ap.add_argument("--n", type=int, default=8, help="number of independent runs")
    args = ap.parse_args()

    client = LLMClient()
    print(f"Backend: {client.backend} / model: {client.model} / "
          f"temperature: {client.temperature}\n")
    summary = check_consistency(args.algo_name, args.n, client)
    _print_table(summary)


if __name__ == "__main__":
    main()
