# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import List, Dict, Any

from lunar_api.flows.flow_registry import FlowRegistry


class ListFlowsUseCase:
    def __init__(self, flow_registry: FlowRegistry):
        self._flow_registry = flow_registry

    def execute(self) -> List[Dict[str, Any]]:
        """List all registered agents with their configurations.

        Returns:
            List of agent configuration dictionaries with id, name, description, and inputs
        """
        configs = self._flow_registry.list_all_configs()
        return [config.to_dict() for config in configs]
