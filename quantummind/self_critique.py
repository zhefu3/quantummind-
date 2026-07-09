"""
Self-critique calibration (roadmap step 2).

A diagnostic step that runs AFTER the pipeline has committed to a verdict. It answers
one question: "assuming this verdict is wrong, where is the error most plausibly
hiding?" -- and it must answer by citing specific knowledge-base entries, not generic
hedges. The motivating finding (docs/consistency_experiment.md): the system's own
confidence is NOT a reliability signal, so we need a signal that is checkable.

Design constraints:
  - Purely diagnostic: never triggers refinement, never changes pipeline behaviour.
    (If it could, calibration would be confounded -- we could not tell "it predicts
    errors well" apart from "it changed the errors".)
  - Pure function of a saved run record (algorithm/structure/matching/scheme/review),
    so it can be run OFFLINE over the archived real-model runs in outputs/ without
    re-running the pipeline.
  - Every failure hypothesis must cite a kb_id from the closed vocabulary
    KB_ENTRY_IDS; citations outside it are flagged by post-hoc validation.

CLI:
  python -m quantummind.self_critique --record outputs/result_X.json   # one record
  python -m quantummind.self_critique --batch                          # all archived runs
  python -m quantummind.self_critique --injection                      # known-error case (Set A)

Batch mode reads outputs/ records READ-ONLY and writes critiques to a separate
directory (outputs/self_critique/, or outputs/self_critique_mock/ on the mock
backend so placeholder output never mixes with real results). Completed critiques
are cached on disk, so an interrupted batch resumes where it stopped.
"""

from __future__ import annotations
import argparse
import glob
import json
import os
import sys
import time

from .knowledge_base import knowledge_base_as_text, KB_ENTRY_IDS
from .llm_client import LLMClient
from .paths import REAL_OUT_DIR, outputs_root

RETRY_BACKOFFS = (30, 90)  # match consistency_check.py

FRAGILITY_LEVELS = ("fragile", "moderate", "robust")


SELF_CRITIQUE_SYSTEM = f"""You are the SELF-CRITIQUE AUDITOR, the final diagnostic step of a
quantum-algorithm analysis pipeline. The pipeline has committed to a final verdict on the
algorithm below. Your job is NOT to re-judge whether it is right, and NOT to defend it.

PREMORTEM FRAMING: Assume a domain expert has just proven this verdict WRONG. Your task is
to reconstruct the most plausible way that happened. Every judgement the pipeline made
rests on the knowledge base below; an error, if it exists, lives in a specific misapplied
prerequisite or barrier. Find the weakest links.

{knowledge_base_as_text()}

RULES -- every failure hypothesis MUST:
1. Cite exactly one kb_id: either a specific prerequisite of a specific primitive (e.g.
   "hhl.readout") or a specific barrier (e.g. "output_dense"), exactly as written in the
   knowledge base above.
2. State a problem-specific doubt: a checkable claim about THIS algorithm which, if it
   turned out true, would flip the verdict. It must engage with concrete content of the
   structural report or scheme, not raise a generic concern.
3. State the flipped verdict: what the recommendation would become if the doubt holds.

BANNED as hypotheses (these make your output worthless):
- Generic hedges that apply to every problem equally: hardware maturity, noise,
  decoherence, "QRAM is an open problem" (unless input loading is specifically unresolved
  for THIS problem's input format), "LLMs can be inconsistent".
- Restating a caveat the scheme already lists, without adding a new doubt.
- A doubt with no identifiable flip.

DIRECTION DISCIPLINE:
- If the verdict claims a speedup, your top hypothesis is how it could be a phantom: which
  prerequisite was assumed rather than established, or which barrier was quietly ignored.
- If the verdict is "none", your top hypothesis is how a real speedup was missed: which
  cited barrier may not actually apply under its rule, or which primitive's prerequisites
  may in fact all hold.
- Also give at least one hypothesis of the OTHER kind when coherent (e.g. right speedup
  claim but wrong primitive, or wrong magnitude).

FRAGILITY RUBRIC (operational, not vibes):
- "fragile": your top hypothesis targets a prerequisite/barrier whose status the pipeline
  ASSUMED -- you cannot quote a structural-report item that settles it.
- "moderate": your top hypothesis targets a genuinely contested condition (evidence cuts
  both ways, e.g. query-model vs realistic-cost-model speedups).
- "robust": every hypothesis you can construct requires contradicting a fact the
  structural report explicitly established.

Produce 2-3 hypotheses, ranked by plausibility (rank 1 = most plausible). For each,
"evidence_status" says how the pipeline left the cited condition: "assumed" (asserted
without support), "contested" (evidence cuts both ways), or "established" (settled by an
explicit structural-report item). "expert_check" is the single most efficient thing a
human expert could examine to test the doubt.

Output JSON with exactly these keys:
{{"failure_hypotheses": [
   {{"rank": int,
     "kb_id": str,
     "doubt": str,
     "evidence_status": "assumed|contested|established",
     "flip_to": str,
     "expert_check": str}}],
  "weakest_agent_claim": {{"agent": "1|2|3", "claim": str}},
  "fragility": "fragile|moderate|robust",
  "reasoning": str}}"""


