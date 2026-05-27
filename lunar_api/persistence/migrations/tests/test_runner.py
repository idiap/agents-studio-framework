# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from pathlib import Path

from lunar_api.persistence.connections.sqlite_connection import SQLiteConnection
from lunar_api.persistence.migrations.runner import run_migrations


def _table_names(connection: SQLiteConnection) -> set[str]:
    cursor = connection.connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    return {row[0] for row in cursor.fetchall() if row and row[0]}


def _migration_count(connection: SQLiteConnection) -> int:
    cursor = connection.connection.execute(
        "SELECT COUNT(*) FROM schema_migrations"
    )
    return int(cursor.fetchone()[0])


def _column_names(connection: SQLiteConnection, table_name: str) -> set[str]:
    cursor = connection.connection.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall() if row and row[1]}


def test_run_migrations_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    connection = SQLiteConnection(str(db_path))
    connection.connect()

    applied = run_migrations(connection)

    tables = _table_names(connection)
    assert "schema_migrations" in tables
    assert "reports" in tables
    assert "kv_storage" in tables
    assert "users" in tables
    assert "user_sessions" in tables
    assert "user_id" in _column_names(connection, "reports")
    assert len(applied) >= 4
    assert _migration_count(connection) == len(applied)

    system_user = connection.connection.execute(
        "SELECT id FROM users WHERE login = 'system'"
    ).fetchone()
    assert system_user is not None

    connection.disconnect()


def test_run_migrations_idempotent(tmp_path):
    db_path = tmp_path / "test_idempotent.db"
    connection = SQLiteConnection(str(db_path))
    connection.connect()

    run_migrations(connection)
    count_after_first = _migration_count(connection)

    applied_second = run_migrations(connection)
    count_after_second = _migration_count(connection)

    assert applied_second == []
    assert count_after_second == count_after_first

    connection.disconnect()
