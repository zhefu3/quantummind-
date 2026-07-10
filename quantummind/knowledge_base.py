"""
Quantum speedup knowledge base.

Encodes Sections 3.1-3.3 of the QuantumMind proposal:
  - 3.1  The taxonomy of quantum primitives and the speedup class each provides.
  - 3.2  The structural prerequisites each primitive demands of a classical problem.
  - 3.3  Known quantization barriers (situations where speedup is unlikely / proven absent).

This file is the single source of truth that Agent 2 (the pattern matcher) reasons
against. It is injected into Agent 2's prompt so its judgements are grounded in an
explicit, auditable rule set rather than the model's free-floating recall.
"""

# ---------------------------------------------------------------------------
# 3.1 + 3.2  Quantum primitives: speedup class + structural prerequisites
# ---------------------------------------------------------------------------

PRIMITIVES = [
    {
        "id": "grover",
        "name": "Grover / Amplitude Amplification",
        "classical_problem_types": ["unstructured search", "constraint satisfaction"],
        "speedup_class": "quadratic: O(N) -> O(sqrt(N))",
        "prerequisites": [
            {"id": "grover.oracle_reduction",
             "text": "The problem must reduce to evaluating a boolean oracle f(x) in {0,1} over a search space."},
            {"id": "grover.efficient_oracle",
             "text": "The oracle must be implementable efficiently as a quantum circuit."},
            {"id": "grover.no_classical_structure",
             "text": "The speedup is only meaningful if there is NO exploitable classical structure "
                     "beyond brute-force search (otherwise a structured classical algorithm may already win)."},
        ],
    },
    {
        "id": "qft",
        "name": "Quantum Fourier Transform (QFT)",
        "classical_problem_types": ["periodicity", "hidden subgroup", "number theory"],
        "speedup_class": "exponential for period-finding problems",
        "prerequisites": [
            {"id": "qft.periodic_structure",
             "text": "The problem must have an underlying periodic or group-theoretic structure."},
            {"id": "qft.superposition_recovery",
             "text": "The period must be recoverable from a superposition of evaluations."},
            {"id": "qft.hsp_framework",
             "text": "It must fit the hidden subgroup problem (HSP) framework."},
        ],
    },
    {
        "id": "quantum_walk",
        "name": "Quantum Walk",
        "classical_problem_types": ["graph traversal", "element distinctness", "collision"],
        "speedup_class": "polynomial to exponential, problem dependent",
        "prerequisites": [
            {"id": "quantum_walk.graph_representation",
             "text": "The problem must be naturally expressible as traversal on a graph or Markov chain."},
            {"id": "quantum_walk.spectral_conditions",
             "text": "The speedup depends on the spectral gap and on hitting/mixing times."},
        ],
    },
    {
        "id": "hhl",
        "name": "HHL (linear systems)",
        "classical_problem_types": ["sparse linear algebra", "PDE solving"],
        "speedup_class": "exponential, but under strict conditions",
        "prerequisites": [
            {"id": "hhl.sparse_well_conditioned",
             "text": "The input matrix must be sparse and well-conditioned (low condition number)."},
            {"id": "hhl.readout",
             "text": "The solution must be readable as a quantum state -- you may only extract an "
                     "AGGREGATE quantity of x (e.g. <x|M|x>), NOT the full solution vector. "
                     "This is the 'readout problem'."},
            {"id": "hhl.input_loading",
             "text": "Input loading must be efficient (the 'input problem'): preparing |b> must not "
                     "itself cost O(N), or the speedup is lost."},
            {"id": "hhl.quantum_io",
             "text": "Both input and output must be in quantum form."},
        ],
    },
    {
        "id": "amplitude_estimation",
        "name": "Amplitude Estimation",
        "classical_problem_types": ["Monte Carlo simulation", "counting"],
        "speedup_class": "quadratic: O(1/eps^2) -> O(1/eps)",
        "prerequisites": [
            {"id": "amplitude_estimation.amplitude_form",
             "text": "The quantity of interest must be expressible as an amplitude / expectation to estimate."},
            {"id": "amplitude_estimation.efficient_estimator",
             "text": "The estimator circuit must be implementable efficiently."},
        ],
    },
    {
        "id": "vqa_qaoa",
        "name": "Variational Algorithms / QAOA",
        "classical_problem_types": ["combinatorial optimization (NISQ era)"],
        "speedup_class": "heuristic; NO proven asymptotic speedup",
        "prerequisites": [
            {"id": "vqa_qaoa.hamiltonian_encoding",
             "text": "The problem must be encodable as a cost Hamiltonian."},
            {"id": "vqa_qaoa.heuristic_only",
             "text": "Note: any 'speedup' here is heuristic and unproven -- flag as such, never claim "
                     "an asymptotic advantage."},
        ],
    },
    {
        "id": "quantum_backtracking",
        "name": "Quantum Backtracking / Tree Search",
        "classical_problem_types": ["backtracking search", "constraint satisfaction",
                                    "branch-and-bound", "DP with an unstructured inner search"],
        "speedup_class": "up to quadratic in the size of the explored search tree",
        "prerequisites": [
            {"id": "quantum_backtracking.tree_structure",
             "text": "The computation must be expressible as exploring a search tree whose nodes "
                     "are checked by an efficient predicate (a partial-assignment validity test or "
                     "an inner 'does any choice work?' scan), e.g. CSP backtracking, branch-and-bound, "
                     "or the inner loop of a polynomial DP recurrence."},
            {"id": "quantum_backtracking.speedup_scope",
             "text": "The speedup is at most QUADRATIC and applies to the TREE SEARCH / inner "
                     "loop only. Any sequential outer structure (DP layer order, round count of a "
                     "local search) is NOT accelerated -- the net gain is bounded by the share of "
                     "runtime spent in the searchable part. Never claim a speedup for the whole "
                     "algorithm when only a sub-step qualifies."},
            {"id": "quantum_backtracking.oracle_access",
             "text": "Node evaluation must be implementable as an efficient quantum oracle, and "
                     "reaching the accelerated regime typically assumes QRAM-style access to the "
                     "instance (state-loading cost must not itself erase the gain)."},
        ],
    },
    {
        "id": "qsvt",
        "name": "Quantum Singular Value Transformation / block-encoding",
        "classical_problem_types": ["sparse/structured linear algebra", "singular-value "
                                    "estimation", "matrix functions", "Hamiltonian simulation"],
        "speedup_class": "polynomial-to-exponential, under the same strict I/O conditions as HHL",
        "prerequisites": [
            {"id": "qsvt.block_encoding",
             "text": "The operator must admit an efficient block-encoding (sparse + efficiently "
                     "computable entries, or otherwise structured). This generalizes HHL, amplitude "
                     "amplification, and Hamiltonian simulation into one framework."},
            {"id": "qsvt.aggregate_readout",
             "text": "You may only extract an AGGREGATE of the result (an expectation, a singular "
                     "value, an overlap) -- NOT the full transformed vector. Same readout wall as "
                     "HHL: if the required output is the whole vector/matrix, the speedup is erased."},
            {"id": "qsvt.efficient_polynomial",
             "text": "The target matrix function must be approximable by a low-degree polynomial of "
                     "the singular values (well-conditioned / bounded-degree); otherwise the circuit "
                     "depth blows up and the advantage is lost."},
        ],
    },
    {
        "id": "quantum_mean_estimation",
        "name": "Quantum Mean / Moment Estimation",
        "classical_problem_types": ["mean estimation of a random variable", "subgraph/edge counting",
                                    "frequency moments", "high-variance Monte Carlo"],
        "speedup_class": "up to quadratic over classical sampling in the accuracy/variance ratio",
        "prerequisites": [
            {"id": "quantum_mean_estimation.bounded_estimator",
             "text": "The target must be the mean/expectation of a random variable produced by an "
                     "efficient quantum sampler (a coherent implementation of the sampling process). "
                     "Stronger than plain amplitude estimation: it handles relative-error mean "
                     "estimation given a variance bound (the 'quantum Chebyshev' regime)."},
            {"id": "quantum_mean_estimation.scalar_output",
             "text": "The required output must be a small aggregate (a scalar mean or a few moments). "
                     "If per-item outputs are required the readout bottleneck applies as usual."},
        ],
    },
]

