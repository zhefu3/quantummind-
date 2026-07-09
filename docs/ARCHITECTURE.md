# QuantumMind — architecture & status

One-page map of the whole system. Detailed experiment records are linked at the end.

## What it is

A multi-agent LLM instrument that reads a **classical algorithm** and outputs a
**candidate quantization** — which quantum primitive (if any) could accelerate it,
the net speedup after honest I/O accounting, and how confident to be — packaged so a
quantum-computing expert can verify or dismiss it in minutes.

The scientific contribution is **characterizing where LLM multi-agent reasoning is
reliable and where it fails** on cross-domain structural analysis; discovering a new
speedup is the ultimate goal but is gated by the *verification problem* (no ground
truth on novel cases). With an expert in the loop, the binding constraint becomes
**expert time**, so the system is built as a funnel that compresses many candidates
into a few high-confidence, verification-ready ones.

## The pipeline (per algorithm)

```
Agent 1  Structure Analyst    quantum-blind decomposition (paradigm, bottleneck,
   │                          structural features, barrier flags)
Agent 2  Pattern Matcher      scores each primitive against an auditable knowledge
   │                          base (9 primitives, 28 citable conditions); cites the
   │                          specific prerequisite/barrier behind every verdict
Agent 3  Scheme Generator     concrete scheme + honest I/O accounting + speedup_scope
   │                          (full_algorithm | sub_step | conditional | none) + novelty
Agent 4  Independent Reviewer bidirectional audit: catches over-claims AND
   │                          over-conservative "none"s; checks scope consistency
Self-critique (diagnostic)    premortem: "if this is wrong, which specific KB
                              condition is the weak link?" + what an expert should
                              check first
```
Orchestrator runs iterative refinement (Agent 4 → Agent 2 bounce-back, ≤ 3 rounds).
Every run's full reasoning is archived under `outputs/`.

## The discovery funnel (expert time is scarce)

```
candidate pool  ──Stage 1──▶  survivors  ──Stage 2──▶  confirmed  ──Stage 3──▶  dossiers
 (v1 gray zone /   pipeline +    (advance /   K-vote        (CONFIRM/    novelty     expert-facing
  v2 cold domains) self-critique  escalate)   majority      PROMOTE)     filter vs   candidates +
                   triage                      recheck                   known_results calibration
                                                                                       appendix
```
- **Stage 1** (`screen.py`): triage = advance (non-"none") / escalate (fragile "none"
  → cheap recheck) / cut. The escalate tier exists because the documented failure
  mode is a real speedup hiding in an over-conservative "none".
- **Stage 2** (`stage2.py`): K=3 majority vote — single samples are unreliable.
- **Stage 3 / novelty** (`known_results.py`): a rediscovery is not sent to an expert;
  it becomes calibration evidence ("the system independently reproduced a known
  result"), which is *stronger* than the labeled benchmark because the inputs were
  never phrased as quantum questions.
- **Dossiers** (`dossier.py`): self-contained expert briefs, honestly scoped,
  separating genuine candidates from rediscoveries.

## Reliability instruments (the science)

1. **Single samples are unreliable** → all evaluation is majority-vote.
2. **High confidence is not reliability** → operationalized as the self-critique
   layer; each verdict must name its own most-plausible failure and cite a specific
   KB condition. Calibrated on 42 archived runs: it localizes the historical
   graph-connectivity error and doubts its own speedup claims more than its nulls.
3. **The reviewer had a blind spot** (only caught over-claims) → Agent 4 is now
   bidirectional, regression-tested by `review_injection_test.py`.
4. **Over-claim is structurally preventable** → `speedup_scope` stops a sub-step-only
   speedup being reported as whole-algorithm (the MCTS problem), enforced in Agent 4.

## Two levers for discovery yield (v1 produced zero — 100% rediscovery)

1. **Richer primitive library** — *built & validated.* Added quantum backtracking,
   QSVT/block-encoding, quantum mean estimation; hard negatives still resolve to
   "none". The 6-primitive library literally could not express modern quantum tools.
2. **Colder candidate pool** — *v2 drafted (38 candidates, 10 under-explored
   domains).* v1's clean textbook-adjacent structure was the same axis as
   already-studied; v2 targets structurally-promising-but-unswept domains.
Both need a paid run to produce candidates; the run is gated on advisor direction.

A third reasoning aid — **near-neighbor anchoring** (roadmap step 3) — is built and
opt-in (`--anchoring`): it feeds Agent 3 the candidate's nearest known quantum
results and forces an explicit "reduces to X (rediscovery)" or "differs decisively
because Y" call, moving novelty reasoning upstream of the post-hoc filter. Agent 2
stays blind; the default pipeline is unchanged (comparability). Needs an A/B run to
confirm it sharpens rather than biases before becoming default.

## Honest status

- End-to-end on v1: 49 blind candidates → 9 survivors → **all 9 literature-confirmed
  rediscoveries, zero false discovery claims**. No new algorithm discovered.
- Positive-verdict literature-confirmation rate: 100% (blind inputs) — the strongest
  calibration evidence to date.
- Cost to date ≈ $16; future runs cheaper (KB prompt caching, ~85% off KB-bearing
  input). Model fixed at `claude-sonnet-4-6` (experimental variable).

## Decisions needed (advisor)

1. Confirm Agent 4 + the self-critique layer (both implement the proposal's §5.2
   Layer-2 evaluation — not scope creep).
2. Expert bandwidth: how many dossiers is realistic (sets the funnel's final cutoff)?
3. Candidate-pool direction: prune/extend the v2 cold domains.

## Detailed records
- [self_critique_calibration.md](self_critique_calibration.md) — self-critique calibration + deeper analysis
- [funnel_stage1_run.md](funnel_stage1_run.md) / [funnel_stage2_run.md](funnel_stage2_run.md) — the full v1 funnel run
- [primitive_library_expansion.md](primitive_library_expansion.md) — lever 1
- [consistency_experiment.md](consistency_experiment.md) / [exploration_experiment.md](exploration_experiment.md) — reliability findings
