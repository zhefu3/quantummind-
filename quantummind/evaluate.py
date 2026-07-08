"""
Layer-1 evaluation (proposal 5.1): run the pipeline on the labelled test set and compare
the system's primitive recommendation against the known answer.

IMPORTANT caveat (kept visible by design): these known cases are textbook and heavily
present in LLM training data, so a high score here largely reflects RETRIEVAL, not
reasoning. The "trap" rate below -- whether the system avoids the HHL/readout false
positive -- is a more honest signal than raw accuracy. Treat this layer as a sanity check,
not as evidence of discovery ability.
"""

from __future__ import annotations
import json
import os
from .algorithms import ALGORITHMS
from .orchestrator import analyze_algorithm
from .llm_client import LLMClient

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
EVAL_DETAILS_DIR = os.path.join(OUT_DIR, "eval_details")


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)[:40]


def evaluate(client: LLMClient | None = None) -> dict:
    client = client or LLMClient()
    os.makedirs(EVAL_DETAILS_DIR, exist_ok=True)
    # Questions labelled "unknown" have no fixed ground truth (they are open-ended
    # exploration cases) -- the system can never literally answer "unknown", so
    # scoring them as wrong would only pollute the accuracy. Score the labelled
    # set; report the exploratory set separately without a correct/incorrect call.
    labeled_results, exploratory_results, correct = [], [], 0
    for algo in ALGORITHMS:
        out = analyze_algorithm(algo, client, verbose=False)
        got = (out["matching"].get("recommendation") or "none").lower()
        want = algo["known_label"]["primitive"].lower()

        # Full Agent 1-4 output (structure/matching/scheme/review) so a failed case
        # can be replayed after the fact -- evaluate() previously discarded this.
        detail_path = os.path.join(EVAL_DETAILS_DIR, f"{_slug(algo['name'])}.json")
        with open(detail_path, "w") as f:
            json.dump(out, f, indent=2)

        entry = {
            "algorithm": algo["name"],
            "got": got,
            "scheme_speedup": out["scheme"].get("speedup_estimate"),
            "review_verdict": out["review"].get("verdict"),
            "rounds_used": out["rounds_used"],
            "detail_file": os.path.relpath(detail_path, OUT_DIR),
        }
        if want == "unknown":
            entry["confidence"] = out["matching"].get("overall_confidence")
            exploratory_results.append(entry)
        else:
            ok = got == want
            correct += ok
            entry.update({
                "expected": want,
                "correct": ok,
                "is_hard_negative": "HARD NEGATIVE" in algo["known_label"]["note"],
            })
            labeled_results.append(entry)

    hard = [r for r in labeled_results if r["is_hard_negative"]]
    summary = {
        "n_labeled": len(labeled_results),
        "n_exploratory": len(exploratory_results),
        "labeled_accuracy": round(correct / len(labeled_results), 3) if labeled_results else None,
        "hard_negative_handled": all(r["correct"] for r in hard) if hard else None,
        "labeled_results": labeled_results,
        "exploratory_results": exploratory_results,
        "backend": client.backend,
        "model": client.model,
    }
    return summary


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
