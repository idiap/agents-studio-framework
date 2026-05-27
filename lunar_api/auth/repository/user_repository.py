# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from datetime import UTC, datetime, timedelta
from typing import Any, Optional, Tuple
from uuid import UUID

from lunar_api.auth.model import User
from lunar_api.persistence.connections import SQLiteConnection
from lunar_api.persistence.connections.sqlite_connection import ExecuteMode


def _coerce_row(value: Any) -> Optional[Tuple[Any, ...]]:
    if value is None:
        return None
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return None


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now(UTC)


class UserRepository:
    def __init__(self, sql_database_connection: SQLiteConnection):
        self.sql_database_connection = sql_database_connection

    def create_user(self, login: str, password_hash: str) -> User:
        statement = """
        INSERT INTO users (login, password_hash)
        VALUES (%s, %s)
        RETURNING id, login, password_hash, created_at
        """
        row = self.sql_database_connection.execute(
            query=statement,
            values=(login, password_hash),
            mode=ExecuteMode.FETCH_ONE,
            commit=True,
        )
        row = _coerce_row(row)
        if not row:
            raise Exception("Failed to create user")

        return User(
            id=UUID(str(row[0])),
            login=str(row[1]),
            password_hash=str(row[2]),
            created_at=_coerce_datetime(row[3]),
        )

    def get_user_by_login(self, login: str) -> Optional[User]:
        statement = """
        SELECT id, login, password_hash, created_at
        FROM users
        WHERE login = %s
        """
        row = self.sql_database_connection.execute(
            query=statement,
            values=(login,),
            mode=ExecuteMode.FETCH_ONE,
        )
        row = _coerce_row(row)
        if not row:
            return None
        return User(
            id=UUID(str(row[0])),
            login=str(row[1]),
            password_hash=str(row[2]),
            created_at=_coerce_datetime(row[3]),
        )

    def get_user_by_session_token(self, token: str) -> Optional[User]:
        statement = """
        SELECT u.id, u.login, u.password_hash, u.created_at
        FROM users u
        INNER JOIN user_sessions s ON s.user_id = u.id
        WHERE s.token = %s
          AND (s.expires_at IS NULL OR s.expires_at > CURRENT_TIMESTAMP)
        """
        row = self.sql_database_connection.execute(
            query=statement,
            values=(token,),
            mode=ExecuteMode.FETCH_ONE,
        )
        row = _coerce_row(row)
        if not row:
            return None
        return User(
            id=UUID(str(row[0])),
            login=str(row[1]),
            password_hash=str(row[2]),
            created_at=_coerce_datetime(row[3]),
        )

    def create_session(
        self,
        user_id: UUID,
        token: str,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        expires_at: Optional[str] = None
        if ttl_seconds is not None:
            expires_at = (datetime.now(UTC) + timedelta(seconds=ttl_seconds)).isoformat()

        statement = """
        INSERT INTO user_sessions (token, user_id, expires_at)
        VALUES (%s, %s, %s)
        """
        self.sql_database_connection.execute(
            query=statement,
            values=(token, str(user_id), expires_at),
            commit=True,
        )
