# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import pytest
from unittest.mock import Mock
from datetime import datetime, UTC
import json
from lunar_api.auth.model import SYSTEM_USER_ID
from lunar_api.flows.task_status import (
    TaskStatus,
    TaskInfo,
    TaskStatusManager,
)


@pytest.fixture
def mock_kv_storage():
    """Create a mock KV storage."""
    kv = Mock()
    kv.storage = {}

    def get_impl(key):
        return kv.storage.get(key)

    def put_impl(key, value):
        kv.storage[key] = value

    def delete_impl(key):
        if key in kv.storage:
            del kv.storage[key]

    kv.get = Mock(side_effect=get_impl)
    kv.put = Mock(side_effect=put_impl)
    kv.delete = Mock(side_effect=delete_impl)

    return kv


@pytest.fixture
def task_manager(mock_kv_storage):
    """Create a TaskStatusManager with mock KV storage."""
    return TaskStatusManager(mock_kv_storage)


class TestTaskInfo:
    """Test TaskInfo model."""

    def test_task_info_creation(self):
        """Test creating a TaskInfo object."""
        task_info = TaskInfo(status=TaskStatus.IDLE)
        assert task_info.status == TaskStatus.IDLE
        assert task_info.started_at is None
        assert task_info.completed_at is None
        assert task_info.progress is None
        assert task_info.error is None
        assert task_info.result is None
        assert task_info.metadata is None

    def test_task_info_with_all_fields(self):
        """Test creating a TaskInfo with all fields."""
        now = datetime.now(UTC).isoformat()
        task_info = TaskInfo(
            status=TaskStatus.RUNNING,
            started_at=now,
            completed_at=None,
            progress="Processing...",
            error=None,
            result={"data": "test"},
            metadata={"key": "value"},
        )
        assert task_info.status == TaskStatus.RUNNING
        assert task_info.started_at == now
        assert task_info.progress == "Processing..."
        assert task_info.result == {"data": "test"}
        assert task_info.metadata == {"key": "value"}

    def test_task_info_serialization(self):
        """Test that TaskInfo can be serialized to JSON."""
        task_info = TaskInfo(status=TaskStatus.COMPLETED, result={"count": 42})
        json_str = task_info.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["status"] == "completed"
        assert parsed["result"] == {"count": 42}


