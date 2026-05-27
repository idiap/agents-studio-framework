# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Optional, Dict, Any

from lunar_api.flows.flow_registry import FlowRegistry
from lunar_api.flows.task_status import TaskStatusManager


class GetAgentProvenanceTriGUseCase:
    def __init__(
        self,
        flow_registry: FlowRegistry,
        task_manager: TaskStatusManager,
    ):
        self._flow_registry = flow_registry
        self._task_manager = task_manager

    async def execute(self, flow_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the full TriG RDF provenance data for a completed agent execution.

        Args:
            flow_id: The flow ID to get TriG data for

        Returns:
            Dictionary with trig_data and flow_id, or None/error dict if issues occur
        """
        flow = self._flow_registry.get(flow_id)
        if not flow:
            return None

        task_info = await self._task_manager.get_status(flow.get_id(), user_id=user_id)

        if task_info.status.value != "completed":
            return {
                "error": "not_completed",
                "flow_id": flow_id,
                "status": task_info.status.value,
            }

        result = task_info.result
        if not result:
            return {"error": "no_result", "flow_id": flow_id}

        provenance = result.get("provenance", {})
        trig_data = provenance.get("trig")

        if not trig_data:
            return {"error": "no_trig_data", "flow_id": flow_id}

        return {"trig_data": trig_data, "flow_id": flow_id}
