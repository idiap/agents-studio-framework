# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for the provenance-related router endpoints.

These tests verify the API endpoints for retrieving provenance data.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from fastapi import HTTPException
from uuid import uuid4

from lunar_api.auth.model import AuthenticatedUser

TEST_AUTHENTICATED_USER = AuthenticatedUser(id=uuid4(), login="test-user")


# ============================================================================
# Test fixtures
# ============================================================================


@pytest.fixture
def mock_flow():
    """Create a mock Flow object."""
    flow = Mock()
    flow.get_id.return_value = "test_flow"
    flow.get_name.return_value = "Test Flow"
    flow.get_description.return_value = "Test description"
    flow.get_inputs.return_value = {"input": "value"}
    return flow


@pytest.fixture
def mock_task_manager():
    """Create a mock TaskStatusManager."""
    manager = Mock()
    manager.get_status = AsyncMock()
    manager.is_running = AsyncMock(return_value=False)
    manager.start_task = AsyncMock(return_value=True)
    manager.update_progress = AsyncMock()
    manager.complete_task = AsyncMock()
    manager.fail_task = AsyncMock()
    return manager


@pytest.fixture
def mock_task_info_completed():
    """Create a mock TaskInfo for completed state with provenance."""
    from lunar_api.flows.task_status import TaskInfo, TaskStatus

    return TaskInfo(
        status=TaskStatus.COMPLETED,
        started_at="2025-01-05T12:00:00+00:00",
        completed_at="2025-01-05T12:00:05+00:00",
        result={
            "execution_result": {"step_1": {"value": "result"}},
            "provenance": {
                "manifest": {
                    "base_uri": "http://lunarbase.ai/prov",
                    "flow_id": "test_flow",
                    "run_id": "test_flow-2025-01-05T12:00:00+00:00",
                    "bundles": {
                        "prospective": "http://lunarbase.ai/prov/bundle/prospective",
                        "retrospective": "http://lunarbase.ai/prov/bundle/retrospective/test_flow-2025-01-05T12:00:00+00:00",
                    },
                    "generated_at": "2025-01-05T12:00:05+00:00",
                    "bundle_hashes": {
                        "http://lunarbase.ai/prov/bundle/prospective": {
                            "sha256_nt_sorted": "abc123",
                            "triple_count": 10,
                        },
                    },
                },
                "trig": "@prefix prov: <http://www.w3.org/ns/prov#> .",
                "view_model": {"steps": [], "edges": []},
            },
        },
    )


@pytest.fixture
def mock_task_info_running():
    """Create a mock TaskInfo for running state."""
    from lunar_api.flows.task_status import TaskInfo, TaskStatus

    return TaskInfo(
        status=TaskStatus.RUNNING,
        started_at="2025-01-05T12:00:00+00:00",
    )


@pytest.fixture
def mock_task_info_idle():
    """Create a mock TaskInfo for idle state."""
    from lunar_api.flows.task_status import TaskInfo, TaskStatus

    return TaskInfo(status=TaskStatus.IDLE)


@pytest.fixture
def mock_task_info_failed():
    """Create a mock TaskInfo for failed state."""
    from lunar_api.flows.task_status import TaskInfo, TaskStatus

    return TaskInfo(
        status=TaskStatus.FAILED,
        error="Execution failed",
    )


# ============================================================================
# Test get_agent_provenance endpoint logic
# ============================================================================


class TestGetAgentProvenanceLogic:
    """Tests for the provenance endpoint logic."""

    @pytest.mark.asyncio
    async def test_provenance_not_found_flow(self, mock_task_manager):
        """Test that 404 is returned when flow doesn't exist."""
        from lunar_api.flows.router import get_agent_provenance, flow_registry

        # Temporarily patch the flow_registry
        original_get = flow_registry.get
        flow_registry.get = Mock(return_value=None)

        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_agent_provenance(
                    "nonexistent_flow",
                    current_user=TEST_AUTHENTICATED_USER,
                )
            assert exc_info.value.status_code == 404
        finally:
            flow_registry.get = original_get

    @pytest.mark.asyncio
    async def test_provenance_flow_still_running(
        self, mock_flow, mock_task_manager, mock_task_info_running
    ):
        """Test that 409 is returned when flow is still running."""
        from lunar_api.flows.router import get_agent_provenance, flow_registry, task_manager

        original_get = flow_registry.get
        flow_registry.get = Mock(return_value=mock_flow)

        original_task_manager_get = task_manager.get_status
        task_manager.get_status = AsyncMock(return_value=mock_task_info_running)

        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_agent_provenance(
                    "test_flow",
                    current_user=TEST_AUTHENTICATED_USER,
                )
            assert exc_info.value.status_code == 409
        finally:
            flow_registry.get = original_get
            task_manager.get_status = original_task_manager_get

    @pytest.mark.asyncio
    async def test_provenance_flow_not_run(
        self, mock_flow, mock_task_manager, mock_task_info_idle
    ):
        """Test that 404 is returned when flow hasn't been run."""
        from lunar_api.flows.router import get_agent_provenance, flow_registry, task_manager

        original_get = flow_registry.get
        flow_registry.get = Mock(return_value=mock_flow)

        original_task_manager_get = task_manager.get_status
        task_manager.get_status = AsyncMock(return_value=mock_task_info_idle)

        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_agent_provenance(
                    "test_flow",
                    current_user=TEST_AUTHENTICATED_USER,
                )
            assert exc_info.value.status_code == 404
        finally:
            flow_registry.get = original_get
            task_manager.get_status = original_task_manager_get

    @pytest.mark.asyncio
    async def test_provenance_flow_failed(
        self, mock_flow, mock_task_manager, mock_task_info_failed
    ):
        """Test that 400 is returned when flow execution failed."""
        from lunar_api.flows.router import get_agent_provenance, flow_registry, task_manager

        original_get = flow_registry.get
        flow_registry.get = Mock(return_value=mock_flow)

        original_task_manager_get = task_manager.get_status
        task_manager.get_status = AsyncMock(return_value=mock_task_info_failed)

        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_agent_provenance(
                    "test_flow",
                    current_user=TEST_AUTHENTICATED_USER,
                )
            assert exc_info.value.status_code == 400
        finally:
            flow_registry.get = original_get
            task_manager.get_status = original_task_manager_get

    @pytest.mark.asyncio
    async def test_provenance_success(
        self, mock_flow, mock_task_manager, mock_task_info_completed
    ):
        """Test successful provenance retrieval."""
        from lunar_api.flows.router import get_agent_provenance, flow_registry, task_manager

        original_get = flow_registry.get
        flow_registry.get = Mock(return_value=mock_flow)

        original_task_manager_get = task_manager.get_status
        task_manager.get_status = AsyncMock(return_value=mock_task_info_completed)

        try:
            result = await get_agent_provenance(
                "test_flow",
                current_user=TEST_AUTHENTICATED_USER,
            )

            assert "flow_id" in result
            assert "manifest" in result
            assert "view_model" in result
            assert result["flow_id"] == "test_flow"
        finally:
            flow_registry.get = original_get
            task_manager.get_status = original_task_manager_get


