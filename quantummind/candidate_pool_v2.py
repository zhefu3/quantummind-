"""
Candidate pool v2 -- the "cold water" pool (discovery lever 2).

Why a v2. The first pool (candidate_pool.py) returned a 100% rediscovery rate on
every positive verdict. That is the tell that the net was cast in waters the quantum
community already swept: clean, textbook-adjacent structure is exactly what gets a
quantum paper written about it. v1 optimized for *screenability* (does the pipeline
have a primitive for it?), which is the same axis as *already-studied*.

v2 inverts the selection axis. It targets domains where speedup-relevant structure
demonstrably exists -- oracle-checkable search over structured exponential spaces
(Grover / quantum backtracking), scalar/aggregate estimation targets (amplitude /
mean estimation), or fixpoint iterations whose inner step is itself a search -- but
where the quantum-algorithms literature is genuinely thin because the problems live
in applied systems/software fields, not in the mathematical core the community
mines. Compiler internals, database query planners, formal-methods search loops,
bioinformatics combinatorics, probabilistic inference, and concrete scheduling are
the sweet spots: NP-hard or search-heavy, structurally promising, and under-swept.

Honesty guards baked into the framing:
  - Each description states the REQUIRED OUTPUT and its size explicitly (the single
    most decision-relevant fact for readout accounting) and stays blind: no quantum
    hints, so the verdict is the pipeline's own.
  - Many of these are NP-hard. The honest prior for those is "Grover/backtracking
    quadratically speeds up an exponential search -- still exponential," a real but
    modest result that is often near-known (cf. Ambainis et al. 2019). The novelty
    filter is expected to flag those; the genuinely interesting outputs are the
    estimation sub-steps and structured inner loops that no one has written up.
  - `cold_rationale` records WHY the domain is under-explored, for advisor review --
    it is documentation, never fed to the pipeline.

This is a draft for advisor pruning; entries are cheap to add or drop.
"""

