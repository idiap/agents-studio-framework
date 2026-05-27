# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import sqlite3
from contextlib import contextmanager
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

from .storage_connection import StorageConnection


class ExecuteMode(Enum):
    NONE = auto()
    FETCH_ONE = auto()
    FETCH_ALL = auto()


class SQLiteConnection(StorageConnection):
    def __init__(self, db_path: str = ":memory:"):
        super().__init__()
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self) -> "SQLiteConnection":
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
        return self

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def get_cursor(self):
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        return self.connection.cursor()

    def _convert_query(self, query: str) -> str:
        """Convert PostgreSQL-style %s placeholders to SQLite ? placeholders."""
        # Simple conversion - replace %s with ?
        return query.replace("%s", "?")

    def execute(
        self,
        query: str,
        values: Optional[Union[Dict, Tuple[Any, ...], List[Any], None]] = None,
        mode: ExecuteMode = ExecuteMode.NONE,
        commit: bool = False,
        cursor_factory: Optional[type] = None,
        bulk: bool = False,
    ) -> Union[
        None,
        dict,
        List[dict],
        Tuple[Any, ...],
        List[Tuple[Any, ...]],
    ]:
        if self.connection is None:
            raise Exception("No active database connection.")
        
        # Convert PostgreSQL-style query to SQLite
        sqlite_query = self._convert_query(query)
        
        result = None
        try:
            cursor = self.get_cursor()
            if bulk and values is not None:
                cursor.executemany(sqlite_query, values)
            elif values is not None:
                if isinstance(values, dict):
                    cursor.execute(sqlite_query, values)
                else:
                    cursor.execute(sqlite_query, values)
            else:
                cursor.execute(sqlite_query)
            
            if mode == ExecuteMode.FETCH_ONE:
                result = cursor.fetchone()
            elif mode == ExecuteMode.FETCH_ALL:
                result = cursor.fetchall()
            
            if commit:
                self.connection.commit()
            
            cursor.close()
        except Exception as e:
            self.connection.rollback()
            raise e
        return result

    @contextmanager
    def transaction(self):
        if self.connection is None:
            raise Exception("No active database connection.")
        try:
            yield
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
