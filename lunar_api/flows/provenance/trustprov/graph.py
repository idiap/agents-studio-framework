# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Graph utilities for provenance step dependencies.

The Trust Index is computed for an output artifact by:
1) picking a target step (e.g., "final_report"),
2) extracting the set of *ancestor* steps that contributed to it, and
3) aggregating per-step risks across that ancestor subgraph.

This module provides:
- adjacency list construction from the parsed run,
- ancestor extraction (reverse traversal),
- depth computation within the induced subgraph.

Terminology
-----------
- forward adjacency (fwd): u -> v means "u contributes to v"
- reverse adjacency (rev): v -> u for ancestor traversal

Note on dependency sources
--------------------------
We support two ways of representing lineage:

1) `run.edges`: explicit edges list (if present in the provenance format)
2) `step.depends_on`: per-step list of parent step IDs

Current behavior:
- If `run.edges` is present and non-empty, we use edges.
- Otherwise we fall back to `depends_on`.

This is a pragmatic choice for the synthetic fixtures. If your provenance includes
both, or if edges can be partial, you may prefer to combine them.
"""

from __future__ import annotations
from collections import defaultdict, deque
from typing import Dict, Iterable, List, Set, Tuple

from .types import ProvenanceRun


def build_adjacency(
    run: ProvenanceRun,
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Build adjacency lists among steps.

    Returns:
        (fwd, rev)

    The adjacency lists include only known step IDs. Unknown references are ignored.
    """
    fwd: Dict[str, List[str]] = defaultdict(list)
    rev: Dict[str, List[str]] = defaultdict(list)

    # Prefer explicit edges if present. Otherwise use lightweight depends_on.
    if run.edges:
        for e in run.edges:
            u = e.from_step
            v = e.to_step
            if not u or not v:
                continue
            if u not in run.steps or v not in run.steps:
                continue
            fwd[u].append(v)
            rev[v].append(u)
    else:
        for sid, s in run.steps.items():
            for parent in s.depends_on:
                if parent not in run.steps:
                    continue
                fwd[parent].append(sid)
                rev[sid].append(parent)

    return fwd, rev


def ancestors_of(target: str, rev: Dict[str, List[str]]) -> Set[str]:
    """
    Compute the set of ancestor steps (including `target`) in the reverse graph.

    This is a standard BFS/DFS over `rev`.
    """
    seen: Set[str] = set()
    q = deque([target])
    while q:
        cur = q.popleft()
        if cur in seen:
            continue
        seen.add(cur)
        for parent in rev.get(cur, []):
            if parent not in seen:
                q.append(parent)
    return seen


def compute_depths(
    fwd: Dict[str, List[str]], subgraph: Set[str], roots: Iterable[str]
) -> Dict[str, int]:
    """
    Compute a simple "depth" for each node in `subgraph`.

    Depth is used as a *chain-length proxy*:
    - deeper steps are further upstream and may contribute to risk accumulation.

    Implementation detail:
    We do a BFS-like relaxation starting from `roots` (usually the target itself)
    and keep the maximum depth found for each node.
    """
    depth: Dict[str, int] = {}
    qq = deque(roots)
    for r in roots:
        depth.setdefault(r, 0)

    while qq:
        u = qq.popleft()
        for v in fwd.get(u, []):
            if v not in subgraph:
                continue
            nd = depth.get(u, 0) + 1
            # Keep the deepest path length found so far.
            if nd > depth.get(v, -1):
                depth[v] = nd
                qq.append(v)

    return depth
