# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from lunar_api.auth.model import SYSTEM_USER_ID
from lunar_api.persistence.connections import SQLiteConnection
from lunar_api.persistence.connections.sqlite_connection import ExecuteMode
from lunar_api.report.model import Report, ReportInput

SYSTEM_USER_ID_STR = str(SYSTEM_USER_ID)


def _parse_provenance_data(value: Any) -> Optional[Dict[str, Any]]:
    """Parse provenance data from database, handling both dict and JSON string."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _coerce_row(value: Any) -> Optional[Tuple[Any, ...]]:
    if value is None:
        return None
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return None


def _coerce_int(value: Any, default: int = 1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_report(row: Tuple[Any, ...]) -> Report:
    return Report(
        id=(
            UUID(str(row[0]))
            if row[0]
            else UUID("00000000-0000-0000-0000-000000000000")
        ),
        name=str(row[1]) if row[1] is not None else "",
        content=str(row[2]) if row[2] is not None else "",
        created_at=row[3] if isinstance(row[3], datetime) else datetime.now(),
        provenance_data=_parse_provenance_data(row[4]) if len(row) > 4 else None,
        version=_coerce_int(row[5]) if len(row) > 5 else 1,
    )


class ReportRepository:
    def __init__(
        self,
        sql_database_connection: SQLiteConnection,
        default_user_id: Optional[str] = None,
    ):
        self.sql_database_connection = sql_database_connection
        self.default_user_id = default_user_id

    def for_user(self, user_id: str) -> "ReportRepository":
        return ReportRepository(
            sql_database_connection=self.sql_database_connection,
            default_user_id=user_id,
        )

    def _resolve_user_id(self, user_id: Optional[str]) -> str:
        if user_id:
            return user_id
        if self.default_user_id:
            return self.default_user_id
        return SYSTEM_USER_ID_STR

    def create_report(
        self,
        report_input: ReportInput,
        user_id: Optional[str] = None,
    ) -> Report:
        resolved_user_id = self._resolve_user_id(user_id)
        statement = """
        INSERT INTO reports (name, content, version, user_id)
        VALUES (%s, %s, 1, %s)
        RETURNING id, name, content, created_at, provenance_data, version
        """
        params = (report_input.name, report_input.content, resolved_user_id)
        row = self.sql_database_connection.execute(
            query=statement,
            values=params,
            commit=True,
            mode=ExecuteMode.FETCH_ONE,
        )
        row = _coerce_row(row)
        if not row:
            raise Exception("Failed to insert report")
        return _build_report(row)

    def get_report(self, report_id: UUID, user_id: Optional[str] = None) -> Optional[Report]:
        resolved_user_id = self._resolve_user_id(user_id)
        statement = """
        SELECT id, name, content, created_at, provenance_data, version
        FROM reports
        WHERE id = %s
          AND user_id = %s
        """
        params = (str(report_id), resolved_user_id)
        row = self.sql_database_connection.execute(
            query=statement,
            values=params,
            commit=False,
            mode=ExecuteMode.FETCH_ONE,
        )
        row = _coerce_row(row)
        if not row:
            return None
        return _build_report(row)

    def get_report_version(
        self,
        report_id: UUID,
        version: int,
        user_id: Optional[str] = None,
    ) -> Optional[Report]:
        """Get a specific version of a report from provenance data."""
        report = self.get_report(report_id, user_id=user_id)
        if not report:
            return None

        if version == report.version:
            return report

        if not report.provenance_data:
            return None

        versions = report.provenance_data.get("versions", [])
        for v in versions:
            if v.get("version") == version:
                return Report(
                    id=report.id,
                    name=report.name,
                    content=v.get("content", ""),
                    created_at=report.created_at,
                    provenance_data=report.provenance_data,
                    version=version,
                )

        return None

    def list_reports(
        self,
        limit: Optional[int] = 100,
        user_id: Optional[str] = None,
    ) -> List[Report]:
        resolved_user_id = self._resolve_user_id(user_id)
        statement = """
        SELECT id, name, content, created_at, provenance_data, version
        FROM reports
        WHERE user_id = %s
        ORDER BY created_at DESC
        """
        values: tuple[Any, ...]
        if limit is not None:
            statement += " LIMIT %s"
            values = (resolved_user_id, limit)
        else:
            values = (resolved_user_id,)

        rows = self.sql_database_connection.execute(
            query=statement,
            values=values,
            commit=False,
            mode=ExecuteMode.FETCH_ALL,
        )
        results: List[Report] = []
        if rows:
            for raw_row in rows:
                row = _coerce_row(raw_row)
                if not row:
                    continue
                results.append(_build_report(row))
        return results

    def update_report(
        self,
        report_id: UUID,
        name: Optional[str] = None,
        content: Optional[str] = None,
        increment_version: bool = False,
        user_id: Optional[str] = None,
    ) -> Optional[Report]:
        """Update a report's name and/or content."""
        resolved_user_id = self._resolve_user_id(user_id)
        updates = []
        params: list[Any] = []

        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if content is not None:
            updates.append("content = %s")
            params.append(content)
        if increment_version:
            updates.append("version = version + 1")

        if not updates:
            return self.get_report(report_id, user_id=resolved_user_id)

        params.append(str(report_id))
        params.append(resolved_user_id)
        statement = f"""
        UPDATE reports
        SET {", ".join(updates)}
        WHERE id = %s
          AND user_id = %s
        RETURNING id, name, content, created_at, provenance_data, version
        """
        row = self.sql_database_connection.execute(
            query=statement,
            values=tuple(params),
            commit=True,
            mode=ExecuteMode.FETCH_ONE,
        )
        row = _coerce_row(row)
        if not row:
            return None
        return _build_report(row)

    def update_provenance_data(
        self,
        report_id: UUID,
        provenance_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Optional[Report]:
        """Update the provenance data for an existing report."""
        resolved_user_id = self._resolve_user_id(user_id)
        statement = """
        UPDATE reports
        SET provenance_data = %s
        WHERE id = %s
          AND user_id = %s
        RETURNING id, name, content, created_at, provenance_data, version
        """
        params = (json.dumps(provenance_data), str(report_id), resolved_user_id)
        row = self.sql_database_connection.execute(
            query=statement,
            values=params,
            commit=True,
            mode=ExecuteMode.FETCH_ONE,
        )
        row = _coerce_row(row)
        if not row:
            return None
        return _build_report(row)

    def update_report_with_provenance_and_content(
        self,
        report_id: UUID,
        content: str,
        provenance_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Optional[Report]:
        """Update a report's content and provenance data atomically."""
        resolved_user_id = self._resolve_user_id(user_id)
        statement = """
        UPDATE reports
        SET content = %s, provenance_data = %s
        WHERE id = %s
          AND user_id = %s
        RETURNING id, name, content, created_at, provenance_data, version
        """
        params = (
            content,
            json.dumps(provenance_data),
            str(report_id),
            resolved_user_id,
        )
        row = self.sql_database_connection.execute(
            query=statement,
            values=params,
            commit=True,
            mode=ExecuteMode.FETCH_ONE,
        )
        row = _coerce_row(row)
        if not row:
            return None
        return _build_report(row)

    def delete_report(self, report_id: UUID, user_id: Optional[str] = None) -> bool:
        resolved_user_id = self._resolve_user_id(user_id)
        statement = """
        DELETE FROM reports
        WHERE id = %s
          AND user_id = %s
        """
        params = (str(report_id), resolved_user_id)
        self.sql_database_connection.execute(
            query=statement,
            values=params,
            commit=True,
        )
        return True
