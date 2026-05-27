# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from pathlib import Path
import json

from lunar_api.flows.provenance.lunar_prov.parsers import (
    load_execution_log,
    load_workflow,
    flow_start_event,
    index_events,
)


def test_load_workflow_examples():
    wf_path = (
        Path(__file__).parent.parent / "examples" / "portfolio_allocation_flow.yaml"
    )
    wf = load_workflow(str(wf_path))

    # Flow uses methods, not attributes
    assert wf.get_id() == "portfolio_allocation_flow"
    assert wf.get_name() != ""

    # Check nodes instead of steps
    flow_dict = json.loads(wf.to_json())
    nodes = flow_dict.get("nodes", [])
    assert len(nodes) == 7

    expected_steps = {
        "portfolio_allocation_input_formatter",
        "get_cma_node",
        "portfolio_allocation",
        "executive_summary_generator",
        "portfolio_allocation_table",
        "key_metrics_extractor",
        "report",
    }
    node_ids = {node.get("id") for node in nodes}
    assert node_ids == expected_steps


def test_load_execution_log_examples_and_indexing():
    lg_path = Path(__file__).parent.parent / "examples" / "reasoning_log.json"
    log = load_execution_log(str(lg_path))

    assert log.status in {"success", "failed", "running", "completed", ""}  # permissive
    assert log.started_at != ""
    assert log.completed_at != ""
    assert isinstance(log.event_log, list)

    start = flow_start_event(log.event_log)
    assert start is not None
    assert start.get("type") == "flow:started"
    inputs = (start.get("payload") or {}).get("inputs") or {}
    assert set(inputs.keys()) == {"user_instructions", "kb_field_id"}

    idx = index_events(log.event_log)
    # At least the main steps should have started/finished recorded
    assert "report" in idx
    assert "step:started" in idx["report"]
    assert "step:finished" in idx["report"]
