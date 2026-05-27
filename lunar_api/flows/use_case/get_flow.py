# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import json
from typing import Optional, Dict, Any

from lunar_api.flows.flow_registry import FlowRegistry


class GetFlowUseCase:
    def __init__(self, flow_registry: FlowRegistry):
        self._flow_registry = flow_registry

    def execute(
        self,
        flow_id: str,
        *,
        definition: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Get flow configuration by ID.

        Args:
            flow_id: The flow ID to retrieve

        Returns:
            Flow configuration dictionary or None if not found
        """
        flow = self._flow_registry.get(flow_id)
        if not flow:
            return None

        if not definition:
            config = self._flow_registry.get_config(flow_id)
            return config.to_dict() if config else None

        flow_json = flow.to_json()
        return json.loads(flow_json)
