# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json

from lunar_api.flows.provenance.lunar_prov.edits_spec import load_edits_json


def test_load_edits_json_reads_paths(tmp_path):
    v0 = tmp_path / "v0.md"
    v1 = tmp_path / "v1.md"
    v0.write_text("a\n", encoding="utf-8")
    v1.write_text("b\n", encoding="utf-8")

    spec = {
        "report_id": "r",
        "edits": [
            {
                "username": "alice",
                "started_at": "2025-12-28T00:00:00Z",
                "ended_at": "2025-12-28T00:01:00Z",
                "before_path": "v0.md",
                "after_path": "v1.md",
            }
        ],
    }
    p = tmp_path / "edits.json"
    p.write_text(json.dumps(spec), encoding="utf-8")

    rid, attach, edits = load_edits_json(str(p))
    assert rid == "r"
    assert attach is None
    assert len(edits) == 1
    assert edits[0].before_text.strip() == "a"
    assert edits[0].after_text.strip() == "b"


def test_load_edits_json_versions_dir_pairs_consecutive_files(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "v0.md").write_text("v0\n", encoding="utf-8")
    (reports / "v1.md").write_text("v1\n", encoding="utf-8")
    (reports / "v2.md").write_text("v2\n", encoding="utf-8")

    spec = {
        "report_id": "r",
        "versions_dir": "reports",
        "edits": [
            {
                "username": "alice",
                "started_at": "2025-12-28T00:00:00Z",
                "ended_at": "2025-12-28T00:01:00Z",
            },
            {
                "username": "alice",
                "started_at": "2025-12-28T00:02:00Z",
                "ended_at": "2025-12-28T00:03:00Z",
            },
        ],
    }

    p = tmp_path / "edits.json"
    p.write_text(json.dumps(spec), encoding="utf-8")

    rid, attach, edits = load_edits_json(str(p))
    assert rid == "r"
    assert attach is None
    assert len(edits) == 2
    assert edits[0].before_text.strip() == "v0"
    assert edits[0].after_text.strip() == "v1"
    assert edits[1].before_text.strip() == "v1"
    assert edits[1].after_text.strip() == "v2"
