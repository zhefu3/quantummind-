"""
Orchestrator: runs Agent 1 -> Agent 2 -> Agent 3 -> Agent 4 for one classical algorithm,
with iterative refinement (proposal allows agents to query back, up to 3 rounds).

Two independent refinement triggers, sharing the same MAX_ROUNDS budget:
  1. Agent 2 reports overall_confidence "low" with a non-empty gap_analysis -> Agent 1
     re-analyzes the structure with a hint, then Agent 2 re-runs.
  2. Agent 4 (independent reviewer) judges Agent 3's scheme "unsound" -> Agent 2 re-runs
     with the reviewer's critique as a hint (structure from Agent 1 is reused, not
     recomputed), then Agent 3 and Agent 4 re-run.
"""

from . import agents
from .known_results import match_known_results
from .llm_client import LLMClient

MAX_ROUNDS = 3


def analyze_algorithm(algorithm: dict, client: LLMClient, verbose: bool = True,
                      anchoring: bool = False) -> dict:
    rounds = 0
    agent1_hint = ""
    agent2_hint = ""
    structure = None

    # Near-neighbor anchoring (roadmap step 3, opt-in): the candidate's nearest
    # known quantum results, computed once from its structure-level description and
    # fed only to Agent 3 to ground its novelty call. Off by default so the blind
    # pipeline (and comparability with recorded experiments) is preserved.
    anchors = None
    if anchoring:
        anchors = match_known_results(
            f"{algorithm['name']} {algorithm.get('description', '')}")

    while True:
        rounds += 1

        # --- Agent 1: structure (only re-run if a hint was set) ---
        if structure is None or agent1_hint:
            a1_user = agents.agent1_user(algorithm)
            if agent1_hint:
                a1_user += f"\n\nRefinement hint from matcher: {agent1_hint}"
            structure = client.complete_json(agents.AGENT1_SYSTEM, a1_user)
            agent1_hint = ""
            if verbose:
                print(f"  [round {rounds}] Agent 1 -> paradigm: {structure.get('paradigm')}")

        # --- Agent 2: matching ---
        a2_user = agents.agent2_user(algorithm, structure)
        if agent2_hint:
            a2_user += f"\n\nRefinement hint from reviewer: {agent2_hint}"
            agent2_hint = ""
        matching = client.complete_json(agents.AGENT2_SYSTEM, a2_user)
        if verbose:
            print(f"  [round {rounds}] Agent 2 -> recommendation: {matching.get('recommendation')} "
                  f"(confidence: {matching.get('overall_confidence')})")

        needs_structure_rework = (matching.get("overall_confidence") == "low"
                                   and matching.get("gap_analysis") not in (None, "", "none"))
        if needs_structure_rework and rounds < MAX_ROUNDS:
            agent1_hint = f"Previous gap analysis: {matching.get('gap_analysis')}. Re-examine structural features."
            continue

        # --- Agent 3: scheme ---
        scheme = client.complete_json(agents.AGENT3_SYSTEM,
                                      agents.agent3_user(algorithm, structure, matching, anchors))
        if verbose:
            print(f"  [round {rounds}] Agent 3 -> speedup: {scheme.get('speedup_estimate')}")

        # --- Agent 4: independent review of the scheme ---
        review = client.complete_json(agents.AGENT4_SYSTEM,
                                      agents.agent4_user(algorithm, structure, matching, scheme))
        if verbose:
            extra = f" issues: {review.get('issues')}" if review.get("verdict") != "sound" else ""
            print(f"  [round {rounds}] Agent 4 -> verdict: {review.get('verdict')}{extra}")

        if review.get("verdict") != "sound" and rounds < MAX_ROUNDS:
            agent2_hint = f"Reviewer rejected previous scheme: {review.get('issues')}. {review.get('reasoning')}"
            continue

        break

    result = {
        "algorithm": algorithm["name"],
        "rounds_used": rounds,
        "structure": structure,
        "matching": matching,
        "scheme": scheme,
        "review": review,
        "backend": client.backend,
        "model": client.model,
    }
    if anchoring:
        result["anchors_used"] = [a["id"] for a in (anchors or [])]
    return result
