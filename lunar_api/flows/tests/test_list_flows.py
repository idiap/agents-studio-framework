# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for the ListFlowsUseCase."""

from unittest.mock import Mock
from lunar_api.flows.use_case.list_flows import ListFlowsUseCase
from lunar_api.flows.flow_registry import FlowRegistry
from lunar_api.flows.models import AgentInputConfig


def create_mock_flow(flow_id: str, name: str, description: str = ""):
    """Helper to create a mock Flow object."""
    flow = Mock()
    flow.get_id.return_value = flow_id
    flow.get_name.return_value = name
    flow.get_description.return_value = description
    flow.get_inputs.return_value = {}
    return flow


class TestListFlowsUseCase:
    """Test ListFlowsUseCase class."""

    def test_execute_with_no_flows(self):
        """Test executing use case with empty registry."""
        registry = FlowRegistry()
        use_case = ListFlowsUseCase(flow_registry=registry)

        result = use_case.execute()

        assert result == []

    def test_execute_with_single_flow(self):
        """Test executing use case with a single flow."""
        registry = FlowRegistry()
        flow = create_mock_flow(
            "test_flow", "Test Flow", "A test flow description"
        )
        inputs = [
            AgentInputConfig(
                id="input1",
                label="Input One",
                type="string",
                required=True,
            ),
        ]
        registry.register(flow, inputs=inputs)
        use_case = ListFlowsUseCase(flow_registry=registry)

        result = use_case.execute()

        assert len(result) == 1
        assert result[0]["id"] == "test_flow"
        assert result[0]["name"] == "Test Flow"
        assert result[0]["description"] == "A test flow description"
        assert len(result[0]["inputs"]) == 1
        assert result[0]["inputs"][0]["id"] == "input1"
        assert result[0]["inputs"][0]["label"] == "Input One"
        assert result[0]["inputs"][0]["type"] == "string"
        assert result[0]["inputs"][0]["required"] is True

    def test_execute_with_multiple_flows(self):
        """Test executing use case with multiple flows."""
        registry = FlowRegistry()

        flow1 = create_mock_flow("flow1", "Flow One", "First flow")
        flow2 = create_mock_flow("flow2", "Flow Two", "Second flow")
        flow3 = create_mock_flow("flow3", "Flow Three", "Third flow")

        registry.register(
            flow1,
            inputs=[
                AgentInputConfig(
                    id="kb_field",
                    label="Knowledge Base Field",
                    type="knowledge-base-field",
                    required=True,
                ),
            ],
        )
        registry.register(
            flow2,
            inputs=[
                AgentInputConfig(
                    id="param1",
                    label="Parameter 1",
                    type="string",
                    required=True,
                ),
                AgentInputConfig(
                    id="param2",
                    label="Parameter 2",
                    type="string",
                    required=False,
                ),
            ],
        )
        registry.register(flow3, inputs=[])

        use_case = ListFlowsUseCase(flow_registry=registry)

        result = use_case.execute()

        assert len(result) == 3

        # Find each flow in results (order may vary)
        flow1_result = next((f for f in result if f["id"] == "flow1"), None)
        flow2_result = next((f for f in result if f["id"] == "flow2"), None)
        flow3_result = next((f for f in result if f["id"] == "flow3"), None)

        assert flow1_result is not None
        assert len(flow1_result["inputs"]) == 1
        assert flow1_result["inputs"][0]["type"] == "knowledge-base-field"

        assert flow2_result is not None
        assert len(flow2_result["inputs"]) == 2

        assert flow3_result is not None
        assert len(flow3_result["inputs"]) == 0

    def test_execute_returns_correct_input_types(self):
        """Test that all input types are correctly returned."""
        registry = FlowRegistry()
        flow = create_mock_flow("type_test_flow", "Type Test Flow", "Testing input types")

        inputs = [
            AgentInputConfig(
                id="string_input",
                label="String Input",
                type="string",
                required=True,
            ),
            AgentInputConfig(
                id="kb_input",
                label="Knowledge Base",
                type="knowledge-base",
                required=True,
            ),
            AgentInputConfig(
                id="kb_field_input",
                label="Knowledge Base Field",
                type="knowledge-base-field",
                required=False,
            ),
        ]

        registry.register(flow, inputs=inputs)
        use_case = ListFlowsUseCase(flow_registry=registry)

        result = use_case.execute()

        assert len(result) == 1
        assert len(result[0]["inputs"]) == 3

        input_types = {inp["id"]: inp["type"] for inp in result[0]["inputs"]}
        assert input_types["string_input"] == "string"
        assert input_types["kb_input"] == "knowledge-base"
        assert input_types["kb_field_input"] == "knowledge-base-field"

        input_required = {inp["id"]: inp["required"] for inp in result[0]["inputs"]}
        assert input_required["string_input"] is True
        assert input_required["kb_input"] is True
        assert input_required["kb_field_input"] is False