# ---------------------------------------------------------------------------
# 3.3  Known quantization barriers (no-go / unlikely conditions)
# ---------------------------------------------------------------------------

BARRIERS = [
    {
        "id": "sorting_lower_bound",
        "name": "Comparison-sorting lower bound",
        "rule": "Comparison-based sorting has a proven quantum lower bound of Omega(N log N), "
                "identical to the classical optimum. It cannot be meaningfully quantized.",
        "signals": ["comparison sort", "sorting by comparisons", "ordering elements"],
    },
    {
        "id": "output_dense",
        "name": "Output-dense problems",
        "rule": "If the algorithm must produce O(N) distinct output values, the quantum readout "
                "bottleneck destroys any speedup (you would need O(N) measurements to extract them).",
        "signals": ["returns the full array", "outputs all elements", "produces N results",
                    "needs the entire solution vector"],
    },
    {
        "id": "strong_adaptivity",
        "name": "Highly adaptive / sequential dependence",
        "rule": "If every step depends on the result of the previous step (strong data "
                "dependency), it is hard to parallelize via superposition. Heuristic barrier, "
                "not a theorem -- some adaptive algorithms can be restructured.",
        "signals": ["each step depends on previous", "sequential dependency", "inherently iterative"],
    },
    {
        "id": "bqp_hardness",
        "name": "DLOG / BQP-hardness boundary",
        "rule": "Some problems are believed hard even for quantum computers. Knowing the "
                "complexity-class landscape (P, BPP, BQP, NP) is required background; do not "
                "claim a speedup for problems outside BQP's reach.",
        "signals": ["NP-hard", "no known efficient quantum algorithm", "believed hard for quantum"],
    },
]


