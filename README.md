# QuantumMind — multi-agent quantum-acceleration analyzer

A faithful implementation of the QuantumMind proposal (Sections 3–5): a three-agent LLM
pipeline that takes a **classical algorithm** as input and produces a **candidate
quantization scheme** — which quantum primitive (if any) could accelerate it, the estimated
speedup after honest input/output accounting, prerequisites, obstacles, and novelty.

## Pipeline

```
classical algorithm
   │
   ▼  Agent 1 · Structure Analyst   (4.1)  decompose: paradigm, bottleneck, features, barriers
   ▼  Agent 2 · Quantum Pattern Matcher (4.2)  score each primitive vs the knowledge base (3.1–3.3)
   ▼  Agent 3 · Scheme Generator    (4.3)  concrete scheme + speedup + I/O accounting + novelty
   ▼
candidate scheme  (+ structured JSON, + Markdown report)
```

Agents pass structured JSON. The orchestrator supports **iterative refinement** (up to 3
rounds): if the matcher is low-confidence with an open gap analysis, it asks Agent 1 to
re-analyze with a hint.

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

Real backends default to a 120s per-request timeout (override with `QM_TIMEOUT=<seconds>`)
so a dropped connection raises instead of hanging the run indefinitely.

## Evaluation (Layer 1, proposal 5.1)

`evaluate.py` runs the pipeline on a labelled test set and compares the recommended
primitive to the known answer. The set mixes positives (search→Grover, factoring→Shor/QFT,
Monte Carlo→amplitude estimation), a no-go (comparison sort), and a **hard negative**: a
linear system requiring the full solution vector — superficially HHL, but the readout
problem voids the speedup. Avoiding that false positive is the honest signal.

> **Caveat baked into the code:** the known cases are textbook and saturate LLM training
> data, so raw accuracy mostly measures retrieval, not reasoning. Treat Layer 1 as a sanity
> check. Real evidence needs novel cases (no ground truth) + expert review (Layer 3).

## Files

| file | role |
|---|---|
| `knowledge_base.py` | primitives, prerequisites, barriers (3.1–3.3) |
| `agents.py` | the three agent prompts + I/O contracts (4.1–4.3) |
| `orchestrator.py` | pipeline + iterative refinement |
| `algorithms.py` | labelled test set |
| `evaluate.py` | Layer-1 evaluation harness (5.1) |
| `llm_client.py` | model-agnostic client (mock / anthropic / openai) |
| `mock_brain.py` | deterministic placeholder so it runs without a key |
| `run.py` | CLI |

## Next steps (not yet built)

- Add a **functional-correctness check** on tiny instances (noiseless simulator) so Agent 3
  schemes are sanity-checked, not just asserted.
- Grow the benchmark with more **hard negatives** to stress-test false positives.
- Layer 2 (LLM-judge consistency) and Layer 3 (expert review) harnesses.
