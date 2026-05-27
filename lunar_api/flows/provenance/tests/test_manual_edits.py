# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from rdflib import Dataset
from rdflib import RDF, RDFS, URIRef, Literal

from lunar_api.flows.provenance.lunar_prov.manual_edits import (
    ManualEdit,
    add_manual_edits_bundle,
)
from lunar_api.flows.provenance.lunar_prov.prov_dataset import PROV


def test_add_manual_edits_bundle_creates_chain_and_diffstats():
    ds = Dataset()
    edits = [
        ManualEdit(
            username="alice",
            started_at="2025-12-28T12:00:00Z",
            ended_at="2025-12-28T12:05:00Z",
            before_text="# Title\nHello\n",
            after_text="# Title\nHello world\n",
            note="add a word",
        ),
        ManualEdit(
            username="bob",
            started_at="2025-12-28T12:10:00Z",
            ended_at="2025-12-28T12:12:00Z",
            before_text="# Title\nHello world\n",
            after_text="# Title\nHello world!\n",
            note="punctuation",
        ),
    ]

    info = add_manual_edits_bundle(
        ds=ds,
        base_uri="http://lunarbase.ai/prov",
        run_id="run123",
        report_id="final_report",
        edits=edits,
        attach_to_entity_iri="http://lunarbase.ai/prov/run/run123/entity/output/final_report",
        embed_values=True,
        emit_redacted=True,
    )

    assert "manual_edits_bundle" in info
    g = ds.graph(info["manual_edits_bundle"])
    # We should have at least: 2 activities, 3 report versions, 2 diff entities, 2 user agents
    assert len(g) > 0
    # Spot-check that both user agents exist (different usernames)
    ttl = g.serialize(format="turtle")
    assert "agent/user/alice" in ttl
    assert "agent/user/bob" in ttl
    # Report version chain
    assert "report:final_report:v0" in ttl
    assert "report:final_report:v1" in ttl
    assert "report:final_report:v2" in ttl
    # DiffStats annotation exists
    assert "diffStats" in ttl

    # Redacted bundle is present and linked
    assert "manual_edits_redacted_bundle" in info
    g_red = ds.graph(info["manual_edits_redacted_bundle"])
    assert len(g_red) > 0


def test_add_manual_edits_bundle_is_append_safe_across_multiple_calls():
    ds = Dataset()
    base = "http://lunarbase.ai/prov"

    # First call creates v0->v1 and manual_edit:1
    edits1 = [
        ManualEdit(
            username="alice",
            started_at="2025-12-28T12:00:00Z",
            ended_at="2025-12-28T12:01:00Z",
            before_text="A\n",
            after_text="A1\n",
        )
    ]
    add_manual_edits_bundle(
        ds, base_uri=base, run_id="run123", report_id="rep", edits=edits1
    )

    # Second call should continue: v1->v2 and manual_edit:2 (no collisions)
    edits2 = [
        ManualEdit(
            username="alice",
            started_at="2025-12-28T12:02:00Z",
            ended_at="2025-12-28T12:03:00Z",
            before_text="A1\n",
            after_text="A2\n",
        )
    ]
    info2 = add_manual_edits_bundle(
        ds, base_uri=base, run_id="run123", report_id="rep", edits=edits2
    )

    g = ds.graph(info2["manual_edits_bundle"])
    ttl = g.serialize(format="turtle")

    # Versions v0, v1, v2 exist
    assert "report:rep:v0" in ttl
    assert "report:rep:v1" in ttl
    assert "report:rep:v2" in ttl

    # Activity numbering continues
    assert "manual_edit:rep:1" in ttl
    assert "manual_edit:rep:2" in ttl


def test_add_manual_edits_bundle_infers_attachment_when_missing_exact_output_match():
    ds = Dataset()
    base = "http://lunarbase.ai/prov"
    run_id = "run123"

    # Create an output entity that matches the report_id step id
    out = URIRef(f"{base}/run/{run_id}/entity/output/report")
    ds.add((out, RDF.type, PROV.Entity))
    ds.add((out, RDFS.label, Literal("output:report")))

    edits = [
        ManualEdit(
            username="alice",
            started_at="2025-12-28T12:00:00Z",
            ended_at="2025-12-28T12:01:00Z",
            before_text="A\n",
            after_text="B\n",
        )
    ]

    info = add_manual_edits_bundle(
        ds, base_uri=base, run_id=run_id, report_id="report", edits=edits
    )
    g = ds.graph(info["manual_edits_bundle"])

    # v0 specializes the workflow output entity
    v0 = URIRef(f"{base}/run/{run_id}/entity/report/report/v0")
    assert (v0, PROV.specializationOf, out) in g
    assert "matched output entity" in (info.get("attach_reason") or "")


def test_add_manual_edits_bundle_infers_attachment_by_final_step_when_no_exact_match():
    ds = Dataset()
    base = "http://lunarbase.ai/prov"
    run_id = "run123"

    # Create two step activities: step2 depends on step1, so step2 is "final".
    step1 = URIRef(f"{base}/run/{run_id}/activity/step/step1")
    step2 = URIRef(f"{base}/run/{run_id}/activity/step/step2")
    ds.add((step1, RDF.type, PROV.Activity))
    ds.add((step2, RDF.type, PROV.Activity))
    ds.add((step1, RDFS.label, Literal("step:step1")))
    ds.add((step2, RDFS.label, Literal("step:step2")))
    ds.add((step2, PROV.wasInformedBy, step1))

    out2 = URIRef(f"{base}/run/{run_id}/entity/output/step2")
    ds.add((out2, RDF.type, PROV.Entity))
    ds.add((out2, RDFS.label, Literal("output:step2")))
    ds.add((out2, PROV.wasGeneratedBy, step2))

    edits = [
        ManualEdit(
            username="alice",
            started_at="2025-12-28T12:00:00Z",
            ended_at="2025-12-28T12:01:00Z",
            before_text="A\n",
            after_text="B\n",
        )
    ]

    info = add_manual_edits_bundle(
        ds, base_uri=base, run_id=run_id, report_id="final_report", edits=edits
    )
    g = ds.graph(info["manual_edits_bundle"])
    v0 = URIRef(f"{base}/run/{run_id}/entity/report/final_report/v0")
    assert (v0, PROV.specializationOf, out2) in g
    assert "picked final step" in (info.get("attach_reason") or "")
