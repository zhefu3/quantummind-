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
from .algorithms import ALGORITHMS
from .orchestrator import analyze_algorithm
from .llm_client import LLMClient


def evaluate(client: LLMClient | None = None) -> dict:
    client = client or LLMClient()
    results, correct = [], 0
    for algo in ALGORITHMS:
        out = analyze_algorithm(algo, client, verbose=False)
        got = (out["matching"].get("recommendation") or "none").lower()
        want = algo["known_label"]["primitive"].lower()
        ok = got == want
        correct += ok
        results.append({
            "algorithm": algo["name"],
            "expected": want,
            "got": got,
            "correct": ok,
            "is_hard_negative": "HARD NEGATIVE" in algo["known_label"]["note"],
            "scheme_speedup": out["scheme"].get("speedup_estimate"),
            "review_verdict": out["review"].get("verdict"),
            "rounds_used": out["rounds_used"],
        })

    hard = [r for r in results if r["is_hard_negative"]]
    summary = {
        "n": len(results),
        "accuracy": round(correct / len(results), 3),
        "hard_negative_handled": all(r["correct"] for r in hard) if hard else None,
        "results": results,
        "backend": client.backend,
        "model": client.model,
    }
    return summary


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate(), indent=2))
