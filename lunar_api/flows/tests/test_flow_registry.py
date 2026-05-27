# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for the FlowRegistry."""

import pytest
from unittest.mock import Mock
from lunar_api.flows.flow_registry import FlowRegistry
from lunar_api.flows.models import AgentInputConfig


def create_mock_flow(flow_id: str, name: str, description: str = ""):
    """Helper to create a mock Flow object."""
    flow = Mock()
    flow.get_id.return_value = flow_id
    flow.get_name.return_value = name
    flow.get_description.return_value = description
    flow.get_inputs.return_value = {}
    flow.get_nodes.return_value = []
    return flow


class TestFlowRegistry:
    """Test FlowRegistry class."""

    def test_register_flow_without_inputs(self):
        """Test registering a flow without input configurations."""
        registry = FlowRegistry()
        flow = create_mock_flow("test_flow", "Test Flow", "A test flow")

        registry.register(flow)

        assert registry.get("test_flow") == flow
        config = registry.get_config("test_flow")
        assert config is not None
        assert config.id == "test_flow"
        assert config.name == "Test Flow"
        assert config.description == "A test flow"
        assert config.inputs == []

    def test_register_flow_infers_inputs_when_not_provided(self):
        """Test registering a flow infers inputs from node references."""
        registry = FlowRegistry()
        flow = create_mock_flow("inferred_flow", "Inferred Flow", "Uses inferred inputs")
        flow.get_nodes.return_value = [
            Mock(inputs={"prompt": "Analyze &argument using &knowledge_base_id"}),
            Mock(inputs={"field": "&kb_field_id", "note": "&optional_instructions"}),
        ]

        registry.register(flow)

        config = registry.get_config("inferred_flow")
        assert config is not None
        assert [input_config.id for input_config in config.inputs] == [
            "argument",
            "kb_field_id",
            "knowledge_base_id",
            "optional_instructions",
        ]
        assert [input_config.type for input_config in config.inputs] == [
            "string",
            "knowledge-base-field",
            "knowledge-base",
            "string",
        ]
        assert [input_config.required for input_config in config.inputs] == [
            True,
            True,
            True,
            False,
        ]

    def test_register_flow_with_inputs(self):
        """Test registering a flow with input configurations."""
        registry = FlowRegistry()
        flow = create_mock_flow("agent_flow", "Agent Flow", "An agent flow")
        inputs = [
            AgentInputConfig(
                id="kb_field_id",
                label="Knowledge Base Field",
                type="knowledge-base-field",
                required=True,
            ),
            AgentInputConfig(
                id="user_input",
                label="User Input",
                type="string",
                required=False,
            ),
        ]

        registry.register(flow, inputs=inputs)

        config = registry.get_config("agent_flow")
        assert config is not None
        assert len(config.inputs) == 2
        assert config.inputs[0].id == "kb_field_id"
        assert config.inputs[0].type == "knowledge-base-field"
        assert config.inputs[0].required is True
        assert config.inputs[1].id == "user_input"
        assert config.inputs[1].required is False

    def test_register_duplicate_raises_error(self):
        """Test that registering a duplicate flow raises an error."""
        registry = FlowRegistry()
        flow1 = create_mock_flow("duplicate_flow", "Flow 1")
        flow2 = create_mock_flow("duplicate_flow", "Flow 2")

        registry.register(flow1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(flow2)

    def test_get_nonexistent_flow_returns_none(self):
        """Test that getting a nonexistent flow returns None."""
        registry = FlowRegistry()

        assert registry.get("nonexistent") is None
        assert registry.get_config("nonexistent") is None

    def test_get_with_config(self):
        """Test getting both flow and config together."""
        registry = FlowRegistry()
        flow = create_mock_flow("combo_flow", "Combo Flow", "Test combo")
        inputs = [
            AgentInputConfig(
                id="input1",
                label="Input 1",
                type="string",
                required=True,
            ),
        ]

        registry.register(flow, inputs=inputs)

        result = registry.get_with_config("combo_flow")
        assert result is not None
        flow_result, config_result = result
        assert flow_result == flow
        assert config_result.id == "combo_flow"
        assert len(config_result.inputs) == 1

    def test_get_with_config_nonexistent_returns_none(self):
        """Test that get_with_config returns None for nonexistent flow."""
        registry = FlowRegistry()

        assert registry.get_with_config("nonexistent") is None

    def test_list_all_flows(self):
        """Test listing all registered flows."""
        registry = FlowRegistry()
        flow1 = create_mock_flow("flow1", "Flow 1")
        flow2 = create_mock_flow("flow2", "Flow 2")
        flow3 = create_mock_flow("flow3", "Flow 3")

        registry.register(flow1)
        registry.register(flow2)
        registry.register(flow3)

        flows = registry.list_all()
        assert len(flows) == 3

    def test_list_all_configs(self):
        """Test listing all agent configurations."""
        registry = FlowRegistry()
        flow1 = create_mock_flow("flow1", "Flow 1", "Description 1")
        flow2 = create_mock_flow("flow2", "Flow 2", "Description 2")

        registry.register(
            flow1,
            inputs=[
                AgentInputConfig(
                    id="input1", label="Input 1", type="string", required=True
                )
            ],
        )
        registry.register(flow2, inputs=[])

        configs = registry.list_all_configs()
        assert len(configs) == 2

        config_ids = [c.id for c in configs]
        assert "flow1" in config_ids
        assert "flow2" in config_ids

    def test_list_all_configs_empty_registry(self):
        """Test listing configs from an empty registry."""
        registry = FlowRegistry()

        configs = registry.list_all_configs()
        assert configs == []
