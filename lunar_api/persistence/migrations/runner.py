# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

from lunar_api.persistence.connections.sqlite_connection import (
    ExecuteMode,
    SQLiteConnection,
)


def _ensure_schema_migrations_table(connection: SQLiteConnection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """,
        commit=True,
    )


def _get_applied_migrations(connection: SQLiteConnection) -> set[str]:
    rows = connection.execute(
        "SELECT filename FROM schema_migrations",
        mode=ExecuteMode.FETCH_ALL,
    )
    if not rows:
        return set()
    return {row[0] for row in rows if row and row[0]}


def _migration_files(migrations_dir: Path) -> Sequence[Path]:
    return sorted(p for p in migrations_dir.glob("*.sql") if p.is_file())


def run_migrations(
    connection: SQLiteConnection,
    migrations_dir: Optional[Path] = None,
) -> List[str]:
    if connection.connection is None:
        connection.connect()

    migrations_path = migrations_dir or Path(__file__).parent / "sql"
    if not migrations_path.exists():
        return []

    _ensure_schema_migrations_table(connection)
    applied = _get_applied_migrations(connection)

    applied_now: List[str] = []
    for file_path in _migration_files(migrations_path):
        filename = file_path.name
        if filename in applied:
            continue
        sql = file_path.read_text(encoding="utf-8")
        if not sql.strip():
            continue
        if connection.connection is None:
            connection.connect()
        connection.connection.executescript(sql)
        connection.connection.commit()
        connection.execute(
            "INSERT INTO schema_migrations (filename) VALUES (?)",
            values=(filename,),
            commit=True,
        )
        applied_now.append(filename)
    return applied_now