def self_critique_user(record: dict) -> str:
    return (f"Algorithm: {record['algorithm']}\n\n"
            f"STRUCTURAL REPORT (Agent 1):\n{json.dumps(record['structure'], indent=2)}\n\n"
            f"MATCHER VERDICT (Agent 2):\n{json.dumps(record['matching'], indent=2)}\n\n"
            f"SCHEME (Agent 3):\n{json.dumps(record['scheme'], indent=2)}\n\n"
            f"INDEPENDENT REVIEW (Agent 4):\n{json.dumps(record['review'], indent=2)}")


def validate_critique(critique: dict) -> list[str]:
    """Post-hoc contract checks. Returns a list of violations (empty = clean)."""
    problems = []
    hyps = critique.get("failure_hypotheses")
    if not isinstance(hyps, list) or not hyps:
        return ["no failure_hypotheses produced"]
    for h in hyps:
        kb_id = h.get("kb_id", "")
        if kb_id not in KB_ENTRY_IDS:
            problems.append(f"kb_id not in knowledge base: {kb_id!r}")
        if not h.get("flip_to"):
            problems.append(f"hypothesis rank {h.get('rank')} has no flip_to")
    if critique.get("fragility") not in FRAGILITY_LEVELS:
        problems.append(f"invalid fragility: {critique.get('fragility')!r}")
    return problems


def run_self_critique(record: dict, client: LLMClient) -> dict:
    """Critique one saved pipeline record. Returns the critique + validation metadata."""
    critique = client.complete_json(SELF_CRITIQUE_SYSTEM, self_critique_user(record))
    critique["_contract_violations"] = validate_critique(critique)
    critique["_algorithm"] = record["algorithm"]
    critique["_pipeline_recommendation"] = record.get("matching", {}).get("recommendation")
    critique["_pipeline_confidence"] = record.get("matching", {}).get("overall_confidence")
    return critique


def _critique_with_cache(record: dict, client: LLMClient, out_path: str) -> dict:
    """Disk-cached, retrying critique of one record (same pattern as consistency_check)."""
    if os.path.exists(out_path):
        with open(out_path) as f:
            return json.load(f)
    for attempt in range(len(RETRY_BACKOFFS) + 1):
        try:
            critique = run_self_critique(record, client)
            break
        except Exception as e:  # noqa: BLE001 -- API/network errors vary by backend
            if attempt < len(RETRY_BACKOFFS):
                delay = RETRY_BACKOFFS[attempt]
                print(f"    API error: {e} -- retry {attempt + 1}/{len(RETRY_BACKOFFS)} in {delay}s")
                time.sleep(delay)
            else:
                raise
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(critique, f, indent=2)
    return critique


def _find_batch_records() -> list[str]:
    """All archived REAL-model records under outputs/ (read-only inputs).

    Records whose "backend" is mock are skipped: mock output is canned placeholder
    text, and critiquing it would pollute the calibration data. (This also guards
    against mock artifacts that ever leaked into the real outputs/ tree.)
    """
    patterns = [
        os.path.join(REAL_OUT_DIR, "result_*.json"),
        os.path.join(REAL_OUT_DIR, "consistency_*", "run_*.json"),
        os.path.join(REAL_OUT_DIR, "archive_pre_b4", "consistency_*", "run_*.json"),
    ]
    paths = sorted(p for pat in patterns for p in glob.glob(pat))
    real = []
    for p in paths:
        with open(p) as f:
            if json.load(f).get("backend") != "mock":
                real.append(p)
    skipped = len(paths) - len(real)
    if skipped:
        print(f"(skipping {skipped} mock-backend record(s))")
    return real


