# Discovery funnel: Stage-2 K-vote recheck

**Date:** 2026-07-10 · **Backend:** anthropic / claude-sonnet-4-6, temperature 0.2
**Input:** the 33 Stage-1 survivors (7 advance + 26 escalate), K=3 total runs each
(the Stage-1 run counts as run 1). **Cost:** ≈ $7 across two sessions — the first
was interrupted by API credit exhaustion mid-run; the disk cache resumed it with
zero waste (35 remaining runs, no recomputation).

## Result

**7 CONFIRM · 2 PROMOTE · 0 DEMOTE · 24 cut**

### All 7 Stage-1 advances survived their own majority vote

k-mismatch matching, triangle counting, trace estimation, quadrature (3/3 each);
condition number 2/3 (one dissent to "none", consistent with its marginal
quadratic-in-precision-only value); LOO-1-NN and perceptron 3/3 (completed after
the resume). All seven remain classified as rediscoveries (see
funnel_stage1_run.md) — none proceeds to an expert dossier.

### The escalation path produced its first recoveries — 2 of 26 fragile "none"s flipped

| promoted | majority | what the runs proposed | self-declared novelty |
|---|---|---|---|
| CYK membership parsing | grover 2/3 | Grover over the O(n·\|G\|) split-point/rule inner search per DP cell: O(n³\|G\|) → ~O(n^2.5) with QRAM caveats stated | "rediscovery … known observation in quantum algorithms for dynamic programming" |
| 2-opt local search | grover 2/3 | Dürr-Høyer minimum-finding over the O(n²) swap neighborhood per round; round count k explicitly unchanged | "rediscovery / straightforward application … noted in the quantum optimization literature (Montanaro 2020)" |

Both flips are structurally sound quantum-speedup patterns that the Stage-1
single run had conservatively rejected — **the exact failure mode (a real
speedup hiding in an over-conservative "none") that the symmetric-review and
escalation designs were built for, now observed and repaired at pool scale.**
Both are also self-declared rediscoveries; two known-results entries were added
(quantum_local_search, quantum_dp_inner_loop) so future runs flag them
automatically.

### The other 24 escalations resolved to unanimous or near-unanimous "none"

Fragile-none flip rate: 2/26 ≈ 8%. This quantifies the calibration finding:
*fragile* is a risk-ranking signal, not an error verdict — most fragile nones
are correct, and a cheap K-vote resolves which. Texture note: the betweenness-
centrality cut (2/3) had one dissenting amplitude_estimation run whose own
novelty field identified itself as near-known (Montanaro-family estimation) —
even the dissents self-report honestly.

## Funnel accounting, Stage 0 → 2

49 blind gray-zone candidates → 33 Stage-1 survivors → **9 Stage-2 survivors —
all nine independently identified as rediscoveries or known-direction
applications (6 by the novelty library, 3 by the schemes' own novelty
self-assessment, all manually confirmed). Zero false discovery claims
end-to-end.**

## Interpretation (honest)

1. As a **screening instrument**, the funnel is validated end-to-end on this
   pool: every positive it produced is literature-confirmed, every stage
   compressed, and the recovery path for over-conservative rejections works.
2. As a **discovery instrument**, this pool yielded zero novel candidates. The
   two levers that could change that are upstream: a colder, more structurally
   unusual candidate pool (this draft skewed toward clean textbook-adjacent
   structure), and a richer primitive library (the system can only recommend
   what its knowledge base can express — six primitives is a narrow net).
3. The nine rediscoveries are not waste: they are the strongest calibration
   evidence the project has (blind, non-quantum-phrased inputs; 100%
   literature confirmation), and exactly the material Layer 3 experts can
   verify cheaply.

## Next steps

- Advisor: pool direction (colder domains) and primitive-library expansion
  (e.g. quantum walks on DP DAGs, QSVT family, span programs) — the latter is
  the single highest-leverage change for discovery yield.
- Dossier template for the two legacy Layer-3 candidates (NNS, MCTS) plus the
  nine rediscoveries as a calibration appendix.
