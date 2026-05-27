# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Optional

from lunar_api.flows.flow_registry import FlowRegistry
from lunar_api.flows.task_status import TaskStatusManager, TaskInfo


class GetAgentStatusUseCase:
    def __init__(
        self,
        flow_registry: FlowRegistry,
        task_manager: TaskStatusManager,
    ):
        self._flow_registry = flow_registry
        self._task_manager = task_manager

    async def execute(self, flow_id: str, user_id: Optional[str] = None) -> Optional[TaskInfo]:
        """Get the status of a specific agent by ID.

        Args:
            flow_id: The flow ID to check status for

        Returns:
            TaskInfo object or None if flow not found
        """
        flow = self._flow_registry.get(flow_id)
        if not flow:
            return None

        return await self._task_manager.get_status(flow.get_id(), user_id=user_id)