# ============================================================================
# Test get_agent_provenance_trig endpoint logic
# ============================================================================


class TestGetAgentProvenanceTriGLogic:
    """Tests for the TriG provenance endpoint logic."""

    @pytest.mark.asyncio
    async def test_trig_success(
        self, mock_flow, mock_task_manager, mock_task_info_completed
    ):
        """Test successful TriG retrieval."""
        from lunar_api.flows.router import (
            get_agent_provenance_trig,
            flow_registry,
            task_manager,
        )

        original_get = flow_registry.get
        flow_registry.get = Mock(return_value=mock_flow)

        original_task_manager_get = task_manager.get_status
        task_manager.get_status = AsyncMock(return_value=mock_task_info_completed)

        try:
            result = await get_agent_provenance_trig(
                "test_flow",
                current_user=TEST_AUTHENTICATED_USER,
            )

            # Should return a PlainTextResponse
            assert hasattr(result, "body")
        finally:
            flow_registry.get = original_get
            task_manager.get_status = original_task_manager_get

    @pytest.mark.asyncio
    async def test_trig_not_completed(
        self, mock_flow, mock_task_manager, mock_task_info_running
    ):
        """Test that 400 is returned when flow is not completed."""
        from lunar_api.flows.router import (
            get_agent_provenance_trig,
            flow_registry,
            task_manager,
        )

        original_get = flow_registry.get
        flow_registry.get = Mock(return_value=mock_flow)

        original_task_manager_get = task_manager.get_status
        task_manager.get_status = AsyncMock(return_value=mock_task_info_running)

        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_agent_provenance_trig(
                    "test_flow",
                    current_user=TEST_AUTHENTICATED_USER,
                )
            assert exc_info.value.status_code == 400
        finally:
            flow_registry.get = original_get
            task_manager.get_status = original_task_manager_get


# ============================================================================
# Test execute_flow with provenance
# ============================================================================


class TestExecuteFlowWithProvenance:
    """Tests for execute_flow function with provenance generation."""

    @pytest.mark.asyncio
    async def test_execute_flow_generates_provenance(
        self, mock_flow, mock_task_manager
    ):
        """Test that RunAgentUseCase generates provenance data."""
        from lunar_api.flows.use_case.run_agent import RunAgentUseCase
        from lunar_api.flows.flow_registry import FlowRegistry
        from fastapi import BackgroundTasks

        background_tasks = BackgroundTasks()
        mock_registry = MagicMock(spec=FlowRegistry)
        mock_registry.get.return_value = mock_flow

        mock_task_manager.is_running.return_value = False

        use_case = RunAgentUseCase(
            flow_registry=mock_registry,
            task_manager=mock_task_manager,
        )

        result = await use_case.execute(
            flow_id="test_flow",
            inputs={"test": "input"},
            background_tasks=background_tasks,
            generate_prov=True,
        )

        assert result is not None

        assert result["status"] == "accepted"
        assert result["agent_id"] == "test_flow"

    @pytest.mark.asyncio
    async def test_execute_flow_already_running(self, mock_flow, mock_task_manager):
        """Test that error is returned when flow is already running."""
        from lunar_api.flows.use_case.run_agent import RunAgentUseCase
        from lunar_api.flows.flow_registry import FlowRegistry
        from fastapi import BackgroundTasks

        background_tasks = BackgroundTasks()
        mock_registry = MagicMock(spec=FlowRegistry)
        mock_registry.get.return_value = mock_flow

        mock_task_manager.is_running.return_value = True

        use_case = RunAgentUseCase(
            flow_registry=mock_registry,
            task_manager=mock_task_manager,
        )

        result = await use_case.execute(
            flow_id="test_flow",
            inputs={},
            background_tasks=background_tasks,
        )

        assert result is not None

        assert result["error"] == "already_running"
