# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for the provenance service module.

These tests verify the conversion of Flow objects and execution results
to PROV-O provenance data.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from lunar_api.flows.provenance.provenance_service import (
    result_to_execution_log,
    generate_provenance,
    generate_provenance_html,
    _serialize_payload,
    _serialize_result_value,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_flow():
    """Create a mock Flow object for testing."""
    flow = Mock()
    flow.get_id.return_value = "test_flow"
    flow.get_name.return_value = "Test Flow"
    flow.get_description.return_value = "A test flow for provenance"
    flow.to_json.return_value = """{
        "id": "test_flow",
        "name": "Test Flow",
        "description": "A test flow for provenance",
        "version": "1.0.0",
        "nodes": [
            {
                "id": "step_1",
                "component_token": "test_component",
                "inputs": {"input_a": "&flow_input"}
            },
            {
                "id": "step_2",
                "component_token": "another_component",
                "inputs": {"data": "$step_1.output"}
            }
        ]
    }"""
    return flow


@pytest.fixture
def mock_event():
    """Create a mock event for testing."""
    event = Mock()
    event.type = Mock(value="step:started")
    event.timestamp = datetime(2025, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    event.payload = {"step_id": "step_1"}
    event.metadata = {"flow_id": "test_flow"}
    return event


@pytest.fixture
def mock_result():
    """Create a mock execution result for testing."""
    result = Mock()

    # Create mock events
    events = []

    # Flow started event
    flow_start = Mock()
    flow_start.type = Mock(value="flow:started")
    flow_start.timestamp = datetime(2025, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    flow_start.payload = {"inputs": {"flow_input": "test_value"}}
    flow_start.metadata = {"flow_id": "test_flow"}
    events.append(flow_start)

    # Step 1 started
    step1_start = Mock()
    step1_start.type = Mock(value="step:started")
    step1_start.timestamp = datetime(2025, 1, 5, 12, 0, 1, tzinfo=timezone.utc)
    step1_start.payload = None
    step1_start.metadata = {"id": "step_1"}
    events.append(step1_start)

    # Step 1 finished
    step1_finish = Mock()
    step1_finish.type = Mock(value="step:finished")
    step1_finish.timestamp = datetime(2025, 1, 5, 12, 0, 2, tzinfo=timezone.utc)
    step1_finish.payload = None
    step1_finish.metadata = {"id": "step_1"}
    events.append(step1_finish)

    # Step 1 result
    step1_result = Mock()
    step1_result.type = Mock(value="step:result")
    step1_result.timestamp = datetime(2025, 1, 5, 12, 0, 2, tzinfo=timezone.utc)
    step1_result.payload = {"value": {"output": "step_1_output"}}
    step1_result.metadata = {"id": "step_1"}
    events.append(step1_result)

    # Step 2 started
    step2_start = Mock()
    step2_start.type = Mock(value="step:started")
    step2_start.timestamp = datetime(2025, 1, 5, 12, 0, 3, tzinfo=timezone.utc)
    step2_start.payload = None
    step2_start.metadata = {"id": "step_2"}
    events.append(step2_start)

    # Step 2 finished
    step2_finish = Mock()
    step2_finish.type = Mock(value="step:finished")
    step2_finish.timestamp = datetime(2025, 1, 5, 12, 0, 4, tzinfo=timezone.utc)
    step2_finish.payload = None
    step2_finish.metadata = {"id": "step_2"}
    events.append(step2_finish)

    # Step 2 result
    step2_result = Mock()
    step2_result.type = Mock(value="step:result")
    step2_result.timestamp = datetime(2025, 1, 5, 12, 0, 4, tzinfo=timezone.utc)
    step2_result.payload = {"value": {"final_output": "done"}}
    step2_result.metadata = {"id": "step_2"}
    events.append(step2_result)

    # Flow finished event
    flow_finish = Mock()
    flow_finish.type = Mock(value="flow:finished")
    flow_finish.timestamp = datetime(2025, 1, 5, 12, 0, 5, tzinfo=timezone.utc)
    flow_finish.payload = None
    flow_finish.metadata = {"flow_id": "test_flow"}
    events.append(flow_finish)

    result.event_log = events

    # Create mock step results
    step1_value = Mock()
    step1_value.value = {"output": "step_1_output"}

    step2_value = Mock()
    step2_value.value = {"final_output": "done"}

    result.value = {
        "step_1": step1_value,
        "step_2": step2_value,
    }

    return result


# ============================================================================
# Test result_to_execution_log
# ============================================================================


class TestResultToExecutionLog:
    """Tests for result_to_execution_log conversion."""

    def test_basic_conversion(self, mock_flow, mock_result):
        """Test basic conversion of result to ExecutionLog."""
        started_at = "2025-01-05T12:00:00+00:00"
        completed_at = "2025-01-05T12:00:05+00:00"

        log = result_to_execution_log(
            result=mock_result,
            flow=mock_flow,
            inputs={"flow_input": "test_value"},
            started_at=started_at,
            completed_at=completed_at,
            status="completed",
        )

        assert log.status == "completed"
        assert log.started_at == started_at
        assert log.completed_at == completed_at
        assert len(log.event_log) > 0

    def test_event_log_structure(self, mock_flow, mock_result):
        """Test that event log has proper structure."""
        log = result_to_execution_log(
            result=mock_result,
            flow=mock_flow,
            inputs={"flow_input": "test_value"},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
        )

        # Check that we have flow:started and flow:finished events
        event_types = [e.get("type") for e in log.event_log]
        assert "flow:started" in event_types
        assert "flow:finished" in event_types

    def test_inputs_in_flow_started(self, mock_flow, mock_result):
        """Test that inputs are included in flow:started event."""
        inputs = {"flow_input": "test_value", "another_input": 42}

        log = result_to_execution_log(
            result=mock_result,
            flow=mock_flow,
            inputs=inputs,
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
        )

        flow_started = None
        for e in log.event_log:
            if e.get("type") == "flow:started":
                flow_started = e
                break

        assert flow_started is not None
        assert flow_started.get("payload", {}).get("inputs") == inputs

    def test_no_event_log(self, mock_flow):
        """Test handling of result without event_log."""
        result = Mock()
        result.event_log = None
        result.value = {}

        log = result_to_execution_log(
            result=result,
            flow=mock_flow,
            inputs={},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
        )

        # Should still have flow:started and flow:finished
        event_types = [e.get("type") for e in log.event_log]
        assert "flow:started" in event_types
        assert "flow:finished" in event_types


# ============================================================================
# Test _serialize_payload
# ============================================================================


class TestSerializePayload:
    """Tests for payload serialization."""

    def test_serialize_primitives(self):
        """Test serialization of primitive types."""
        assert _serialize_payload(None) is None
        assert _serialize_payload("hello") == "hello"
        assert _serialize_payload(42) == 42
        assert _serialize_payload(3.14) == 3.14
        assert _serialize_payload(True) is True

    def test_serialize_dict(self):
        """Test serialization of dictionaries."""
        payload = {"key": "value", "number": 42}
        result = _serialize_payload(payload)
        assert result == {"key": "value", "number": 42}

    def test_serialize_nested(self):
        """Test serialization of nested structures."""
        payload = {
            "outer": {
                "inner": [1, 2, 3],
                "data": {"key": "value"},
            }
        }
        result = _serialize_payload(payload)
        assert result == payload

    def test_serialize_pydantic_model(self):
        """Test serialization of objects with model_dump."""
        obj = Mock()
        obj.model_dump.return_value = {"field": "value"}

        result = _serialize_payload(obj)
        assert result == {"field": "value"}


# ============================================================================
# Test _serialize_result_value
# ============================================================================


class TestSerializeResultValue:
    """Tests for result value serialization."""

    def test_serialize_step_results(self):
        """Test serialization of step results with .value attributes."""
        step_result = Mock()
        step_result.value = {"output": "data"}

        result = _serialize_result_value({"step_1": step_result})
        assert result == {"step_1": {"value": {"output": "data"}}}

    def test_serialize_plain_dict(self):
        """Test serialization of plain dictionaries."""
        result = _serialize_result_value({"key": "value"})
        assert result == {"key": "value"}


# ============================================================================
# Test generate_provenance
# ============================================================================


class TestGenerateProvenance:
    """Tests for provenance generation."""

    def test_basic_provenance_generation(self, mock_flow, mock_result):
        """Test basic provenance generation."""
        provenance = generate_provenance(
            flow=mock_flow,
            result=mock_result,
            inputs={"flow_input": "test_value"},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
            status="completed",
        )

        assert provenance.manifest is not None
        assert provenance.trig is not None
        assert provenance.view_model is not None

    def test_manifest_structure(self, mock_flow, mock_result):
        """Test that manifest has expected structure."""
        provenance = generate_provenance(
            flow=mock_flow,
            result=mock_result,
            inputs={},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
        )

        manifest = provenance.manifest

        assert manifest.base_uri is not None
        assert manifest.flow_id is not None
        assert manifest.run_id is not None
        assert manifest.bundles is not None
        assert manifest.generated_at is not None
        assert manifest.bundle_hashes is not None

    def test_bundles_created(self, mock_flow, mock_result):
        """Test that prospective and retrospective bundles are created."""
        provenance = generate_provenance(
            flow=mock_flow,
            result=mock_result,
            inputs={},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
        )

        bundles = provenance.manifest.bundles
        assert "prospective" in bundles
        assert "retrospective" in bundles

    def test_trig_format(self, mock_flow, mock_result):
        """Test that TriG output is valid."""
        provenance = generate_provenance(
            flow=mock_flow,
            result=mock_result,
            inputs={},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
        )

        trig = provenance.trig
        assert isinstance(trig, (str, bytes))
        # TriG should contain @prefix declarations
        trig_str = trig if isinstance(trig, str) else trig.decode("utf-8")
        assert "@prefix" in trig_str or "PREFIX" in trig_str

    def test_bundle_hashes(self, mock_flow, mock_result):
        """Test that bundle hashes are computed."""
        provenance = generate_provenance(
            flow=mock_flow,
            result=mock_result,
            inputs={},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
        )

        bundle_hashes = provenance.manifest.bundle_hashes
        assert len(bundle_hashes) > 0

        # At least one bundle should have triples
        has_triples = False
        for bundle_iri, info in bundle_hashes.items():
            assert info.sha256_nt_sorted is not None
            assert info.triple_count is not None
            if info.triple_count > 0:
                has_triples = True

        assert has_triples, "At least one bundle should have triples"

    def test_with_embed_values_false(self, mock_flow, mock_result):
        """Test provenance generation without embedded values."""
        provenance = generate_provenance(
            flow=mock_flow,
            result=mock_result,
            inputs={},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
            embed_values=False,
        )

        assert provenance.manifest is not None
        # Should still work without embedded values

    def test_with_emit_redacted(self, mock_flow, mock_result):
        """Test provenance generation with redacted bundle."""
        provenance = generate_provenance(
            flow=mock_flow,
            result=mock_result,
            inputs={},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
            emit_redacted=True,
        )

        bundles = provenance.manifest.bundles
        assert "redacted" in bundles


# ============================================================================
# Test generate_provenance_html
# ============================================================================


class TestGenerateProvenanceHtml:
    """Tests for HTML provenance visualization generation."""

    def test_html_generation(self, mock_flow, mock_result):
        """Test basic HTML generation."""
        html = generate_provenance_html(
            flow=mock_flow,
            result=mock_result,
            inputs={"flow_input": "test_value"},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
        )

        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html or "<html" in html

    def test_html_contains_flow_info(self, mock_flow, mock_result):
        """Test that HTML contains flow information."""
        html = generate_provenance_html(
            flow=mock_flow,
            result=mock_result,
            inputs={},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:05+00:00",
        )

        # HTML should contain the flow name or id
        assert "test_flow" in html or "Test Flow" in html


# ============================================================================
# Integration tests
# ============================================================================


class TestProvenanceIntegration:
    """Integration tests for the full provenance pipeline."""

    def test_provenance_determinism(self, mock_flow, mock_result):
        """Test that provenance generation is deterministic."""
        inputs = {"flow_input": "test"}
        started_at = "2025-01-05T12:00:00+00:00"
        completed_at = "2025-01-05T12:00:05+00:00"

        prov1 = generate_provenance(
            flow=mock_flow,
            result=mock_result,
            inputs=inputs,
            started_at=started_at,
            completed_at=completed_at,
        )

        prov2 = generate_provenance(
            flow=mock_flow,
            result=mock_result,
            inputs=inputs,
            started_at=started_at,
            completed_at=completed_at,
        )

        # Manifests should match (except generated_at)
        assert prov1.manifest.flow_id == prov2.manifest.flow_id
        assert prov1.manifest.run_id == prov2.manifest.run_id

        # Bundle hashes should match
        for bundle_iri in prov1.manifest.bundle_hashes:
            hash1 = prov1.manifest.bundle_hashes[bundle_iri].sha256_nt_sorted
            hash2 = prov2.manifest.bundle_hashes[bundle_iri].sha256_nt_sorted
            assert hash1 == hash2

    def test_llm_metadata_extraction_in_service(self):
        """Test that LLM metadata is properly extracted through the provenance service."""
        from lunarflow.flows import Flow
        from lunarflow.flows.models import LLMNodeModel, ComponentNodeModel

        # Create a flow with an LLM node
        llm_node = LLMNodeModel(
            id="llm_step",
            token="llm-component",
            inputs={"prompt": "test prompt"},
            kind="llm",
            provider="openai",
            model="gpt-4o",
        )

        non_llm_node = ComponentNodeModel(
            id="regular_step",
            token="regular-component",
            inputs={"data": "$llm_step"},
            kind="component",
        )

        flow = Flow(
            id="llm_test_flow",
            name="LLM Test Flow",
            description="Flow with LLM node for testing",
            nodes=[llm_node, non_llm_node],
        )

        # Create mock result with LLM metadata
        result = Mock()

        # Flow events
        flow_start = Mock()
        flow_start.type = Mock(value="flow:started")
        flow_start.timestamp = datetime(2025, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
        flow_start.payload = {"inputs": {}}
        flow_start.metadata = {"flow_id": "llm_test_flow"}

        # LLM step events with token usage
        llm_start = Mock()
        llm_start.type = Mock(value="step:started")
        llm_start.timestamp = datetime(2025, 1, 5, 12, 0, 1, tzinfo=timezone.utc)
        llm_start.payload = None
        llm_start.metadata = {"id": "llm_step"}

        llm_finish = Mock()
        llm_finish.type = Mock(value="step:finished")
        llm_finish.timestamp = datetime(2025, 1, 5, 12, 0, 3, tzinfo=timezone.utc)
        llm_finish.payload = None
        llm_finish.metadata = {"id": "llm_step"}

        llm_result = Mock()
        llm_result.type = Mock(value="step:result")
        llm_result.timestamp = datetime(2025, 1, 5, 12, 0, 3, tzinfo=timezone.utc)
        llm_result.payload = {
            "value": {
                "content": "LLM generated text",
                "model": "gpt-4o-2024-08-06",
                "usage": {
                    "input": 250,
                    "output": 150,
                    "total": 400,
                },
            }
        }
        llm_result.metadata = {"id": "llm_step"}

        # Regular step events
        reg_start = Mock()
        reg_start.type = Mock(value="step:started")
        reg_start.timestamp = datetime(2025, 1, 5, 12, 0, 4, tzinfo=timezone.utc)
        reg_start.payload = None
        reg_start.metadata = {"id": "regular_step"}

        reg_finish = Mock()
        reg_finish.type = Mock(value="step:finished")
        reg_finish.timestamp = datetime(2025, 1, 5, 12, 0, 5, tzinfo=timezone.utc)
        reg_finish.payload = None
        reg_finish.metadata = {"id": "regular_step"}

        reg_result = Mock()
        reg_result.type = Mock(value="step:result")
        reg_result.timestamp = datetime(2025, 1, 5, 12, 0, 5, tzinfo=timezone.utc)
        reg_result.payload = {"value": {"result": "processed"}}
        reg_result.metadata = {"id": "regular_step"}

        flow_finish = Mock()
        flow_finish.type = Mock(value="flow:finished")
        flow_finish.timestamp = datetime(2025, 1, 5, 12, 0, 6, tzinfo=timezone.utc)
        flow_finish.payload = None
        flow_finish.metadata = {"flow_id": "llm_test_flow"}

        result.event_log = [
            flow_start,
            llm_start,
            llm_finish,
            llm_result,
            reg_start,
            reg_finish,
            reg_result,
            flow_finish,
        ]

        llm_value = Mock()
        llm_value.value = {
            "content": "LLM generated text",
            "model": "gpt-4o-2024-08-06",
            "usage": {"input": 250, "output": 150, "total": 400},
        }

        reg_value = Mock()
        reg_value.value = {"result": "processed"}

        result.value = {
            "llm_step": llm_value,
            "regular_step": reg_value,
        }

        # Generate provenance
        prov = generate_provenance(
            flow=flow,
            result=result,
            inputs={},
            started_at="2025-01-05T12:00:00+00:00",
            completed_at="2025-01-05T12:00:06+00:00",
        )

        # Verify provenance was generated
        assert prov.manifest is not None
        assert prov.trig is not None

        # Parse the RDF and verify LLM metadata
        from rdflib import Dataset, URIRef

        ds = Dataset()
        ds.parse(data=prov.trig, format="trig")

        base = "http://lunarbase.ai/prov"
        run_id = prov.manifest.run_id
        b_ret_iri = prov.manifest.bundles["retrospective"]
        g_ret = ds.graph(URIRef(b_ret_iri))

        # Check LLM step has generative=True, model, and token usage
        act_llm = URIRef(f"{base}/run/{run_id}/activity/step/llm_step")

        generativeProperty = URIRef(f"{base}/generative")
        modelProperty = URIRef(f"{base}/model")
        inputTokensProperty = URIRef(f"{base}/inputTokens")
        outputTokensProperty = URIRef(f"{base}/outputTokens")
        totalTokensProperty = URIRef(f"{base}/totalTokens")

        # Verify generative flag
        gen_values = list(g_ret.objects(act_llm, generativeProperty))
        assert len(gen_values) > 0, "LLM step should have generative property"
        assert gen_values[0].toPython() is True  # type: ignore[attr-defined]

        # Verify model
        model_values = list(g_ret.objects(act_llm, modelProperty))
        assert len(model_values) > 0
        assert "gpt-4o" in str(model_values[0])

        # Verify token usage
        input_tokens = list(g_ret.objects(act_llm, inputTokensProperty))
        assert len(input_tokens) > 0
        assert input_tokens[0].toPython() == 250  # type: ignore[attr-defined]

        output_tokens = list(g_ret.objects(act_llm, outputTokensProperty))
        assert len(output_tokens) > 0
        assert output_tokens[0].toPython() == 150  # type: ignore[attr-defined]

        total_tokens = list(g_ret.objects(act_llm, totalTokensProperty))
        assert len(total_tokens) > 0
        assert total_tokens[0].toPython() == 400  # type: ignore[attr-defined]

        # Check non-LLM step has generative=False and no LLM metadata
        act_reg = URIRef(f"{base}/run/{run_id}/activity/step/regular_step")

        gen_reg_values = list(g_ret.objects(act_reg, generativeProperty))
        assert len(gen_reg_values) > 0
        assert gen_reg_values[0].toPython() is False  # type: ignore[attr-defined]

        model_reg_values = list(g_ret.objects(act_reg, modelProperty))
        assert len(model_reg_values) == 0

        input_tokens_reg = list(g_ret.objects(act_reg, inputTokensProperty))
        assert len(input_tokens_reg) == 0