class TestTaskStatusManager:
    """Test TaskStatusManager class."""

    @pytest.mark.asyncio
    async def test_get_status_idle_when_not_exists(self, task_manager):
        """Test getting status returns IDLE when task doesn't exist."""
        status = await task_manager.get_status("nonexistent")
        assert status.status == TaskStatus.IDLE

    @pytest.mark.asyncio
    async def test_start_task(self, task_manager):
        """Test starting a task."""
        result = await task_manager.start_task("test_task", metadata={"user": "test"})
        assert result is True

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.RUNNING
        assert status.started_at is not None
        assert status.metadata == {"user": "test"}

    @pytest.mark.asyncio
    async def test_start_task_already_running(self, task_manager):
        """Test starting a task that's already running returns False."""
        await task_manager.start_task("test_task")
        result = await task_manager.start_task("test_task")
        assert result is False

    @pytest.mark.asyncio
    async def test_start_task_overrides_completed(self, task_manager):
        """Test that starting a task overrides a previously completed task."""
        # First run
        await task_manager.start_task("test_task", metadata={"run": 1})
        await task_manager.complete_task("test_task", result={"data": "first"})

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.COMPLETED
        assert status.result == {"data": "first"}
        assert status.metadata == {"run": 1}

        # Second run should override
        result = await task_manager.start_task("test_task", metadata={"run": 2})
        assert result is True

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.RUNNING
        assert status.result is None
        assert status.metadata == {"run": 2}

        # Complete second run
        await task_manager.complete_task("test_task", result={"data": "second"})

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.COMPLETED
        assert status.result == {"data": "second"}
        assert status.metadata == {"run": 2}

    @pytest.mark.asyncio
    async def test_start_task_overrides_failed(self, task_manager):
        """Test that starting a task overrides a previously failed task."""
        # First run that fails
        await task_manager.start_task("test_task", metadata={"run": 1})
        await task_manager.fail_task("test_task", "First run failed")

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.FAILED
        assert status.error == "First run failed"
        assert status.metadata == {"run": 1}

        # Second run should override
        result = await task_manager.start_task("test_task", metadata={"run": 2})
        assert result is True

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.RUNNING
        assert status.error is None
        assert status.metadata == {"run": 2}

        # Complete second run successfully
        await task_manager.complete_task("test_task", result={"data": "success"})

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.COMPLETED
        assert status.result == {"data": "success"}
        assert status.error is None

    @pytest.mark.asyncio
    async def test_is_running(self, task_manager):
        """Test checking if a task is running."""
        assert await task_manager.is_running("test_task") is False

        await task_manager.start_task("test_task")
        assert await task_manager.is_running("test_task") is True

    @pytest.mark.asyncio
    async def test_update_progress(self, task_manager):
        """Test updating task progress."""
        await task_manager.start_task("test_task")
        await task_manager.update_progress("test_task", "50% complete")

        status = await task_manager.get_status("test_task")
        assert status.progress == "50% complete"
        assert status.status == TaskStatus.RUNNING

    @pytest.mark.asyncio
    async def test_update_progress_non_running_task(self, task_manager):
        """Test updating progress on non-running task does nothing."""
        await task_manager.update_progress("test_task", "Should not work")

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.IDLE

    @pytest.mark.asyncio
    async def test_complete_task(self, task_manager):
        """Test completing a task."""
        await task_manager.start_task("test_task")
        await task_manager.complete_task("test_task", result={"output": "success"})

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.COMPLETED
        assert status.completed_at is not None
        assert status.result == {"output": "success"}
        assert status.progress == "Completed"

    @pytest.mark.asyncio
    async def test_fail_task(self, task_manager):
        """Test failing a task."""
        await task_manager.start_task("test_task")
        await task_manager.fail_task("test_task", "Something went wrong")

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.FAILED
        assert status.completed_at is not None
        assert status.error == "Something went wrong"
        assert status.progress == "Failed"

    @pytest.mark.asyncio
    async def test_cancel_task(self, task_manager):
        """Test cancelling a running task."""
        await task_manager.start_task("test_task")
        result = await task_manager.cancel_task("test_task")
        
        assert result is True
        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.CANCELLED
        assert status.completed_at is not None
        assert status.progress == "Cancelled by user"

    @pytest.mark.asyncio
    async def test_cancel_non_running_task(self, task_manager):
        """Test cancelling a task that's not running returns False."""
        # Task doesn't exist (IDLE)
        result = await task_manager.cancel_task("test_task")
        assert result is False
        
        # Task is completed
        await task_manager.start_task("test_task")
        await task_manager.complete_task("test_task", result={"done": True})
        result = await task_manager.cancel_task("test_task")
        assert result is False
        
    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_task(self, task_manager):
        """Test cancelling an already cancelled task returns False."""
        await task_manager.start_task("test_task")
        await task_manager.cancel_task("test_task")
        
        # Try to cancel again
        result = await task_manager.cancel_task("test_task")
        assert result is False

    @pytest.mark.asyncio
    async def test_start_after_cancel(self, task_manager):
        """Test that a cancelled task can be restarted."""
        await task_manager.start_task("test_task", metadata={"run": 1})
        await task_manager.cancel_task("test_task")
        
        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.CANCELLED
        
        # Start again should work
        result = await task_manager.start_task("test_task", metadata={"run": 2})
        assert result is True
        
        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.RUNNING
        assert status.metadata == {"run": 2}

    @pytest.mark.asyncio
    async def test_clear_task(self, task_manager):
        """Test clearing a task."""
        await task_manager.start_task("test_task")
        await task_manager.clear_task("test_task")

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.IDLE

    @pytest.mark.asyncio
    async def test_task_lifecycle(self, task_manager):
        """Test complete task lifecycle."""
        # Start
        result = await task_manager.start_task(
            "lifecycle_task", metadata={"test": True}
        )
        assert result is True
        assert await task_manager.is_running("lifecycle_task") is True

        # Update progress
        await task_manager.update_progress("lifecycle_task", "Step 1")
        status = await task_manager.get_status("lifecycle_task")
        assert status.progress == "Step 1"

        await task_manager.update_progress("lifecycle_task", "Step 2")
        status = await task_manager.get_status("lifecycle_task")
        assert status.progress == "Step 2"

        # Complete
        await task_manager.complete_task("lifecycle_task", result={"final": "data"})
        assert await task_manager.is_running("lifecycle_task") is False

        status = await task_manager.get_status("lifecycle_task")
        assert status.status == TaskStatus.COMPLETED
        assert status.result == {"final": "data"}
        assert status.metadata == {"test": True}

    @pytest.mark.asyncio
    async def test_no_redis_fallback(self):
        """Test behavior when Redis is None."""
        manager = TaskStatusManager(None)  # type: ignore[arg-type]

        status = await manager.get_status("test")
        assert status.status == TaskStatus.IDLE

        assert await manager.is_running("test") is False

        result = await manager.start_task("test")
        assert result is False

        # These should not raise errors
        await manager.update_progress("test", "progress")
        await manager.complete_task("test")
        await manager.fail_task("test", "error")
        await manager.clear_task("test")
        
        # Cancel should return False when no storage
        result = await manager.cancel_task("test")
        assert result is False

    @pytest.mark.asyncio
    async def test_safe_serialization_fallback(self, task_manager, mock_kv_storage):
        """Test that serialization fallback works with problematic data."""
        # Create a task with complex result that might cause issues
        await task_manager.start_task("test_task")

        # Mock a scenario where normal serialization might have issues
        # by testing with various data types
        result_data = {
            "simple": "text",
            "number": 42,
            "nested": {"key": "value"},
            "list": [1, 2, 3],
        }

        await task_manager.complete_task("test_task", result=result_data)

        status = await task_manager.get_status("test_task")
        assert status.status == TaskStatus.COMPLETED
        assert status.result == result_data

    def test_get_key(self, task_manager):
        """Test Redis key generation."""
        key = task_manager._get_key("my_task")
        assert key == f"agent_task_status:{SYSTEM_USER_ID}:my_task"
        assert key.startswith(task_manager.prefix)

    @pytest.mark.asyncio
    async def test_concurrent_task_types(self, task_manager):
        """Test managing multiple different task types simultaneously."""
        # Start multiple different tasks
        await task_manager.start_task("task_a", metadata={"type": "A"})
        await task_manager.start_task("task_b", metadata={"type": "B"})
        await task_manager.start_task("task_c", metadata={"type": "C"})

        # All should be running
        assert await task_manager.is_running("task_a") is True
        assert await task_manager.is_running("task_b") is True
        assert await task_manager.is_running("task_c") is True

        # Complete one
        await task_manager.complete_task("task_a", result={"done": "A"})

        # Check states
        assert await task_manager.is_running("task_a") is False
        assert await task_manager.is_running("task_b") is True
        assert await task_manager.is_running("task_c") is True

        status_a = await task_manager.get_status("task_a")
        assert status_a.status == TaskStatus.COMPLETED

        status_b = await task_manager.get_status("task_b")
        assert status_b.status == TaskStatus.RUNNING

    @pytest.mark.asyncio
    async def test_multiple_runs_same_task(self, task_manager):
        """Test running the same task multiple times, each run overrides the previous."""
        # Run 1
        await task_manager.start_task("repeat_task", metadata={"attempt": 1})
        await task_manager.update_progress("repeat_task", "Run 1 in progress")
        await task_manager.complete_task("repeat_task", result={"output": "result1"})

        status1 = await task_manager.get_status("repeat_task")
        assert status1.status == TaskStatus.COMPLETED
        assert status1.result == {"output": "result1"}
        assert status1.metadata == {"attempt": 1}

        # Run 2 - should override
        result = await task_manager.start_task("repeat_task", metadata={"attempt": 2})
        assert result is True

        status2 = await task_manager.get_status("repeat_task")
        assert status2.status == TaskStatus.RUNNING
        assert status2.result is None  # Previous result cleared
        assert status2.metadata == {"attempt": 2}

        await task_manager.complete_task("repeat_task", result={"output": "result2"})

        status2_final = await task_manager.get_status("repeat_task")
        assert status2_final.status == TaskStatus.COMPLETED
        assert status2_final.result == {"output": "result2"}
        assert status2_final.metadata == {"attempt": 2}

        # Run 3 - should override again
        result = await task_manager.start_task("repeat_task", metadata={"attempt": 3})
        assert result is True

        await task_manager.fail_task("repeat_task", "Run 3 failed")

        status3 = await task_manager.get_status("repeat_task")
        assert status3.status == TaskStatus.FAILED
        assert status3.error == "Run 3 failed"
        assert status3.metadata == {"attempt": 3}
        assert status3.result is None  # No result on failure
