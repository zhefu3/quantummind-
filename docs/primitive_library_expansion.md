# Primitive-library expansion (discovery lever)

**Date:** 2026-07-10 · **Backend:** anthropic / claude-sonnet-4-6 (unchanged — the
model is a fixed experimental variable). **Cost:** ~$0.6 validation (kept small by
prompt caching, below).

## Motivation

The first full funnel run (docs/funnel_stage1_run.md, funnel_stage2_run.md) exposed
a ceiling that is **upstream of the pipeline's reasoning**: Agent 2 can only
recommend a primitive its knowledge base contains. With six primitives, modern
quantum algorithmic tools were simply unsayable, so the matcher jammed structurally-
different candidates into the nearest available id — CYK and 2-opt into `grover`,
condition-number estimation into `amplitude_estimation`, even though the schemes'
own reasoning described backtracking / QSVT. A discovery instrument that cannot
express a speedup class cannot discover one in it.

## Change

Added three primitives to `knowledge_base.py` (now 9 primitives, 28 citable KB
entries), each with **strict** prerequisites written to preserve the hard-negative
traps:

| id | covers | key guard |
|---|---|---|
| `quantum_backtracking` | CSP/backtracking, branch-and-bound, DP inner-loop search (Montanaro 2018) | speedup is **sub-step / tree-search only**, at most quadratic; sequential outer structure is not accelerated |
| `qsvt` | block-encoding, singular-value estimation, matrix functions (Gilyén et al. 2019) | **aggregate readout only** — same readout wall as HHL; full-vector output erases it |
| `quantum_mean_estimation` | relative-error mean / moment / subgraph-counting estimation (Montanaro 2015; Hamoudi-Magniez 2019) | scalar/aggregate output; coherent sampler required |

A matching `qsvt_framework` novelty entry was added to `known_results.py` so QSVT
recommendations are literature-checked like the others.

## Validation (bounded, high-signal — no full sweep)

**False-positive guard (the important direction).** All 5 labeled hard negatives
still resolve to `none` with the expanded, more permissive-looking library:

| hard negative | verdict |
|---|---|
| sparse linear system, full vector | none ✓ |
| all-pairs shortest paths, full matrix | none ✓ |
| search a SORTED list | none ✓ |
| return ALL elements satisfying a predicate | none ✓ |
| strongly sequential recurrence | none ✓ |

Sampled positives held (linear search→grover, factoring→qft, Monte Carlo→
amplitude_estimation). **No regression.**

**Payoff — candidates the old library mis-slotted now match cleanly:**

- **Condition number estimation → `qsvt`** (was `amplitude_estimation`). The
  recommendation now agrees with the scheme's own QSVT/Gilyén reasoning — this
  closes the recommendation-vs-reasoning mismatch documented for this candidate.
- **CYK parsing** now surfaces `quantum_backtracking` as a partial match (the
  DP-inner-loop structure is finally visible), alongside grover.
- **2-opt** correctly *stayed* `grover` — Dürr-Høyer minimum-finding is
  grover-family, and the new primitive did not wrongly displace it.
- **Best-split selection → clean `none` (high)**, previously a fragile escalation:
  the richer library let the matcher reject it precisely instead of hedging — one
  fewer Stage-2 recheck.

## Cost note: prompt caching

The knowledge base (~1.6k tokens) is injected into every Agent 2 / Agent 4 /
self-critique system prompt and is byte-identical across candidates. It is now sent
with an ephemeral `cache_control` breakpoint (`llm_client.py`), so after the first
write those tokens bill at ~0.1×. The validation run above read 35.8k tokens from
cache vs 5.1k written — the expansion was validated for well under what an uncached
run would cost, and every future funnel run inherits the discount.

## Status

The expansion is validated against regression and demonstrably lets the system
express speedup classes it previously could not. It does **not** by itself produce a
discovery — the second lever (a colder candidate pool, away from textbook-adjacent
structure) is still needed, and a full labeled-benchmark + funnel re-run at K≥2 is
the next paid step once the advisor confirms pool direction.
