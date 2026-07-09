"""
Layer-1 evaluation, repeated-run variant.

evaluate.py scores each algorithm on a single sample. A consistency check on
"Graph connectivity: are two vertices connected?" showed that single sample
isn't reliable -- one run said "none", eight independent re-runs all said
"quantum_walk". A one-shot evaluate() can silently report a fluke as ground
truth. This module runs each algorithm K independent times and scores by
MAJORITY VOTE instead, and reports how often the K runs actually agree.

Runs are resumable: each run's full output is written to disk as it
completes, and existing run_<i>.json files are reused instead of re-spending
API calls. Re-running the same command after a crash continues from where it
stopped; pass --fresh to force a complete re-run.
"""

from __future__ import annotations
import argparse
import json
import os
import time
from collections import Counter

from .algorithms import ALGORITHMS
from .consistency_check import run_pipeline_once
from .llm_client import LLMClient
from .paths import outputs_root


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)[:40]


def _format_votes(counts: Counter, k: int) -> str:
    return ", ".join(f"{ans}: {n}/{k}" for ans, n in counts.most_common())


def _format_confidence(counts: Counter) -> str:
    return ", ".join(f"{c}×{n}" for c, n in counts.most_common())


def evaluate_consistency(client: LLMClient | None = None, k: int = 3,
                          fresh: bool = False) -> dict:
    client = client or LLMClient()
    out_dir = outputs_root(client.backend)
    details_dir = os.path.join(out_dir, "consistency_eval")
    os.makedirs(details_dir, exist_ok=True)

    # "unknown"-labelled questions are open-ended exploration cases with no ground
    # truth -- the system can never literally answer "unknown", so scoring them as
    # wrong would only pollute the accuracy. Report their answers and stability
    # separately, unscored (same split as evaluate.py).
    labeled_results, exploratory_results = [], []
    total = len(ALGORITHMS)
    t0 = time.time()
    try:
        for idx, algo in enumerate(ALGORITHMS, 1):
            want = algo["known_label"]["primitive"].lower()
            algo_dir = os.path.join(details_dir, _slug(algo["name"]))
            os.makedirs(algo_dir, exist_ok=True)

            gots, confidences, failed = [], [], 0
            for i in range(1, k + 1):
                out_path = os.path.join(algo_dir, f"run_{i}.json")
                out, err, cached = run_pipeline_once(algo, client, out_path, fresh=fresh)
                elapsed_min = (time.time() - t0) / 60
                if err is not None:
                    failed += 1
                    print(f"[{idx}/{total}] {algo['name'][:45]}: run {i}/{k} "
                          f"FAILED -- {err} ({elapsed_min:.1f} min elapsed)")
                    continue
                got = (out["matching"].get("recommendation") or "none").lower()
                gots.append(got)
                confidences.append(out["matching"].get("overall_confidence"))
                print(f"[{idx}/{total}] {algo['name'][:45]}: run {i}/{k} got={got} "
                      f"({elapsed_min:.1f} min elapsed{', cached' if cached else ''})")

            if gots:
                vote_counts = Counter(gots)
                # ties keep first-occurrence order (Counter.most_common is stable)
                majority_answer, majority_count = vote_counts.most_common(1)[0]
            else:
                vote_counts, majority_answer, majority_count = Counter(), None, 0

            entry = {
                "algorithm": algo["name"],
                "k": k,
                "completed_runs": len(gots),
                "failed_runs": failed,
                "runs": gots,
                "votes": _format_votes(vote_counts, k),
                "majority_answer": majority_answer,
                "majority_count": majority_count,
                "consistency_ratio": (round(majority_count / len(gots), 3)
                                       if gots else None),
                # only claim full consistency when every run completed AND agreed
                "fully_consistent": len(gots) == k and majority_count == k,
                "confidence_distribution": _format_confidence(Counter(confidences)),
            }
            if want == "unknown":
                exploratory_results.append(entry)
            else:
                entry.update({
                    "expected": want,
                    "correct": majority_answer == want,
                    "is_hard_negative": "HARD NEGATIVE" in algo["known_label"]["note"],
                })
                labeled_results.append(entry)
    finally:
        # Always write the summary, even on interrupt -- partial data beats none.
        all_results = labeled_results + exploratory_results
        summary = {
            "k": k,
            "n_labeled": len(labeled_results),
            "n_exploratory": len(exploratory_results),
            "labeled_majority_vote_accuracy": (
                round(sum(r["correct"] for r in labeled_results) / len(labeled_results), 3)
                if labeled_results else None),
            "fully_consistent_fraction": (
                round(sum(r["fully_consistent"] for r in all_results) / len(all_results), 3)
                if all_results else None),
            "labeled_results": labeled_results,
            "exploratory_results": exploratory_results,
            "backend": client.backend,
            "model": client.model,
        }
        with open(os.path.join(out_dir, "consistency_evaluation.json"), "w") as f:
            json.dump(summary, f, indent=2)

    return summary


def _print_table(summary: dict) -> None:
    k = summary["k"]
    print(f"\nConsistency evaluation (K={k}, backend: {summary['backend']} / {summary['model']})\n")

    print("LABELED (scored by majority vote)")
    print(f"{'algorithm':<52}{'majority':<23}{'consistency':<13}{'correct':<9}{'confidence dist'}")
    for r in summary["labeled_results"]:
        print(f"{r['algorithm'][:50]:<52}{(r['majority_answer'] or '—'):<23}"
              f"{str(r['majority_count']) + '/' + str(k):<13}"
              f"{'yes' if r['correct'] else 'no':<9}{r['confidence_distribution']}")

    print("\nEXPLORATORY (no ground truth -- not scored)")
    print(f"{'algorithm':<52}{'majority':<23}{'consistency':<13}{'':<9}{'confidence dist'}")
    for r in summary["exploratory_results"]:
        print(f"{r['algorithm'][:50]:<52}{(r['majority_answer'] or '—'):<23}"
              f"{str(r['majority_count']) + '/' + str(k):<13}"
              f"{'':<9}{r['confidence_distribution']}")

    print(f"\nLabeled majority-vote accuracy: {summary['labeled_majority_vote_accuracy']} "
          f"(n={summary['n_labeled']})")
    print(f"Fully consistent (K/K same answer, all questions): "
          f"{summary['fully_consistent_fraction']}")
    n_failed = sum(r["failed_runs"] for r in
                   summary["labeled_results"] + summary["exploratory_results"])
    if n_failed:
        print(f"WARNING: {n_failed} run(s) failed after retries -- see FAILED lines above; "
              f"re-run the same command to fill them in (completed runs are cached).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3, help="independent runs per algorithm")
    ap.add_argument("--fresh", action="store_true",
                     help="re-run everything, ignoring existing run_<i>.json files")
    args = ap.parse_args()

    client = LLMClient()
    print(f"Backend: {client.backend} / model: {client.model} / temperature: {client.temperature}")
    summary = evaluate_consistency(client, k=args.k, fresh=args.fresh)
    _print_table(summary)
    out_dir = outputs_root(client.backend)
    print(f"\nWrote {os.path.join(out_dir, 'consistency_evaluation.json')}")
    print(f"Per-run reasoning saved under {os.path.join(out_dir, 'consistency_eval')}/<algorithm>/run_<i>.json")


if __name__ == "__main__":
    main()
