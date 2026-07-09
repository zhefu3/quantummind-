"""
Gray-zone candidate pool: the discovery funnel's input (Stage 0).

Selection principle: famous textbook algorithms are the LEAST likely to hide an
undiscovered speedup -- the quantum community has swept them. The opportunities, if
any, sit in the "gray zone": algorithms with clear structural features (checkable
predicates, scalar/aggregate outputs, estimation targets, graph/walk structure) that
are NOT headline cases in the quantum-algorithms literature.

Curation rules applied here:
  - Every description states the REQUIRED OUTPUT and its size explicitly (the single
    most decision-relevant fact for readout analysis).
  - No quantum hints in the text: candidates are blind, so the pipeline's verdict is
    its own (deliberate overlaps with known results are caught by known_results.py
    at triage time and become free calibration evidence, not expert-facing claims).
  - Domain-stratified, biased toward domains the quantum literature has covered
    thinly (geometry, strings, streaming, OR, ML subroutines).

This is a first draft for advisor review; entries are cheap to add/remove.
"""

CANDIDATES = [
    # --- Computational geometry ---------------------------------------------
    {"name": "Closest pair of points in the plane",
     "domain": "geometry",
     "description": "Given N points in the plane, find the pair with minimum Euclidean "
                    "distance. Classical divide-and-conquer runs in O(N log N). Output is a "
                    "single pair of indices (O(1) size). The bottleneck is examining "
                    "candidate pairs near the dividing strip."},
    {"name": "Convex hull of a planar point set",
     "domain": "geometry",
     "description": "Compute the convex hull of N planar points (Graham scan, O(N log N), "
                    "dominated by the sort). Output is the h hull vertices in order, where h "
                    "can range from O(1) to O(N)."},
    {"name": "Any-intersection test among N line segments",
     "domain": "geometry",
     "description": "Decide whether ANY two of N line segments intersect (Bentley-Ottmann "
                    "sweep, O(N log N)). Output is a single boolean (O(1)). Each sweep event "
                    "updates an ordered status structure, and events are processed in sorted "
                    "order."},
    {"name": "Smallest enclosing circle",
     "domain": "geometry",
     "description": "Find the minimum-radius circle containing all N points (Welzl's "
                    "randomized incremental algorithm, expected O(N)). Output is a center and "
                    "radius (O(1)). Each insertion may trigger a recomputation over the "
                    "points seen so far."},
    {"name": "Diameter of a point set",
     "domain": "geometry",
     "description": "Find the maximum pairwise distance among N points. Naive is O(N^2) over "
                    "all pairs; planar case reduces to rotating calipers on the hull. Output "
                    "is a single number and one pair of indices (O(1)). The bottleneck is "
                    "the pairwise-distance maximization."},
    {"name": "Orthogonal range counting",
     "domain": "geometry",
     "description": "Preprocess N points in d dimensions so that axis-aligned box queries "
                    "return the COUNT of points inside (k-d tree / range tree). Each query's "
                    "output is one integer (O(1)); classical query time is O(N^(1-1/d)) for "
                    "k-d trees."},

    # --- Strings --------------------------------------------------------------
    {"name": "Longest common substring of two strings",
     "domain": "strings",
     "description": "Given strings of lengths n and m, find the longest contiguous substring "
                    "occurring in both (suffix automaton / generalized suffix tree, O(n+m)). "
                    "Output is one substring position and length (O(1) beyond the substring "
                    "itself). Structure: shared-substructure detection over all O(nm) pairs."},
    {"name": "Approximate string matching with k mismatches",
     "domain": "strings",
     "description": "Find all positions where a pattern of length m matches a text of length "
                    "n with at most k character mismatches. Classical kangaroo-jump methods "
                    "run in O(nk). Output is the set of matching positions (can be O(n) in "
                    "the worst case, often sparse). Each position test is an independent "
                    "predicate: count mismatches <= k."},
    {"name": "Longest repeated substring",
     "domain": "strings",
     "description": "Find the longest substring occurring at least twice in a string of "
                    "length n (suffix array + LCP, O(n)). Output is one position/length pair "
                    "(O(1)). Structure: maximization over LCP values, which requires the "
                    "sorted suffix order."},
    {"name": "Burrows-Wheeler transform",
     "domain": "strings",
     "description": "Compute the BWT of a string of length n: sort all rotations and output "
                    "the last column. O(n) via suffix arrays, but the required output is the "
                    "full transformed string of length n."},
    {"name": "Dictionary matching against many patterns",
     "domain": "strings",
     "description": "Given a fixed set of D patterns (total length M) and a text of length "
                    "n, report which patterns occur (Aho-Corasick automaton, O(n + M + "
                    "occurrences)). Output is the set of occurring pattern ids (at most D "
                    "values). The text is consumed left-to-right through automaton states."},

    # --- Graphs ----------------------------------------------------------------
    {"name": "Graph bipartiteness test",
     "domain": "graphs",
     "description": "Decide whether an undirected graph (V vertices, E edges) is bipartite "
                    "via BFS 2-coloring, O(V+E). Output is a single boolean (O(1)); a "
                    "witness odd cycle can certify 'no'. Traversal explores the graph "
                    "frontier by frontier."},
    {"name": "Directed cycle detection",
     "domain": "graphs",
     "description": "Decide whether a directed graph contains any cycle (DFS with colors, "
                    "O(V+E)). Output is one boolean (O(1)). A witness cycle certifies 'yes' "
                    "and is checkable in O(cycle length)."},
    {"name": "Unweighted graph diameter",
     "domain": "graphs",
     "description": "Compute the maximum eccentricity over all vertices of an unweighted "
                    "graph: classically BFS from every vertex, O(V(V+E)). The required "
                    "output is a single integer (O(1)), but the standard method computes "
                    "all-pairs distances as an intermediate."},
    {"name": "Betweenness centrality of one target vertex",
     "domain": "graphs",
     "description": "Estimate the betweenness centrality of a SINGLE designated vertex: the "
                    "fraction of shortest paths passing through it (Brandes' algorithm does "
                    "all vertices in O(VE); sampling estimators trade accuracy for time). "
                    "Output is one scalar (O(1)). Structure: an average over sampled "
                    "vertex-pair shortest-path computations."},
    {"name": "k-core decomposition",
     "domain": "graphs",
     "description": "Repeatedly peel vertices of degree < k to find the maximal subgraph "
                    "with all degrees >= k, O(V+E) with bucket queues. Output is the core "
                    "number of every vertex (O(V) values). Peeling order is adaptive: each "
                    "removal changes remaining degrees."},
    {"name": "Label-propagation community detection",
     "domain": "graphs",
     "description": "Iteratively relabel each vertex with the majority label of its "
                    "neighbors until stable (near-linear per sweep, few sweeps in practice). "
                    "Output is a label per vertex (O(V) values). Each sweep is parallel over "
                    "vertices, but sweeps are sequential."},
    {"name": "Triangle counting in a sparse graph",
     "domain": "graphs",
     "description": "Count (not just detect) all triangles in a graph with E edges; "
                    "classical is O(E^1.5). The required output is a single integer (O(1)). "
                    "Structure: a sum over edge pairs of an independent membership predicate."},
    {"name": "Random spanning tree sampling",
     "domain": "graphs",
     "description": "Sample a uniformly random spanning tree (Wilson's algorithm via "
                    "loop-erased random walks; expected time related to hitting times). "
                    "Output is V-1 edges (O(V)). The core operation is repeated random "
                    "walks on the graph until cover."},

    # --- Numerical / linear algebra --------------------------------------------
    {"name": "Dominant eigenvalue by power iteration",
     "domain": "numerical",
     "description": "Estimate the largest eigenvalue (and its eigenvector direction quality) "
                    "of a sparse matrix by repeated matrix-vector products; convergence "
                    "depends on the spectral gap. The required output is ONE scalar "
                    "eigenvalue estimate (O(1)); the eigenvector itself is not required."},
    {"name": "Implicit-matrix trace estimation",
     "domain": "numerical",
     "description": "Estimate trace(f(A)) for a large sparse matrix accessed only via "
                    "matrix-vector products (Hutchinson estimator: average of z^T f(A) z "
                    "over random probe vectors; error falls as 1/sqrt(#probes)). Output is "
                    "one scalar (O(1)). Structure: a Monte Carlo average of independent "
                    "quadratic-form evaluations."},
    {"name": "Log-determinant of a sparse SPD matrix",
     "domain": "numerical",
     "description": "Estimate log det(A) for sparse symmetric positive-definite A, e.g. via "
                    "stochastic trace estimation of log(A) with Chebyshev/Lanczos expansions. "
                    "Output is one scalar (O(1)). Bottleneck: many independent "
                    "matrix-vector product chains."},
    {"name": "Adaptive numerical quadrature",
     "domain": "numerical",
     "description": "Approximate a definite integral of a black-box smooth function to "
                    "precision eps; classical Monte Carlo needs O(1/eps^2) samples "
                    "(deterministic rules do better for low dimension). Output is one scalar "
                    "(O(1)). Structure: an average/weighted sum of independent function "
                    "evaluations."},
    {"name": "Condition number estimation",
     "domain": "numerical",
     "description": "Estimate the condition number kappa(A) of a sparse matrix (largest over "
                    "smallest singular value), classically via a few iterations of power "
                    "and inverse-power methods. Output is one scalar (O(1))."},
    {"name": "FFT-based polynomial multiplication",
     "domain": "numerical",
     "description": "Multiply two degree-n polynomials via FFT in O(n log n). The required "
                    "output is ALL 2n+1 coefficients of the product (O(n) values)."},
    {"name": "k-step sparse matrix power action",
     "domain": "numerical",
     "description": "Compute A^k b for sparse A and vector b by k successive sparse "
                    "matrix-vector products. The required output is the full resulting "
                    "vector (O(N) values); the k products are inherently sequential."},

    # --- Dynamic programming / combinatorics -----------------------------------
    {"name": "Longest increasing subsequence",
     "domain": "dp",
     "description": "Find the length of the longest increasing subsequence of N numbers "
                    "(patience sorting, O(N log N)). Output is one integer (O(1)) or "
                    "optionally one witness subsequence. Each element's placement depends on "
                    "the structure built from all previous elements."},
    {"name": "Weighted interval scheduling",
     "domain": "dp",
     "description": "Choose non-overlapping intervals maximizing total weight (sort + 1D DP, "
                    "O(N log N)). The required output is the optimal VALUE (one scalar); the "
                    "DP recurrence consults earlier entries via binary search."},
    {"name": "Counting lattice paths with forbidden cells",
     "domain": "dp",
     "description": "Count monotone lattice paths from corner to corner of an n x n grid "
                    "avoiding a set of forbidden cells (2D DP, O(n^2)). Output is a single "
                    "(large) integer count. Each cell's count is the sum of two neighbors -- "
                    "a strict row-by-row dependency."},
    {"name": "CYK membership parsing",
     "domain": "dp",
     "description": "Decide whether a string of length n is generated by a context-free "
                    "grammar in CNF (CYK, O(n^3 |G|)). Output is one boolean (O(1)). The DP "
                    "combines all split points of all substrings, in increasing span order."},
    {"name": "Optimal matrix-chain parenthesization",
     "domain": "dp",
     "description": "Choose the multiplication order of a chain of n matrices minimizing "
                    "scalar operations (interval DP, O(n^3)). Output is the optimal cost "
                    "(one scalar) and optionally the O(n)-size parenthesization."},
    {"name": "Subset-sum decision with small target",
     "domain": "dp",
     "description": "Decide whether some subset of N integers sums exactly to target T "
                    "(pseudo-polynomial DP, O(NT)). Output is one boolean (O(1)); a witness "
                    "subset certifies 'yes'. The DP table row for item i depends on row i-1."},

    # --- Operations research / optimization -------------------------------------
    {"name": "Assignment problem (Hungarian algorithm)",
     "domain": "optimization",
     "description": "Find a minimum-cost perfect matching in an n x n cost matrix "
                    "(Hungarian algorithm, O(n^3)). The required output is the full "
                    "assignment (n pairs, O(n) values) and its cost. Iterations adjust dual "
                    "potentials based on the current partial matching."},
    {"name": "Stable matching (Gale-Shapley)",
     "domain": "optimization",
     "description": "Compute a stable matching between two sides of size n from preference "
                    "lists (O(n^2) proposals). Output is the full matching (O(n) values). "
                    "Each proposal round depends on the current tentative matching."},
    {"name": "Branch-and-bound for small integer programs",
     "domain": "optimization",
     "description": "Solve a small 0/1 integer program exactly by exploring a search tree "
                    "with LP-relaxation bounds for pruning. Output is the optimal solution "
                    "vector (O(n)) and value. The explored tree size varies wildly with "
                    "instance; node evaluation (an LP solve) is the unit cost."},
    {"name": "Golden-section search on a unimodal function",
     "domain": "optimization",
     "description": "Minimize a unimodal black-box function on an interval to precision eps "
                    "using O(log(1/eps)) sequential evaluations. Output is one scalar "
                    "location (O(1)). Each next query point depends on all previous "
                    "comparisons."},
    {"name": "2-opt local search for tour improvement",
     "domain": "optimization",
     "description": "Improve a traveling-salesman tour by repeatedly finding an improving "
                    "2-opt swap among O(n^2) candidate swaps until none exists. Output is "
                    "the final tour (O(n) values). Structure: each round is a search over a "
                    "quadratic candidate set for ANY improving move; rounds are sequential."},
    {"name": "Knapsack branch-and-bound with fractional bounds",
     "domain": "optimization",
     "description": "Solve 0/1 knapsack exactly via depth-first branch-and-bound using the "
                    "fractional-knapsack upper bound for pruning. Output is the optimal "
                    "subset (O(n)) and value. Tree size is instance-dependent; node tests "
                    "are cheap predicates."},

    # --- ML subroutines -----------------------------------------------------------
    {"name": "Lloyd's k-means iteration",
     "domain": "ml",
     "description": "One iteration assigns each of N points to the nearest of k centroids "
                    "(N*k distance evaluations) and recomputes centroids. Output per "
                    "iteration is the assignment (O(N) values) and k centroids; iterations "
                    "are sequential until convergence."},
    {"name": "Best-split selection for a decision-tree node",
     "domain": "ml",
     "description": "Given N labeled samples and d features, find the (feature, threshold) "
                    "pair maximizing information gain: a maximization over O(d*N) candidate "
                    "splits, each scored by a counting pass. The required output is ONE "
                    "(feature, threshold) pair (O(1))."},
    {"name": "Kernel Gram matrix computation",
     "domain": "ml",
     "description": "Compute the full N x N kernel matrix K(x_i, x_j) for N samples. The "
                    "required output is O(N^2) values; each entry is an independent "
                    "evaluation."},
    {"name": "Random-forest inference for one sample",
     "domain": "ml",
     "description": "Classify ONE input by routing it through T independent decision trees "
                    "of depth ~D and taking the majority vote. Output is a single class "
                    "label (O(1)). Tree traversals are independent of each other; each "
                    "traversal is a short sequential path."},
    {"name": "Leave-one-out cross-validation error of a 1-NN classifier",
     "domain": "ml",
     "description": "Compute the LOO error rate of 1-nearest-neighbor on N points: for each "
                    "point, find its nearest other point and check label agreement, then "
                    "average. The required output is one scalar error rate (O(1)). "
                    "Structure: an average over N independent nearest-neighbor queries."},
    {"name": "Perceptron training to convergence",
     "domain": "ml",
     "description": "Train a linear separator by cycling through samples and updating on "
                    "each mistake; converges in O((R/gamma)^2) updates for margin gamma. "
                    "Output is the weight vector (O(d) values). The update sequence is "
                    "strictly order-dependent; finding ANY currently-misclassified sample "
                    "is the inner search step."},

    # --- Streaming / sketching -----------------------------------------------------
    {"name": "Exact number of distinct elements",
     "domain": "streaming",
     "description": "Count the number of DISTINCT values among N items exactly (hashing, "
                    "O(N) time, O(N) space). Output is one integer (O(1)). Each item "
                    "contributes an independent membership test against the growing set."},
    {"name": "Median (selection) of an unsorted array",
     "domain": "streaming",
     "description": "Find the exact median of N unsorted numbers (quickselect, expected "
                    "O(N)). Output is one value (O(1)). Structure: rank-based selection, "
                    "where partitioning decisions depend on previous pivots."},
    {"name": "Heavy hitters over a stream",
     "domain": "streaming",
     "description": "Report all items whose frequency exceeds a phi fraction of a length-N "
                    "stream (Misra-Gries, one pass, O(1/phi) space). Output is at most "
                    "1/phi item ids (small). Counters are updated sequentially per item."},
    {"name": "Sliding-window maxima",
     "domain": "streaming",
     "description": "For every window of size w over an N-item sequence, output the window "
                    "maximum (monotone deque, O(N) total). The required output is O(N) "
                    "values -- one per window position."},
    {"name": "Reservoir sampling of k items",
     "domain": "streaming",
     "description": "Maintain a uniform k-sample over a stream of unknown length N in one "
                    "pass. Output is k items (O(k)). Each item's inclusion decision is an "
                    "independent coin flip given its index."},
]


if __name__ == "__main__":
    from collections import Counter
    domains = Counter(c["domain"] for c in CANDIDATES)
    print(f"{len(CANDIDATES)} candidates: "
          + ", ".join(f"{d}={n}" for d, n in sorted(domains.items())))
