"""
Consistency check: run one algorithm through the full pipeline N independent
times and report how often the recommendation agrees across runs.

Each run is a fresh, independent set of API calls (same as evaluate.py) --
no state is shared between runs. Useful for borderline cases where the
model's judgement might not be stable across samples.

Runs are resumable: each run's full output is written to disk as it
completes, and an existing run_<i>.json is reused instead of re-spending API
calls. Re-running the same command after a crash continues from where it
stopped; pass --fresh to force a complete re-run.
"""

from __future__ import annotations
import argparse
import json
import os
import time

from .algorithms import ALGORITHMS
from .orchestrator import analyze_algorithm
from .llm_client import LLMClient
from .paths import outputs_root

RETRY_BACKOFFS = (30, 90)  # seconds to wait before retry 1 and retry 2


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)[:40]


def run_pipeline_once(algo: dict, client: LLMClient, out_path: str,
                      fresh: bool = False) -> tuple[dict | None, str | None, bool]:
    """One full pipeline pass with a disk cache and retry-with-backoff.

    If out_path already exists (and fresh is False), load and return it
    instead of spending API calls -- this is what makes a crashed batch run
    resumable. On failure, retry after RETRY_BACKOFFS delays; after the last
    attempt, return the error instead of raising so a batch caller can record
    it and move on rather than losing the whole run.

    Returns (result, error, from_cache) -- exactly one of result/error is set.
    """
    if not fresh and os.path.exists(out_path):
        with open(out_path) as f:
            return json.load(f), None, True

    last_err = None
    for attempt in range(len(RETRY_BACKOFFS) + 1):
        try:
            out = analyze_algorithm(algo, client, verbose=False)
            with open(out_path, "w") as f:
                json.dump(out, f, indent=2)
            return out, None, False
        except Exception as e:  # deliberately broad: record and continue the batch
            last_err = e
            if attempt < len(RETRY_BACKOFFS):
                delay = RETRY_BACKOFFS[attempt]
                print(f"    API error: {e} -- retry {attempt + 1}/{len(RETRY_BACKOFFS)} in {delay}s")
                time.sleep(delay)
    return None, f"{type(last_err).__name__}: {last_err}", False


def check_consistency(algorithm_name: str, n_runs: int,
                      client: LLMClient | None = None, fresh: bool = False) -> dict:
    client = client or LLMClient()
    algo = next(a for a in ALGORITHMS if a["name"] == algorithm_name)
    want = algo["known_label"]["primitive"].lower()

    out_dir = os.path.join(outputs_root(client.backend), "consistency_" + _slug(algorithm_name))
    os.makedirs(out_dir, exist_ok=True)

    runs = []
    try:
        for i in range(1, n_runs + 1):
            out_path = os.path.join(out_dir, f"run_{i}.json")
            out, err, cached = run_pipeline_once(algo, client, out_path, fresh=fresh)
            if err is not None:
                runs.append({"run": i, "error": err})
                print(f"  run {i}/{n_runs}: FAILED after retries -- {err}")
                continue
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
            print(f"  run {i}/{n_runs}: got={got} confidence={entry['overall_confidence']} "
                  f"review={entry['review_verdict']} rounds={entry['rounds_used']}"
                  f"{' (cached)' if cached else ''}")
    finally:
        # Always write the summary, even on interrupt -- partial data beats none.
        ok_runs = [r for r in runs if "error" not in r]
        correct_count = sum(r["correct"] for r in ok_runs)
        summary = {
            "algorithm": algorithm_name,
            "expected": want,
            "n_runs": n_runs,
            "completed_runs": len(ok_runs),
            "failed_runs": len(runs) - len(ok_runs),
            "correct_count": correct_count,
            "incorrect_count": len(ok_runs) - correct_count,
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
        if "error" in r:
            print(f"{r['run']:<5}FAILED: {r['error']}")
            continue
        print(f"{r['run']:<5}{r['got']:<20}{(r['overall_confidence'] or ''):<12}"
              f"{(r['review_verdict'] or ''):<10}{r['rounds_used']:<8}"
              f"{'yes' if r['correct'] else 'no':<8}")
    print(f"\n{summary['correct_count']}/{summary['completed_runs']} correct "
          f"(expected: {summary['expected']}), "
          f"{summary['incorrect_count']}/{summary['completed_runs']} incorrect"
          + (f", {summary['failed_runs']} failed" if summary["failed_runs"] else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo-name", default="Graph connectivity: are two vertices connected?",
                     help="exact 'name' field from algorithms.py")
    ap.add_argument("--n", type=int, default=8, help="number of independent runs")
    ap.add_argument("--fresh", action="store_true",
                     help="re-run everything, ignoring existing run_<i>.json files")
    args = ap.parse_args()

    client = LLMClient()
    print(f"Backend: {client.backend} / model: {client.model} / "
          f"temperature: {client.temperature}\n")
    summary = check_consistency(args.algo_name, args.n, client, fresh=args.fresh)
    _print_table(summary)


if __name__ == "__main__":
    main()
