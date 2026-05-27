# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, UTC
from uuid import UUID
from lunar_api.persistence.kv_storage.sqlite_kv_storage import SQLiteKVStorage
from lunar_api.auth.model import SYSTEM_USER_ID
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUIDs and other common non-serializable types."""

    def default(self, o):  # type: ignore[override]
        if isinstance(o, bytes):
            return ""
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "__dict__"):
            # For objects with __dict__, try to serialize their attributes
            return {k: v for k, v in o.__dict__.items() if not k.startswith("_")}
        if hasattr(o, "model_dump"):
            # For Pydantic models
            return o.model_dump()
        # Let the base class raise the TypeError
        return super().default(o)


class TaskStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskInfo(BaseModel):
    status: TaskStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskStatusManager:
    """Manages task status using SQLite KV storage as the backing store."""

    def __init__(self, kv_storage: SQLiteKVStorage):
        self.kv_storage = kv_storage
        self.prefix = "agent_task_status:"
        self._default_user_id = str(SYSTEM_USER_ID)

    def _get_key(self, task_type: str, user_id: Optional[str] = None) -> str:
        """Generate storage key for a task type."""
        resolved_user_id = user_id or self._default_user_id
        return f"{self.prefix}{resolved_user_id}:{task_type}"

    def _safe_serialize(self, task_info: TaskInfo) -> str:
        """Safely serialize TaskInfo to JSON, handling serialization errors."""
        try:
            # First try with custom encoder for common non-serializable types
            data = task_info.model_dump()
            return json.dumps(data, cls=CustomJSONEncoder)
        except Exception as e:
            logger.warning(
                f"Failed to serialize task_info with custom encoder, attempting fallback: {e}"
            )
            # Try to serialize with fallback for problematic fields
            try:
                data = task_info.model_dump()
                # Replace any values that might cause serialization issues
                for field in ["result", "metadata", "error", "progress"]:
                    if field in data and data[field] is not None:
                        try:
                            # Test if this field can be serialized with custom encoder
                            json.dumps(data[field], cls=CustomJSONEncoder)
                        except Exception as field_error:
                            logger.warning(
                                f"Field {field} caused serialization issues, replacing with placeholder: {field_error}"
                            )
                            data[field] = (
                                f"Failed to serialize {field}: {str(field_error)}"
                            )
                return json.dumps(data, cls=CustomJSONEncoder)
            except Exception as fallback_error:
                logger.error(f"Fallback serialization also failed: {fallback_error}")
                # Last resort: return minimal status
                return json.dumps(
                    {
                        "status": task_info.status,
                        "error": "Failed to serialize complete task info",
                    }
                )

    async def get_status(self, task_type: str, user_id: Optional[str] = None) -> TaskInfo:
        """Get the current status of a task type."""
        if self.kv_storage is None:
            logger.warning("KV storage is not available, returning IDLE status")
            return TaskInfo(status=TaskStatus.IDLE)

        key = self._get_key(task_type, user_id=user_id)
        data = self.kv_storage.get(key)

        if data is None:
            return TaskInfo(status=TaskStatus.IDLE)

        try:
            task_dict = json.loads(data)
            return TaskInfo(**task_dict)
        except Exception as e:
            logger.error(f"Error parsing task status for {task_type}: {e}")
            return TaskInfo(status=TaskStatus.IDLE)

    async def is_running(self, task_type: str, user_id: Optional[str] = None) -> bool:
        """Check if a task is currently running."""
        if self.kv_storage is None:
            return False
        task_info = await self.get_status(task_type, user_id=user_id)
        return task_info.status == TaskStatus.RUNNING

    async def start_task(
        self,
        task_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Mark a task as started.
        Returns True if started successfully, False if already running.
        If a previous run exists (completed/failed), it will be overridden.
        """
        if self.kv_storage is None:
            logger.warning(
                f"KV storage is not available, cannot start task {task_type}"
            )
            return False

        # Only prevent start if task is currently RUNNING
        # Allow overriding COMPLETED, FAILED, or IDLE states
        if await self.is_running(task_type, user_id=user_id):
            logger.warning(f"Task {task_type} is already running")
            return False

        task_info = TaskInfo(
            status=TaskStatus.RUNNING,
            started_at=datetime.now(UTC).isoformat(),
            metadata=metadata,
        )

        key = self._get_key(task_type, user_id=user_id)
        self.kv_storage.put(key, self._safe_serialize(task_info))
        logger.info(f"Task {task_type} started")
        return True

    async def update_progress(
        self,
        task_type: str,
        progress: str,
        user_id: Optional[str] = None,
    ):
        """Update the progress message for a running task."""
        if self.kv_storage is None:
            logger.warning(
                f"KV storage is not available, cannot update progress for task {task_type}"
            )
            return

        task_info = await self.get_status(task_type, user_id=user_id)

        if task_info.status != TaskStatus.RUNNING:
            logger.warning(f"Cannot update progress for non-running task {task_type}")
            return

        task_info.progress = progress
        key = self._get_key(task_type, user_id=user_id)
        self.kv_storage.put(key, self._safe_serialize(task_info))
        logger.info(f"Task {task_type} progress: {progress}")

    async def complete_task(
        self,
        task_type: str,
        result: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ):
        """Mark a task as completed."""
        if self.kv_storage is None:
            logger.warning(
                f"KV storage is not available, cannot complete task {task_type}"
            )
            return

        task_info = await self.get_status(task_type, user_id=user_id)
        task_info.status = TaskStatus.COMPLETED
        task_info.completed_at = datetime.now(UTC).isoformat()
        task_info.result = result
        task_info.progress = "Completed"

        key = self._get_key(task_type, user_id=user_id)
        self.kv_storage.put(key, self._safe_serialize(task_info))
        logger.info(f"Task {task_type} completed")

    async def fail_task(
        self,
        task_type: str,
        error: str,
        user_id: Optional[str] = None,
    ):
        """Mark a task as failed."""
        if self.kv_storage is None:
            logger.warning(
                f"KV storage is not available, cannot mark task {task_type} as failed"
            )
            return

        task_info = await self.get_status(task_type, user_id=user_id)
        task_info.status = TaskStatus.FAILED
        task_info.completed_at = datetime.now(UTC).isoformat()
        task_info.error = error
        task_info.progress = "Failed"

        key = self._get_key(task_type, user_id=user_id)
        self.kv_storage.put(key, self._safe_serialize(task_info))
        logger.error(f"Task {task_type} failed: {error}")

    async def cancel_task(self, task_type: str, user_id: Optional[str] = None) -> bool:
        """Cancel a running task.
        
        Returns True if the task was successfully cancelled, False if the task
        was not running.
        """
        if self.kv_storage is None:
            logger.warning(
                f"KV storage is not available, cannot cancel task {task_type}"
            )
            return False

        task_info = await self.get_status(task_type, user_id=user_id)
        if task_info.status != TaskStatus.RUNNING:
            logger.warning(f"Cannot cancel task {task_type} - not running (status: {task_info.status})")
            return False

        task_info.status = TaskStatus.CANCELLED
        task_info.completed_at = datetime.now(UTC).isoformat()
        task_info.progress = "Cancelled by user"

        key = self._get_key(task_type, user_id=user_id)
        self.kv_storage.put(key, self._safe_serialize(task_info))
        logger.info(f"Task {task_type} cancelled")
        return True

    async def clear_task(self, task_type: str, user_id: Optional[str] = None):
        """Clear the task status (reset to idle)."""
        if self.kv_storage is None:
            logger.warning(
                f"KV storage is not available, cannot clear task {task_type}"
            )
            return

        key = self._get_key(task_type, user_id=user_id)
        self.kv_storage.delete(key)
        logger.info(f"Task {task_type} status cleared")
