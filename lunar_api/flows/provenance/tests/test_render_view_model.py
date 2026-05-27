# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from pathlib import Path
import json

from ..lunar_prov.parsers import load_execution_log, load_workflow
from ..lunar_prov.render import build_view_model, render_html


def test_view_model_contains_sources_recent_outputs_and_steps():
    wf_path = (
        Path(__file__).parent.parent / "examples" / "portfolio_allocation_flow.yaml"
    )
    lg_path = Path(__file__).parent.parent / "examples" / "reasoning_log.json"

    wf = load_workflow(str(wf_path))
    log = load_execution_log(str(lg_path))

    base = "http://lunarbase.ai/prov"
    model = build_view_model(workflow=wf, log=log, base_uri=base, embed_values=False)

    assert model["base_uri"] == base
    assert model["run_id"]
    assert model["workflow"]["id"] == "portfolio_allocation_flow"

    # Data sources should list the original flow inputs.
    src_ids = [s["id"] for s in model.get("data_sources", [])]
    assert set(src_ids) == {"user_instructions", "kb_field_id"}

    # Should expose steps and dependency edges.
    step_ids = [s["id"] for s in model.get("steps", [])]
    # Flow uses nodes instead of steps
    flow_dict = json.loads(wf.to_json())
    node_ids = {node.get("id") for node in flow_dict.get("nodes", [])}
    assert set(step_ids) == node_ids

    edge_pairs = {
        (e["from_step"], e["to_step"])
        for e in model.get("edges", [])
        if e.get("type") == "dependsOn"
    }
    assert ("portfolio_allocation", "report") in edge_pairs
    assert ("executive_summary_generator", "report") in edge_pairs

    # Recent outputs should be sorted with the most recent first (ended_at descending).
    rec = model.get("recent_outputs", [])
    assert isinstance(rec, list)
    if len(rec) >= 2:
        assert rec[0]["ended_at"] >= rec[1]["ended_at"]


def test_render_html_contains_mode_toggles_and_embedded_model():
    wf_path = (
        Path(__file__).parent.parent / "examples" / "portfolio_allocation_flow.yaml"
    )
    lg_path = Path(__file__).parent.parent / "examples" / "reasoning_log.json"

    wf = load_workflow(str(wf_path))
    log = load_execution_log(str(lg_path))

    model = build_view_model(
        workflow=wf, log=log, base_uri="http://lunarbase.ai/prov", embed_values=False
    )
    html = render_html(model)

    assert "Lunar Provenance Explorer" in html
    assert 'id="prov-data"' in html
    assert "mode-steps" in html and "mode-entities" in html
    assert "toggle-trace" in html


def test_view_model_includes_step_output_values():
    """Test that step output values are correctly extracted from result_value."""
    wf_path = (
        Path(__file__).parent.parent / "examples" / "portfolio_allocation_flow.yaml"
    )
    lg_path = Path(__file__).parent.parent / "examples" / "reasoning_log.json"

    wf = load_workflow(str(wf_path))
    log = load_execution_log(str(lg_path))

    # Build view model with embed_values=True to include actual values
    model = build_view_model(
        workflow=wf, log=log, base_uri="http://lunarbase.ai/prov", embed_values=True
    )

    # Check that steps have non-null output values and summaries
    steps = model.get("steps", [])
    assert len(steps) > 0, "Should have at least one step"

    # At least some steps should have non-null outputs
    steps_with_outputs = [
        s for s in steps if s.get("output", {}).get("value") is not None
    ]

    # Some steps might legitimately have null outputs, but most should have values
    # if the execution completed successfully
    assert (
        len(steps_with_outputs) > 0
    ), "Should have at least one step with output value"

    # Check that summaries are not all "(null)"
    summaries = [s.get("output", {}).get("summary", "") for s in steps]
    non_null_summaries = [s for s in summaries if s != "(null)"]
    assert len(non_null_summaries) > 0, "Should have at least one non-null summary"
