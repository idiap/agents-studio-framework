# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import json
from pathlib import Path

from lunar_api.flows.provenance.lunar_prov.export import export_prov


def test_export_trig(tmp_path: Path):
    wf = Path(__file__).parent.parent / "examples" / "portfolio_allocation_flow.yaml"
    lg = Path(__file__).parent.parent / "examples" / "reasoning_log.json"
    out = tmp_path / "prov.trig"
    html = tmp_path / "prov.html"
    manifest = tmp_path / "prov.manifest.json"
    export_prov(
        str(wf),
        str(lg),
        str(out),
        html_path=str(html),
        manifest_path=str(manifest),
        emit_redacted=True,
    )
    assert out.exists()
    assert html.exists()
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert "bundle_hashes" in data
    # Basic sanity check that the HTML is a drill-down explorer and embeds the model.
    h = html.read_text(encoding="utf-8")
    assert "Lunar Provenance Explorer" in h
    assert "prov-data" in h