def _out_path_for(record_path: str, critique_dir: str) -> str:
    rel = os.path.relpath(record_path, REAL_OUT_DIR)
    return os.path.join(critique_dir, rel.replace(os.sep, "__"))


def _critique_dir(client: LLMClient) -> str:
    # outputs/self_critique/ for real backends, outputs/mock/self_critique/ for mock.
    return os.path.join(outputs_root(client.backend), "self_critique")


def _summarize(critiques: list[dict]) -> None:
    print(f"\n{'algorithm':<45} {'pipeline':<22} {'fragility':<10} top kb_id")
    print("-" * 110)
    for c in critiques:
        hyps = c.get("failure_hypotheses") or [{}]
        top = min(hyps, key=lambda h: h.get("rank", 99))
        flags = " !CONTRACT" if c.get("_contract_violations") else ""
        print(f"{c.get('_algorithm', '?')[:44]:<45} "
              f"{str(c.get('_pipeline_recommendation'))[:21]:<22} "
              f"{str(c.get('fragility')):<10} {top.get('kb_id', '?')}{flags}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Self-critique a saved pipeline record.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--record", help="path to one saved run/result JSON")
    mode.add_argument("--batch", action="store_true",
                      help="critique every archived record under outputs/")
    mode.add_argument("--injection", action="store_true",
                      help="critique the known-error graph-connectivity artifacts (Set A)")
    ap.add_argument("--limit", type=int, default=0,
                    help="batch: stop after N records (0 = no limit)")
    args = ap.parse_args()

    client = LLMClient()
    print(f"Backend: {client.backend} / model: {client.model}")
    if client.backend == "mock":
        print("WARNING: mock backend -- critiques are canned placeholders, plumbing only.\n")
    critique_dir = _critique_dir(client)

    if args.record:
        with open(args.record) as f:
            record = json.load(f)
        critique = run_self_critique(record, client)
        print(json.dumps(critique, indent=2))
        return 0

    if args.injection:
        # Set A: the documented wrongly-conservative "none" on graph connectivity,
        # reusing the reconstruction from the Agent-4 injection test. The critique
        # should locate the real fault: quantum_walk dismissed via a misapplied /
        # generic barrier despite O(1) output.
        from .review_injection_test import (GRAPH_CONN_STRUCTURE,
                                            GRAPH_CONN_WRONG_MATCHING,
                                            GRAPH_CONN_WRONG_SCHEME)
        record = {
            "algorithm": "Graph connectivity: are two vertices connected? [INJECTED WRONG NONE]",
            "structure": GRAPH_CONN_STRUCTURE,
            "matching": GRAPH_CONN_WRONG_MATCHING,
            "scheme": GRAPH_CONN_WRONG_SCHEME,
            "review": {"verdict": "sound", "issues": [],
                       "reasoning": "(historical rubber-stamp reconstructed for injection)",
                       "confidence": "high"},
        }
        critique = _critique_with_cache(record, client,
                                        os.path.join(critique_dir, "injection__graph_conn_wrong_none.json"))
        print(json.dumps(critique, indent=2))
        top = min(critique.get("failure_hypotheses") or [{}], key=lambda h: h.get("rank", 99))
        hit = top.get("kb_id", "").startswith("quantum_walk") or top.get("kb_id") == "strong_adaptivity"
        print(f"\ntop-1 kb_id: {top.get('kb_id')}  fragility: {critique.get('fragility')}")
        print("SET-A CHECK:", "PASS (top hypothesis targets the quantum-walk dismissal)"
              if hit else "FAIL (top hypothesis does not target the real fault)")
        return 0 if hit else 1

    # --batch
    records = _find_batch_records()
    if args.limit:
        records = records[:args.limit]
    print(f"{len(records)} archived records -> {critique_dir}\n")
    critiques = []
    for i, path in enumerate(records, 1):
        with open(path) as f:
            record = json.load(f)
        out_path = _out_path_for(path, critique_dir)
        cached = os.path.exists(out_path)
        critique = _critique_with_cache(record, client, out_path)
        critiques.append(critique)
        tag = "(cached)" if cached else ""
        print(f"[{i}/{len(records)}] {record['algorithm'][:50]:<52} "
              f"-> {critique.get('fragility')} {tag}")
    _summarize(critiques)
    summary_path = os.path.join(critique_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(critiques, f, indent=2)
    print(f"\nSummary written to {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
