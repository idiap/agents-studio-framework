# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from contextlib import contextmanager
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

import psycopg2
from psycopg2.extras import execute_values

from .storage_connection import StorageConnection


class ExecuteMode(Enum):
    NONE = auto()
    FETCH_ONE = auto()
    FETCH_ALL = auto()


class PostgresConnection(StorageConnection):
    def __init__(self, db_url: str):
        super().__init__()
        self.db_url = db_url
        self.connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> "PostgresConnection":
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(self.db_url)
        return self

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def get_cursor(self, cursor_factory: Optional[type] = None):
        if not self.connection:
            raise Exception("Connection not established. Call connect() first.")
        return self.connection.cursor(cursor_factory=cursor_factory)

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
        result = None
        try:
            with self.get_cursor(cursor_factory) as cursor:
                if bulk and values is not None:
                    execute_values(cursor, query, values)
                elif values is not None:
                    cursor.execute(query, values)
                else:
                    cursor.execute(query)
                if mode == ExecuteMode.FETCH_ONE:
                    result = cursor.fetchone()
                elif mode == ExecuteMode.FETCH_ALL:
                    result = cursor.fetchall()
                if commit:
                    self.connection.commit()
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
