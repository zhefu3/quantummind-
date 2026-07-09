# Discovery funnel: first full Stage-1 run

**Date:** 2026-07-09/10 (overnight) · **Backend:** anthropic / claude-sonnet-4-6,
temperature 0.2 · **Input:** all 49 gray-zone candidates (`candidate_pool.py`)
**Cost:** ~79 min wall clock, ≈ $4.3 (cost model predicted 2.5 min/candidate;
observed ~1.6 — model updated by observation, assumptions in `screen.py`).

Per candidate: full Agent 1–4 pipeline + self-critique + known-results keyword
match + three-tier triage. Full records in `outputs/screening/<candidate>/`.

## Headline

**7 ADVANCE · 26 ESCALATE · 16 CUT**

## The 7 advances (non-"none" verdicts)

| candidate | verdict | novelty filter |
|---|---|---|
| Adaptive numerical quadrature | amplitude_estimation | rediscovery: Montanaro 2015 |
| Approximate matching, k mismatches | grover | rediscovery: Ramesh-Vinay 2000 |
| Implicit-matrix trace estimation | amplitude_estimation | rediscovery: Montanaro 2015 family |
| Perceptron training | grover | rediscovery: Wiebe-Kapoor-Svore 2016 * |
| LOO error of 1-NN classifier | grover | rediscovery: Wiebe-Kapoor-Svore 2015 * |
| Condition number estimation | amplitude_estimation | flagged, but to a WRONG entry (keyword noise) — needs manual check |
| **Triangle counting (sparse graph)** | **amplitude_estimation** | **unflagged — the one candidate for a literature deep-check** |

\* Caught only AFTER this run exposed two gaps in the known-results library
(quantum perceptron and quantum nearest-neighbor entries were missing; added,
re-triaged from cache).

## Honest reading

1. **The funnel behaves as designed.** Blind candidates with real (known)
   quantum speedups were recommended by the pipeline and then routed away from
   expert attention by the novelty filter. Six independent blind reproductions
   of known results is calibration evidence for the pipeline's positive
   verdicts — stronger than the labeled benchmark, since these were not
   phrased as quantum questions at all.
2. **No discovery claim.** The single unflagged advance (triangle counting via
   amplitude estimation over edge-pair predicates) is *adjacent to* known
   quantum triangle-detection and approximate-counting work; the honest prior
   is that a literature check finds it known or near-known. It is the right
   KIND of output to hand an expert, not a finding.
3. **Library completeness is the Stage-3 bottleneck.** Two of six
   rediscoveries were initially missed for lack of an entry, and one flag
   pointed at the wrong entry (keyword matcher is a recall device, not a
   judge). Every advance needs a manual/LLM literature pass before any expert
   dossier — the keyword filter only sets the default routing.
4. **Escalation pressure confirms the calibration finding at scale.** 26/49
   (53%) landed in ESCALATE (fragile "none"), matching the 52% fragile rate
   observed in calibration. Stage 2 (K-vote recheck of escalations, ~$5 for
   K=+2) is the designed next step; its budget/cutoff should follow the
   advisor's decision on expert bandwidth.
5. **The 16 cuts look right on spot-check:** output-dense transforms (BWT,
   FFT products), already-optimal linear scans (median selection), and
   sequential-by-construction algorithms (Gale-Shapley) — all cut on moderate
   "none" with correctly cited barriers.

## Next steps

- Stage 2: K=+2 majority-vote recheck of the 26 escalations (needs a small
  runner over cached candidates; ~$5, ~90 min).
- Literature deep-check of triangle counting + manual check of the condition
  number scheme, before either is described as anything but "pending".
- Advisor review of the pool (domains to add/drop) and expert bandwidth
  (sets the final dossier count).
