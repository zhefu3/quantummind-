"""
Test set of classical algorithms.

Each entry carries a known_label = the accepted quantum-acceleration status, used by the
Layer-1 evaluator (proposal 5.1). The set deliberately mixes:
  - clear positives (search -> Grover, factoring -> Shor/QFT)
  - clear negatives / no-go (comparison sort)
  - a HARD NEGATIVE: a linear system where the FULL solution is required. It superficially
    matches HHL but the readout problem voids the speedup -- this is the canonical trap that
    separates pattern-matching from real reasoning.
"""

ALGORITHMS = [
    {
        "name": "Linear search in an unsorted list",
        "description": "Given an unsorted list of N items and a predicate, find an item "
                       "satisfying the predicate by checking items one by one.",
        "pseudocode": "for x in list: if predicate(x): return x",
        "known_label": {"primitive": "grover", "speedup": "quadratic",
                        "note": "textbook Grover positive"},
    },
    {
        "name": "Integer factorization (trial division)",
        "description": "Given a composite integer M, find a non-trivial factor. The hidden "
                       "structure is the period of a modular exponentiation function.",
        "pseudocode": "for d in 2..sqrt(M): if M % d == 0: return d",
        "known_label": {"primitive": "qft", "speedup": "exponential",
                        "note": "Shor positive via period finding"},
    },
    {
        "name": "Comparison-based sorting (merge sort)",
        "description": "Sort N elements into total order using pairwise comparisons; output "
                       "the full sorted array of all N elements.",
        "pseudocode": "merge_sort(A): split, recurse, merge",
        "known_label": {"primitive": "none", "speedup": "none",
                        "note": "proven Omega(N log N) quantum lower bound"},
    },
    {
        "name": "Solve a sparse linear system, return the full solution vector",
        "description": "Given a sparse well-conditioned matrix A and vector b, solve Ax=b and "
                       "RETURN THE ENTIRE solution vector x (all N components).",
        "pseudocode": "x = solve(A, b); return x  # all N entries needed",
        "known_label": {"primitive": "none", "speedup": "none",
                        "note": "HARD NEGATIVE: looks like HHL but full readout voids speedup"},
    },
    {
        "name": "All-pairs shortest paths, return the full distance matrix",
        "description": "Given a weighted graph with V vertices, compute the shortest "
                       "path distance between EVERY pair of vertices and return the "
                       "complete V x V distance matrix.",
        "pseudocode": "for each pair (u,v): d[u][v] = shortest_path(u, v); return full matrix",
        "known_label": {"primitive": "none", "speedup": "none",
                        "note": "HARD NEGATIVE: graph problem suggests quantum walk, but "
                                "outputting the full O(V^2) distance matrix is output-dense "
                                "-- readout voids any speedup"},
    },
    {
        "name": "Monte Carlo expectation estimation",
        "description": "Estimate the expectation of a random variable to precision eps by "
                       "averaging many samples.",
        "pseudocode": "avg = mean(sample() for _ in range(1/eps^2))",
        "known_label": {"primitive": "amplitude_estimation", "speedup": "quadratic",
                        "note": "amplitude estimation positive"},
    },

    # ---------- clear positives (fill out primitive coverage) ----------
    {
        "name": "Find the minimum in an unsorted list",
        "description": "Given an unsorted list of N numbers, find the minimum element "
                       "by examining candidates.",
        "pseudocode": "m = inf; for x in list: if x < m: m = x; return m",
        "known_label": {"primitive": "grover", "speedup": "quadratic",
                        "note": "Grover-based minimum finding (Durr-Hoyer): O(sqrt(N))"},
    },
    {
        "name": "Element distinctness",
        "description": "Given N elements, decide whether any two of them are equal.",
        "pseudocode": "check all pairs / hash; report if any duplicate exists",
        "known_label": {"primitive": "quantum_walk", "speedup": "polynomial",
                        "note": "quantum walk positive: O(N^{2/3}) vs classical O(N)"},
    },
    {
        "name": "Counting solutions to an unstructured predicate",
        "description": "Count how many of N items satisfy a boolean predicate, to a "
                       "target relative precision.",
        "pseudocode": "count = sum(1 for x in items if predicate(x))",
        "known_label": {"primitive": "amplitude_estimation", "speedup": "quadratic",
                        "note": "quantum counting / amplitude estimation positive"},
    },
    {
        "name": "Discrete logarithm problem",
        "description": "Given a generator g, a modulus, and a value y = g^x, recover the "
                       "exponent x. Has hidden periodic / group structure.",
        "pseudocode": "find x such that g^x = y (mod p)",
        "known_label": {"primitive": "qft", "speedup": "exponential",
                        "note": "hidden-subgroup / QFT positive (like Shor)"},
    },
    {
        "name": "Graph connectivity: are two vertices connected?",
        "description": "Given a graph and two vertices s and t, decide whether there is a "
                       "path from s to t. The output is a single yes/no answer.",
        "pseudocode": "return reachable(s, t)  # single boolean",
        "known_label": {"primitive": "quantum_walk", "speedup": "polynomial",
                        "note": "quantum walk positive -- CONTRAST with the all-pairs "
                                "shortest-path hard negative: same graph domain, but here "
                                "the output is a single bit, so no readout bottleneck"},
    },
    {
        "name": "Hamiltonian simulation of a quantum system",
        "description": "Simulate the time evolution of a quantum system given its "
                       "Hamiltonian, to compute an observable at time t.",
        "pseudocode": "evolve state under exp(-iHt); measure observable",
        "known_label": {"primitive": "none", "speedup": "exponential",
                        "note": "natively quantum problem -- exponential advantage but does "
                                "not map to the listed classical->quantum primitives; expect "
                                "system to flag it as a native-quantum case"},
    },

    # ---------- hard negatives (traps) ----------
    {
        "name": "Search a SORTED list for a target",
        "description": "Given an ALREADY-SORTED list of N items, find a target value.",
        "pseudocode": "binary_search(sorted_list, target)  # classical O(log N)",
        "known_label": {"primitive": "none", "speedup": "none",
                        "note": "HARD NEGATIVE: looks like search->Grover, but the list is "
                                "sorted so classical binary search is O(log N), already "
                                "faster than Grover's O(sqrt(N)). Exploitable classical "
                                "structure exists -- Grover not meaningful"},
    },
    {
        "name": "Return ALL elements satisfying a predicate",
        "description": "Given N items and a predicate, return every item that satisfies "
                       "it (there may be up to O(N) such items).",
        "pseudocode": "return [x for x in items if predicate(x)]",
        "known_label": {"primitive": "none", "speedup": "none",
                        "note": "HARD NEGATIVE: looks like Grover search, but must output "
                                "up to O(N) results -> output-dense, readout voids speedup"},
    },
    {
        "name": "Solve a sparse linear system, return only <x|M|x>",
        "description": "Given a sparse well-conditioned matrix A and vector b, solve Ax=b "
                       "and return ONLY a single scalar aggregate of x (an expectation "
                       "value <x|M|x>), NOT the full vector.",
        "pseudocode": "x = solve(A, b); return dot(x, M @ x)  # single scalar",
        "known_label": {"primitive": "hhl", "speedup": "exponential",
                        "note": "REVERSE of the linear-system hard negative: only an "
                                "aggregate of x is needed, so HHL's readout prerequisite IS "
                                "satisfied -> exponential speedup genuinely applies. Tests "
                                "whether the system distinguishes 'full vector' from "
                                "'aggregate' -- differs by one condition from the trap"},
    },
    {
        "name": "Strongly sequential iterative recurrence",
        "description": "Compute a sequence where each term depends on the full result of "
                       "the previous term via a non-invertible update, for N steps.",
        "pseudocode": "s = s0; for i in range(N): s = f(s); return s",
        "known_label": {"primitive": "none", "speedup": "none",
                        "note": "HARD NEGATIVE: strong sequential data dependency blocks "
                                "superposition-based parallelism"},
    },

    # ---------- to explore (no fixed ground truth -- watch reasoning quality) ----------
    {
        "name": "0/1 Knapsack via dynamic programming",
        "description": "Given N items with weights and values and a capacity, find the "
                       "maximum total value subset. Solved classically by DP.",
        "pseudocode": "dp[i][w] = max(dp[i-1][w], dp[i-1][w-wt]+val)",
        "known_label": {"primitive": "unknown", "speedup": "unknown",
                        "note": "TO EXPLORE: no fixed ground truth; evaluate the quality of "
                                "the system's reasoning, not correctness"},
    },
    {
        "name": "Exact string / pattern matching",
        "description": "Find all occurrences of a pattern P of length m in a text T of "
                       "length n.",
        "pseudocode": "for i in range(n-m): if T[i:i+m] == P: record i",
        "known_label": {"primitive": "unknown", "speedup": "unknown",
                        "note": "TO EXPLORE: no fixed ground truth; watch reasoning"},
    },
    {
        "name": "Low-rank recommendation from a preference matrix",
        "description": "Given a large sparse user-item preference matrix, recommend items "
                       "to a user based on low-rank structure.",
        "pseudocode": "approximate low-rank factorization; sample recommendations",
        "known_label": {"primitive": "unknown", "speedup": "unknown",
                        "note": "TO EXPLORE: historically a famous dequantization case; "
                                "watch how the system reasons about I/O access model"},
    },
    {
        "name": "Max-Cut combinatorial optimization",
        "description": "Partition the vertices of a weighted graph into two sets to "
                       "maximize the total weight of edges crossing the partition.",
        "pseudocode": "maximize sum of weights of cut edges over all bipartitions",
        "known_label": {"primitive": "unknown", "speedup": "unknown",
                        "note": "TO EXPLORE: expect QAOA to be mentioned; check whether the "
                                "system honestly notes QAOA has NO proven asymptotic speedup"},
    },
]
