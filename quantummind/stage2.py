"""
Stage-2 of the discovery funnel: K-vote recheck of Stage-1 survivors.

Stage 1 (screen.py) triages on a SINGLE pipeline run plus self-critique. But the
consistency experiments showed single samples are unreliable, and calibration showed
fragile "none"s are only *suspicious*, not wrong. Stage 2 answers both cheaply:

  - ESCALATE tier (fragile "none"): run K-1 additional independent pipeline runs.
    If the majority across all K flips to a non-"none" primitive, the Stage-1 none
    was indeed over-conservative -> PROMOTE. Otherwise -> CUT (the fragile flag was
    risk-ranking, and the vote resolved it).
  - ADVANCE tier (non-"none"): same K runs as a stability check. A speedup claim
    that cannot win its own majority vote does not go into an expert dossier ->
    DEMOTE. Stable claims -> CONFIRM (novelty routing still applies downstream).

Usage:
  python -m quantummind.stage2 --estimate
  python -m quantummind.stage2                # all advance+escalate candidates
  python -m quantummind.stage2 --k 3          # total runs per candidate (default 3)

Resumable: run i lives at outputs/screening/<slug>/record_<i>.json (record.json
from Stage 1 counts as run 1). Mock output is isolated under outputs/mock/.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from collections import Counter

from .consistency_check import run_pipeline_once, _slug
from .llm_client import LLMClient
from .paths import outputs_root
from .pools import DEFAULT_POOL, get_pool
from .screen import EST_USD_PER_M_INPUT, EST_USD_PER_M_OUTPUT

# A Stage-2 rerun is one pipeline pass (no self-critique), slightly cheaper than a
# Stage-1 candidate. Recalibrated against the observed Stage-1 run (~1.6 min each).
EST_INPUT_TOKENS_PER_RUN = 11_000
EST_OUTPUT_TOKENS_PER_RUN = 2_800
EST_MINUTES_PER_RUN = 1.5


def _stage1_tiers(screen_dir: str) -> dict[str, str]:
    path = os.path.join(screen_dir, "screening_summary.json")
    if not os.path.exists(path):
        raise SystemExit(f"No Stage-1 summary at {path} -- run screen.py first.")
    with open(path) as f:
        data = json.load(f)
    # Summary is {pool, ..., entries:[...]}; tolerate the legacy bare-list form too.
    entries = data["entries"] if isinstance(data, dict) else data
    return {e["name"]: e.get("tier", "cut") for e in entries if "error" not in e}


def vote(records: list[dict]) -> tuple[str, int, int]:
    """Majority recommendation across runs -> (answer, votes_for, total).

    Returns ('none', 0, 0) when no run completed -- e.g. every rerun failed and the
    Stage-1 record was absent -- so a candidate whose runs all error does not crash
    the whole batch with an empty Counter.
    """
    gots = [(r.get("matching", {}).get("recommendation") or "none").lower()
            for r in records]
    if not gots:
        return "none", 0, 0
    counts = Counter(gots)
    answer, n = counts.most_common(1)[0]
    return answer, n, len(gots)


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage-2 K-vote recheck of Stage-1 survivors.")
    ap.add_argument("--k", type=int, default=3,
                    help="total independent runs per candidate incl. the Stage-1 run")
    ap.add_argument("--estimate", action="store_true",
                    help="print projected cost and exit without running")
    ap.add_argument("--limit", type=int, default=0, help="recheck only the first N")
    ap.add_argument("--pool", default=DEFAULT_POOL,
                    help="which pool's Stage-1 results to recheck (must match screen --pool)")
    args = ap.parse_args()

    client = LLMClient()
    screen_dir = os.path.join(outputs_root(client.backend), "screening", args.pool)
    tiers = _stage1_tiers(screen_dir)
    names = [n for n, t in tiers.items() if t in ("advance", "escalate")]
    by_name = {c["name"]: c for c in get_pool(args.pool)}
    todo = [by_name[n] for n in names if n in by_name]
    if args.limit:
        todo = todo[:args.limit]
    extra_runs = max(args.k - 1, 0)

    if args.estimate:
        n_runs = len(todo) * extra_runs
        usd = (n_runs * EST_INPUT_TOKENS_PER_RUN * EST_USD_PER_M_INPUT
               + n_runs * EST_OUTPUT_TOKENS_PER_RUN * EST_USD_PER_M_OUTPUT) / 1e6
        print(f"Candidates to recheck: {len(todo)} "
              f"({sum(1 for n in names if tiers[n]=='advance')} advance, "
              f"{sum(1 for n in names if tiers[n]=='escalate')} escalate)")
        print(f"Additional runs:       {n_runs} (K={args.k}, Stage-1 run counts as run 1)")
        print(f"Projected cost:        ~${usd:.2f}")
        print(f"Projected wall clock:  ~{n_runs * EST_MINUTES_PER_RUN / 60:.1f} h sequential")
        return 0

    print(f"Backend: {client.backend} / model: {client.model}")
    if client.backend == "mock":
        print("WARNING: mock backend -- plumbing only.")

    results = []
    out_path = os.path.join(screen_dir, "stage2_summary.json")
    t0 = time.time()
    try:
        for i, cand in enumerate(todo, 1):
            cand_dir = os.path.join(screen_dir, _slug(cand["name"]))
            records = []
            failed = 0
            for run_i in range(1, args.k + 1):
                # Stage-1 record is run 1; extra runs get their own files.
                path = (os.path.join(cand_dir, "record.json") if run_i == 1
                        else os.path.join(cand_dir, f"record_{run_i}.json"))
                rec, err, _cached = run_pipeline_once(cand, client, path)
                if err is not None:
                    failed += 1
                    print(f"  {cand['name'][:40]}: run {run_i} FAILED -- {err}")
                    continue
                records.append(rec)

            answer, n_votes, n_total = vote(records)
            stage1_tier = tiers[cand["name"]]
            if stage1_tier == "escalate":
                outcome = "PROMOTE" if answer != "none" else "cut"
            else:  # advance
                outcome = "CONFIRM" if answer != "none" else "DEMOTE"
            results.append({
                "name": cand["name"], "domain": cand["domain"],
                "stage1_tier": stage1_tier,
                "votes": dict(Counter((r.get("matching", {}).get("recommendation") or
                                       "none").lower() for r in records)),
                "majority": answer, "majority_count": n_votes, "k_completed": n_total,
                "failed_runs": failed, "stage2_outcome": outcome,
            })
            elapsed = (time.time() - t0) / 60
            print(f"[{i}/{len(todo)}] {cand['name'][:44]:<46} {stage1_tier:<9} "
                  f"majority={answer:<22} {n_votes}/{n_total}  -> {outcome} "
                  f"({elapsed:.1f} min)")
    finally:
        # Always persist what completed -- a crash or interrupt mid-batch must not
        # lose the candidates already rechecked (they cost real API calls).
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    print(f"\n===== STAGE 2 (K={args.k}) =====")
    for label in ("CONFIRM", "PROMOTE", "DEMOTE", "cut"):
        group = [r for r in results if r["stage2_outcome"] == label]
        print(f"\n--- {label}: {len(group)} ---")
        for r in group:
            print(f"  {r['name'][:50]:<52} {r['majority']:<22} "
                  f"{r['majority_count']}/{r['k_completed']}")

    print(f"\nSummary written to {out_path}")
    n_failed = sum(r["failed_runs"] for r in results)
    if n_failed:
        print(f"WARNING: {n_failed} run(s) failed -- re-run to fill in (cached runs skip).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
