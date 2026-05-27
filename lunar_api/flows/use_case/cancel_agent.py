# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Optional, Dict, Any

from lunar_api.flows.flow_registry import FlowRegistry
from lunar_api.flows.task_status import TaskStatusManager


class CancelAgentUseCase:
    def __init__(
        self,
        flow_registry: FlowRegistry,
        task_manager: TaskStatusManager,
    ):
        self._flow_registry = flow_registry
        self._task_manager = task_manager

    async def execute(self, flow_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Cancel a running agent by ID.

        Args:
            flow_id: The flow ID to cancel

        Returns:
            Dict with status info, or None if flow not found
        """
        flow = self._flow_registry.get(flow_id)
        if not flow:
            return None

        # Check if the task is running
        status = await self._task_manager.get_status(flow.get_id(), user_id=user_id)
        if status.status != "running":
            return {
                "error": "not_running",
                "flow_id": flow_id,
                "flow_name": flow.get_name(),
                "current_status": status.status,
            }

        # Cancel the task
        cancelled = await self._task_manager.cancel_task(flow.get_id(), user_id=user_id)
        
        if not cancelled:
            return {
                "error": "cancel_failed",
                "flow_id": flow_id,
                "flow_name": flow.get_name(),
            }

        return {
            "status": "cancelled",
            "message": f"{flow.get_name()} has been cancelled",
            "flow_id": flow_id,
        }
