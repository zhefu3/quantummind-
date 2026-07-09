# v2 run plan — cost/outcome for the funding decision

Decision-support for whether (and how) to fund a real-model run on the cold pool.
All figures are from zero-cost tooling (`--preflight`, `--estimate`) and v1's
observed rates; no model was called to produce this.

## What v2 is

43 candidates across 10 under-explored domains. `--preflight` (nearest known
result, no pipeline run) splits them **16 cold / 27 warm**:

| | count | reading |
|---|---|---|
| **warm** | 27 | already resembles a proven/conditional known result → will very likely screen as a rediscovery |
| **cold** | 16 | no strong library match → *but* most still reduce structurally to a known template (see below) |

The 16 cold candidates by structural type (the honest reason "cold" ≠ "novel"):
- **Oracle-checkable search over an exponential space** → Grover / quantum
  backtracking: superoptimization, SyGuS synthesis, peephole discovery, index
  selection, loop-invariant search, motif search, RNA inverse folding, MAP
  inference, VRP, nurse rostering, cutting-stock, fault localization, coverage
  subset, packet-classification minimization (14 of 16).
- **Mean/count estimation** → amplitude/mean estimation: distinct-value estimation.
- **Design negative** (should be "none"): topological sort.

So even the cold set is expected to produce mostly rediscoveries — they miss the
keyword filter only because the library lacks an *applied-problem* entry, not
because their structure is new.

## Cost

| stage | scope | est. cost | note |
|---|---|---|---|
| Stage 1 (full v2) | 43 candidates | ≤ $3.7 | upper bound; KB prompt caching makes it less |
| Stage 2 (K=3 recheck) | ~survivors | ~$1–2 | only escalations/advances |
| **full funnel** | | **~$5–6** | vs $16 spent on v1 |

## Expected outcome (from v1's rates)

v1: 49 → 9 survivors, **all rediscoveries, 0 genuine candidates**. On structural
grounds v2 should be similar: ~5–10 survivors, mostly rediscoveries routed to the
calibration appendix. Genuine-discovery probability is honestly low — the frontier
is "a problem whose structure does not reduce to a known template," which is rare.

The run's value is therefore: (a) more blind-reproduction calibration evidence
(the strongest evidence we have), (b) a real test of the two new levers (expanded
primitives + cold pool) end-to-end, and (c) the small, real chance that a specific
sub-structure — most plausibly among the aggregate-output spectral/linear-algebra
queries — resists reduction.

## Recommendation (cost-conscious)

Rather than fund the full 43 up front, **fund a targeted ~12-candidate probe (~$1.5)**
spanning the structural diversity:
- the 5 spectral/linear-algebra queries (the only non-search/estimation template —
  the likeliest genuine shot),
- 3–4 genuinely cold search problems (superoptimization, SyGuS, MAP inference),
- 2 contrast negatives (topological sort, union-find — confirm no false positives),
- 1–2 warm controls (confirm the novelty filter routes them to the appendix).

This tests both levers, the honesty schema, and the novelty filter for ~$1.5, and
tells us whether a full v2 run is worth it — before committing the full ~$5–6. Run:

```
python -m quantummind.screen --pool v2 --preflight   # confirm the split (free)
python -m quantummind.screen --pool v2 --estimate     # confirm cost (free)
# then a targeted run once the advisor picks the subset
```
