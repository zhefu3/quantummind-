# Self-critique calibration experiment (roadmap step 2)

**Date:** 2026-07-09 · **Backend:** anthropic / claude-sonnet-4-6, temperature 0.2
**Method:** `self_critique.py` run OFFLINE over 42 archived real-model pipeline records
(no pipeline re-runs) + 1 injected known-error case. Total ~48 single calls
(incl. 5 re-runs after a prompt fix), ≈ $1.6.

## Question

The consistency experiments established that neither confidence nor stability is a
reliability signal. Can the system's **structured self-critique** — "assuming this
verdict is wrong, which specific knowledge-base condition is the weak link" — do
better? We test it where ground truth exists before trusting it where it doesn't.

## Set A — error localization on a known-wrong verdict: PASS

Input: the documented wrongly-conservative graph-connectivity "none" (high
confidence, rubber-stamped by the pre-upgrade reviewer; reconstruction from
`review_injection_test.py`).

- `fragility: fragile` — correct: this verdict was actually wrong.
- Top-1 hypothesis targets `quantum_walk.spectral_conditions` — the wrongly
  dismissed primitive. **Check passes.**
- Rank-2 hypothesis states precisely the real mechanism: `strong_adaptivity` was
  **misapplied** — "the sequential dependency of BFS/DFS is a property of the
  classical algorithm, not of the quantum walk formulation … a category error",
  pointing the expert at MNRS/span-program formulations.
- `weakest_agent_claim` identifies the query-model vs classical-RAM conflation in
  the matcher's loading argument.

This is the exact content an expert needs to overturn the error, produced by the
system about its own (injected) output.

## Set B — behavior across the 42 real archived records

| group | n | fragile | moderate | robust |
|---|---|---|---|---|
| correct hard-negative "none" runs | 10 | 3 | 7 | 0 |
| graph connectivity (true borderline) | 16 | 9 | 7 | 0 |
| stable non-none verdicts (NNS→grover, MCTS→AE) | 4 | 4 | 0 | 0 |
| all 42 | 42 | 22 | 20 | 0 |

**Direction is right:** the reproducibly unstable question and the two
speculative "has speedup" candidates skew fragile; solid hard negatives skew
moderate.

**The three fragile ratings on "correct" hard negatives are not noise.** All
three target the same genuine issue — our labels are unconditional while the
ground truth is regime-dependent:

- *Return ALL elements satisfying a predicate* (×2): the critique notes the
  `output_dense` barrier only applies when the match count k = Θ(N); for
  k = o(N), Grover enumeration costs O(√(kN)) < O(N). The benchmark label
  "none" is only right in the worst-case regime. **The calibration layer
  caught an imprecision in our own benchmark.**
- *Strongly sequential recurrence* (1 of 2 runs): notes `strong_adaptivity` is
  labeled "heuristic, not a theorem" in the KB itself, and structured f (e.g.
  affine) admits restructuring the label ignores.

Whether these count as false alarms or as caught label imprecision is a framing
decision — either way the flags are substantive, not generic hedging.

## Limitations (as observed, not hypothesized)

1. **"robust" never fired (0/42).** The rubric's bar ("every hypothesis must
   contradict an established fact") is unreachable in practice; the scale is
   effectively binary (fragile/moderate). Follow-up: either recalibrate the
   rubric or treat *moderate* as the safe tier — we adopted the latter in
   screening triage.
2. **Fragile fires broadly (52%).** Useful as a ranking/escalation signal, NOT
   as a standalone gate. Consequence implemented in `screen.py`: a fragile
   "none" now **escalates to a K-vote recheck** instead of surviving Stage 1
   outright (the naive rule passed 4/5 in the pilot — no compression).
3. **Citation discipline needed one iteration.** With prompt v1, 5/42 critiques
   cited a bare primitive id (e.g. "quantum_walk") instead of a condition-level
   id — a vocabulary slip, not a reasoning failure. An explicit prompt rule
   fixed it: 0/42 violations after re-running those 5.

## Screening pilot (Stage 1, first 5 geometry candidates, ~$0.5)

All five verdicts were "none". Three-tier triage: **0 advance / 4 escalate /
1 cut** (~1.7 min per candidate — under the 2.5 min cost-model assumption).
The four escalations each carry a specific expert-checkable doubt (e.g. closest
pair: whether any speedup survives outside the query model).

## Verdict

The self-critique signal is **usable now** for (a) ranking candidates by risk,
(b) escalating suspicious "none"s, and (c) generating the "what to check first"
line of expert dossiers — and it localized a real historical error precisely.
It is **not yet** a standalone reliability gate: fragile over-fires, and the
robust tier is dead. Both facts are now encoded in the triage logic rather than
papered over.

**Files:** critiques in `outputs/self_critique/` (one per archived record +
`summary.json`); injection case in
`outputs/self_critique/injection__graph_conn_wrong_none.json`; pilot in
`outputs/screening/`.
