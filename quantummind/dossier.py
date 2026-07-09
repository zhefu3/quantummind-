"""
Expert dossier generator (Layer 3 deliverable).

The funnel's payoff is that an expert can verify a candidate cheaply. That only
happens if the candidate arrives as a self-contained brief, not scattered JSON.
This module assembles, per surviving candidate, exactly what a quantum-computing
expert needs to accept or kill it in minutes:

  - the claim, HONESTLY SCOPED (primitive + speedup_scope + net estimate; a
    sub-step-only speedup is labelled as such, never dressed up as whole-algorithm);
  - the pipeline's own reliability signals (review verdict, K-vote agreement,
    self-critique fragility);
  - the single most efficient thing to check first (the self-critique's expert_check);
  - novelty: which known results this resembles, with references;
  - the full Agent 1-4 reasoning chain;
  - a short verification checklist.

Crucially it SEPARATES expert-facing candidates from rediscoveries. Rediscoveries
are not sent to an expert -- they go in a calibration appendix ("the system
independently reproduced these known results"), which is evidence FOR the
instrument, not a demand on expert time.

Pure file processing over outputs/screening/<pool>/ -- no model calls, no cost.

  python -m quantummind.dossier --pool v1          # index + one dossier per survivor
  python -m quantummind.dossier --pool v1 --name "Triangle counting in a sparse graph"
"""

from __future__ import annotations
import argparse
import json
import os
import sys

from .consistency_check import _slug
from .known_results import KNOWN_RESULTS, match_known_results
from .paths import REAL_OUT_DIR
from .pools import get_pool

_KR_BY_ID = {k["id"]: k for k in KNOWN_RESULTS}


def _resolve(entry: dict, screen_dir: str, stage2_entry: dict | None,
             description: str) -> dict:
    """Resolve a survivor to its EFFECTIVE verdict + novelty.

    A Stage-1 summary entry reflects a single run. When Stage 2 PROMOTEd a
    candidate (a fragile 'none' that flipped on the K-vote), the real verdict lives
    in the majority rerun, and novelty must be re-matched against THAT scheme --
    otherwise the dossier reports the stale 'none'. Returns the record to display,
    the effective recommendation, and freshly matched known-results.
    """
    cand_dir = os.path.join(screen_dir, _slug(entry["name"]))
    stage1 = _load_json(os.path.join(cand_dir, "record.json"))

    record = stage1
    if stage2_entry and stage2_entry.get("stage2_outcome") == "PROMOTE":
        majority = stage2_entry.get("majority")
        for fn in ("record.json", "record_2.json", "record_3.json"):
            r = _load_json(os.path.join(cand_dir, fn))
            if r and (r.get("matching", {}).get("recommendation") or "none").lower() == majority:
                record = r
                break

    rec = (record or {}).get("matching", {}).get("recommendation", entry.get("recommendation")) \
        if record else entry.get("recommendation")
    rec = (rec or "none").lower()
    scheme_text = json.dumps((record or {}).get("scheme", {}))
    novelty = match_known_results(f"{entry['name']} {description} {scheme_text}")
    rediscovery = bool(rec != "none" and novelty
                       and novelty[0]["status"] in ("proven", "conditional"))
    return {"record": record, "recommendation": rec,
            "novelty": novelty, "rediscovery_risk": rediscovery}


def _load_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def surfaced(entry: dict, stage2_entry: dict | None) -> bool:
    """Whether a candidate reaches an expert. Stage-2 outcome is authoritative when
    present -- CONFIRM/PROMOTE surface, DEMOTE/cut do not (a demoted advance FAILED
    its K-vote). Without a Stage-2 entry, fall back to the Stage-1 tier."""
    if stage2_entry is not None:
        return stage2_entry.get("stage2_outcome") in ("PROMOTE", "CONFIRM")
    return entry.get("tier") == "advance"


def _load_summary(screen_dir: str) -> dict:
    path = os.path.join(screen_dir, "screening_summary.json")
    if not os.path.exists(path):
        raise SystemExit(f"No Stage-1 summary at {path} -- run screen.py first.")
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {"entries": data, "pool": "?"}


