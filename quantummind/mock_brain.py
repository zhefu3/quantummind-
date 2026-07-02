"""
Deterministic mock "brain".

This is NOT a model and does NOT reason. It inspects the agent role (from the system
prompt) and a few keyword signals (from the algorithm description) and returns
schema-valid placeholder JSON. Its only job is to prove the pipeline plumbing and let
you preview the report format without an API key.

Every mock output carries "_mock": true. Replace with a real backend
(QM_BACKEND=anthropic) to get genuine reasoning.
"""

import json


def _role(system: str) -> str:
    s = system.upper()
    if "STRUCTURE ANALYST" in s:
        return "agent1"
    if "PATTERN MATCHER" in s:
        return "agent2"
    if "SCHEME GENERATOR" in s:
        return "agent3"
    if "INDEPENDENT REVIEWER" in s:
        return "agent4"
    return "unknown"


def _signal(user: str) -> str:
    u = user.lower()
    if "sorting" in u or "merge sort" in u or "comparison-based sort" in u:
        return "sorting"
    if "linear system" in u or "ax=b" in u or "ax = b" in u or "solution vector" in u:
        return "linear_system"
    if ("shortest path" in u or "distance matrix" in u or "all-pairs" in u
            or "graph" in u):
        return "graph_dense"
    if "monte carlo" in u or "expectation" in u or ("estimate" in u and "precision" in u):
        return "montecarlo"
    if "unsorted" in u or "unstructured search" in u or "linear search" in u:
        return "search"
    if "period" in u or "factor" in u or "discrete log" in u or "hidden subgroup" in u:
        return "periodic"
    return "generic"


