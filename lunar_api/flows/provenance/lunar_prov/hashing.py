# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations
import json
from hashlib import sha256
from typing import Any

from rdflib import Graph


def graph_sha256_nt(graph: Graph) -> str:
    """Deterministic-ish hash: serialize to N-Triples, sort lines, sha256."""
    nt = graph.serialize(format="nt")
    if isinstance(nt, bytes):
        nt = nt.decode("utf-8")
    lines = [ln.strip() for ln in nt.splitlines() if ln.strip()]
    lines.sort()
    digest = sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()
    return digest


def stable_json_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()
