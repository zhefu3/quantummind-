"""
Output-path isolation.

Mock output must NEVER share a path with real experiment results: twice now a mock
regression run has silently overwritten real-model run records (single-run results on
2026-07-09, a K=2 batch before that), and outputs/ is not under version control, so
an overwrite is unrecoverable. Every module that writes under outputs/ must derive its
directory from the active backend via outputs_root() instead of hardcoding one path.
"""

import os

REAL_OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


def outputs_root(backend: str) -> str:
    """Root directory for run artifacts: outputs/ for real backends, the disjoint
    outputs/mock/ subtree for the mock backend."""
    if backend == "mock":
        return os.path.join(REAL_OUT_DIR, "mock")
    return REAL_OUT_DIR
