# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Optional, Dict, Any

from lunar_api.flows.flow_registry import FlowRegistry
from lunar_api.flows.task_status import TaskStatusManager


class GetAgentProvenanceUseCase:
    def __init__(
        self,
        flow_registry: FlowRegistry,
        task_manager: TaskStatusManager,
    ):
        self._flow_registry = flow_registry
        self._task_manager = task_manager

    async def execute(self, flow_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the provenance data for a completed agent execution.

        Returns the PROV-O provenance data including manifest and view model.

        Args:
            flow_id: The flow ID to get provenance for

        Returns:
            Dictionary with provenance data or None/error dict if issues occur
        """
        flow = self._flow_registry.get(flow_id)
        if not flow:
            return None

        task_info = await self._task_manager.get_status(flow.get_id(), user_id=user_id)

        if task_info.status.value == "running":
            return {"error": "still_running", "flow_id": flow_id}

        if task_info.status.value == "idle":
            return {"error": "not_executed", "flow_id": flow_id}

        if task_info.status.value == "failed":
            return {
                "error": "execution_failed",
                "flow_id": flow_id,
                "message": task_info.error,
            }

        # Extract provenance from result
        result = task_info.result
        if not result:
            return {"error": "no_result", "flow_id": flow_id}

        provenance = result.get("provenance")
        if not provenance:
            return {"error": "no_provenance", "flow_id": flow_id}

        if "error" in provenance:
            return {
                "error": "provenance_generation_failed",
                "message": provenance["error"],
            }

        return {
            "flow_id": flow_id,
            "manifest": provenance.get("manifest"),
            "view_model": provenance.get("view_model"),
        }
