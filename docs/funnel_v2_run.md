# Discovery funnel: v2 cold-pool run (the discovery attempt)

**Date:** 2026-07-09 · **Backend:** anthropic / claude-sonnet-4-6, temperature 0.2
**Input:** all 43 v2 candidates (`candidate_pool_v2.py`) — genuinely under-explored
domains, run **blind** (no anchoring). This is the project's first deliberate attempt
to discover a new speedup, with the funnel doing the rediscovery-filtering.
**Cost:** ≈ $6.5 (Stage 1 ~$4, escalate-only Stage 2 ~$2.5).

## Result

**43 blind candidates → 18 survivors → 0 expert-facing candidates / 18 rediscoveries /
0 false discovery claims. No new algorithm discovered.**

### Stage 1 (blind screen)
17 advance / 17 escalate / 8 cut (1 candidate — Union-Find, a contrast negative —
failed on a network drop; expected "none").

The expanded primitive library visibly worked: 17 non-"none" verdicts vs. 7 on v1,
because the system now has `quantum_backtracking` and `qsvt` to *recognize* search
and linear-algebra speedups it previously could not express. All 7 backtracking
verdicts were correctly scoped `sub_step` — the honesty schema held.

### Zero-cost deep-dive (method A)
All 17 advances are rediscoveries, confirmed by **two independent signals**: the
novelty filter *and* the scheme's own `novelty` self-assessment (nearly every one
says "textbook" / "known canonical example" / "not novel"). No rediscovery flag was
a false positive hiding a genuine candidate. The 3–4 that hedged ("not fully
formalized") are known-technique compositions with known (often sub-step or nil)
net speedups — a paper-writing gap, not a new speedup.

### Stage 2 (escalate-only, K=3)
Of the 17 fragile "none"s — the place the project's own thesis says a real speedup
would hide — **exactly 1 flipped on the majority vote**: optimal register allocation
→ `quantum_backtracking` (2/3). The other 16 held "none" (including every candidate
whose self-critique had *suggested* an under-claim — the flips they predicted did not
survive K=3). The one flip is Montanaro backtracking applied to graph coloring — a
known application, i.e. another rediscovery.

## What this establishes (honest)

1. **The instrument is reliable end-to-end on genuinely-unknown inputs.** 18/18
   positive verdicts are literature-confirmed rediscoveries; **0 false discoveries**
   reached an expert dossier. On inputs never phrased as quantum questions, that is
   the strongest calibration evidence the project has.
2. **The bidirectional-review / escalate mechanism works as designed.** It *did*
   recover an under-claimed "none" (register allocation) on K-vote — validating the
   "opportunities hide in conservative nones" design — but the recovered item was a
   rediscovery, not a discovery.
3. **"Cold domain" ≠ "novel", confirmed empirically.** Every positive — advance or
   promoted — reduced to a known template (Grover / Montanaro backtracking /
   amplitude estimation / QSVT). Under-explored *applied* problems still map onto the
   known primitive templates; they simply lacked an applied-problem library entry.
4. **No new algorithm.** This is a rigorous negative result on discovery, which the
   proposal (§6) states is itself informative and publishable.

## Genuinely novel directions the system surfaced (open problems, not discoveries)

The gap analyses honestly flagged research directions the schemes do **not** solve —
worth recording as future work, not sent to an expert as results:
- a quantum primitive that coherently exploits **grammar-DP / memoization over shared
  subderivations** (from SyGuS synthesis);
- coherent acceleration of **DP over junction-tree / treewidth structure** beyond
  plain inner-loop Grover (from MAP inference);
- coherent simulation of the **residual-push (local-push) process** for single-vertex
  PageRank (non-Szegedy angle).

## Implication for the discovery goal

The frontier is not "run more under-explored domains" — those reduce to templates.
It is "find a problem whose structure does **not** reduce to a known template," which
is rare and is where the three open directions above point. The instrument is now
proven trustworthy enough to be aimed at that harder target once one is identified.
