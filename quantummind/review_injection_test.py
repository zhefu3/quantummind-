"""
Injection test for Agent 4's over-conservatism (false-negative) clause.

Feeds pre-built Agent 1-3 artifacts directly to Agent 4 -- two API calls
total, no pipeline runs -- to check the symmetric review clause triggers
where it should and stays quiet where it shouldn't:

  Case A (expected: unsound) -- Graph connectivity with a wrongly
    conservative "none": quantum_walk scored partial, its known query-model
    speedup acknowledged and then dismissed via generic loading/adaptivity
    hedges, despite an O(1) output. The real pipeline produced exactly this
    failure twice (the original single-shot eval and once in the K=2 batch).
    The original artifacts were lost to an outputs/ cleanup accident, so the
    matching/scheme here are a reconstruction of the documented failure
    pattern; the structural report is the real Agent-1 output copied
    verbatim from a saved run of the same question.

  Case B (expected: sound) -- Single-source shortest path to one target
    with a correctly conservative "none": the real, unmodified artifact from
    outputs/consistency_Single_source_shortest_path_to_one_targe/run_1.json,
    where strong_adaptivity is applied WITH a concrete complexity argument
    (Durr-Hoyer substitution gives O(V*sqrt(V)), worse than classical on
    sparse graphs). The clause must NOT flag this one -- if it does, the
    wording is over-triggering and needs another pass.

Run with a real backend (ANTHROPIC_API_KEY set). On the mock backend the
verdicts come from keyword tables and prove nothing beyond plumbing.
"""

from __future__ import annotations
import json
import os
import sys

from . import agents
from .algorithms import ALGORITHMS
from .llm_client import LLMClient

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")

SSSP_ARTIFACT = os.path.join(
    OUT_DIR, "consistency_Single_source_shortest_path_to_one_targe", "run_1.json")

# Real Agent-1 structural report for "Graph connectivity: are two vertices
# connected?", copied verbatim from a saved run (the 8-run batch, run_1).
# Note it already contains the tension that makes this question a trap: O(1)
# output in structural_features, sequential-dependency language in
# barrier_flags.
GRAPH_CONN_STRUCTURE = {
    "paradigm": "graph traversal",
    "classical_complexity": "O(V + E)",
    "bottleneck": "breadth-first or depth-first traversal of vertices and edges reachable from s",
    "structural_features": [
        "binary output (single boolean yes/no)",
        "output size is O(1)",
        "solution is oracle-checkable: a witness path can be verified in O(V) time",
        "graph may be sparse (E << V^2)",
        "subgraph reachability has repeated substructure exploitable via BFS/DFS layering",
        "adjacency structure defines a search space of size O(V + E)",
        "problem reduces to set membership: is t in the connected component of s?",
    ],
    "barrier_flags": [
        "sequential data dependency: each traversal step depends on which vertices were "
        "previously visited (frontier expansion is inherently sequential)",
        "adaptive branching: next nodes to explore depend on current discovered set",
        "output is O(1) so no output-size advantage from parallelism",
    ],
}

# SYNTHETIC reconstruction of the documented wrong-"none" verdict: the known
# quantum-walk speedup is acknowledged, then waved away with generic hedges
# (loading cost, "realistic settings", adaptivity) rather than an argument
# specific to this problem. The new clause should flag exactly this.
GRAPH_CONN_WRONG_MATCHING = {
    "scores": [
        {
            "primitive": "quantum_walk",
            "verdict": "partial",
            "justification": "Graph connectivity is a canonical graph-traversal problem and "
                "quantum walk algorithms achieve O(sqrt(VE)) query complexity for "
                "st-connectivity, a known polynomial improvement over classical O(V+E) in "
                "the query model. However, in any realistic circuit/time model the adjacency "
                "structure must first be loaded into a quantum-accessible form, which costs "
                "O(V+E) and erases the advantage; furthermore the frontier expansion of the "
                "underlying traversal is inherently sequential (each step depends on the "
                "previously visited set), which limits coherent superposition over traversal "
                "states. Given hardware maturity and these loading considerations, the "
                "speedup is unlikely to be realized in practice.",
        },
        {
            "primitive": "grover",
            "verdict": "low",
            "justification": "Reachability is not an unstructured search; BFS/DFS exploit the "
                "adjacency structure and outperform naive oracle search over paths.",
        },
        {
            "primitive": "hhl",
            "verdict": "inapplicable",
            "justification": "No linear system to solve; reachability is combinatorial.",
        },
        {
            "primitive": "qft",
            "verdict": "inapplicable",
            "justification": "No periodic or group-theoretic structure.",
        },
    ],
    "barrier_hits": [
        "strong_adaptivity: frontier expansion depends on the previously visited set, "
        "making the traversal inherently sequential",
    ],
    "gap_analysis": "none",
    "recommendation": "none",
    "overall_confidence": "high",
    "note": "Quantum walk matches the surface structure but the sequential nature of "
            "traversal and input-loading costs mean no practical speedup is expected.",
}

