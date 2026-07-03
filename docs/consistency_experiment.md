# Consistency experiment: K=2 repeated-sample evaluation

## Motivation

`evaluate.py` scores each algorithm on a single sample. An ad-hoc check on
"Graph connectivity: are two vertices connected?" showed that single sample
isn't reliable: one `evaluate.py` run recommended `none`, then eight
independent reruns of the exact same question all recommended `quantum_walk`.
That raises the obvious question: is a single-shot evaluation reporting a
stable judgment, or a fluke that happened to land in the report?

This experiment scores every algorithm in the test set by **majority vote
over K=2 independent full-pipeline runs**, and reports how often the K runs
actually agree with each other -- not just whether the majority answer is
correct.

## Setup

| | |
|---|---|
| Script | `python3 -m quantummind.evaluate_consistency --k 2` |
| K | 2 independent full-pipeline runs per algorithm |
| Test set | 20 algorithms (`quantummind/algorithms.py`) |
| Backend / model | `anthropic` / `claude-sonnet-4-6` |
| Temperature | `0.2` (the `LLMClient` default, unchanged from a normal `evaluate.py` run) |
| Per-run reasoning | full Agent 1-4 output saved to `outputs/consistency_eval/<algorithm>/run_{1,2}.json` |
| Aggregate summary | `outputs/consistency_evaluation.json` |
| Wall-clock time | ~72 minutes for 40 independent pipeline runs (algorithms that trigger the 3-round refinement loop take proportionally longer per run) |

K=3 across the full test set was estimated in advance at roughly $5-6.5 and
was not run -- see Conclusion below.

## Aggregate results

- **Majority-vote accuracy: 0.75** (15/20; 15/16 = 93.75% excluding the 4
  open-ended "unknown"-label questions, which can never literally match
  since the system never outputs the string `"unknown"`)
- **Fully-consistent fraction: 0.95** (19/20 algorithms gave the identical
  answer on both runs)

## Full table

| Algorithm | Majority answer | Consistency | Correct | Confidence dist |
|---|---|---|---|---|
| Linear search in an unsorted list | grover | 2/2 | yes | high×2 |
| Integer factorization (trial division) | qft | 2/2 | yes | high×2 |
| Comparison-based sorting (merge sort) | none | 2/2 | yes | high×2 |
| Solve a sparse linear system, return the full solution vector | none | 2/2 | yes | high×2 |
| All-pairs shortest paths, return the full distance matrix | none | 2/2 | yes | high×2 |
| Monte Carlo expectation estimation | amplitude_estimation | 2/2 | yes | high×2 |
| Find the minimum in an unsorted list | grover | 2/2 | yes | high×1, medium×1 |
| Element distinctness | quantum_walk | 2/2 | yes | high×2 |
| Counting solutions to an unstructured predicate | amplitude_estimation | 2/2 | yes | high×2 |
| Discrete logarithm problem | qft | 2/2 | yes | high×2 |
| **Graph connectivity: are two vertices connected?** | **none** | **⚠️ 1/2** | **no** | high×1, medium×1 |
| Hamiltonian simulation of a quantum system | none | 2/2 | yes | high×2 |
| Search a SORTED list for a target | none | 2/2 | yes | high×2 |
| Return ALL elements satisfying a predicate | none | 2/2 | yes | high×2 |
| Solve a sparse linear system, return only ⟨x\|M\|x⟩ | hhl | 2/2 | yes | high×2 |
| Strongly sequential iterative recurrence | none | 2/2 | yes | high×2 |
| 0/1 Knapsack via dynamic programming *(unknown-label)* | none | 2/2 | no* | high×2 |
| Exact string / pattern matching *(unknown-label)* | none | 2/2 | no* | high×2 |
| Low-rank recommendation from a preference matrix *(unknown-label)* | none | 2/2 | no* | high×2 |
| Max-Cut combinatorial optimization *(unknown-label)* | vqa_qaoa | 2/2 | no* | medium×2 |

\* These 4 questions have no fixed ground truth (`known_label.primitive` is
literally `"unknown"` in `algorithms.py`, by design -- see `evaluate.py`'s
caveat). `correct: no` here is structurally guaranteed, not a system error.

## Findings

### 1. 19/20 fully consistent; the one swaying case is reproducibly unstable, not a one-off

"Graph connectivity: are two vertices connected?" is the only algorithm
where the two K=2 samples disagreed (`none`, then `quantum_walk`), with
`overall_confidence` also shifting (medium → high) rather than staying flat.
This is not an isolated blip: across three independent batches of sampling
on this exact question, the model's answer has never settled --

1. the original single-shot `evaluate.py` run: `none`
2. a follow-up batch of 8 independent reruns: unanimous `quantum_walk`
3. this K=2 batch: 1× `none`, 1× `quantum_walk`

Every other algorithm in the test set -- including all 4 hard negatives --
agreed across both K=2 samples. The instability is concentrated in this one
reproducible case, not spread thinly across many borderline questions.

### 2. The open-ended "unknown" questions are stably, confidently wrong -- and that's the concerning part, not the score

The four questions with no fixed ground truth (0/1 Knapsack, Exact
string/pattern matching, Low-rank recommendation, Max-Cut) each landed on
the identical answer both times, at high or medium confidence, every time.
Their `no*` in the table is expected and not meaningful by itself -- the
system can never output the literal string `"unknown"`.

What *is* meaningful: these are exactly the cases where there is no ground
truth to check the model against, and the model is just as stable and
confident here as it is on the questions it gets objectively right.
Stability and high confidence, by themselves, are not evidence of
correctness -- they show up equally in the one area we have no way to
verify. **`overall_confidence` should not be read as a reliability proxy on
its own**; it needs corroboration from majority-vote agreement (this
experiment) or ground truth, neither of which is available for genuinely
novel cases -- which is exactly the use case the project's proposal cites as
the interesting one.

## Conclusion

K=2 was judged sufficient to stop on. It already shows the instability is
concentrated in a single reproducible case (Graph connectivity) rather than
spread across many borderline questions, so a third full pass across all 20
algorithms (~$5-6.5 estimated) was judged unlikely to surface new findings
proportional to its cost.

If Agent 4's review criteria are ever extended to catch under-claimed
(false-negative) speedups -- not just over-claimed ones, which is all it
currently checks for -- Graph connectivity is the concrete, reproducible
test case to validate the fix against.
