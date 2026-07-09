"""
Free structural regression test (mock backend only -- no API cost).

Runs the checks that catch the ways this codebase breaks without spending a cent:
knowledge-base / known-results / pool integrity, agent output schemas, end-to-end
pipeline plumbing, self-critique contract, output isolation, and dossier assembly.
Run this before trusting any real-model run after a change to the knowledge base,
agents, pools, or output paths.

  python -m quantummind.regression_test        # -> PASS / N FAILURE(S), exit code

It is deliberately mock-only: mock verdicts prove nothing about reasoning quality,
but they DO prove every data contract still holds and nothing crashes.
"""

from __future__ import annotations
import os
import sys
import tempfile

from . import agents
from .knowledge_base import PRIMITIVES, BARRIERS, PRIMITIVE_IDS, KB_ENTRY_IDS
from .known_results import KNOWN_RESULTS, match_known_results
from .llm_client import LLMClient
from .orchestrator import analyze_algorithm, MAX_ROUNDS
from .paths import REAL_OUT_DIR, outputs_root
from .pools import POOLS, get_pool
from .self_critique import run_self_critique, validate_critique, FRAGILITY_LEVELS
from . import dossier

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _client() -> LLMClient:
    return LLMClient(backend="mock")


# --- A. knowledge base --------------------------------------------------------
def test_knowledge_base():
    check(len(KB_ENTRY_IDS) == len(set(KB_ENTRY_IDS)), "KB_ENTRY_IDS has duplicates")
    check(PRIMITIVE_IDS[-1] == "none", "PRIMITIVE_IDS must end with 'none'")
    for p in PRIMITIVES:
        check(bool(p.get("id") and p.get("speedup_class")), f"primitive missing id/speedup: {p}")
        for pre in p["prerequisites"]:
            check("id" in pre and "text" in pre,
                  f"prerequisite missing id/text in {p['id']}: {pre}")
            check(pre["id"].startswith(p["id"] + "."),
                  f"prerequisite id {pre['id']} should be namespaced under {p['id']}")
    for b in BARRIERS:
        check(bool(b.get("id") and b.get("rule")), f"barrier missing id/rule: {b}")


# --- B. known results ---------------------------------------------------------
def test_known_results():
    ids = [k["id"] for k in KNOWN_RESULTS]
    check(len(ids) == len(set(ids)), "KNOWN_RESULTS ids have duplicates")
    valid = set(PRIMITIVE_IDS)
    for k in KNOWN_RESULTS:
        for field in ("id", "problem", "primitive", "status", "keywords", "reference"):
            check(field in k, f"known result {k.get('id')} missing '{field}'")
        check(k["primitive"] in valid,
              f"known result {k['id']} names unknown primitive {k['primitive']}")
    hits = match_known_results("solve a sparse linear system, return the full solution vector")
    check(isinstance(hits, list), "match_known_results must return a list")


# --- C. pools -----------------------------------------------------------------
def test_pools():
    for name, pool in POOLS.items():
        seen = set()
        for c in pool:
            for field in ("name", "domain", "description"):
                check(field in c, f"pool {name} candidate missing '{field}': {c.get('name')}")
            check(c["name"] not in seen, f"pool {name} has duplicate name {c['name']!r}")
            seen.add(c["name"])
    try:
        get_pool("nonexistent")
        check(False, "get_pool should raise on an unknown pool")
    except SystemExit:
        pass


# --- D. agent output schemas (mock) -------------------------------------------
def test_agent_schemas():
    c = _client()
    algo = {"name": "Linear search in an unsorted list",
            "description": "scan N items for a target"}
    struct = c.complete_json(agents.AGENT1_SYSTEM, agents.agent1_user(algo))
    for k in ("paradigm", "classical_complexity", "bottleneck", "structural_features", "barrier_flags"):
        check(k in struct, f"Agent 1 output missing '{k}'")
    matching = c.complete_json(agents.AGENT2_SYSTEM, agents.agent2_user(algo, struct))
    for k in ("scores", "barrier_hits", "gap_analysis", "recommendation", "overall_confidence"):
        check(k in matching, f"Agent 2 output missing '{k}'")
    check(matching["recommendation"] in PRIMITIVE_IDS,
          f"Agent 2 recommendation not a valid primitive id: {matching['recommendation']}")
    scheme = c.complete_json(agents.AGENT3_SYSTEM, agents.agent3_user(algo, struct, matching))
    for k in ("scheme", "speedup_estimate", "speedup_scope", "io_accounting",
              "prerequisites", "obstacles", "novelty", "confidence"):
        check(k in scheme, f"Agent 3 output missing '{k}'")
    check(scheme["speedup_scope"] in ("full_algorithm", "sub_step", "conditional", "none"),
          f"Agent 3 speedup_scope invalid: {scheme['speedup_scope']}")
    review = c.complete_json(agents.AGENT4_SYSTEM, agents.agent4_user(algo, struct, matching, scheme))
    for k in ("verdict", "issues", "reasoning", "confidence"):
        check(k in review, f"Agent 4 output missing '{k}'")


