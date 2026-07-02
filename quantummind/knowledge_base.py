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
            "The problem must reduce to evaluating a boolean oracle f(x) in {0,1} over a search space.",
            "The oracle must be implementable efficiently as a quantum circuit.",
            "The speedup is only meaningful if there is NO exploitable classical structure "
            "beyond brute-force search (otherwise a structured classical algorithm may already win).",
        ],
    },
    {
        "id": "qft",
        "name": "Quantum Fourier Transform (QFT)",
        "classical_problem_types": ["periodicity", "hidden subgroup", "number theory"],
        "speedup_class": "exponential for period-finding problems",
        "prerequisites": [
            "The problem must have an underlying periodic or group-theoretic structure.",
            "The period must be recoverable from a superposition of evaluations.",
            "It must fit the hidden subgroup problem (HSP) framework.",
        ],
    },
    {
        "id": "quantum_walk",
        "name": "Quantum Walk",
        "classical_problem_types": ["graph traversal", "element distinctness", "collision"],
        "speedup_class": "polynomial to exponential, problem dependent",
        "prerequisites": [
            "The problem must be naturally expressible as traversal on a graph or Markov chain.",
            "The speedup depends on the spectral gap and on hitting/mixing times.",
        ],
    },
    {
        "id": "hhl",
        "name": "HHL (linear systems)",
        "classical_problem_types": ["sparse linear algebra", "PDE solving"],
        "speedup_class": "exponential, but under strict conditions",
        "prerequisites": [
            "The input matrix must be sparse and well-conditioned (low condition number).",
            "The solution must be readable as a quantum state -- you may only extract an "
            "AGGREGATE quantity of x (e.g. <x|M|x>), NOT the full solution vector. "
            "This is the 'readout problem'.",
            "Input loading must be efficient (the 'input problem'): preparing |b> must not "
            "itself cost O(N), or the speedup is lost.",
            "Both input and output must be in quantum form.",
        ],
    },
    {
        "id": "amplitude_estimation",
        "name": "Amplitude Estimation",
        "classical_problem_types": ["Monte Carlo simulation", "counting"],
        "speedup_class": "quadratic: O(1/eps^2) -> O(1/eps)",
        "prerequisites": [
            "The quantity of interest must be expressible as an amplitude / expectation to estimate.",
            "The estimator circuit must be implementable efficiently.",
        ],
    },
    {
        "id": "vqa_qaoa",
        "name": "Variational Algorithms / QAOA",
        "classical_problem_types": ["combinatorial optimization (NISQ era)"],
        "speedup_class": "heuristic; NO proven asymptotic speedup",
        "prerequisites": [
            "The problem must be encodable as a cost Hamiltonian.",
            "Note: any 'speedup' here is heuristic and unproven -- flag as such, never claim "
            "an asymptotic advantage.",
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
            lines.append(f"    * {pre}")

    lines.append("\n## KNOWN QUANTIZATION BARRIERS (check every candidate against these)")
    for b in BARRIERS:
        lines.append(f"\n### {b['name']}  [id: {b['id']}]")
        lines.append(f"- Rule: {b['rule']}")
        lines.append(f"- Watch for signals: {', '.join(b['signals'])}")
    return "\n".join(lines)


PRIMITIVE_IDS = [p["id"] for p in PRIMITIVES] + ["none"]

if __name__ == "__main__":
    print(knowledge_base_as_text())
