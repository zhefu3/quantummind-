# Exploration experiment: K=2 consistency on the 8 open-ended questions

Companion to [consistency_experiment.md](consistency_experiment.md), which covers the
labeled test set. This experiment covers the 8 "TO EXPLORE" questions added on top of
it -- cases with **no fixed ground truth** (`known_label.primitive` is `"unknown"`),
where the object of study is the reasoning's quality and honesty, not correctness.

## Setup

| | |
|---|---|
| Script | `python3 -m quantummind.exploration_consistency --n 2` |
| K | 2 independent full-pipeline runs per question |
| Questions | the 8 exploration entries at the tail of `quantummind/algorithms.py` |
| Backend / model | `anthropic` / `claude-sonnet-4-6` |
| Temperature | `0.2` (the `LLMClient` default, unchanged) |
| Per-run reasoning | full Agent 1-4 output in `outputs/consistency_<algorithm>/run_{1,2}.json` |
| Per-question summary | `outputs/consistency_<algorithm>/summary.json` |

Operational note: the batch script crashed on the last question (Monte Carlo tree
search) after an unhandled API error, so that question's two runs were completed by a
standalone `consistency_check` invocation and the batch-level
`exploration_consistency_summary.json` was never written -- the per-question
`summary.json` files are the authoritative record. (This incident motivated adding
retry/resume to the runners; see the git history.)

## Results

| Question | Runs (got) | Consistency | Confidence | Review | Rounds |
|---|---|---|---|---|---|
| Graph isomorphism | none, none | 2/2 | high×2 | sound×2 | 1, 1 |
| **High-dimensional nearest neighbor search** | **grover, grover** | 2/2 | medium×2 | sound×2 | 1, 1 |
| Single-source shortest path to one target | none, none | 2/2 | high×2 | sound×2 | 1, 1 |
| Dense matrix multiplication | none, none | 2/2 | high×2 | sound×2 | 1, 1 |
| Solve a PDE on a grid | none, none | 2/2 | high×2 | sound×2 | 1, 1 |
| Traveling salesman problem (TSP) | none, none | 2/2 | high×2 | sound×2 | 1, 1 |
| Train a small feedforward neural network | none, none | 2/2 | high×2 | sound×2 | 1, 1 |
| **Monte Carlo tree search** | **amplitude_estimation, amplitude_estimation** | 2/2 | medium×2 | sound×2 | 1, 1 |

- **Swayed (answers disagreed across runs): 0/8.** Unlike Graph connectivity in the
  labeled set, none of these open-ended cases showed sampling instability.
- **Stable non-"none" verdicts: 2/8** -- High-dimensional NNS (`grover`) and Monte
  Carlo tree search (`amplitude_estimation`). These are the pipeline's closest thing
  to a positive "discovery" output and the natural candidates for Layer-3 expert
  review.

## Observations

### 1. Confidence is *lower* on the "has speedup" verdicts -- reasonable conservatism

The two questions where the system claims a speedup both come in at **medium**
confidence, while the six "none" verdicts are all **high**. That is the right
direction: the speedup claims are the riskier assertions, and the system hedges them
rather than the other way around. This complements the labeled-set finding (see
consistency_experiment.md) that high confidence alone is not a reliability signal --
here, at least, the confidence gradient points the sensible way.

### 2. The designed probes were passed

Two of the questions carried specific traps in their design notes, and the reasoning
(spot-checked in the run_1 files) handled both:

- **Single-source shortest path to one target** (contrast probe against the all-pairs
  hard negative): the matcher explicitly notes "output_dense: NOT hit -- output is
  O(1) (single scalar), which is favorable" and rejects the speedup on a *different*,
  correct ground -- strong sequential dependency (Dijkstra's adaptivity), with a
  concrete complexity argument (Dürr–Høyer substitution gives O(V·√V), worse than
  classical O((V+E) log V) on sparse graphs). It was not misled by surface similarity
  to the all-pairs case.
- **High-dimensional nearest neighbor search** (I/O-bottleneck probe): the scheme's
  io_accounting states the speedup survives *if and only if* QRAM-style access
  exists, and the obstacles list opens with "QRAM remains a largely theoretical
  construct; no scalable physical implementation exists, and without it the speedup
  is entirely erased by classical data loading." The medium confidence is explicitly
  attributed in part to this dependency.

### 3. No refinement loops triggered

All 16 runs completed in 1 round -- Agent 4 stamped every scheme `sound` on the first
pass. Consistent with the known asymmetry (Agent 4 only checks for over-claimed
speedups, and these runs mostly conclude "none"), but also consistent with the
schemes simply being internally coherent. Nothing here exercises the bounce-back
path.
