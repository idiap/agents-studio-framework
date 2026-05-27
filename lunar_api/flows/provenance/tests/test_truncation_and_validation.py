# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pytest
from rdflib import Dataset
from rdflib import URIRef

from lunar_api.flows.provenance.lunar_prov.embedding import embed_json, embed_text
from lunar_api.flows.provenance.lunar_prov.manual_edits import (
    ManualEdit,
    add_manual_edits_bundle,
)
from lunar_api.flows.provenance.lunar_prov.prov_dataset import dt_literal


def test_dt_literal_validates_iso8601():
    # Valid forms should parse
    dt_literal("2025-12-28T12:00:00")
    dt_literal("2025-12-28T12:00:00Z")
    dt_literal("2025-12-28T12:00:00+01:00")

    # Invalid should raise
    with pytest.raises(ValueError):
        dt_literal("not-a-datetime")


def test_embed_helpers_truncate_and_return_meta():
    lit, meta = embed_text("x" * 100, max_bytes=10)
    assert meta is not None
    assert meta.truncated is True
    assert len(str(lit)) <= 10

    lit2, meta2 = embed_json({"a": "x" * 100}, max_bytes=20)
    assert meta2 is not None
    assert meta2.truncated is True
    assert len(str(lit2)) <= 20


def test_manual_edits_reject_inverted_time_window():
    ds = Dataset()
    edits = [
        ManualEdit(
            username="alice",
            started_at="2025-12-28T12:05:00Z",
            ended_at="2025-12-28T12:00:00Z",
            before_text="A\n",
            after_text="B\n",
        )
    ]
    with pytest.raises(ValueError):
        add_manual_edits_bundle(
            ds,
            base_uri="http://lunarbase.ai/prov",
            run_id="r",
            report_id="rep",
            edits=edits,
        )


def test_manual_edits_adds_truncation_metadata_when_values_are_large():
    ds = Dataset()
    big = "A" * 200
    edits = [
        ManualEdit(
            username="alice",
            started_at="2025-12-28T12:00:00Z",
            ended_at="2025-12-28T12:01:00Z",
            before_text=big,
            after_text=big + "B",
        )
    ]
    info = add_manual_edits_bundle(
        ds,
        base_uri="http://lunarbase.ai/prov",
        run_id="run123",
        report_id="rep",
        edits=edits,
        embed_values=True,
        max_embed_bytes=50,
    )
    g = ds.graph(info["manual_edits_bundle"])
    # The 'truncated' predicate should exist on at least one report/diff entity.
    truncated_pred = URIRef("http://lunarbase.ai/prov/truncated")
    assert any(True for _ in g.triples((None, truncated_pred, None)))
