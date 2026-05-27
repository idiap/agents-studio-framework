# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Heuristics for locating "attachment" entities inside an existing PROV dataset.

Why this exists
--------------
When we append *manual* edits to an existing provenance record, we often want
to link the first manual report version (v0) back to the *workflow output*
entity that originally produced the report.

In many real-world settings users don't want to provide the exact IRI of that
workflow output. This module provides deterministic, explainable heuristics
to locate a good attachment candidate.

The primary strategy is:
  1) Prefer an output entity whose step id matches the report_id.
  2) Otherwise, prefer the *final* step activity (no other step depends on it),
     and choose its output entity.
  3) Use keyword ranking ("report", "summary", "final") as tie-breakers.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from rdflib import Dataset, Literal, RDF, RDFS, URIRef

from .prov_dataset import PROV
from .utils import safe_id


@dataclass(frozen=True)
class AttachDiscoveryResult:
    iri: Optional[str]
    reason: str


_RE_STEP_ACT = re.compile(r"/activity/step/([^/#?]+)$")
_RE_OUTPUT_ENT = re.compile(r"/entity/output/([^/#?]+)$")


def _label(ds: Dataset, node: URIRef) -> str:
    for o in ds.objects(node, RDFS.label):
        if isinstance(o, Literal):
            return str(o)
    return ""


def _iter_step_activities(ds: Dataset) -> List[URIRef]:
    out: List[URIRef] = []
    for s in set(ds.subjects(RDF.type, PROV.Activity)):
        if _RE_STEP_ACT.search(str(s)):
            out.append(URIRef(str(s)))
    return out


def _iter_output_entities(ds: Dataset) -> List[URIRef]:
    out: List[URIRef] = []
    for s in set(ds.subjects(RDF.type, PROV.Entity)):
        if _RE_OUTPUT_ENT.search(str(s)):
            out.append(URIRef(str(s)))
    return out


def _step_id_from_activity(act: URIRef) -> Optional[str]:
    m = _RE_STEP_ACT.search(str(act))
    return m.group(1) if m else None


def _step_id_from_output(ent: URIRef) -> Optional[str]:
    m = _RE_OUTPUT_ENT.search(str(ent))
    return m.group(1) if m else None


def infer_attach_entity_iri(
    ds: Dataset,
    report_id: str,
) -> AttachDiscoveryResult:
    """Infer the workflow-output entity IRI that a manual report should attach to.

    Parameters
    ----------
    ds:
        Existing provenance dataset (TriG/JSON-LD already loaded).
    report_id:
        Human-facing report identifier (e.g., "report", "final_report").

    Returns
    -------
    AttachDiscoveryResult
        .iri is None if no plausible candidate exists.
    """
    prov = PROV
    target = safe_id(report_id)

    # 1) Exact match against output entity step-id
    outputs = _iter_output_entities(ds)
    for ent in outputs:
        sid = _step_id_from_output(ent)
        if sid and sid == target:
            return AttachDiscoveryResult(
                str(ent), f"matched output entity step id == {target}"
            )

    # 2) Infer "final" step activity: a step activity that is NOT used as a dependency
    #    of any other step activity.
    step_acts = _iter_step_activities(ds)
    informed_objs = set(ds.objects(None, prov.wasInformedBy))
    finals = [a for a in step_acts if a not in informed_objs]

    def score_activity(a: URIRef) -> Tuple[int, int, str]:
        sid = _step_id_from_activity(a) or ""
        lab = _label(ds, a).lower()
        sid_l = sid.lower()

        # Higher is better
        s0 = 0
        if sid == target or target in sid_l or target in lab:
            s0 += 100
        if "report" in sid_l or "report" in lab:
            s0 += 50
        if "summary" in sid_l or "summary" in lab:
            s0 += 20
        if "final" in sid_l or "final" in lab:
            s0 += 10

        # Prefer longer ids when tied (often more specific)
        s1 = len(sid)
        return (s0, s1, sid)

    ranked_finals = sorted(finals, key=score_activity, reverse=True)
    if ranked_finals:
        best_act = ranked_finals[0]
        # find its generated output entity
        for ent in ds.subjects(prov.wasGeneratedBy, best_act):
            if _RE_OUTPUT_ENT.search(str(ent)):
                sid = _step_id_from_activity(best_act) or ""
                return AttachDiscoveryResult(
                    str(ent), f"picked final step activity '{sid}'"
                )

    # 3) Fallback: keyword-rank output entities by their labels/ids
    def score_output(e: URIRef) -> Tuple[int, int, str]:
        sid = _step_id_from_output(e) or ""
        lab = _label(ds, e).lower()
        sid_l = sid.lower()
        sc = 0
        if sid == target or target in sid_l or target in lab:
            sc += 100
        if "report" in sid_l or "report" in lab:
            sc += 50
        if "summary" in sid_l or "summary" in lab:
            sc += 20
        if "final" in sid_l or "final" in lab:
            sc += 10
        return (sc, len(sid), sid)

    ranked_out = sorted(outputs, key=score_output, reverse=True)
    if ranked_out:
        best = ranked_out[0]
        sid = _step_id_from_output(best) or ""
        return AttachDiscoveryResult(
            str(best), f"fallback picked output entity '{sid}'"
        )

    return AttachDiscoveryResult(None, "no output entities found to attach to")
