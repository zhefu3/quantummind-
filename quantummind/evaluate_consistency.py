"""
Layer-1 evaluation, repeated-run variant.

evaluate.py scores each algorithm on a single sample. A consistency check on
"Graph connectivity: are two vertices connected?" showed that single sample
isn't reliable -- one run said "none", eight independent re-runs all said
"quantum_walk". A one-shot evaluate() can silently report a fluke as ground
truth. This module runs each algorithm K independent times and scores by
MAJORITY VOTE instead, and reports how often the K runs actually agree.
"""

from __future__ import annotations
import argparse
import json
import os
from collections import Counter

from .algorithms import ALGORITHMS
from .orchestrator import analyze_algorithm
from .llm_client import LLMClient

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
DETAILS_DIR = os.path.join(OUT_DIR, "consistency_eval")


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)[:40]


def _format_votes(counts: Counter, k: int) -> str:
    return ", ".join(f"{ans}: {n}/{k}" for ans, n in counts.most_common())


def _format_confidence(counts: Counter) -> str:
    return ", ".join(f"{c}×{n}" for c, n in counts.most_common())


def evaluate_consistency(client: LLMClient | None = None, k: int = 3) -> dict:
    client = client or LLMClient()
    os.makedirs(DETAILS_DIR, exist_ok=True)

    # "unknown"-labelled questions are open-ended exploration cases with no ground
    # truth -- the system can never literally answer "unknown", so scoring them as
    # wrong would only pollute the accuracy. Report their answers and stability
    # separately, unscored (same split as evaluate.py).
    labeled_results, exploratory_results = [], []
    for algo in ALGORITHMS:
        want = algo["known_label"]["primitive"].lower()
        algo_dir = os.path.join(DETAILS_DIR, _slug(algo["name"]))
        os.makedirs(algo_dir, exist_ok=True)

        gots, confidences = [], []
        for i in range(1, k + 1):
            out = analyze_algorithm(algo, client, verbose=False)
            got = (out["matching"].get("recommendation") or "none").lower()
            gots.append(got)
            confidences.append(out["matching"].get("overall_confidence"))
            with open(os.path.join(algo_dir, f"run_{i}.json"), "w") as f:
                json.dump(out, f, indent=2)

        vote_counts = Counter(gots)
        # ties keep first-occurrence order (Counter.most_common is a stable sort)
        majority_answer, majority_count = vote_counts.most_common(1)[0]
        confidence_counts = Counter(confidences)

        entry = {
            "algorithm": algo["name"],
            "k": k,
            "runs": gots,
            "votes": _format_votes(vote_counts, k),
            "majority_answer": majority_answer,
            "majority_count": majority_count,
            "consistency_ratio": round(majority_count / k, 3),
            "fully_consistent": majority_count == k,
            "confidence_distribution": _format_confidence(confidence_counts),
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

    with open(os.path.join(OUT_DIR, "consistency_evaluation.json"), "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def _print_table(summary: dict) -> None:
    k = summary["k"]
    print(f"\nConsistency evaluation (K={k}, backend: {summary['backend']} / {summary['model']})\n")
    header = f"{'algorithm':<52}{'majority':<23}{'consistency':<13}{'correct':<9}{'confidence dist'}"

    print("LABELED (scored by majority vote)")
    print(header)
    for r in summary["labeled_results"]:
        print(f"{r['algorithm'][:50]:<52}{r['majority_answer']:<23}"
              f"{str(r['majority_count']) + '/' + str(k):<13}"
              f"{'yes' if r['correct'] else 'no':<9}{r['confidence_distribution']}")

    print("\nEXPLORATORY (no ground truth -- not scored)")
    print(f"{'algorithm':<52}{'majority':<23}{'consistency':<13}{'':<9}{'confidence dist'}")
    for r in summary["exploratory_results"]:
        print(f"{r['algorithm'][:50]:<52}{r['majority_answer']:<23}"
              f"{str(r['majority_count']) + '/' + str(k):<13}"
              f"{'':<9}{r['confidence_distribution']}")

    print(f"\nLabeled majority-vote accuracy: {summary['labeled_majority_vote_accuracy']} "
          f"(n={summary['n_labeled']})")
    print(f"Fully consistent (K/K same answer, all questions): "
          f"{summary['fully_consistent_fraction']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3, help="independent runs per algorithm")
    args = ap.parse_args()

    client = LLMClient()
    print(f"Backend: {client.backend} / model: {client.model} / temperature: {client.temperature}")
    summary = evaluate_consistency(client, k=args.k)
    _print_table(summary)
    print(f"\nWrote {os.path.join(OUT_DIR, 'consistency_evaluation.json')}")
    print(f"Per-run reasoning saved under {DETAILS_DIR}/<algorithm>/run_<i>.json")


if __name__ == "__main__":
    main()
