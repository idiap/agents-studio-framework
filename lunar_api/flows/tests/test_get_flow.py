# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for the GetFlowUseCase."""

from unittest.mock import Mock

from lunar_api.flows.flow_registry import FlowRegistry
from lunar_api.flows.models import AgentInputConfig
from lunar_api.flows.use_case.get_flow import GetFlowUseCase


def create_mock_flow(flow_id: str, name: str, description: str = ""):
    """Helper to create a mock Flow object."""
    flow = Mock()
    flow.get_id.return_value = flow_id
    flow.get_name.return_value = name
    flow.get_description.return_value = description
    flow.get_nodes.return_value = []
    flow.to_json.return_value = (
        '{"id": "'
        + flow_id
        + '", "name": "'
        + name
        + '", "description": "'
        + description
        + '", "steps": {}}'
    )
    return flow


class TestGetFlowUseCase:
    """Test GetFlowUseCase."""

    def test_execute_returns_normalized_agent_config_by_default(self):
        """Test default get-flow response uses normalized config shape."""
        registry = FlowRegistry()
        flow = create_mock_flow("test_flow", "Test Flow", "Flow description")
        registry.register(
            flow,
            inputs=[
                AgentInputConfig(
                    id="argument",
                    label="Argument",
                    type="string",
                    required=True,
                )
            ],
        )

        use_case = GetFlowUseCase(flow_registry=registry)

        result = use_case.execute("test_flow")

        assert result == {
            "id": "test_flow",
            "name": "Test Flow",
            "description": "Flow description",
            "inputs": [
                {
                    "id": "argument",
                    "label": "Argument",
                    "type": "string",
                    "required": True,
                }
            ],
        }

    def test_execute_returns_raw_definition_when_requested(self):
        """Test raw flow definition can still be fetched for the editor."""
        registry = FlowRegistry()
        flow = create_mock_flow("test_flow", "Test Flow", "Flow description")
        registry.register(flow)

        use_case = GetFlowUseCase(flow_registry=registry)

        result = use_case.execute("test_flow", definition=True)

        assert result == {
            "id": "test_flow",
            "name": "Test Flow",
            "description": "Flow description",
            "steps": {},
        }

    def test_execute_returns_none_for_unknown_flow(self):
        """Test missing flows return None."""
        use_case = GetFlowUseCase(flow_registry=FlowRegistry())

        assert use_case.execute("missing") is None
        assert use_case.execute("missing", definition=True) is None