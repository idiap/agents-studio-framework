# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import pytest
from unittest.mock import Mock, AsyncMock

from lunar_api.flows.use_case.cancel_agent import CancelAgentUseCase
from lunar_api.flows.task_status import TaskStatus, TaskInfo


@pytest.fixture
def mock_flow():
    """Create a mock flow."""
    flow = Mock()
    flow.get_id.return_value = "test_flow"
    flow.get_name.return_value = "Test Flow"
    return flow


@pytest.fixture
def mock_flow_registry(mock_flow):
    """Create a mock flow registry."""
    registry = Mock()
    registry.get.return_value = mock_flow
    return registry


@pytest.fixture
def mock_task_manager():
    """Create a mock task manager."""
    manager = Mock()
    manager.get_status = AsyncMock()
    manager.cancel_task = AsyncMock()
    return manager


class TestCancelAgentUseCase:
    """Test CancelAgentUseCase."""

    @pytest.mark.asyncio
    async def test_cancel_running_agent(self, mock_flow_registry, mock_task_manager, mock_flow):
        """Test cancelling a running agent."""
        mock_task_manager.get_status.return_value = TaskInfo(status=TaskStatus.RUNNING)
        mock_task_manager.cancel_task.return_value = True

        use_case = CancelAgentUseCase(
            flow_registry=mock_flow_registry,
            task_manager=mock_task_manager,
        )

        result = await use_case.execute(flow_id="test_flow")

        assert result is not None
        assert result["status"] == "cancelled"
        assert result["flow_id"] == "test_flow"
        assert "Test Flow" in result["message"]
        mock_task_manager.cancel_task.assert_called_once_with(
            "test_flow",
            user_id=None,
        )

    @pytest.mark.asyncio
    async def test_cancel_non_existent_flow(self, mock_task_manager):
        """Test cancelling a flow that doesn't exist."""
        registry = Mock()
        registry.get.return_value = None

        use_case = CancelAgentUseCase(
            flow_registry=registry,
            task_manager=mock_task_manager,
        )

        result = await use_case.execute(flow_id="nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_cancel_non_running_agent(self, mock_flow_registry, mock_task_manager, mock_flow):
        """Test cancelling an agent that's not running."""
        mock_task_manager.get_status.return_value = TaskInfo(status=TaskStatus.COMPLETED)

        use_case = CancelAgentUseCase(
            flow_registry=mock_flow_registry,
            task_manager=mock_task_manager,
        )

        result = await use_case.execute(flow_id="test_flow")

        assert result is not None
        assert result["error"] == "not_running"
        assert result["current_status"] == TaskStatus.COMPLETED
        mock_task_manager.cancel_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancel_idle_agent(self, mock_flow_registry, mock_task_manager, mock_flow):
        """Test cancelling an agent that's idle."""
        mock_task_manager.get_status.return_value = TaskInfo(status=TaskStatus.IDLE)

        use_case = CancelAgentUseCase(
            flow_registry=mock_flow_registry,
            task_manager=mock_task_manager,
        )

        result = await use_case.execute(flow_id="test_flow")

        assert result is not None
        assert result["error"] == "not_running"
        assert result["current_status"] == TaskStatus.IDLE

    @pytest.mark.asyncio
    async def test_cancel_failed_agent(self, mock_flow_registry, mock_task_manager, mock_flow):
        """Test cancelling an agent that has already failed."""
        mock_task_manager.get_status.return_value = TaskInfo(status=TaskStatus.FAILED)

        use_case = CancelAgentUseCase(
            flow_registry=mock_flow_registry,
            task_manager=mock_task_manager,
        )

        result = await use_case.execute(flow_id="test_flow")

        assert result is not None
        assert result["error"] == "not_running"
        assert result["current_status"] == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_agent(self, mock_flow_registry, mock_task_manager, mock_flow):
        """Test cancelling an agent that was already cancelled."""
        mock_task_manager.get_status.return_value = TaskInfo(status=TaskStatus.CANCELLED)

        use_case = CancelAgentUseCase(
            flow_registry=mock_flow_registry,
            task_manager=mock_task_manager,
        )

        result = await use_case.execute(flow_id="test_flow")

        assert result is not None
        assert result["error"] == "not_running"
        assert result["current_status"] == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_fails_internally(self, mock_flow_registry, mock_task_manager, mock_flow):
        """Test when cancel_task returns False unexpectedly."""
        mock_task_manager.get_status.return_value = TaskInfo(status=TaskStatus.RUNNING)
        mock_task_manager.cancel_task.return_value = False

        use_case = CancelAgentUseCase(
            flow_registry=mock_flow_registry,
            task_manager=mock_task_manager,
        )

        result = await use_case.execute(flow_id="test_flow")

        assert result is not None
        assert result["error"] == "cancel_failed"
        assert result["flow_id"] == "test_flow"