class MockBrain:
    def complete(self, system: str, user: str) -> str:
        role = _role(system)
        sig = _signal(user)
        if role == "agent1":
            return json.dumps(self._agent1(sig))
        if role == "agent2":
            return json.dumps(self._agent2(sig))
        if role == "agent3":
            return json.dumps(self._agent3(sig))
        if role == "agent4":
            return json.dumps(self._agent4(sig))
        return json.dumps({"_mock": True, "note": "unrecognized agent role"})

    # --- Agent 1: structural analysis -------------------------------------
    def _agent1(self, sig):
        base = {"_mock": True}
        table = {
            "search": dict(paradigm="unstructured search", classical_complexity="O(N)",
                           bottleneck="linear scan over N candidates",
                           structural_features=["solution is efficiently checkable",
                                                "no exploitable ordering/index structure"],
                           barrier_flags=[]),
            "sorting": dict(paradigm="comparison-based sorting", classical_complexity="O(N log N)",
                            bottleneck="pairwise comparisons to establish total order",
                            structural_features=["total ordering required", "outputs all N elements"],
                            barrier_flags=["output_dense", "sorting_lower_bound"]),
            "linear_system": dict(paradigm="linear algebra", classical_complexity="O(N) to O(N^3)",
                                  bottleneck="solving Ax=b",
                                  structural_features=["matrix may be sparse",
                                                       "FULL solution vector x is required as output"],
                                  barrier_flags=["output_dense"]),
            "periodic": dict(paradigm="number-theoretic", classical_complexity="super-polynomial",
                             bottleneck="finding hidden period",
                             structural_features=["underlying periodic structure", "hidden subgroup"],
                             barrier_flags=[]),
            "graph_dense": dict(paradigm="graph traversal", classical_complexity="O(V^3) (Floyd-Warshall)",
                                bottleneck="computing shortest paths for every vertex pair",
                                structural_features=["graph structure amenable to quantum walk",
                                                     "FULL V x V distance matrix is required as output"],
                                barrier_flags=["output_dense"]),
            "montecarlo": dict(paradigm="randomized estimation", classical_complexity="O(1/eps^2)",
                               bottleneck="averaging many samples to reach precision eps",
                               structural_features=["quantity expressible as an expectation/amplitude",
                                                    "output is a single scalar estimate"],
                               barrier_flags=[]),
            "generic": dict(paradigm="unclassified", classical_complexity="unknown",
                            bottleneck="unknown", structural_features=[], barrier_flags=[]),
        }
        base.update(table.get(sig, table["generic"]))
        return base

    # --- Agent 2: primitive matching --------------------------------------
    def _agent2(self, sig):
        def score(pid, verdict, why):
            return {"primitive": pid, "verdict": verdict, "justification": why}
        table = {
            "search": dict(
                scores=[score("grover", "high",
                              "Reduces to a checkable boolean oracle; no classical structure to exploit.")],
                barrier_hits=[], gap_analysis="none",
                recommendation="grover", overall_confidence="medium"),
            "sorting": dict(
                scores=[score("grover", "inapplicable", "No oracle search structure.")],
                barrier_hits=["sorting_lower_bound", "output_dense"],
                gap_analysis="none",
                recommendation="none",
                overall_confidence="high",
                note="Proven Omega(N log N) quantum lower bound -- no meaningful speedup."),
            "linear_system": dict(
                scores=[score("hhl", "partial",
                              "Matches HHL on sparsity, BUT the full solution vector is required as "
                              "output -> readout problem voids the exponential speedup.")],
                barrier_hits=["output_dense"],
                gap_analysis="none",
                recommendation="none",
                overall_confidence="medium",
                note="Classic false-positive trap: looks like HHL, but readout kills it."),
            "periodic": dict(
                scores=[score("qft", "high", "Hidden periodic structure fits the HSP/QFT framework.")],
                barrier_hits=[], gap_analysis="none",
                recommendation="qft", overall_confidence="medium"),
            "graph_dense": dict(
                scores=[score("quantum_walk", "partial",
                              "Matches quantum walk on graph-traversal structure, BUT the full "
                              "V x V distance matrix is required as output -> readout problem "
                              "voids the speedup.")],
                barrier_hits=["output_dense"],
                gap_analysis="none",
                recommendation="none",
                overall_confidence="medium",
                note="Same trap as HHL/linear_system: quantum walk looks applicable, but "
                     "output-dense readout kills it."),
            "montecarlo": dict(
                scores=[{"primitive":"amplitude_estimation","verdict":"high",
                         "justification":"Expectation estimation maps to amplitude estimation."}],
                barrier_hits=[], gap_analysis="none",
                recommendation="amplitude_estimation", overall_confidence="medium", note=""),
            "generic": dict(scores=[], barrier_hits=[], gap_analysis="insufficient information",
                            recommendation="none", overall_confidence="low"),
        }
        out = {"_mock": True}
        out.update(table.get(sig, table["generic"]))
        return out

    # --- Agent 3: scheme generation ---------------------------------------
    def _agent3(self, sig):
        table = {
            "search": dict(
                scheme="Replace the linear scan with Grover amplitude amplification; wrap the "
                       "checker as an oracle U_f.",
                speedup_estimate="O(N) -> O(sqrt(N)) (quadratic)",
                io_accounting="Oracle assumed efficient; output is a single index -> no readout penalty.",
                prerequisites=["efficient oracle circuit"],
                obstacles=["only quadratic; structured classical methods may compete"],
                novelty="rediscovery (this is textbook Grover)",
                confidence="medium"),
            "sorting": dict(
                scheme="No viable quantization.",
                speedup_estimate="none",
                io_accounting="N/A",
                prerequisites=[], obstacles=["proven Omega(N log N) lower bound", "output-dense"],
                novelty="N/A", confidence="high"),
            "linear_system": dict(
                scheme="HHL would prepare |x> exponentially faster, but extracting the full x "
                       "requires O(N) measurements.",
                speedup_estimate="none once honest readout is accounted for",
                io_accounting="Readout of full vector = O(N) measurements -> exponential gain erased. "
                              "State preparation of |b> also at risk.",
                prerequisites=["only an AGGREGATE of x is needed (not satisfied here)"],
                obstacles=["readout problem", "input loading"],
                novelty="N/A -- speedup is illusory under honest accounting",
                confidence="high"),
            "periodic": dict(
                scheme="Reduce to period finding and apply QFT (Shor-style).",
                speedup_estimate="exponential (super-polynomial vs best classical)",
                io_accounting="Period read from measurement; modest output.",
                prerequisites=["period recoverable from superposition"],
                obstacles=["requires fault-tolerant scale for large instances"],
                novelty="rediscovery (Shor)", confidence="medium"),
            "graph_dense": dict(
                scheme="Quantum walk would find individual shortest-path distances faster, but "
                       "extracting the full V x V matrix requires reading out every pair.",
                speedup_estimate="none once honest readout is accounted for",
                io_accounting="Readout of full V x V matrix = O(V^2) measurements -> any per-pair "
                              "quantum walk speedup is erased.",
                prerequisites=["only a SINGLE pair or an aggregate over pairs is needed "
                              "(not satisfied here)"],
                obstacles=["readout problem", "output-dense result"],
                novelty="N/A -- speedup is illusory under honest accounting",
                confidence="high"),
            "montecarlo": dict(
                scheme="Replace classical sampling with amplitude estimation.",
                speedup_estimate="O(1/eps^2) -> O(1/eps) (quadratic)",
                io_accounting="Output is one scalar -> no readout penalty.",
                prerequisites=["quantity expressible as an amplitude"],
                obstacles=["requires coherent oracle for the sampled function"],
                novelty="rediscovery (amplitude estimation)", confidence="medium"),
            "generic": dict(scheme="insufficient information to propose a scheme",
                            speedup_estimate="unknown", io_accounting="N/A",
                            prerequisites=[], obstacles=[], novelty="unknown", confidence="low"),
        }
        out = {"_mock": True}
        out.update(table.get(sig, table["generic"]))
        return out

    # --- Agent 4: independent review ---------------------------------------
    def _agent4(self, sig):
        # Deterministic mock: every signal is rubber-stamped "sound" except the
        # output-dense hard negatives (linear_system, graph_dense), which are always
        # flagged "unsound" so the Agent4 -> Agent2 bounce-back path is exercised by
        # the demo test set. Since the mock has no state/learning, this will keep
        # tripping every round and the pipeline will stop at MAX_ROUNDS -- that's
        # the safety cap working as intended, not a bug.
        table = {
            "linear_system": dict(
                verdict="unsound",
                issues=["prerequisites claims only an aggregate of x is needed, but the "
                        "structural report explicitly says the FULL solution vector is "
                        "required -- that prerequisite is not satisfied, not merely absent"],
                reasoning="io_accounting already admits O(N) readout kills the speedup, yet "
                          "prerequisites is phrased as if satisfying it were still an open "
                          "possibility -- restate as a firm rejection, not a conditional one.",
                confidence="high"),
            "graph_dense": dict(
                verdict="unsound",
                issues=["scheme does not squarely confront the output_dense barrier flagged by "
                        "Agent 1 and the output_dense barrier_hit flagged by Agent 2 -- it "
                        "describes the readout cost but never states outright that the "
                        "quantum-walk speedup is fully erased for this output shape"],
                reasoning="The structural report and matcher verdict both raise output_dense; "
                          "the scheme's io_accounting acknowledges O(V^2) readout but hedges "
                          "with 'any speedup is erased' language instead of treating this as a "
                          "hard no-go the way the analogous linear-system case does.",
                confidence="high"),
        }
        default = dict(verdict="sound", issues=[],
                       reasoning="speedup_estimate is consistent with io_accounting; no "
                                 "barrier_flags or barrier_hits are ignored; prerequisites are "
                                 "supported by the structural report.",
                       confidence="high")
        out = {"_mock": True}
        out.update(table.get(sig, default))
        return out
