"""
Known quantum-algorithm results: the novelty filter's reference library.

With expert verification available, the most expensive failure mode is no longer a
wrong candidate (an expert can kill one quickly) but a REDISCOVERY presented as a
finding -- it burns expert time and credibility. This file encodes the well-known
results a candidate scheme must be checked against before it reaches an expert.
Rediscoveries are not discarded: they are free calibration evidence ("the system
independently reproduced N known results"); they just don't spend expert attention.

Statuses:
  proven       -- established speedup (often in the QUERY model; see model_caveat)
  conditional  -- speedup holds only under strict conditions (state prep, readout, ...)
  heuristic    -- no proven asymptotic advantage (NISQ / variational / annealing)
  dequantized  -- a classical algorithm removed the claimed exponential advantage
  no_speedup   -- proven lower bound or no known meaningful quantum advantage

The keyword matcher is deliberately dumb (token overlap): it is a RECALL device to
surface which entries an expert or LLM judge should compare a scheme against, not a
novelty verdict by itself.
"""

from __future__ import annotations

KNOWN_RESULTS = [
    # --- Search / amplitude techniques -------------------------------------
    {
        "id": "grover_search",
        "problem": "Unstructured search over N items",
        "primitive": "grover",
        "speedup": "O(N) -> O(sqrt(N)), optimal (BBBV lower bound)",
        "status": "proven",
        "model_caveat": "oracle/query model; oracle circuit must be efficient",
        "reference": "Grover 1996; Bennett-Bernstein-Brassard-Vazirani 1997",
        "keywords": ["unstructured search", "unsorted", "brute force", "oracle search",
                     "database search", "satisfying assignment"],
    },
    {
        "id": "durr_hoyer_minimum",
        "problem": "Finding the minimum/maximum of an unsorted list",
        "primitive": "grover",
        "speedup": "O(N) -> O(sqrt(N))",
        "status": "proven",
        "model_caveat": "query model",
        "reference": "Durr-Hoyer 1996",
        "keywords": ["minimum", "maximum", "min-finding", "extremum", "argmin", "argmax"],
    },
    {
        "id": "quantum_counting",
        "problem": "Counting solutions to a predicate / estimating their fraction",
        "primitive": "amplitude_estimation",
        "speedup": "quadratic in precision and in N",
        "status": "proven",
        "model_caveat": "query model",
        "reference": "Brassard-Hoyer-Tapp 1998",
        "keywords": ["counting", "count solutions", "estimate fraction", "cardinality"],
    },
    {
        "id": "montanaro_monte_carlo",
        "problem": "Monte Carlo estimation of an expectation to precision eps",
        "primitive": "amplitude_estimation",
        "speedup": "O(1/eps^2) -> O(1/eps)",
        "status": "proven",
        "model_caveat": "needs a coherent (quantum-circuit) implementation of the sampler",
        "reference": "Montanaro 2015 (quantum speedup of Monte Carlo methods)",
        "keywords": ["monte carlo", "expectation", "sampling estimate", "variance",
                     "rollout", "simulation estimate", "stochastic estimate"],
    },
    {
        "id": "montanaro_backtracking",
        "problem": "Backtracking / tree search with predicate pruning",
        "primitive": "quantum_walk",
        "speedup": "quadratic in the size of the explored tree",
        "status": "proven",
        "model_caveat": "tree explored via oracle predicates; hybrid outer loops stay classical",
        "reference": "Montanaro 2018 (quantum walk backtracking)",
        "keywords": ["backtracking", "tree search", "branch and bound", "csp",
                     "constraint satisfaction", "dfs pruning"],
    },
    {
        "id": "bht_collision",
        "problem": "Collision finding in a 2-to-1 function",
        "primitive": "quantum_walk",
        "speedup": "O(N^(1/2)) -> O(N^(1/3))",
        "status": "proven",
        "model_caveat": "query model",
        "reference": "Brassard-Hoyer-Tapp 1997",
        "keywords": ["collision", "two-to-one", "hash collision", "birthday"],
    },
    {
        "id": "ambainis_element_distinctness",
        "problem": "Element distinctness (are all N elements distinct?)",
        "primitive": "quantum_walk",
        "speedup": "O(N) -> O(N^(2/3)), optimal",
        "status": "proven",
        "model_caveat": "query model",
        "reference": "Ambainis 2004",
        "keywords": ["element distinctness", "duplicate", "distinct elements", "repeated element"],
    },
    {
        "id": "triangle_finding",
        "problem": "Triangle finding in a graph",
        "primitive": "quantum_walk",
        "speedup": "query complexity O(n^1.25) vs classical O(n^2) (adjacency-matrix queries)",
        "status": "proven",
        "model_caveat": "query model",
        "reference": "Magniez-Santha-Szegedy 2005; Le Gall 2014",
        "keywords": ["triangle", "subgraph finding", "clique detection"],
    },
    {
        "id": "matrix_product_verification",
        "problem": "Verify a matrix product AB = C",
        "primitive": "quantum_walk",
        "speedup": "O(n^2) classical (Freivalds, randomized) vs O(n^(5/3)) quantum queries",
        "status": "proven",
        "model_caveat": "query model; note Freivalds already gives fast classical verification",
        "reference": "Buhrman-Spalek 2006",
        "keywords": ["matrix product verification", "verify multiplication", "freivalds"],
    },
    {
        "id": "nand_tree",
        "problem": "Evaluating AND-OR / NAND formula trees (game trees)",
        "primitive": "quantum_walk",
        "speedup": "O(N) -> O(sqrt(N)) for formula evaluation",
        "status": "proven",
        "model_caveat": "query model",
        "reference": "Farhi-Goldstone-Gutmann 2007; ACRSZ 2010",
        "keywords": ["game tree", "and-or tree", "nand tree", "formula evaluation", "minimax"],
    },

    # --- Algebraic / number-theoretic ---------------------------------------
    {
        "id": "shor_factoring",
        "problem": "Integer factorization",
        "primitive": "qft",
        "speedup": "superpolynomial (vs best known classical)",
        "status": "proven",
        "model_caveat": "needs fault-tolerant scale for cryptographic sizes",
        "reference": "Shor 1994",
        "keywords": ["factoring", "factorization", "rsa", "semiprime"],
    },
    {
        "id": "shor_dlog",
        "problem": "Discrete logarithm",
        "primitive": "qft",
        "speedup": "superpolynomial",
        "status": "proven",
        "model_caveat": "",
        "reference": "Shor 1994",
        "keywords": ["discrete logarithm", "discrete log", "diffie-hellman", "elliptic curve"],
    },
    {
        "id": "abelian_hsp",
        "problem": "Hidden subgroup problem over abelian groups (incl. Simon, period finding)",
        "primitive": "qft",
        "speedup": "exponential",
        "status": "proven",
        "model_caveat": "non-abelian HSP (e.g. graph isomorphism route) remains open",
        "reference": "Simon 1994; Kitaev 1995",
        "keywords": ["hidden subgroup", "period finding", "periodicity", "simon", "hidden shift"],
    },
    {
        "id": "pell_hallgren",
        "problem": "Pell's equation / unit group of number fields",
        "primitive": "qft",
        "speedup": "exponential",
        "status": "proven",
        "model_caveat": "",
        "reference": "Hallgren 2002",
        "keywords": ["pell", "unit group", "class group", "number field"],
    },

    # --- Graph algorithms ----------------------------------------------------
    {
        "id": "graph_connectivity_walk",
        "problem": "st-connectivity / graph connectivity",
        "primitive": "quantum_walk",
        "speedup": "st-connectivity O(sqrt(VE)) queries; connectivity Theta(V^(3/2)) (matrix model)",
        "status": "proven",
        "model_caveat": "QUERY model; in realistic cost models input access can absorb the gain "
                        "-- this is the pipeline's known borderline case",
        "reference": "Durr-Heiligman-Hoyer-Mhalla 2004; Belovs-Reichardt 2012",
        "keywords": ["connectivity", "st-connectivity", "reachability", "connected component"],
    },
    {
        "id": "dhhm_graph_problems",
        "problem": "Minimum spanning tree, strong connectivity, single-source shortest paths",
        "primitive": "quantum_walk",
        "speedup": "e.g. MST O(sqrt(VE)) queries; SSSP O(sqrt(VE) polylog) queries",
        "status": "proven",
        "model_caveat": "QUERY model (adjacency access); classical algorithms are near-linear, "
                        "so realistic-model gains are modest",
        "reference": "Durr-Heiligman-Hoyer-Mhalla 2004",
        "keywords": ["minimum spanning tree", "mst", "shortest path", "sssp", "dijkstra",
                     "strong connectivity"],
    },
    {
        "id": "hamoudi_magniez_counting",
        "problem": "Approximate edge / triangle counting in the general graph query model",
        "primitive": "amplitude_estimation",
        "speedup": "quadratically fewer queries than the classical sublinear estimators "
                   "(quantum mean estimation via 'quantum Chebyshev inequality')",
        "status": "proven",
        "model_caveat": "general graph query model (degree/neighbor/edge queries)",
        "reference": "Hamoudi-Magniez, ICALP 2019 (arXiv:1807.06456)",
        "keywords": ["triangle counting", "counting triangles", "edge counting",
                     "subgraph counting", "mean estimation", "frequency moments"],
    },
    {
        "id": "quantum_max_flow_matching",
        "problem": "Maximum matching / network flow",
        "primitive": "quantum_walk",
        "speedup": "polynomial query improvements (e.g. matching O(V*sqrt(E)))",
        "status": "proven",
        "model_caveat": "query model; polynomial factors only",
        "reference": "Ambainis-Spalek 2006; Apers-Lee 2021",
        "keywords": ["matching", "max flow", "network flow", "bipartite", "min cut"],
    },

    # --- Linear algebra / ML -------------------------------------------------
    {
        "id": "hhl",
        "problem": "Solving sparse linear systems (as a quantum state)",
        "primitive": "hhl",
        "speedup": "exponential IF sparse + well-conditioned + efficient state prep + "
                   "only an aggregate of x is read out",
        "status": "conditional",
        "model_caveat": "readout of the full vector, or O(N) state prep, erases the speedup",
        "reference": "Harrow-Hassidim-Lloyd 2009; Aaronson 2015 (fine print)",
        "keywords": ["linear system", "ax=b", "matrix inversion", "solve equations"],
    },
    {
        "id": "hamiltonian_simulation",
        "problem": "Simulating quantum systems / Hamiltonian dynamics",
        "primitive": "hhl",
        "speedup": "exponential (the original Feynman use case; BQP-complete)",
        "status": "proven",
        "model_caveat": "",
        "reference": "Lloyd 1996; Berry et al 2015",
        "keywords": ["hamiltonian simulation", "quantum dynamics", "molecular simulation",
                     "quantum chemistry"],
    },
    {
        "id": "tang_recommendation",
        "problem": "Low-rank recommendation systems",
        "primitive": "hhl",
        "speedup": "claimed exponential (Kerenidis-Prakash) -- REMOVED by classical sampling",
        "status": "dequantized",
        "model_caveat": "Tang's classical algorithm matches it up to polynomial factors "
                        "under the same sampling-access assumptions",
        "reference": "Kerenidis-Prakash 2016; Tang 2019",
        "keywords": ["recommendation", "preference matrix", "low-rank", "collaborative filtering"],
    },
    {
        "id": "dequantized_qml",
        "problem": "Quantum PCA, low-rank regression/clustering, low-rank HHL variants",
        "primitive": "hhl",
        "speedup": "claimed exponential -- removed for the LOW-RANK regime",
        "status": "dequantized",
        "model_caveat": "sparse full-rank regime survives (with HHL's usual conditions)",
        "reference": "Chia-Gilyen-Li-Lin-Tang-Wang 2020",
        "keywords": ["pca", "principal component", "low-rank regression", "clustering",
                     "quantum machine learning", "qml"],
    },
    {
        "id": "qsvt_framework",
        "problem": "Singular-value estimation / matrix functions via QSVT + block-encoding",
        "primitive": "qsvt",
        "speedup": "generalizes HHL / amplitude amplification / Hamiltonian simulation; "
                   "same conditional (aggregate-readout, well-conditioned) advantage",
        "status": "conditional",
        "model_caveat": "block-encoding + aggregate readout required; full-vector output "
                        "or ill-conditioning erases the gain (same wall as HHL)",
        "reference": "Gilyen-Su-Low-Wiebe 2019 (quantum singular value transformation)",
        "keywords": ["singular value", "condition number", "matrix function", "block encoding",
                     "qsvt", "spectral", "eigenvalue estimation"],
    },
    {
        "id": "jordan_gradient",
        "problem": "Estimating a gradient of f: R^d -> R",
        "primitive": "qft",
        "speedup": "O(d) function evaluations -> O(1)",
        "status": "proven",
        "model_caveat": "needs coherent oracle access to f; precision caveats",
        "reference": "Jordan 2005; Gilyen-Arunachalam-Wiebe 2019",
        "keywords": ["gradient", "derivative estimation", "finite differences"],
    },
    {
        "id": "quantum_sdp",
        "problem": "Semidefinite programming",
        "primitive": "amplitude_estimation",
        "speedup": "polynomial in dimension, but with heavy dependence on width/precision",
        "status": "conditional",
        "model_caveat": "advantage regime is narrow; input access assumptions matter",
        "reference": "Brandao-Svore 2017; van Apeldoorn-Gilyen 2019",
        "keywords": ["semidefinite", "sdp", "convex optimization"],
    },
    {
        "id": "quantum_dp_exponential",
        "problem": "Exact algorithms for NP-hard problems via DP over subsets (TSP, set cover)",
        "primitive": "grover",
        "speedup": "e.g. TSP O*(2^n) -> O*(1.728^n): polynomial speedup of an exponential algorithm",
        "status": "proven",
        "model_caveat": "still exponential; requires QRAM-like access to DP tables",
        "reference": "Ambainis et al 2019",
        "keywords": ["traveling salesman", "tsp", "set cover", "dynamic programming subsets",
                     "held-karp", "exact exponential"],
    },

    {
        "id": "quantum_perceptron",
        "problem": "Perceptron training (finding a misclassified sample per update)",
        "primitive": "grover",
        "speedup": "O(N) -> O(sqrt(N)) per mistake-search via Grover over samples",
        "status": "proven",
        "model_caveat": "query model; also a version improving the mistake bound itself",
        "reference": "Wiebe-Kapoor-Svore 2016",
        "keywords": ["perceptron", "misclassified sample", "linear separator", "mistake bound"],
    },
    {
        "id": "quantum_nearest_neighbor",
        "problem": "Nearest-neighbor search / classification",
        "primitive": "grover",
        "speedup": "quadratic in the number of points (Durr-Hoyer minimum over distances)",
        "status": "proven",
        "model_caveat": "query model; distance oracle must be efficient; QRAM caveats "
                        "for loading the point set",
        "reference": "Wiebe-Kapoor-Svore 2015",
        "keywords": ["nearest neighbor", "1-nn", "knn", "closest point", "distance minimization"],
    },

    {
        "id": "quantum_local_search",
        "problem": "Local search / heuristic inner loops (find an improving move, e.g. 2-opt)",
        "primitive": "grover",
        "speedup": "quadratic per round via Durr-Hoyer over the move neighborhood; "
                   "round count unchanged",
        "status": "proven",
        "model_caveat": "per-round only; total speedup bounded by the (data-dependent) "
                        "number of rounds; QRAM access to the instance",
        "reference": "Durr-Hoyer 1996; Montanaro 2020 (heuristics speedups survey/applications)",
        "keywords": ["local search", "improving move", "2-opt", "hill climbing",
                     "neighborhood search", "best swap"],
    },
    {
        "id": "quantum_dp_inner_loop",
        "problem": "Polynomial DP recurrences with an unstructured inner search "
                   "(e.g. split-point scans in CYK / matrix-chain style DPs)",
        "primitive": "grover",
        "speedup": "sub-cubic: Grover over the inner O(n) candidates gives ~sqrt "
                   "factor on the inner loop (e.g. O(n^3) -> O(n^2.5))",
        "status": "proven",
        "model_caveat": "outer DP layers stay sequential; needs QRAM access to the DP "
                        "table; related to quantum Boolean matrix multiplication via the "
                        "parsing-BMM equivalence",
        "reference": "Ambainis et al. 2019 (DP speedups); Le Gall (quantum BMM)",
        "keywords": ["dynamic programming", "split point", "parsing", "cyk",
                     "recurrence inner loop", "dp table"],
    },

    # --- Strings -------------------------------------------------------------
    {
        "id": "quantum_string_matching",
        "problem": "Exact string/pattern matching",
        "primitive": "grover",
        "speedup": "O(n) -> O~(sqrt(n) + sqrt(m)) queries",
        "status": "proven",
        "model_caveat": "query model; classical is already linear and practical",
        "reference": "Ramesh-Vinay 2000",
        "keywords": ["string matching", "pattern matching", "substring", "text search"],
    },
    {
        "id": "edit_distance_open",
        "problem": "Edit distance / sequence alignment",
        "primitive": "none",
        "speedup": "no known quantum speedup beating classical O(n^2) meaningfully",
        "status": "no_speedup",
        "model_caveat": "open problem; strong sequential DP dependency",
        "reference": "Boroujeni et al 2018 (limited approximation results)",
        "keywords": ["edit distance", "levenshtein", "sequence alignment", "dp table"],
    },

    # --- No-go / hype-control ------------------------------------------------
    {
        "id": "sorting_no_go",
        "problem": "Comparison-based sorting",
        "primitive": "none",
        "speedup": "none: Omega(N log N) quantum lower bound, same as classical",
        "status": "no_speedup",
        "model_caveat": "",
        "reference": "Hoyer-Neerbek-Shi 2001",
        "keywords": ["sorting", "merge sort", "comparison sort", "ordering"],
    },
    {
        "id": "ordered_search_no_go",
        "problem": "Searching a sorted list",
        "primitive": "none",
        "speedup": "constant factor only (~0.45 log N vs log N); no asymptotic gain",
        "status": "no_speedup",
        "model_caveat": "",
        "reference": "Ambainis 1999; Hoyer-Neerbek-Shi 2001",
        "keywords": ["sorted list", "binary search", "ordered search"],
    },
    {
        "id": "parity_no_go",
        "problem": "Computing parity / majority of N bits",
        "primitive": "none",
        "speedup": "none: parity needs N/2 quantum queries",
        "status": "no_speedup",
        "model_caveat": "",
        "reference": "Beals et al 1998",
        "keywords": ["parity", "xor of bits", "majority vote"],
    },
    {
        "id": "vqa_heuristics",
        "problem": "Combinatorial optimization via QAOA / VQE / annealing",
        "primitive": "vqa_qaoa",
        "speedup": "heuristic only; no proven asymptotic advantage over classical heuristics",
        "status": "heuristic",
        "model_caveat": "classical heuristics (SA, SDP rounding) are strong baselines",
        "reference": "Farhi et al 2014; extensive benchmarking literature",
        "keywords": ["qaoa", "variational", "annealing", "max-cut", "ising", "combinatorial optimization"],
    },
]


def _tokens(text: str) -> set[str]:
    return set("".join(c if c.isalnum() else " " for c in text.lower()).split())


def match_known_results(text: str, top_n: int = 3) -> list[dict]:
    """Rank known results by keyword overlap with `text` (an algorithm name +
    description and/or a proposed scheme). Recall device, not a verdict: the hits
    tell a reviewer WHICH known results to compare against."""
    toks = _tokens(text)
    scored = []
    for entry in KNOWN_RESULTS:
        score = 0
        for kw in entry["keywords"]:
            kw_toks = _tokens(kw)
            if kw_toks and kw_toks <= toks:
                score += len(kw_toks)
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda pair: -pair[0])
    return [{"id": e["id"], "problem": e["problem"], "status": e["status"],
             "speedup": e["speedup"], "reference": e["reference"],
             "match_score": s} for s, e in scored[:top_n]]


if __name__ == "__main__":
    import json as _json
    import sys as _sys
    query = " ".join(_sys.argv[1:]) or "find the minimum spanning tree of a sparse graph"
    print(_json.dumps(match_known_results(query), indent=2))
