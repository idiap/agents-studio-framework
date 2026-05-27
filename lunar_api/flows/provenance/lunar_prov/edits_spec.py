# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Load manual Markdown edit sessions from a JSON spec.

The JSON file is expected to be either:

1) An object with a top-level "edits" list

  {
    "report_id": "final_report",
    "attach_to_entity_iri": "http://.../run/.../entity/output/final_report",
    "edits": [
      {
        "username": "alice",
        "started_at": "2025-12-28T12:00:00Z",
        "ended_at": "2025-12-28T12:10:00Z",
        "before_path": "reports/v0.md",
        "after_path": "reports/v1.md",
        "note": "Fix wording and add caveats"
      }
    ]
  }

Optionally, you can provide a directory of sequential Markdown versions and omit
before/after fields for each edit. In that mode, edits are paired to
consecutive files in lexicographic order.

  {
    "report_id": "final_report",
    "versions_dir": "reports/",
    "edits": [
      {"username": "alice", "started_at": "...", "ended_at": "..."},
      {"username": "alice", "started_at": "...", "ended_at": "..."}
    ]
  }

2) Or simply a list of edits (same item schema as above)

Paths are read relative to the JSON file directory.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, List, Optional, Tuple

from .manual_edits import ManualEdit
from .utils import parse_iso


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


_NUM_RE = re.compile(r"(\d+)")


def _natural_key(name: str) -> List[Any]:
    """Sort helper: 'v2.md' comes before 'v10.md'."""

    parts: List[Any] = []
    last = 0
    for m in _NUM_RE.finditer(name):
        if m.start() > last:
            parts.append(name[last : m.start()])
        parts.append(int(m.group(1)))
        last = m.end()
    if last < len(name):
        parts.append(name[last:])
    return parts


def _list_md_versions(d: Path) -> List[Path]:
    files = [
        p
        for p in d.iterdir()
        if p.is_file() and p.suffix.lower() in {".md", ".markdown"}
    ]
    return sorted(files, key=lambda p: _natural_key(p.name))


def load_edits_json(path: str) -> Tuple[str, Optional[str], List[ManualEdit]]:
    """Return (report_id, attach_to_entity_iri, edits).

    If the top-level spec provides "versions_dir", edits may omit before/after
    content and will be paired to consecutive Markdown files in that directory.
    """
    p = Path(path)
    obj = json.loads(p.read_text(encoding="utf-8"))
    base = p.parent

    report_id = "report"
    attach = None
    versions_dir: Optional[str] = None
    edits_obj: Any = obj
    if isinstance(obj, dict):
        report_id = str(obj.get("report_id") or report_id)
        attach = obj.get("attach_to_entity_iri") or None
        versions_dir = obj.get("versions_dir") or None
        edits_obj = obj.get("edits") or []

    if not isinstance(edits_obj, list):
        raise ValueError("edits spec must be a list (or a dict with an 'edits' list)")

    # Optional auto-pairing of versions.
    version_pairs: Optional[List[Tuple[str, str, str, str]]] = None
    # (before_text, after_text, before_name, after_name)
    if versions_dir:
        d = (base / str(versions_dir)).resolve()
        if not d.exists() or not d.is_dir():
            raise ValueError(f"versions_dir does not exist or is not a directory: {d}")
        versions = _list_md_versions(d)
        if len(versions) < 2:
            raise ValueError(
                f"versions_dir must contain at least 2 markdown files: {d}"
            )
        version_pairs = []
        for a, b in zip(versions[:-1], versions[1:]):
            version_pairs.append((_read_text(a), _read_text(b), a.name, b.name))

    edits: List[ManualEdit] = []
    for i, e in enumerate(edits_obj):
        if not isinstance(e, dict):
            raise ValueError(f"edit #{i} must be an object")

        username = str(e.get("username") or "")
        started_at = str(e.get("started_at") or "")
        ended_at = str(e.get("ended_at") or "")
        if not started_at or not ended_at:
            raise ValueError(
                f"edit #{i} must provide non-empty started_at and ended_at (ISO8601)"
            )
        # Validate parseability / ordering early so provenance is time-consistent.
        st = parse_iso(started_at)
        en = parse_iso(ended_at)
        if en < st:
            raise ValueError(
                f"edit #{i} has ended_at earlier than started_at: {started_at} -> {ended_at}"
            )
        note = str(e.get("note") or "")

        before_text = e.get("before_text")
        after_text = e.get("after_text")
        before_path = e.get("before_path")
        after_path = e.get("after_path")

        if before_text is None and before_path:
            before_text = _read_text((base / str(before_path)).resolve())
        if after_text is None and after_path:
            after_text = _read_text((base / str(after_path)).resolve())

        # If missing, fill from versions_dir pairing.
        if (before_text is None or after_text is None) and version_pairs is not None:
            if len(edits_obj) != len(version_pairs):
                raise ValueError(
                    "When using versions_dir, the number of edits must match the number of version transitions "
                    f"({len(version_pairs)}). Got {len(edits_obj)} edits."
                )
            bt, at, bn, an = version_pairs[i]
            before_text = bt if before_text is None else before_text
            after_text = at if after_text is None else after_text
            if not note:
                note = f"Manual edit: {bn} → {an}"

        if before_text is None or after_text is None:
            raise ValueError(
                f"edit #{i} must provide before/after via *_text or *_path, or provide versions_dir at the top level"
            )

        edits.append(
            ManualEdit(
                username=username,
                started_at=started_at,
                ended_at=ended_at,
                before_text=str(before_text),
                after_text=str(after_text),
                note=note,
            )
        )

    return report_id, attach, edits
