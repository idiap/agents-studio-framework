# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Dict, List, Optional, Tuple
from lunarflow.flows import Flow

from lunar_api.flows.input_inference import infer_inputs_from_flow
from lunar_api.flows.models import AgentConfig, AgentInputConfig


class FlowRegistry:
    """Central registry for all available agents."""

    def __init__(self):
        self._flows: Dict[str, Flow] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}

    def register(
        self,
        flow: Flow,
        inputs: Optional[List[AgentInputConfig]] = None,
    ) -> None:
        """Register a new agent with optional input configuration.

        Args:
            flow: The lunarflow Flow object
            inputs: Optional list of input configurations with metadata
        """
        flow_id = flow.get_id()
        if flow_id in self._flows:
            raise ValueError(f"Agent with id '{flow_id}' is already registered")

        self._flows[flow_id] = flow
        resolved_inputs = inputs if inputs is not None else infer_inputs_from_flow(flow)
        self._agent_configs[flow_id] = AgentConfig(
            id=flow_id,
            name=flow.get_name(),
            description=flow.get_description() or "",
            inputs=resolved_inputs,
        )

    def get(self, agent_id: str) -> Optional[Flow]:
        """Get agent flow by ID."""
        return self._flows.get(agent_id)

    def get_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID."""
        return self._agent_configs.get(agent_id)

    def get_with_config(
        self, agent_id: str
    ) -> Optional[Tuple[Flow, AgentConfig]]:
        """Get both flow and config by ID."""
        flow = self._flows.get(agent_id)
        config = self._agent_configs.get(agent_id)
        if flow and config:
            return (flow, config)
        return None

    def get_by_task_type(self, task_type: str) -> Optional[Flow]:
        """Get agent configuration by task type."""
        for config in self._flows.values():
            if hasattr(config, "task_type") and config.task_type == task_type:  # type: ignore[attr-defined]
                return config
        return None

    def list_all(self) -> List[Flow]:
        """List all registered agent flows."""
        return list(self._flows.values())

    def list_all_configs(self) -> List[AgentConfig]:
        """List all registered agent configurations."""
        return list(self._agent_configs.values())

    def get_task_types(self) -> List[str]:
        """Get all task types."""
        return [config.task_type for config in self._flows.values() if hasattr(config, "task_type")]  # type: ignore[attr-defined]


flow_registry = FlowRegistry()
