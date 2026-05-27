# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Manual Markdown report edits → PROV-O provenance.

Motivation
----------
Lunar flows can generate narrative reports (e.g., Markdown) that are later reviewed
and edited by human experts. Those edits are part of the real decision pipeline
and should be captured as retrospective provenance.

This module turns a sequence of edits (or a sequence of versions) into:
  - prov:Activity instances (manual edit sessions)
  - prov:Entity instances (report versions + diff records)
  - prov:used / prov:wasGeneratedBy links
  - prov:wasRevisionOf links between versions

The resulting triples can be appended to an existing Dataset ("add to current
workflow"), typically into a dedicated prov:Bundle.
"""

from __future__ import annotations
import difflib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from rdflib import Dataset, Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD

from .prov_dataset import PROV, Namespaces, add_bundle_header, dt_literal, lit_json
from .embedding import embed_text
from .utils import safe_id, parse_iso
from .discovery import infer_attach_entity_iri


@dataclass(frozen=True)
class ManualEdit:
    """One manual edit session transforming report `before` → `after`."""

    username: str
    started_at: str  # ISO 8601 string
    ended_at: str  # ISO 8601 string
    before_text: str
    after_text: str
    note: str = ""  # optional free-text rationale/comment


def unified_diff(
    before: str, after: str, fromfile: str = "before.md", tofile: str = "after.md"
) -> str:
    """Return a unified diff string."""
    a = before.splitlines(keepends=True)
    b = after.splitlines(keepends=True)
    d = difflib.unified_diff(a, b, fromfile=fromfile, tofile=tofile)
    return "".join(d)


def diff_stats(before: str, after: str) -> Dict[str, Any]:
    """Compute lightweight, human-friendly diff statistics."""
    a_lines = before.splitlines()
    b_lines = after.splitlines()

    # Line-level deltas
    sm = difflib.SequenceMatcher(a=a_lines, b=b_lines)
    added = removed = changed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "replace":
            changed += max(i2 - i1, j2 - j1)

    # Word-level rough deltas
    a_words = before.split()
    b_words = after.split()
    smw = difflib.SequenceMatcher(a=a_words, b=b_words)
    w_added = w_removed = 0
    for tag, i1, i2, j1, j2 in smw.get_opcodes():
        if tag == "insert":
            w_added += j2 - j1
        elif tag == "delete":
            w_removed += i2 - i1
        elif tag == "replace":
            w_added += j2 - j1
            w_removed += i2 - i1

    return {
        "lines_added": int(added),
        "lines_removed": int(removed),
        "lines_changed": int(changed),
        "words_added": int(w_added),
        "words_removed": int(w_removed),
        "chars_before": len(before),
        "chars_after": len(after),
    }


def edits_from_versions(
    versions: List[str],
    username: str,
    windows: List[Tuple[str, str]],
    notes: Optional[List[str]] = None,
) -> List[ManualEdit]:
    """Convert a list of versions into a list of ManualEdit transitions.

    Parameters
    ----------
    versions:
        Ordered list of markdown strings: [v0, v1, ..., vN]
    username:
        Editor username for all edits
    windows:
        List of (started_at, ended_at) for each transition. Must have length N.
    notes:
        Optional per-edit notes.
    """
    if len(versions) < 2:
        return []
    if len(windows) != len(versions) - 1:
        raise ValueError("windows must have length len(versions)-1")
    notes = notes or [""] * (len(versions) - 1)
    if len(notes) != len(versions) - 1:
        raise ValueError("notes must have length len(versions)-1")
    out: List[ManualEdit] = []
    for i in range(len(versions) - 1):
        st, en = windows[i]
        out.append(
            ManualEdit(
                username=username,
                started_at=st,
                ended_at=en,
                before_text=versions[i],
                after_text=versions[i + 1],
                note=notes[i] or "",
            )
        )
    return out


def _max_numeric_suffix(ds: Dataset, prefix: str) -> int:
    """Return the maximum integer suffix for terms that start with `prefix`.

    Example: if prefix is '.../v' and dataset contains '.../v2' and '.../v7',
    return 7. If none match, return -1.
    """
    mx = -1
    for s, p, o, g in ds.quads((None, None, None, None)):
        for term in (s, o):
            t = str(term)
            if not t.startswith(prefix):
                continue
            suf = t[len(prefix) :]
            if suf.isdigit():
                mx = max(mx, int(suf))
    return mx


def add_manual_edits_bundle(
    ds: Dataset,
    base_uri: str,
    run_id: str,
    report_id: str,
    edits: List[ManualEdit],
    attach_to_entity_iri: Optional[str] = None,
    embed_values: bool = True,
    max_embed_bytes: Optional[int] = 500_000,
    emit_redacted: bool = False,
) -> Dict[str, Any]:
    """Append a manual-edit bundle into an existing provenance Dataset.

    The bundle is created at:
      {base}/bundle/manual_edits/{run_id}/{report_id}

    Append-safe behaviour
    ---------------------
    This function is designed to be called multiple times over the lifetime of a
    report. If the dataset already contains report versions (v0..vK) or manual
    edit activities (..../1..../M), we continue numbering from the current max
    to avoid IRI collisions and preserve an auditable version chain.

    If attach_to_entity_iri is provided and this is the first time the report is
    being added, v0 is linked via prov:specializationOf.
    """
    base = base_uri.rstrip("/") + "/"
    ns = Namespaces(base=Namespace(base))
    EX = ns.base

    b_me = URIRef(
        str(EX) + f"bundle/manual_edits/{safe_id(run_id)}/{safe_id(report_id)}"
    )
    g = ds.graph(b_me)

    # Local helper for bounded embedding metadata
    def _add_meta(gg: Graph, subj: URIRef, meta: Any) -> None:
        if not meta:
            return
        gg.add(
            (
                subj,
                URIRef(str(EX) + "sha256"),
                Literal(str(meta.sha256), datatype=XSD.string),
            )
        )
        gg.add(
            (
                subj,
                URIRef(str(EX) + "byteLength"),
                Literal(int(meta.byte_length), datatype=XSD.integer),
            )
        )
        gg.add(
            (subj, URIRef(str(EX) + "truncated"), Literal(True, datatype=XSD.boolean))
        )

    # Validate and normalize edit windows early (deterministic failures)
    for i, ed in enumerate(edits):
        st = parse_iso(ed.started_at)
        en = parse_iso(ed.ended_at)
        if en < st:
            raise ValueError(
                f"manual edit #{i} has ended_at earlier than started_at: {ed.started_at} -> {ed.ended_at}"
            )
    add_bundle_header(g, b_me)

    # Optional redacted mirror
    b_red = (
        URIRef(
            str(EX)
            + f"bundle/manual_edits_redacted/{safe_id(run_id)}/{safe_id(report_id)}"
        )
        if emit_redacted
        else None
    )
    g_red = ds.graph(b_red) if b_red else None
    if g_red is not None and b_red is not None:
        add_bundle_header(g_red, b_red)

    # Track how we decided the attach target (user-provided vs inferred)
    attach_reason: str = "provided" if attach_to_entity_iri else ""

    # Agents (one per distinct username)
    agents: Dict[str, URIRef] = {}
    for ed in edits:
        if ed.username in agents:
            continue
        a = URIRef(str(EX) + f"agent/user/{safe_id(ed.username)}")
        agents[ed.username] = a
        for gg in (g, g_red) if g_red is not None else (g,):
            gg.add((a, RDF.type, PROV.Person))
            gg.add((a, RDFS.label, Literal(ed.username)))

    # Entity IRI helpers
    def report_entity(version_idx: int) -> URIRef:
        return URIRef(
            str(EX)
            + f"run/{safe_id(run_id)}/entity/report/{safe_id(report_id)}/v{version_idx}"
        )

    def report_entity_red(version_idx: int) -> URIRef:
        return URIRef(
            str(EX)
            + f"run/{safe_id(run_id)}/entity/report_redacted/{safe_id(report_id)}/v{version_idx}"
        )

    # Determine current max version and max edit activity indices (append-safe)
    report_prefix = (
        str(EX) + f"run/{safe_id(run_id)}/entity/report/{safe_id(report_id)}/v"
    )
    max_v = _max_numeric_suffix(ds, report_prefix)

    act_prefix = (
        str(EX) + f"run/{safe_id(run_id)}/activity/manual_edit/{safe_id(report_id)}/"
    )
    max_act = _max_numeric_suffix(ds, act_prefix)
    next_act_num = (max_act + 1) if max_act >= 0 else 1

    # Seed a starting version if this is the first time we see this report.
    # If the caller didn't provide attach_to_entity_iri, we attempt to infer it
    # from the existing dataset (e.g., attach to the final workflow output entity).
    if edits and max_v < 0:
        if not attach_to_entity_iri:
            inferred = infer_attach_entity_iri(ds, report_id=report_id)
            attach_to_entity_iri = inferred.iri or None
            attach_reason = inferred.reason
        e0 = report_entity(0)
        g.add((e0, RDF.type, PROV.Entity))
        g.add((e0, RDFS.label, Literal(f"report:{report_id}:v0")))
        if embed_values:
            lit, meta = embed_text(edits[0].before_text, max_bytes=max_embed_bytes)
            g.add((e0, PROV.value, lit))
            _add_meta(g, e0, meta)
        if attach_to_entity_iri:
            g.add((e0, PROV.specializationOf, URIRef(attach_to_entity_iri)))

        if g_red is not None:
            e0r = report_entity_red(0)
            g_red.add((e0r, RDF.type, PROV.Entity))
            g_red.add((e0r, RDFS.label, Literal(f"report_redacted:{report_id}:v0")))
            if attach_to_entity_iri:
                g_red.add((e0r, PROV.specializationOf, URIRef(attach_to_entity_iri)))
            g.add((e0, PROV.alternateOf, e0r))
            g_red.add((e0r, PROV.alternateOf, e0))

        max_v = 0

    # If appending to an existing chain, we want the next edit to use v{max_v} as its 'before' entity.
    # Ensure the current 'before' entity has a prov:value if requested (best effort, non-destructive).
    if edits and max_v >= 0 and embed_values:
        before_ent = report_entity(max_v)
        if (before_ent, PROV.value, None) not in g and edits[0].before_text:
            lit, meta = embed_text(edits[0].before_text, max_bytes=max_embed_bytes)
            g.add((before_ent, PROV.value, lit))
            _add_meta(g, before_ent, meta)

    # Redacted: ensure starting redacted entity exists if we need to reference it as prov:used.
    if g_red is not None and edits and max_v >= 0:
        before_r = report_entity_red(max_v)
        if (before_r, RDF.type, PROV.Entity) not in g_red:
            g_red.add((before_r, RDF.type, PROV.Entity))
            g_red.add(
                (before_r, RDFS.label, Literal(f"report_redacted:{report_id}:v{max_v}"))
            )

    # For each edit: Activity + diff entity + new report entity
    for i, ed in enumerate(edits):
        edit_num = next_act_num + i
        before_idx = max_v + i
        after_idx = max_v + i + 1

        before_ent = report_entity(before_idx)
        after_ent = report_entity(after_idx)

        act = URIRef(
            str(EX)
            + f"run/{safe_id(run_id)}/activity/manual_edit/{safe_id(report_id)}/{edit_num}"
        )
        g.add((act, RDF.type, PROV.Activity))
        g.add((act, RDFS.label, Literal(f"manual_edit:{report_id}:{edit_num}")))
        g.add((act, PROV.startedAtTime, dt_literal(ed.started_at)))
        g.add((act, PROV.endedAtTime, dt_literal(ed.ended_at)))
        g.add(
            (
                act,
                PROV.wasAssociatedWith,
                agents.get(ed.username)
                or URIRef(str(EX) + f"agent/user/{safe_id(ed.username)}"),
            )
        )
        g.add((act, PROV.used, before_ent))

        # New report version
        g.add((after_ent, RDF.type, PROV.Entity))
        g.add((after_ent, RDFS.label, Literal(f"report:{report_id}:v{after_idx}")))
        g.add((after_ent, PROV.wasGeneratedBy, act))
        g.add((after_ent, PROV.wasRevisionOf, before_ent))
        g.add((after_ent, PROV.wasDerivedFrom, before_ent))
        if embed_values:
            lit, meta = embed_text(ed.after_text, max_bytes=max_embed_bytes)
            g.add((after_ent, PROV.value, lit))
            _add_meta(g, after_ent, meta)

        # Diff record
        diff_ent = URIRef(
            str(EX)
            + f"run/{safe_id(run_id)}/entity/diff/{safe_id(report_id)}/{edit_num}"
        )
        g.add((diff_ent, RDF.type, PROV.Entity))
        g.add((diff_ent, RDFS.label, Literal(f"diff:{report_id}:{edit_num}")))
        g.add((diff_ent, PROV.wasGeneratedBy, act))

        stats = diff_stats(ed.before_text, ed.after_text)
        g.add((diff_ent, URIRef(str(EX) + "diffStats"), lit_json(stats)))
        if ed.note:
            g.add((act, RDFS.comment, Literal(ed.note)))

        if embed_values:
            lit, meta = embed_text(
                unified_diff(ed.before_text, ed.after_text), max_bytes=max_embed_bytes
            )
            g.add((diff_ent, PROV.value, lit))
            _add_meta(g, diff_ent, meta)

        # Redacted mirror (structure + stats only)
        if g_red is not None:
            actr = act
            g_red.add((actr, RDF.type, PROV.Activity))
            g_red.add(
                (actr, RDFS.label, Literal(f"manual_edit:{report_id}:{edit_num}"))
            )
            g_red.add((actr, PROV.startedAtTime, dt_literal(ed.started_at)))
            g_red.add((actr, PROV.endedAtTime, dt_literal(ed.ended_at)))
            g_red.add(
                (
                    actr,
                    PROV.wasAssociatedWith,
                    agents.get(ed.username)
                    or URIRef(str(EX) + f"agent/user/{safe_id(ed.username)}"),
                )
            )

            before_r = report_entity_red(before_idx)
            after_r = report_entity_red(after_idx)

            # Ensure before_r exists
            if (before_r, RDF.type, PROV.Entity) not in g_red:
                g_red.add((before_r, RDF.type, PROV.Entity))
                g_red.add(
                    (
                        before_r,
                        RDFS.label,
                        Literal(f"report_redacted:{report_id}:v{before_idx}"),
                    )
                )

            g_red.add((actr, PROV.used, before_r))
            g_red.add((after_r, RDF.type, PROV.Entity))
            g_red.add(
                (
                    after_r,
                    RDFS.label,
                    Literal(f"report_redacted:{report_id}:v{after_idx}"),
                )
            )
            g_red.add((after_r, PROV.wasGeneratedBy, actr))
            g_red.add((after_r, PROV.wasRevisionOf, before_r))
            g_red.add((after_r, PROV.wasDerivedFrom, before_r))

            diff_r = URIRef(
                str(EX)
                + f"run/{safe_id(run_id)}/entity/diff_redacted/{safe_id(report_id)}/{edit_num}"
            )
            g_red.add((diff_r, RDF.type, PROV.Entity))
            g_red.add(
                (diff_r, RDFS.label, Literal(f"diff_redacted:{report_id}:{edit_num}"))
            )
            g_red.add((diff_r, PROV.wasGeneratedBy, actr))
            g_red.add((diff_r, URIRef(str(EX) + "diffStats"), lit_json(stats)))

            # alternate links
            g.add((after_ent, PROV.alternateOf, after_r))
            g_red.add((after_r, PROV.alternateOf, after_ent))
            g.add((diff_ent, PROV.alternateOf, diff_r))
            g_red.add((diff_r, PROV.alternateOf, diff_ent))

    return {
        "manual_edits_bundle": str(b_me),
        **({"manual_edits_redacted_bundle": str(b_red)} if b_red else {}),
        "report_id": report_id,
        "edit_count": len(edits),
        "start_version_index": int(max_v) if max_v >= 0 else 0,
        "start_edit_index": int(next_act_num),
        "attach_to": attach_to_entity_iri or "",
        "attach_reason": attach_reason or "",
    }