# --- E. pipeline end-to-end + refinement bound (mock) -------------------------
def test_pipeline():
    c = _client()
    cases = [
        {"name": "Linear search in an unsorted list", "description": "scan N items"},
        {"name": "CYK membership parsing", "description": "DP with a split point inner search"},
        {"name": "Condition number estimation", "description": "singular value of a sparse matrix"},
    ]
    for algo in cases:
        out = analyze_algorithm(algo, c, verbose=False)
        for k in ("structure", "matching", "scheme", "review", "rounds_used"):
            check(k in out, f"pipeline output missing '{k}' for {algo['name']}")
        check(out["rounds_used"] <= MAX_ROUNDS,
              f"pipeline exceeded MAX_ROUNDS for {algo['name']}")
    # the enriched signals should reach the new primitives with honest scope
    cyk = analyze_algorithm(cases[1], c, verbose=False)
    check(cyk["scheme"]["speedup_scope"] == "sub_step",
          "CYK-like backtracking case should be scoped sub_step")
    # near-neighbor anchoring (opt-in) records which known results it injected
    anch = analyze_algorithm({"name": "Monte Carlo expectation estimation",
                              "description": "estimate an expectation to precision eps"},
                             c, verbose=False, anchoring=True)
    check("anchors_used" in anch and isinstance(anch["anchors_used"], list),
          "anchoring run should record anchors_used")


# --- F. self-critique contract (mock) -----------------------------------------
def test_self_critique():
    c = _client()
    algo = {"name": "Linear search in an unsorted list", "description": "scan N items"}
    out = analyze_algorithm(algo, c, verbose=False)
    record = {"algorithm": algo["name"], **out}
    crit = run_self_critique(record, c)
    check(crit.get("fragility") in FRAGILITY_LEVELS,
          f"self-critique fragility invalid: {crit.get('fragility')}")
    check(crit.get("_contract_violations") == [],
          f"self-critique contract violations on mock: {crit.get('_contract_violations')}")
    # validate_critique should reject a bad kb_id
    bad = {"failure_hypotheses": [{"rank": 1, "kb_id": "not_a_real_id", "flip_to": "x"}],
           "fragility": "fragile"}
    check(validate_critique(bad), "validate_critique should flag an unknown kb_id")


# --- G. output isolation (mock writes only under outputs/mock/) ---------------
def test_output_isolation():
    check(outputs_root("mock").endswith(os.path.join("outputs", "mock")),
          "mock outputs_root must be outputs/mock/")
    check(outputs_root("anthropic") == REAL_OUT_DIR,
          "anthropic outputs_root must be the real outputs/ dir")
    with tempfile.NamedTemporaryFile(dir=REAL_OUT_DIR, delete=False) as tf:
        marker = tf.name
    marker_mtime = os.path.getmtime(marker)
    # exercise a writing entry point on mock
    from .evaluate import evaluate
    evaluate(_client())
    # nothing in the real tree (excluding outputs/mock and the marker) is newer
    newer = []
    for root, _dirs, files in os.walk(REAL_OUT_DIR):
        if os.path.join("outputs", "mock") in root:
            continue
        for fn in files:
            p = os.path.join(root, fn)
            if p != marker and os.path.getmtime(p) > marker_mtime:
                newer.append(os.path.relpath(p, REAL_OUT_DIR))
    os.remove(marker)
    check(not newer, f"mock run wrote outside outputs/mock/: {newer[:5]}")


# --- H. dossier assembly ------------------------------------------------------
def test_dossier():
    entry = {"name": "Test candidate", "domain": "test", "recommendation": "grover",
             "speedup_scope": "full_algorithm", "fragility": "moderate",
             "review_verdict": "sound", "top_doubt_kb_id": "grover.no_classical_structure",
             "expert_check": "check the oracle", "known_results_matches": []}
    resolved = {"record": {"structure": {"paradigm": "search"},
                           "matching": {"recommendation": "grover", "scores": []},
                           "scheme": {"scheme": "Grover", "speedup_estimate": "O(sqrt N)",
                                      "speedup_scope": "full_algorithm"},
                           "review": {"verdict": "sound"}},
                "recommendation": "grover",
                "novelty": match_known_results("unstructured search grover"),
                "rediscovery_risk": True}
    doc = dossier.build_dossier(entry, resolved, None)
    check("Expert dossier" in doc and "What to check first" in doc,
          "dossier body missing expected sections")


ALL = [test_knowledge_base, test_known_results, test_pools, test_agent_schemas,
       test_pipeline, test_self_critique, test_output_isolation, test_dossier]


def main() -> int:
    print("QuantumMind structural regression (mock backend, no API cost)\n")
    for t in ALL:
        before = len(_failures)
        try:
            t()
        except Exception as e:  # noqa: BLE001 -- a crash is itself a regression
            _failures.append(f"{t.__name__} raised {type(e).__name__}: {e}")
        status = "ok" if len(_failures) == before else "FAIL"
        print(f"  [{status:>4}] {t.__name__}")
    print()
    if _failures:
        print(f"{len(_failures)} FAILURE(S):")
        for f in _failures:
            print(f"  - {f}")
        return 1
    print("PASS -- all structural contracts hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
