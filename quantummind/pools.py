"""
Candidate-pool registry.

The funnel can run against different candidate pools (v1 = textbook-adjacent gray
zone, v2 = genuinely cold domains). Screening records which pool it used so Stage 2
can look candidates up in the same one.
"""

from . import candidate_pool, candidate_pool_v2

POOLS = {
    "v1": candidate_pool.CANDIDATES,
    "v2": candidate_pool_v2.CANDIDATES,
}

DEFAULT_POOL = "v1"


def get_pool(name: str) -> list[dict]:
    if name not in POOLS:
        raise SystemExit(f"Unknown pool {name!r}; choices: {', '.join(POOLS)}")
    return POOLS[name]