def _load_stage2(screen_dir: str) -> dict:
    path = os.path.join(screen_dir, "stage2_summary.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return {e["name"]: e for e in json.load(f)}


def _scope_line(scope: str | None, estimate: str | None) -> str:
    labels = {
        "full_algorithm": "**whole-algorithm** speedup",
        "sub_step": "**sub-step only** -- the net gain is bounded by that step's share of "
                    "runtime; this is NOT a whole-algorithm speedup",
        "conditional": "**conditional** -- holds only under strict I/O conditions "
                       "(aggregate readout / efficient loading)",
        "none": "no net speedup",
    }
    scope_txt = labels.get(scope, f"scope: {scope or 'unstated'}")
    return f"{scope_txt}. Net estimate: {estimate or 'n/a'}"


def _novelty_block(hits: list[dict]) -> str:
    if not hits:
        return ("- No entry in the known-results library matched this scheme. That is a "
                "recall signal only -- it means a manual/expert literature check is "
                "REQUIRED before treating this as unexplored, not that it is novel.\n")
    lines = []
    for h in hits:
        kr = _KR_BY_ID.get(h["id"], {})
        ref = kr.get("reference", "?")
        status = h.get("status", kr.get("status", "?"))
        lines.append(f"- **{h.get('problem', h['id'])}** — status *{status}* — {ref}")
    return "\n".join(lines) + "\n"


def _reasoning_chain(record: dict) -> str:
    if not record:
        return "_(full reasoning record not found on disk)_\n"
    s = record.get("structure", {})
    m = record.get("matching", {})
    sc = record.get("scheme", {})
    rv = record.get("review", {})
    scores = "; ".join(f"{x.get('primitive')}={x.get('verdict')}"
                       for x in m.get("scores", []) if x.get("verdict") in ("high", "partial")) or "—"
    return (
        f"**Agent 1 — structure.** Paradigm: {s.get('paradigm')}. "
        f"Classical complexity: {s.get('classical_complexity')}. "
        f"Bottleneck: {s.get('bottleneck')}. "
        f"Barrier flags: {', '.join(s.get('barrier_flags', [])) or 'none'}.\n\n"
        f"**Agent 2 — match.** Recommendation `{m.get('recommendation')}` "
        f"(confidence {m.get('overall_confidence')}); high/partial scores: {scores}; "
        f"barrier hits: {', '.join(m.get('barrier_hits', [])) or 'none'}.\n\n"
        f"**Agent 3 — scheme.** {sc.get('scheme')}\n\n"
        f"  - Speedup estimate: {sc.get('speedup_estimate')} "
        f"(scope: `{sc.get('speedup_scope', 'n/a')}`)\n"
        f"  - I/O accounting: {sc.get('io_accounting')}\n"
        f"  - Obstacles: {', '.join(sc.get('obstacles', [])) or 'none'}\n"
        f"  - Novelty (self-assessed): {sc.get('novelty')}\n\n"
        f"**Agent 4 — independent review.** Verdict `{rv.get('verdict')}`. "
        f"{rv.get('reasoning', '')}\n"
    )


def build_dossier(entry: dict, resolved: dict, stage2: dict | None) -> str:
    name = entry["name"]
    record = resolved["record"]
    rec = resolved["recommendation"]
    scope = (record or {}).get("scheme", {}).get("speedup_scope") or entry.get("speedup_scope")
    est = (record or {}).get("scheme", {}).get("speedup_estimate")

    kvote = ""
    if stage2:
        kvote = (f"- **K-vote (Stage 2):** majority `{stage2.get('majority')}` "
                 f"{stage2.get('majority_count')}/{stage2.get('k_completed')} "
                 f"→ {stage2.get('stage2_outcome')}\n")

    return f"""# Expert dossier — {name}

*Domain: {entry.get('domain')} · pipeline recommendation: `{rec}`*

## Claim (honestly scoped)

**{rec}** — {_scope_line(scope, est)}

- **Independent review (Agent 4):** {entry.get('review_verdict')}
- **Self-critique fragility:** {entry.get('fragility')}
{kvote}
> A "sub-step only" or "conditional" claim is a real result but must not be read as a
> whole-algorithm speedup. Verify the scope before the magnitude.

## What to check first

The system's own premortem names its weakest link — the cheapest place for an expert
to start:

- **Knowledge-base condition at risk:** `{entry.get('top_doubt_kb_id')}`
- **Concrete check:** {entry.get('expert_check')}

## Novelty (is this already known?)

{_novelty_block(resolved['novelty'])}

## Reasoning chain

{_reasoning_chain(record)}

## Verification checklist

1. Does the claimed primitive→problem mapping already appear in the literature? (see Novelty)
2. Is the `speedup_scope` accurate — does any sequential outer structure remain unaccelerated?
3. Do the readout and input-loading costs in the I/O accounting actually hold for this problem?
4. Resolve the specific doubt above (`{entry.get('top_doubt_kb_id')}`).
5. If all four survive: is the structural reasoning sound enough to warrant a formal derivation?

---
*Generated from archived pipeline records; no claim is asserted beyond "provides evidence
that", pending expert verification.*
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate expert dossiers from screening archives.")
    ap.add_argument("--pool", default="v1", help="which pool's screening results to use")
    ap.add_argument("--name", help="generate a dossier for one candidate only (prints to stdout)")
    args = ap.parse_args()

    screen_dir = os.path.join(REAL_OUT_DIR, "screening", args.pool)
    summary = _load_summary(screen_dir)
    entries = summary["entries"]
    stage2 = _load_stage2(screen_dir)
    desc = {c["name"]: c.get("description", "") for c in get_pool(args.pool)}

    if args.name:
        entry = next((e for e in entries if e["name"] == args.name), None)
        if not entry:
            raise SystemExit(f"No screened candidate named {args.name!r} in pool {args.pool}.")
        resolved = _resolve(entry, screen_dir, stage2.get(args.name), desc.get(args.name, ""))
        print(build_dossier(entry, resolved, stage2.get(args.name)))
        return 0

    out_dir = os.path.join(REAL_OUT_DIR, "dossiers", args.pool)
    os.makedirs(out_dir, exist_ok=True)

    survivors = [e for e in entries
                 if "error" not in e and surfaced(e, stage2.get(e["name"]))]
    resolved = {e["name"]: _resolve(e, screen_dir, stage2.get(e["name"]), desc.get(e["name"], ""))
                for e in survivors}
    expert_facing = [e for e in survivors if not resolved[e["name"]]["rediscovery_risk"]]
    rediscoveries = [e for e in survivors if resolved[e["name"]]["rediscovery_risk"]]

    for e in survivors:
        doc = build_dossier(e, resolved[e["name"]], stage2.get(e["name"]))
        with open(os.path.join(out_dir, f"{_slug(e['name'])}.md"), "w") as f:
            f.write(doc)

    # Index, separating expert-facing candidates from the calibration appendix.
    idx = [f"# Candidate dossiers — pool {args.pool}\n",
           f"*{len(survivors)} survivors: {len(expert_facing)} expert-facing candidate(s), "
           f"{len(rediscoveries)} rediscovery(ies) (calibration appendix).*\n",
           "## Expert-facing candidates\n"]
    if expert_facing:
        for e in sorted(expert_facing, key=lambda x: x["name"]):
            r = resolved[e["name"]]
            scope = (r["record"] or {}).get("scheme", {}).get("speedup_scope") or "?"
            idx.append(f"- **[{e['name']}]({_slug(e['name'])}.md)** — `{r['recommendation']}` "
                       f"(scope: {scope}; fragility: {e.get('fragility')})")
    else:
        idx.append("_(none on this pool — every positive verdict resolved to a rediscovery.)_")
    idx.append("\n## Calibration appendix — independent rediscoveries of known results\n")
    idx.append("These are NOT sent to an expert; they are evidence the instrument's positive "
               "verdicts land on real, literature-confirmed speedups.\n")
    for e in sorted(rediscoveries, key=lambda x: x["name"]):
        hit = (resolved[e["name"]]["novelty"] or [{}])[0]
        idx.append(f"- **{e['name']}** — `{resolved[e['name']]['recommendation']}` "
                   f"≈ {hit.get('problem', hit.get('id', '?'))}")

    with open(os.path.join(out_dir, "index.md"), "w") as f:
        f.write("\n".join(idx) + "\n")

    print(f"Wrote {len(survivors)} dossier(s) + index to {out_dir}")
    print(f"  expert-facing candidates: {len(expert_facing)}; rediscoveries: {len(rediscoveries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