CANDIDATES = [
    # --- Compilers / programming languages ---------------------------------
    {"name": "Superoptimization of a straight-line code sequence",
     "domain": "compilers",
     "description": "Given a short straight-line instruction sequence, find the "
                    "shortest equivalent sequence over a fixed instruction set by "
                    "searching candidate programs of increasing length and checking "
                    "each for input-output equivalence. The search space is exponential "
                    "in length; equivalence of a candidate is an efficiently checkable "
                    "predicate (test vectors, or an SMT query). The required output is a "
                    "single optimal sequence (O(length), small).",
     "cold_rationale": "Superoptimization is an oracle-checkable search over an "
                       "exponential program space -- textbook Grover/backtracking "
                       "territory -- yet essentially unstudied in the quantum literature "
                       "because it lives in compiler engineering, not math."},
    {"name": "Optimal register allocation for a fixed interference graph",
     "domain": "compilers",
     "description": "Assign k physical registers to program variables so that no two "
                    "simultaneously-live variables share a register, minimizing spills. "
                    "This is graph coloring / a constraint search; a candidate assignment "
                    "is checkable in linear time. The required output is one color per "
                    "variable (O(V) values).",
     "cold_rationale": "Graph coloring has quantum-walk/Grover angles but register "
                       "allocation specifically -- with its spill-cost objective and "
                       "backtracking heuristics -- is unswept."},
    {"name": "Basic-block instruction scheduling under latency constraints",
     "domain": "compilers",
     "description": "Order the instructions of a basic block to minimize total cycles "
                    "subject to data-dependency and functional-unit latency constraints. "
                    "Feasible schedules form a constrained permutation space searched by "
                    "list scheduling / branch-and-bound; a schedule's validity and cost "
                    "are cheaply checkable. Output is one ordering (O(n)) plus its cost.",
     "cold_rationale": "A constrained-permutation search with a checkable objective; the "
                       "backtracking primitive fits, but instruction scheduling has no "
                       "quantum treatment."},
    {"name": "Syntax-guided program synthesis from examples",
     "domain": "compilers",
     "description": "Find the smallest expression in a given grammar consistent with a "
                    "set of input-output examples, by enumerating grammar derivations in "
                    "size order and testing each against the examples. Exponential search "
                    "space; each candidate is checked in time linear in the examples. "
                    "Output is one program (small).",
     "cold_rationale": "SyGuS is search over a derivation tree with an oracle-checkable "
                       "predicate -- a natural quantum-backtracking target that the "
                       "synthesis community has never approached from the quantum side."},
    {"name": "Peephole rewrite-rule discovery",
     "domain": "compilers",
     "description": "Given a corpus of instruction patterns, find all pairs (a, b) such "
                    "that a can be rewritten to a cheaper b preserving semantics, by "
                    "searching pattern pairs and verifying equivalence. Output is the set "
                    "of valid rewrite rules found (can be O(1) to many).",
     "cold_rationale": "Equivalence-checked search over pattern pairs; unstudied quantumly."},

    # --- Database internals -------------------------------------------------
    {"name": "Join-order selection for a multi-way query",
     "domain": "databases",
     "description": "Choose the order in which to join n relations to minimize estimated "
                    "total intermediate-result size. The plan space is exponential (like "
                    "matrix-chain but with a data-dependent cost model); a plan's cost is "
                    "cheaply evaluated given cardinality estimates. Required output is one "
                    "optimal join tree (O(n)) and its cost.",
     "cold_rationale": "Structurally a search/DP over an exponential plan space with a "
                       "checkable cost -- close cousin of TSP-DP, but the database "
                       "query-optimization framing is entirely unswept quantumly."},
    {"name": "Cardinality estimation by sampling",
     "domain": "databases",
     "description": "Estimate the number of rows a query predicate will select from a "
                    "large table, to precision eps, by sampling rows and averaging an "
                    "indicator. Classical Monte Carlo needs O(1/eps^2) samples. Required "
                    "output is a single scalar estimate (O(1)).",
     "cold_rationale": "A textbook mean-estimation target (amplitude/mean estimation) "
                       "sitting inside every query planner, never analyzed quantumly."},
    {"name": "Optimal index selection under a workload",
     "domain": "databases",
     "description": "Choose a subset of candidate indexes, within a storage budget, that "
                    "minimizes total estimated cost over a query workload. Subset-selection "
                    "search with a checkable cost function. Output is the chosen index set "
                    "(subset of candidates).",
     "cold_rationale": "Budgeted subset search with a checkable objective -- Grover/"
                       "backtracking-shaped, unstudied."},
    {"name": "Distinct-value estimation over a column",
     "domain": "databases",
     "description": "Estimate the number of distinct values in a large column to relative "
                    "error eps. Classical sketches trade accuracy for one pass. Required "
                    "output is one integer estimate (O(1)).",
     "cold_rationale": "Relative-error count estimation -- exactly the quantum-Chebyshev "
                       "mean-estimation regime -- but framed as a DB sketch nobody has "
                       "quantized."},

    # --- Formal methods / verification --------------------------------------
    {"name": "Bounded model checking for a safety property",
     "domain": "formal_methods",
     "description": "Decide whether a transition system can reach a bad state within k "
                    "steps by searching for a length-<=k execution path violating the "
                    "property (encoded as a satisfiability query). Exponential search "
                    "space; a candidate counterexample is checkable in O(k). Output is a "
                    "single boolean plus, if unsafe, one witness trace.",
     "cold_rationale": "Reachability-as-search with an oracle-checkable witness; SAT/BMC "
                       "is a Grover-shaped decision problem the verification field has "
                       "not approached quantumly beyond generic 'Grover for SAT'."},
    {"name": "Minimal unsatisfiable core extraction",
     "domain": "formal_methods",
     "description": "Given an unsatisfiable constraint set, find a minimal subset that is "
                    "still unsatisfiable, by searching subsets and testing satisfiability. "
                    "Output is one minimal subset (subset of the constraints).",
     "cold_rationale": "Subset search with an unsat oracle; unswept."},
    {"name": "Loop-invariant candidate search",
     "domain": "formal_methods",
     "description": "Search a template space of candidate loop invariants for one that is "
                    "inductive and strong enough to prove a goal, testing each candidate "
                    "with a constraint solver. Exponential template space; each candidate "
                    "checkable by an SMT query. Output is one invariant (small).",
     "cold_rationale": "Template-space search with a checkable predicate -- backtracking-"
                       "shaped, no quantum treatment."},
    {"name": "Shortest counterexample trace in a state machine",
     "domain": "formal_methods",
     "description": "Find the shortest input sequence driving a finite state machine into "
                    "an error state. Graph shortest-path on an implicitly-defined, "
                    "exponentially large state graph. Output is one trace (its length can "
                    "be small even when the state space is huge).",
     "cold_rationale": "Shortest path on an implicit exponential graph with a small "
                       "output -- quantum-walk-adjacent but framed in a way the community "
                       "hasn't examined."},

    # --- Bioinformatics (beyond alignment) ----------------------------------
    {"name": "Maximum-parsimony phylogenetic tree search",
     "domain": "bioinformatics",
     "description": "Find the tree topology over n taxa minimizing the total number of "
                    "character-state changes needed to explain observed data. The number "
                    "of topologies grows super-exponentially; a given topology's parsimony "
                    "score is computed in linear time (Fitch). Output is one optimal tree "
                    "(O(n) structure) and its score.",
     "cold_rationale": "Search over a super-exponential topology space with a cheaply "
                       "scored objective -- prime Grover/backtracking territory; "
                       "phylogenetics has essentially no quantum-algorithms literature."},
    {"name": "Planted motif search in DNA sequences",
     "domain": "bioinformatics",
     "description": "Find a length-l pattern occurring (with up to d mismatches) in each "
                    "of t sequences. The candidate-motif space is 4^l; testing whether a "
                    "candidate is planted is a linear scan of the sequences. Output is one "
                    "motif (O(l)).",
     "cold_rationale": "Oracle-checkable search over an exponential motif space -- "
                       "canonical Grover shape, unstudied quantumly."},
    {"name": "Haplotype phasing by minimum recombination",
     "domain": "bioinformatics",
     "description": "Resolve genotype data into two haplotypes per individual minimizing "
                    "total recombination events across a pedigree, searching phasings "
                    "consistent with inheritance constraints. Output is the phased "
                    "haplotypes (O(sites) per individual).",
     "cold_rationale": "Constraint-consistent combinatorial search; no quantum work."},
    {"name": "RNA secondary-structure design (inverse folding)",
     "domain": "bioinformatics",
     "description": "Find a nucleotide sequence that folds into a target secondary "
                    "structure under a free-energy model, searching sequence space and "
                    "testing each candidate by a folding computation. Exponential search; "
                    "each candidate checkable by a polynomial DP. Output is one sequence "
                    "(O(length)).",
     "cold_rationale": "Search over sequence space with a DP-checkable predicate -- "
                       "backtracking-shaped; inverse folding has no quantum treatment."},
    {"name": "Peptide identification from a mass spectrum",
     "domain": "bioinformatics",
     "description": "Identify the peptide whose theoretical fragment spectrum best matches "
                    "an observed mass spectrum, searching candidate peptides and scoring "
                    "each match. Output is one best-matching peptide (small).",
     "cold_rationale": "Search-and-score over a large candidate space; unswept."},

    # --- Probabilistic inference --------------------------------------------
    {"name": "MAP inference in a discrete graphical model",
     "domain": "probabilistic_inference",
     "description": "Find the joint assignment of discrete variables maximizing the "
                    "probability of a factor graph. Exponential assignment space; a given "
                    "assignment's score is a product of factors evaluated in linear time. "
                    "Output is one assignment (O(n) values).",
     "cold_rationale": "Maximization over an exponential assignment space with a checkable "
                       "score -- Grover-shaped; MAP inference is a workhorse with no "
                       "quantum treatment beyond generic annealing analogies."},
    {"name": "Approximate model counting (#SAT) to relative error",
     "domain": "probabilistic_inference",
     "description": "Estimate the number of satisfying assignments of a boolean formula to "
                    "relative error eps. The count is a scalar; classical approximate "
                    "counters use hashing + sampling. Required output is one number (O(1)).",
     "cold_rationale": "Approximate counting to relative error -- the quantum-counting / "
                       "amplitude-estimation regime -- but the #SAT / weighted-model-count "
                       "framing that inference actually uses is unswept."},
    {"name": "Partition-function estimation for a spin system",
     "domain": "probabilistic_inference",
     "description": "Estimate the partition function Z of a discrete spin model (a sum over "
                    "exponentially many configurations) to relative error, via importance "
                    "sampling or annealed sampling. Required output is one scalar (O(1)).",
     "cold_rationale": "Sum-over-configurations estimation -- mean/amplitude estimation "
                       "shape -- studied for specific quantum Hamiltonians but not for the "
                       "classical-inference partition-function estimator as an algorithm."},
    {"name": "Most-probable-explanation sampling in a Bayesian network",
     "domain": "probabilistic_inference",
     "description": "Estimate the probability of the most likely explanation for observed "
                    "evidence in a Bayes net by sampling high-probability assignments. "
                    "Output is one scalar probability plus one assignment (O(n)).",
     "cold_rationale": "Rare-event / search-and-estimate hybrid; unstudied."},

    # --- Scheduling / operations research (concrete) ------------------------
    {"name": "Job-shop scheduling makespan minimization",
     "domain": "scheduling",
     "description": "Schedule n jobs on m machines respecting operation orders to minimize "
                    "the makespan. Feasible schedules form a constrained combinatorial "
                    "space searched by branch-and-bound; a schedule's makespan is cheaply "
                    "computed. Output is the schedule (O(operations)) and its makespan.",
     "cold_rationale": "Branch-and-bound over an exponential feasible space with a "
                       "checkable objective -- quantum-backtracking target; job-shop has "
                       "no quantum-algorithms (as opposed to QAOA-heuristic) treatment."},
    {"name": "Capacitated vehicle routing",
     "domain": "scheduling",
     "description": "Route a fleet from a depot to serve customers within capacity limits "
                    "minimizing total distance. Exponential routing space; a candidate "
                    "routing's feasibility and cost are cheaply checkable. Output is the "
                    "set of routes (O(customers)).",
     "cold_rationale": "TSP-family but capacitated-multi-vehicle; the exact-search framing "
                       "is under-explored beyond generic annealing."},
    {"name": "Nurse rostering under hard and soft constraints",
     "domain": "scheduling",
     "description": "Assign staff to shifts satisfying hard coverage/rest constraints and "
                    "minimizing soft-constraint penalties, searching feasible rosters. "
                    "Output is one roster (O(staff*days)).",
     "cold_rationale": "Constraint-satisfaction search with a penalty objective; unswept."},
    {"name": "One-dimensional cutting-stock minimization",
     "domain": "scheduling",
     "description": "Cut stock rolls to fill item demands using the fewest rolls, searching "
                    "over cutting patterns. Output is the multiset of patterns used (small "
                    "relative to demand).",
     "cold_rationale": "Pattern-search with a checkable feasibility test; no quantum work."},

    # --- Software testing / analysis ----------------------------------------
    {"name": "Minimal failing-input search (delta debugging)",
     "domain": "testing",
     "description": "Given an input that triggers a bug, find a minimal sub-input that "
                    "still triggers it, by searching subsets and re-running the program. "
                    "Each test is an oracle call (program run). Output is one minimal input.",
     "cold_rationale": "Subset search with an expensive-but-checkable oracle -- Grover "
                       "shape; delta debugging is pure engineering, no quantum angle taken."},
    {"name": "Fault localization by spectrum ranking",
     "domain": "testing",
     "description": "Rank program statements by suspiciousness given pass/fail test "
                    "coverage, to identify the most likely fault location. The required "
                    "output is the single top-ranked statement (O(1)) or a short ranked "
                    "list.",
     "cold_rationale": "A max/selection over a suspiciousness score -- Durr-Hoyer-shaped "
                       "if the score is oracle-accessible; unstudied."},
    {"name": "Higher-order mutation-testing survivor search",
     "domain": "testing",
     "description": "Find combinations of code mutations that survive a test suite "
                    "(are not detected), searching the exponential space of mutant "
                    "combinations and running the suite as the oracle. Output is the set "
                    "of surviving mutants found.",
     "cold_rationale": "Oracle-checkable search over an exponential mutant space; unswept."},
    {"name": "Coverage-maximizing test-suite subset",
     "domain": "testing",
     "description": "Select the smallest subset of a test suite preserving total code "
                    "coverage. Subset search with a checkable coverage predicate. Output "
                    "is one minimal subset.",
     "cold_rationale": "Minimal-subset search with a checkable objective; Grover-shaped."},

    # --- Geometry / planning ------------------------------------------------
    {"name": "Sampling-based motion planning feasibility",
     "domain": "planning",
     "description": "Decide whether a collision-free path exists for a robot between two "
                    "configurations in a high-dimensional configuration space, searching a "
                    "graph of sampled configurations; edge feasibility is a collision "
                    "check (oracle). Output is one boolean plus, if feasible, a path.",
     "cold_rationale": "Reachability search on an implicit high-dimensional graph with an "
                       "oracle edge test -- quantum-walk/Grover-adjacent; motion planning "
                       "has no quantum-algorithms literature."},
    {"name": "Art-gallery minimum guard placement",
     "domain": "planning",
     "description": "Place the fewest point guards to see every point of a polygon, "
                    "searching guard subsets with a visibility-coverage check. Output is "
                    "the guard set (small).",
     "cold_rationale": "Minimum-set-cover search with a geometric checkable predicate; "
                       "unswept quantumly."},
    {"name": "Geometric set-cover for sensor placement",
     "domain": "planning",
     "description": "Choose the fewest sensors (disks) covering a set of target points, a "
                    "subset search with a checkable coverage test. Output is the chosen "
                    "subset.",
     "cold_rationale": "Structured set cover; only generic Grover-for-set-cover exists, "
                       "not this geometric framing."},

    # --- Systems / networks -------------------------------------------------
    {"name": "Offline optimal cache replacement (Belady) verification",
     "domain": "systems",
     "description": "Given a full reference trace and cache size, compute the minimum "
                    "number of misses achievable (the offline optimum). Belady's rule is "
                    "greedy-optimal in O(trace); framed as search, candidate eviction "
                    "policies form a large space. Required output is one integer (O(1)).",
     "cold_rationale": "A scalar-output optimum with both greedy and search framings -- a "
                       "clean contrast probe (greedy already optimal, so honest answer is "
                       "likely 'no speedup'); tests whether the pipeline resists a "
                       "search-shaped false positive."},
    {"name": "Optimal task-to-core assignment minimizing makespan",
     "domain": "systems",
     "description": "Assign independent tasks with known costs to k cores minimizing the "
                    "maximum core load. Assignment search with a cheaply computed makespan. "
                    "Output is the assignment (O(tasks)).",
     "cold_rationale": "Load-balancing / multiprocessor scheduling as exact search; "
                       "unswept beyond heuristics."},
    {"name": "Packet-classification ruleset minimization",
     "domain": "systems",
     "description": "Find the smallest equivalent ruleset for a packet classifier, "
                    "searching rule combinations and checking behavioral equivalence. "
                    "Output is one minimal ruleset.",
     "cold_rationale": "Equivalence-checked minimization search; no quantum treatment."},

    # --- Aggregate-output spectral / linear-algebra queries -----------------
    # Deliberately NOT search- or estimation-template problems. A preflight showed
    # most cold-domain candidates still reduce to Grover/backtracking (search) or
    # amplitude/mean estimation, which are well studied. These target the newer
    # QSVT/linear-systems CONDITIONAL regime: a single scalar/aggregate readout
    # over a large sparse operator, where the interesting question is whether the
    # aggregate-only output dodges the readout wall. Structurally further from the
    # swept templates.
    {"name": "Effective resistance between two nodes of a large network",
     "domain": "spectral_queries",
     "description": "Compute the effective resistance between a single pair of nodes in a "
                    "large sparse resistor network, i.e. one entry of the graph Laplacian "
                    "pseudoinverse. The required output is a single scalar (O(1)); the full "
                    "pseudoinverse is never needed. Classically this is a linear solve "
                    "against the Laplacian.",
     "cold_rationale": "A single-aggregate linear-system query (QSVT/HHL-conditional shape) "
                       "where the O(1) output may dodge the readout wall -- structurally "
                       "distinct from the search/estimation templates that dominate the pool."},
    {"name": "Single-vertex PageRank score query",
     "domain": "spectral_queries",
     "description": "Return the PageRank of ONE designated vertex of a large web graph (one "
                    "entry of the stationary distribution of the Google matrix), not the whole "
                    "ranking. Required output is a single scalar (O(1)). Classically a power "
                    "iteration or a linear solve.",
     "cold_rationale": "One entry of a stationary distribution = aggregate linear-algebra "
                       "query; the single-entry framing (vs full ranking) is the readout-"
                       "favorable case worth a QSVT look."},
    {"name": "Spectral-gap estimation of a sparse Markov chain",
     "domain": "spectral_queries",
     "description": "Estimate the spectral gap (1 minus the second-largest eigenvalue) of a "
                    "large sparse stochastic matrix, which controls mixing time. Required "
                    "output is a single scalar (O(1)). Classically via iterative eigensolvers.",
     "cold_rationale": "Extremal singular/eigenvalue estimation of a sparse operator -- the "
                       "QSVT sweet spot, in an applied Markov-chain framing rather than the "
                       "usual physics Hamiltonian one."},
    {"name": "Katz centrality of a single node via matrix resolvent",
     "domain": "spectral_queries",
     "description": "Compute the Katz centrality of one node -- one entry of (I - alpha A)^{-1} "
                    "summed appropriately -- for a large sparse adjacency matrix A. Required "
                    "output is a single scalar (O(1)).",
     "cold_rationale": "A single resolvent-entry query, aggregate readout, block-encodable "
                       "sparse operator -- QSVT-conditional and not a search/estimation template."},
    {"name": "Triangle-density (global clustering coefficient) estimate",
     "domain": "spectral_queries",
     "description": "Estimate the global clustering coefficient (a normalized triangle count) "
                    "of a large sparse graph to relative error. Required output is a single "
                    "scalar (O(1)); expressible as a normalized trace of A^3.",
     "cold_rationale": "A trace-of-matrix-power aggregate -- sits between mean estimation and "
                       "QSVT; a useful probe of whether the pipeline routes trace queries to "
                       "the right primitive rather than defaulting to plain amplitude estimation."},

    # --- Contrast probes (design negatives for v2) --------------------------
    {"name": "Topological sort of a DAG",
     "domain": "contrast",
     "description": "Produce a linear ordering of a directed acyclic graph's vertices "
                    "consistent with all edges, in O(V+E). The required output is a full "
                    "ordering of all V vertices (O(V) values), and the computation is an "
                    "inherently sequential peeling of zero-indegree vertices.",
     "cold_rationale": "Design negative: output-dense (all V) + sequential; should be a "
                       "clean 'none'. Guards against the cold pool inflating false "
                       "positives."},
    {"name": "Union-Find connected components",
     "domain": "contrast",
     "description": "Compute connected-component labels for all n elements under a sequence "
                    "of union operations, near-linear classically. The required output is a "
                    "label for every element (O(n) values).",
     "cold_rationale": "Design negative: output-dense; near-optimal classical. Should be "
                       "'none'."},
]


if __name__ == "__main__":
    from collections import Counter
    d = Counter(c["domain"] for c in CANDIDATES)
    print(f"{len(CANDIDATES)} candidates: " + ", ".join(f"{k}={v}" for k, v in sorted(d.items())))