def knowledge_base_as_text() -> str:
    """Render the knowledge base as a compact text block for prompt injection."""
    lines = ["## QUANTUM PRIMITIVES (taxonomy + structural prerequisites)"]
    for p in PRIMITIVES:
        lines.append(f"\n### {p['name']}  [id: {p['id']}]")
        lines.append(f"- Classical problem types: {', '.join(p['classical_problem_types'])}")
        lines.append(f"- Speedup class: {p['speedup_class']}")
        lines.append("- Prerequisites (ALL must hold for a 'high' match):")
        for pre in p["prerequisites"]:
            lines.append(f"    * [{pre['id']}] {pre['text']}")

    lines.append("\n## KNOWN QUANTIZATION BARRIERS (check every candidate against these)")
    for b in BARRIERS:
        lines.append(f"\n### {b['name']}  [id: {b['id']}]")
        lines.append(f"- Rule: {b['rule']}")
        lines.append(f"- Watch for signals: {', '.join(b['signals'])}")
    return "\n".join(lines)


PRIMITIVE_IDS = [p["id"] for p in PRIMITIVES] + ["none"]

# Every citable knowledge-base entry: each prerequisite of each primitive
# ("<primitive>.<condition>") plus each barrier id. This is the closed vocabulary
# the self-critique auditor must draw its kb_id citations from.
KB_ENTRY_IDS = ([pre["id"] for p in PRIMITIVES for pre in p["prerequisites"]]
                + [b["id"] for b in BARRIERS])

if __name__ == "__main__":
    print(knowledge_base_as_text())
