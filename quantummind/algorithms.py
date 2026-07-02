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
        "name": "Monte Carlo expectation estimation",
        "description": "Estimate the expectation of a random variable to precision eps by "
                       "averaging many samples.",
        "pseudocode": "avg = mean(sample() for _ in range(1/eps^2))",
        "known_label": {"primitive": "amplitude_estimation", "speedup": "quadratic",
                        "note": "amplitude estimation positive"},
    },
]
