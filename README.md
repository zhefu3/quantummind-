# QuantumMind — multi-agent quantum-acceleration analyzer

A faithful implementation of the QuantumMind proposal (Sections 3–5): a four-agent LLM
pipeline that takes a **classical algorithm** as input and produces a **candidate
quantization scheme** — which quantum primitive (if any) could accelerate it, the estimated
speedup after honest input/output accounting, prerequisites, obstacles, and novelty — plus
an independent review of that scheme before it's accepted.

## Pipeline

```
classical algorithm
   │
   ▼  Agent 1 · Structure Analyst   (4.1)  decompose: paradigm, bottleneck, features, barriers
   ▼  Agent 2 · Quantum Pattern Matcher (4.2)  score each primitive vs the knowledge base (3.1–3.3)
   ▼  Agent 3 · Scheme Generator    (4.3)  concrete scheme + speedup + I/O accounting + novelty
   ▼  Agent 4 · Independent Reviewer (4.4)  audits the scheme for internal consistency and
   ▼                                        ignored barriers before it's accepted
   ▼
candidate scheme  (+ structured JSON, + Markdown report)
```

Agents pass structured JSON. The orchestrator supports **iterative refinement** (up to 3
rounds total, shared across both triggers):

- **Agent 2 → Agent 1**: if the matcher is low-confidence with an open gap analysis, Agent 1
  re-analyzes the structure with a hint, then Agent 2 re-runs.
- **Agent 4 → Agent 2**: if the independent reviewer judges Agent 3's scheme "unsound",
  Agent 2 re-runs with the reviewer's critique as a hint (Agent 1's structural report is
  reused, not recomputed), then Agent 3 and Agent 4 re-run.

## Knowledge base

`knowledge_base.py` encodes the proposal's primitive taxonomy + structural prerequisites
(3.1–3.2) and the known quantization barriers (3.3). Agent 2 reasons **only** against this
explicit, auditable rule set — every verdict must cite a prerequisite or barrier.

## Quick start

```bash
pip install -r requirements.txt      # only needed for real backends

# Easiest: one command. Uses Claude if ANTHROPIC_API_KEY is set, else mock.
export ANTHROPIC_API_KEY=sk-ant-...
./run_claude.sh

# Or run pieces manually. With no key set it auto-runs mock (no key needed):
python -m quantummind.run --all          # full pipeline on the test set
python -m quantummind.run --eval         # Layer-1 evaluation (single sample per question)
python -m quantummind.run --eval --k 3   # evaluation by majority vote over 3 runs each

# Repeated-sampling tools (see Evaluation below for why):
python -m quantummind.consistency_check --algo-name "<exact name>" --n 8
python -m quantummind.exploration_consistency --n 2

# Self-critique calibration (offline, over archived runs -- no pipeline re-runs):
python -m quantummind.self_critique --batch        # critique every archived real run
python -m quantummind.self_critique --injection    # known-error calibration case

# Discovery funnel, Stage 1 (gray-zone candidate pool -> triaged survivors):
python -m quantummind.screen --estimate            # projected cost, runs nothing
python -m quantummind.screen --limit 5             # pilot batch (resumable)

# Force a specific backend/model:
QM_BACKEND=anthropic QM_MODEL=claude-sonnet-4-6 python -m quantummind.run --all
QM_BACKEND=openai    QM_MODEL=gpt-4o            python -m quantummind.run --all
```
Backend selection: explicit `QM_BACKEND` wins; otherwise Claude if `ANTHROPIC_API_KEY`
is present; otherwise mock. Real-backend outputs land in `outputs/`; the mock backend
writes ONLY under `outputs/mock/` (`paths.py`), so placeholder runs can never overwrite
real experiment records -- outputs/ is not version-controlled, and two past mock runs
destroyed real archives by sharing paths.

Real backends default to a 120s per-request timeout (override with `QM_TIMEOUT=<seconds>`)
so a dropped connection raises instead of hanging the run indefinitely. The repeated-run
tools retry failed calls with backoff and are **resumable**: completed runs are cached on
disk, so re-running the same command after a crash continues where it stopped (`--fresh`
forces a full re-run).

