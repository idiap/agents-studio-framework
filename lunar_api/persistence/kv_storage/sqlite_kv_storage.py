# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from typing import Any, Optional
import time
from .base import KVStorage
from ..connections.sqlite_connection import SQLiteConnection
from .keys import KVKey


class SQLiteKVStorage(KVStorage):
    """A key-value storage implementation using SQLite."""

    def __init__(self, connection: SQLiteConnection):
        super().__init__(connection)
        self._ensure_table()

    def _ensure_table(self):
        """Create the KV storage table if it doesn't exist."""
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS kv_storage (
                key TEXT PRIMARY KEY,
                value BLOB,
                expires_at REAL
            )
            """,
            commit=True,
        )

    def _cleanup_expired(self):
        """Remove expired entries."""
        current_time = time.time()
        self.connection.execute(
            "DELETE FROM kv_storage WHERE expires_at IS NOT NULL AND expires_at < ?",
            values=(current_time,),
            commit=True,
        )

    def get(self, key: KVKey) -> Any:
        """Get a value by key. Returns None if not found or expired."""
        self._cleanup_expired()
        from ..connections.sqlite_connection import ExecuteMode

        result = self.connection.execute(
            "SELECT value FROM kv_storage WHERE key = ?",
            values=(key,),
            mode=ExecuteMode.FETCH_ONE,
        )
        if result:
            return result[0]
        return None

    def put(self, key: KVKey, value: Any, ttl: Optional[int] = None):
        """Store a value with an optional TTL in seconds."""
        expires_at = None
        if ttl is not None:
            expires_at = time.time() + ttl

        # Convert value to bytes if it's a string
        if isinstance(value, str):
            value = value.encode("utf-8")

        self.connection.execute(
            """
            INSERT INTO kv_storage (key, value, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at
            """,
            values=(key, value, expires_at),
            commit=True,
        )

    def delete(self, key: KVKey):
        """Delete a key from storage."""
        self.connection.execute(
            "DELETE FROM kv_storage WHERE key = ?",
            values=(key,),
            commit=True,
        )
