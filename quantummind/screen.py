"""
Stage-1 screening: run the full pipeline + self-critique over the gray-zone
candidate pool, then triage.

The funnel logic (expert time is the scarce resource):

  candidate pool (candidate_pool.py)
      |  full pipeline (Agents 1-4) + self-critique + known-results match
      v
  triage (three tiers -- calibrated against the 2026-07-09 pilot, where
  "fragile none => direct survivor" passed 4/5 candidates and compressed nothing):
    ADVANCE  recommendation is not "none" (claimed speedup) -> Stage 2 directly
    ESCALATE "none" but self-critique rates it FRAGILE -> cheap K-vote recheck
             first (the documented failure mode says real speedups hide in
             over-conservative nones, but fragile fires too often to admit
             candidates outright)
    CUT      otherwise (moderate/robust "none")
  plus a REDISCOVERY flag when the scheme keyword-matches a known result --
  rediscoveries are calibration evidence, not expert-facing findings.

Always start with --estimate (prints projected calls/cost, runs nothing):

  python -m quantummind.screen --estimate
  python -m quantummind.screen --limit 5          # pilot batch
  python -m quantummind.screen                    # full pool (resumable)

Writes under <outputs_root>/screening/ -- mock output is isolated in
outputs/mock/ automatically (paths.py).
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time

from .consistency_check import run_pipeline_once, _slug
from .known_results import match_known_results
from .llm_client import LLMClient
from .paths import outputs_root
from .pools import DEFAULT_POOL, get_pool
from .self_critique import run_self_critique

# --- cost model (rough, stated assumptions; verify against the first pilot) ----
# Per candidate: ~4 pipeline calls (1 refinement round in ~20% of cases adds ~3),
# plus 1 self-critique call. Token averages from the K=2 experiment runs.
EST_CALLS_PER_CANDIDATE = 5.6
EST_INPUT_TOKENS_PER_CANDIDATE = 15_000
EST_OUTPUT_TOKENS_PER_CANDIDATE = 3_500
EST_USD_PER_M_INPUT = 3.0     # claude-sonnet pricing at time of writing
EST_USD_PER_M_OUTPUT = 15.0
EST_MINUTES_PER_CANDIDATE = 2.5  # observed ~1.8 min/pipeline-run + critique + margin


def estimate(n: int) -> None:
    usd = (n * EST_INPUT_TOKENS_PER_CANDIDATE * EST_USD_PER_M_INPUT
           + n * EST_OUTPUT_TOKENS_PER_CANDIDATE * EST_USD_PER_M_OUTPUT) / 1e6
    print(f"Candidates:            {n}")
    print(f"Projected LLM calls:   ~{int(n * EST_CALLS_PER_CANDIDATE)}")
    print(f"Projected tokens:      ~{n * EST_INPUT_TOKENS_PER_CANDIDATE / 1000:.0f}k in / "
          f"~{n * EST_OUTPUT_TOKENS_PER_CANDIDATE / 1000:.0f}k out")
    print(f"Projected cost:        ~${usd:.2f}  (Sonnet, ${EST_USD_PER_M_INPUT}/M in, "
          f"${EST_USD_PER_M_OUTPUT}/M out)")
    print(f"Projected wall clock:  ~{n * EST_MINUTES_PER_CANDIDATE / 60:.1f} h sequential")
    print("\nNote: the ~$ figure is an UPPER bound -- it ignores prompt caching. The "
          "knowledge-base system prompt (~1.6k tokens) is cached, so its reuse across "
          "Agent 2 / Agent 4 / self-critique calls bills at ~0.1x after the first write.")
    print("Assumptions are coded at the top of screen.py; recalibrate them against a "
          "--limit 5 pilot before trusting the full-pool figure.")


def triage_entry(record: dict, critique: dict, candidate: dict) -> dict:
    recommendation = (record.get("matching", {}).get("recommendation") or "none").lower()
    fragility = critique.get("fragility")
    if recommendation != "none":
        tier = "advance"
    elif fragility == "fragile":
        tier = "escalate"
    else:
        tier = "cut"

    scheme_text = json.dumps(record.get("scheme", {}))
    novelty_hits = match_known_results(
        f"{candidate['name']} {candidate['description']} {scheme_text}")
    rediscovery_risk = bool(novelty_hits
                            and novelty_hits[0]["status"] in ("proven", "conditional")
                            and recommendation != "none")

    scope = record.get("scheme", {}).get("speedup_scope")
    top_hyp = min(critique.get("failure_hypotheses") or [{}],
                  key=lambda h: h.get("rank", 99))
    return {
        "name": candidate["name"],
        "domain": candidate["domain"],
        "recommendation": recommendation,
        "speedup_scope": scope,
        "confidence": record.get("matching", {}).get("overall_confidence"),
        "review_verdict": record.get("review", {}).get("verdict"),
        "fragility": fragility,
        "top_doubt_kb_id": top_hyp.get("kb_id"),
        "expert_check": top_hyp.get("expert_check"),
        "tier": tier,
        # A sub-step-only advance is a real result but must not be read as a
        # whole-algorithm speedup -- surface it so dossiers scope it honestly.
        "sub_step_only": recommendation != "none" and scope == "sub_step",
        "rediscovery_risk": rediscovery_risk,
        "known_results_matches": novelty_hits,
        "rounds_used": record.get("rounds_used"),
    }


TIER_ORDER = {"advance": 0, "escalate": 1, "cut": 2}


def _print_triage(entries: list[dict]) -> None:
    counts = {t: sum(1 for e in entries if e["tier"] == t) for t in TIER_ORDER}
    print(f"\n===== TRIAGE: {counts['advance']} advance, {counts['escalate']} escalate, "
          f"{counts['cut']} cut, {len(entries)} screened =====")
    print(f"\n{'candidate':<48} {'rec':<22} {'fragility':<10} {'tier':<10} {'flags'}")
    print("-" * 116)
    for e in sorted(entries, key=lambda x: (TIER_ORDER[x["tier"]], x["name"])):
        flags = []
        if e.get("sub_step_only"):
            flags.append("sub-step only")
        if e["rediscovery_risk"]:
            flags.append(f"rediscovery? ({e['known_results_matches'][0]['id']})")
        print(f"{e['name'][:46]:<48} {e['recommendation'][:20]:<22} "
              f"{str(e['fragility']):<10} {e['tier'].upper():<10} {', '.join(flags)}")


def preflight(candidates: list[dict]) -> None:
    """Zero-cost pre-spend triage: for each candidate show its nearest known
    quantum results and a coldness signal, WITHOUT running the pipeline. A strong
    match to a proven/conditional result means the domain is probably already
    studied (likely rediscovery); no strong match means the pipeline's verdict,
    whatever it is, would at least be landing in genuinely unswept territory.
    Use it to prune a pool before spending, and to set expectations."""
    warm, cold = [], []
    print(f"{'candidate':<50} {'signal':<6} nearest known result")
    print("-" * 108)
    for c in sorted(candidates, key=lambda x: x["domain"]):
        hits = match_known_results(f"{c['name']} {c['description']}")
        strong = [h for h in hits if h["status"] in ("proven", "conditional")]
        signal = "WARM" if strong else "cold"
        (warm if strong else cold).append(c["name"])
        top = (strong or hits or [{}])[0]
        note = f"{top.get('id', '—')} ({top.get('status', 'no match')})" if top else "no match"
        print(f"{c['name'][:48]:<50} {signal:<6} {note}")
    print(f"\n{len(cold)} cold (no strong known match) / {len(warm)} warm "
          f"(already resembles a proven/conditional result).")
    print("WARM candidates are likely rediscoveries -- consider pruning before a paid run; "
          "the funnel will still route them to the calibration appendix if run.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage-1 screening over the candidate pool.")
    ap.add_argument("--preflight", action="store_true",
                    help="zero-cost: show nearest known results + coldness per candidate, run nothing")
    ap.add_argument("--estimate", action="store_true",
                    help="print projected calls/cost and exit without running anything")
    ap.add_argument("--limit", type=int, default=0, help="screen only the first N candidates")
    ap.add_argument("--domain", help="screen only candidates from this domain")
    ap.add_argument("--pool", default=DEFAULT_POOL,
                    help="candidate pool to screen (v1 = gray zone, v2 = cold domains)")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore cached results and re-run")
    ap.add_argument("--anchoring", action="store_true",
                    help="ground Agent 3 novelty in nearest known_results (opt-in)")
    args = ap.parse_args()

    candidates = get_pool(args.pool)
    if args.domain:
        candidates = [c for c in candidates if c["domain"] == args.domain]
    if args.limit:
        candidates = candidates[:args.limit]

    if args.preflight:
        print(f"Pool: {args.pool} ({len(candidates)} candidates) -- PREFLIGHT (no pipeline run)\n")
        preflight(candidates)
        return 0

    if args.estimate:
        print(f"Pool: {args.pool}")
        estimate(len(candidates))
        return 0

    client = LLMClient()
    print(f"Backend: {client.backend} / model: {client.model} / pool: {args.pool}")
    if client.backend == "mock":
        print("WARNING: mock backend -- screening output is placeholder, plumbing only.")
    screen_dir = os.path.join(outputs_root(client.backend), "screening", args.pool)
    os.makedirs(screen_dir, exist_ok=True)

    entries = []
    t0 = time.time()
    for i, cand in enumerate(candidates, 1):
        cand_dir = os.path.join(screen_dir, _slug(cand["name"]))
        os.makedirs(cand_dir, exist_ok=True)
        record_path = os.path.join(cand_dir, "record.json")
        critique_path = os.path.join(cand_dir, "critique.json")

        record, err, cached = run_pipeline_once(cand, client, record_path,
                                                fresh=args.fresh, anchoring=args.anchoring)
        if err is not None:
            print(f"[{i}/{len(candidates)}] {cand['name'][:45]}: FAILED -- {err}")
            entries.append({"name": cand["name"], "domain": cand["domain"],
                            "error": err, "tier": "cut", "rediscovery_risk": False})
            continue

        if os.path.exists(critique_path) and not args.fresh:
            with open(critique_path) as f:
                critique = json.load(f)
        else:
            critique = run_self_critique(record, client)
            with open(critique_path, "w") as f:
                json.dump(critique, f, indent=2)

        entry = triage_entry(record, critique, cand)
        entries.append(entry)
        elapsed = (time.time() - t0) / 60
        print(f"[{i}/{len(candidates)}] {cand['name'][:45]:<47} "
              f"rec={entry['recommendation']:<20} fragility={entry['fragility']} "
              f"{entry['tier'].upper()}"
              f"{' (cached)' if cached else ''} ({elapsed:.1f} min)")

    _print_triage([e for e in entries if "error" not in e])
    summary_path = os.path.join(screen_dir, "screening_summary.json")
    with open(summary_path, "w") as f:
        json.dump({"pool": args.pool, "backend": client.backend,
                   "model": client.model, "entries": entries}, f, indent=2)
    print(f"\nSummary written to {summary_path}")
    failed = sum(1 for e in entries if "error" in e)
    if failed:
        print(f"WARNING: {failed} candidate(s) failed -- re-run the same command to "
              f"fill them in (completed candidates are cached).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