GRAPH_CONN_WRONG_SCHEME = {
    "scheme": "No viable quantization.",
    "speedup_estimate": "none",
    "io_accounting": "Input: the graph (V vertices, E edges) must be made quantum-accessible, "
        "an O(V+E) preprocessing cost in any realistic setting. Output: a single boolean, "
        "which poses no readout bottleneck, but the favorable output size cannot compensate "
        "for the loading cost and the sequential dependency of traversal.",
    "prerequisites": [],
    "obstacles": ["sequential frontier expansion", "input loading cost",
                   "hardware maturity for coherent walks"],
    "novelty": "N/A -- no scheme proposed",
    "confidence": "high",
}


def _review(client: LLMClient, algo: dict, structure: dict,
            matching: dict, scheme: dict) -> dict:
    return client.complete_json(
        agents.AGENT4_SYSTEM,
        agents.agent4_user(algo, structure, matching, scheme))


def main() -> int:
    client = LLMClient()
    print(f"Backend: {client.backend} / model: {client.model} / "
          f"temperature: {client.temperature}")
    if client.backend == "mock":
        print("WARNING: mock backend -- verdicts come from keyword tables and prove "
              "nothing beyond plumbing. Set ANTHROPIC_API_KEY for the real test.\n")

    failures = 0

    # --- Case A: wrongly conservative "none" -> expect unsound -------------
    algo_a = next(a for a in ALGORITHMS
                  if a["name"] == "Graph connectivity: are two vertices connected?")
    review_a = _review(client, algo_a, GRAPH_CONN_STRUCTURE,
                       GRAPH_CONN_WRONG_MATCHING, GRAPH_CONN_WRONG_SCHEME)
    verdict_a = review_a.get("verdict")
    print("=== Case A: graph connectivity, wrongly conservative none ===")
    print(f"verdict: {verdict_a}  (expected: unsound)")
    print(f"issues: {json.dumps(review_a.get('issues'), indent=2)}")
    print(f"reasoning: {review_a.get('reasoning')}\n")
    if verdict_a != "unsound":
        failures += 1
        print(">>> CASE A FAILED: the over-conservatism clause did not trigger.\n")

    # --- Case B: correctly conservative "none" -> expect sound -------------
    if not os.path.exists(SSSP_ARTIFACT):
        print(f"Case B SKIPPED: {SSSP_ARTIFACT} not found "
              f"(need the saved exploration run).")
    else:
        with open(SSSP_ARTIFACT) as f:
            run = json.load(f)
        algo_b = next(a for a in ALGORITHMS
                      if a["name"] == "Single-source shortest path to one target")
        review_b = _review(client, algo_b, run["structure"],
                           run["matching"], run["scheme"])
        verdict_b = review_b.get("verdict")
        print("=== Case B: single-target SSSP, correctly conservative none ===")
        print(f"verdict: {verdict_b}  (expected: sound)")
        print(f"issues: {json.dumps(review_b.get('issues'), indent=2)}")
        print(f"reasoning: {review_b.get('reasoning')}\n")
        if verdict_b != "sound":
            failures += 1
            print(">>> CASE B FAILED: the clause over-triggers on a justified none.\n")

    print("RESULT:", "PASS" if failures == 0 else f"{failures} case(s) FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
