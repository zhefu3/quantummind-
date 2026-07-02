# QuantumMind — multi-agent quantum-acceleration analyzer

A faithful implementation of the QuantumMind proposal (Sections 3–5): a four-agent LLM
pipeline that takes a **classical algorithm** as input and produces a **candidate
quantization scheme** — which quantum primitive (if any) could accelerate it, the estimated
speedup after honest input/output accounting, prerequisites, obstacles, and novelty — plus an
independent review of that scheme before it's accepted.

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
rounds total, shared across both triggers below):

- **Agent 2 → Agent 1**: if the matcher is low-confidence with an open gap analysis, Agent 1
  re-analyzes the structure with a hint, then Agent 2 re-runs.
- **Agent 4 → Agent 2**: if the independent reviewer judges Agent 3's scheme "unsound" (e.g.
  the stated speedup contradicts the I/O accounting, or a known barrier was quietly ignored),
  Agent 2 re-runs with the reviewer's critique as a hint — reusing Agent 1's structural report
  rather than recomputing it — then Agent 3 and Agent 4 re-run. This exists because Agent 3's
  output previously went straight into the report unreviewed, and Agent 2 rarely self-reports
  low confidence in practice, so this was the main failure mode the refinement loop missed.

Either trigger can fire in the same run; the shared round counter keeps the total bounded at 3
even if both fire.

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
python -m quantummind.run --all      # full pipeline on the test set
python -m quantummind.run --eval     # Layer-1 evaluation

# Force a specific backend/model:
QM_BACKEND=anthropic QM_MODEL=claude-sonnet-4-6 python -m quantummind.run --all
QM_BACKEND=openai    QM_MODEL=gpt-4o            python -m quantummind.run --all
```
Backend selection: explicit `QM_BACKEND` wins; otherwise Claude if `ANTHROPIC_API_KEY`
is present; otherwise mock. Outputs land in `outputs/`.

## Evaluation (Layer 1, proposal 5.1)

`evaluate.py` runs the pipeline on a labelled test set (6 algorithms) and compares the
recommended primitive to the known answer. The set mixes positives (search→Grover,
factoring→Shor/QFT, Monte Carlo→amplitude estimation), a no-go (comparison sort), and two
**hard negatives** — cases that superficially match a primitive but where an output-dense
result makes readout void the speedup:
- a sparse linear system requiring the full solution vector (looks like HHL)
- all-pairs shortest paths requiring the full V×V distance matrix (looks like quantum walk)

Avoiding those false positives is the honest signal — and both are exactly the shape of case
Agent 4 is meant to catch: in mock mode both trip the reviewer to "unsound" and exhaust the
3-round refinement budget rather than being rubber-stamped.

> **Caveat baked into the code:** the known cases are textbook and saturate LLM training
> data, so raw accuracy mostly measures retrieval, not reasoning. Treat Layer 1 as a sanity
> check. Real evidence needs novel cases (no ground truth) + expert review (Layer 3).

## Files

| file | role |
|---|---|
| `knowledge_base.py` | primitives, prerequisites, barriers (3.1–3.3) |
| `agents.py` | the four agent prompts + I/O contracts (4.1–4.4) |
| `orchestrator.py` | pipeline + iterative refinement (two bounce-back triggers) |
| `algorithms.py` | labelled test set (6 algorithms, incl. 2 hard negatives) |
| `evaluate.py` | Layer-1 evaluation harness (5.1) |
| `llm_client.py` | model-agnostic client (mock / anthropic / openai) |
| `mock_brain.py` | deterministic placeholder so it runs without a key |
| `run.py` | CLI |

## Next steps (not yet built)

- Add a **functional-correctness check** on tiny instances (noiseless simulator) so Agent 3
  schemes are sanity-checked, not just asserted.
- Grow the benchmark with more **hard negatives** to stress-test false positives.
- Layer 2 (LLM-judge consistency) and Layer 3 (expert review) harnesses.