## Test set

`algorithms.py` holds 28 questions in two groups:

- **16 labeled** — known ground truth. Positives covering each primitive (search→Grover,
  factoring/discrete log→QFT, element distinctness→quantum walk, Monte Carlo/counting→
  amplitude estimation, aggregate-output linear system→HHL), plain negatives, and
  **5 hard negatives**: traps that superficially match a primitive but where readout,
  exploitable classical structure, or sequential dependency voids the speedup.
- **12 exploratory** — no fixed ground truth (`known_label.primitive: "unknown"`); open
  problems, subtle contrasts, and hype-prone frontier cases. Judged on reasoning quality
  and honesty, not correctness.

## Evaluation (Layer 1, proposal 5.1)

`evaluate.py` runs the pipeline once per question; `evaluate_consistency.py` (or
`run.py --eval --k N`) runs each question K independent times and scores by **majority
vote**, also reporting how often the K runs agree. The two groups are scored separately:
labeled questions produce `labeled_accuracy` + hard-negative tracking; exploratory
questions are reported unscored. Full Agent 1–4 reasoning for every run is saved under
`outputs/` for post-hoc analysis.

Findings from real-model runs (claude-sonnet-4-6, temperature 0.2) — see
[docs/consistency_experiment.md](docs/consistency_experiment.md) and
[docs/exploration_experiment.md](docs/exploration_experiment.md):

- Labeled majority-vote accuracy 15/16 at K=2; all 5 hard negatives handled every time.
- **A single sample is not reliable**: one labeled question (graph connectivity) is
  reproducibly unstable across independent runs — prefer `--k 2` or higher for any
  real-model evaluation.
- High confidence is **not** a reliability signal by itself: the exploratory questions
  get stable, confident answers despite having no ground truth to check against.

> **Caveat baked into the code:** the known cases are textbook and saturate LLM training
> data, so raw accuracy mostly measures retrieval, not reasoning. Treat Layer 1 as a sanity
> check. Real evidence needs novel cases (no ground truth) + expert review (Layer 3).

## Files

| file | role |
|---|---|
| `knowledge_base.py` | primitives, prerequisites, barriers (3.1–3.3) |
| `agents.py` | the four agent prompts + I/O contracts (4.1–4.4) |
| `orchestrator.py` | pipeline + iterative refinement (two bounce-back triggers) |
| `algorithms.py` | test set: 16 labeled (incl. 5 hard negatives) + 12 exploratory |
| `evaluate.py` | Layer-1 evaluation, single sample per question |
| `evaluate_consistency.py` | Layer-1 evaluation, K samples + majority vote |
| `consistency_check.py` | rerun one question N times (shared retry/resume helper) |
| `exploration_consistency.py` | batch consistency runner for the 8 newest exploratory questions |
| `self_critique.py` | post-hoc "where would I be wrong" auditor + offline calibration runner |
| `known_results.py` | known quantum-speedup results + dequantizations (novelty filter) |
| `candidate_pool.py` | gray-zone candidate algorithms (discovery-funnel input, draft) |
| `screen.py` | Stage-1 screening runner: pipeline + self-critique + triage + cost estimator |
| `paths.py` | output-path isolation (mock writes under `outputs/mock/` only) |
| `llm_client.py` | model-agnostic client (mock / anthropic / openai) |
| `mock_brain.py` | deterministic placeholder so it runs without a key |
| `run.py` | CLI |
| `docs/` | experiment writeups (consistency, exploration) |

## Next steps (not yet built)

- **Symmetric review**: Agent 4 currently only catches over-claimed speedups; extending it
  to flag over-conservative "none" verdicts (the graph-connectivity failure mode) is in
  progress.
- **Expert review (Layer 3)** of the two stable "has speedup" exploratory verdicts
  (high-dimensional NNS → Grover; MCTS → amplitude-estimation rollout oracle).
- Add a **functional-correctness check** on tiny instances (noiseless simulator) so Agent 3
  schemes are sanity-checked, not just asserted.
- Parallelize the repeated-run tools if larger K becomes routine.
