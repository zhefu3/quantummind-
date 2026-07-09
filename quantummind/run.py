"""
CLI entry point.

Examples:
  python -m quantummind.run --all                 # run pipeline on the whole test set
  python -m quantummind.run --eval                # run Layer-1 evaluation (single sample)
  python -m quantummind.run --eval --k 3          # evaluation by majority vote over 3 runs
  python -m quantummind.run --algo 3              # run one algorithm by index

A single sample per question is not always reliable (see
docs/consistency_experiment.md) -- for a real-model evaluation, prefer --k 2
or higher; answers are then scored by majority vote and per-question
agreement is reported alongside.

Backend/model via env:  QM_BACKEND=anthropic QM_MODEL=claude-sonnet-4-6 python -m quantummind.run --all
Default backend is "mock" (no API key needed).
"""

import argparse
import json
import os

from .algorithms import ALGORITHMS
from .orchestrator import analyze_algorithm
from .evaluate import evaluate
from .llm_client import LLMClient
from .paths import outputs_root


def _md_report(result: dict) -> str:
    s, m, sc, rv = result["structure"], result["matching"], result["scheme"], result["review"]
    banner = ("> **MOCK MODE** -- deterministic placeholder output. Set `QM_BACKEND=anthropic` "
              "for real reasoning.\n\n" if result["backend"] == "mock" else "")
    return f"""# Quantization analysis: {result['algorithm']}

{banner}*backend: {result['backend']} / {result['model']} · rounds: {result['rounds_used']}*

## 1. Structural analysis (Agent 1)
- **Paradigm:** {s.get('paradigm')}
- **Classical complexity:** {s.get('classical_complexity')}
- **Bottleneck:** {s.get('bottleneck')}
- **Structural features:** {', '.join(s.get('structural_features', [])) or 'none'}
- **Barrier flags:** {', '.join(s.get('barrier_flags', [])) or 'none'}

## 2. Primitive matching (Agent 2)
- **Recommendation:** `{m.get('recommendation')}` (confidence: {m.get('overall_confidence')})
- **Barrier hits:** {', '.join(m.get('barrier_hits', [])) or 'none'}
- **Gap analysis:** {m.get('gap_analysis')}
- **Scores:**
{chr(10).join(f"    - {x.get('primitive')}: **{x.get('verdict')}** -- {x.get('justification')}" for x in m.get('scores', [])) or '    - (none)'}
- **Note:** {m.get('note', '')}

## 3. Candidate scheme (Agent 3)
- **Scheme:** {sc.get('scheme')}
- **Speedup estimate:** {sc.get('speedup_estimate')}
- **Speedup scope:** `{sc.get('speedup_scope', 'n/a')}`
- **I/O accounting:** {sc.get('io_accounting')}
- **Prerequisites:** {', '.join(sc.get('prerequisites', [])) or 'none'}
- **Obstacles:** {', '.join(sc.get('obstacles', [])) or 'none'}
- **Novelty:** {sc.get('novelty')}
- **Confidence:** {sc.get('confidence')}

## 4. Independent review (Agent 4)
- **Verdict:** `{rv.get('verdict')}` (confidence: {rv.get('confidence')})
- **Issues:** {', '.join(rv.get('issues', [])) or 'none'}
- **Reasoning:** {rv.get('reasoning')}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="run pipeline on the whole test set")
    ap.add_argument("--eval", action="store_true", help="run Layer-1 evaluation")
    ap.add_argument("--k", type=int, default=1,
                    help="with --eval: independent runs per question, scored by "
                         "majority vote (default 1 = classic single-sample eval)")
    ap.add_argument("--algo", type=int, help="run one algorithm by index (0-based)")
    args = ap.parse_args()

    client = LLMClient()
    out_dir = outputs_root(client.backend)
    os.makedirs(out_dir, exist_ok=True)
    print(f"Backend: {client.backend} / model: {client.model}\n")

    if args.eval:
        if args.k > 1:
            from .evaluate_consistency import evaluate_consistency, _print_table
            summary = evaluate_consistency(client, k=args.k)
            _print_table(summary)
            print(f"\nWrote {os.path.join(out_dir, 'consistency_evaluation.json')}")
            return
        summary = evaluate(client)
        path = os.path.join(out_dir, "evaluation.json")
        with open(path, "w") as f:
            json.dump(summary, f, indent=2)
        print(json.dumps(summary, indent=2))
        print(f"\nWrote {path}")
        return

    if args.algo is not None:
        algos = [ALGORITHMS[args.algo]]
    elif args.all:
        algos = ALGORITHMS
    else:
        algos = ALGORITHMS[:1]

    for algo in algos:
        print(f"Analyzing: {algo['name']}")
        result = analyze_algorithm(algo, client)
        slug = "".join(c if c.isalnum() else "_" for c in algo["name"])[:40]
        md_path = os.path.join(out_dir, f"report_{slug}.md")
        json_path = os.path.join(out_dir, f"result_{slug}.json")
        with open(md_path, "w") as f:
            f.write(_md_report(result))
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  -> {md_path}\n")


if __name__ == "__main__":
    main()
