# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from lunar_api.auth.dependencies import get_current_user
from lunar_api.auth.model import AuthenticatedUser
from lunar_api.auth.repository.user_repository import UserRepository
from lunar_api.auth.security import hash_password
from lunar_api.persistence.connections.sqlite_connection import SQLiteConnection
from lunar_api.persistence.migrations.runner import run_migrations
from lunar_api.report.model import ReportInput
from lunar_api.report.repository.report_repository import ReportRepository
from lunar_api.report.router import router as report_router


class _Container:
    def __init__(self, report_repository: ReportRepository):
        self._report_repository = report_repository

    def get(self, _token):
        return self._report_repository


def _setup_repositories(tmp_path):
    db_path = tmp_path / "report_scoping.db"
    connection = SQLiteConnection(str(db_path))
    connection.connect()
    run_migrations(connection)
    return (
        connection,
        UserRepository(connection),
        ReportRepository(connection),
    )


def test_report_repository_is_scoped_by_user(tmp_path):
    connection, user_repository, report_repository = _setup_repositories(tmp_path)
    try:
        user_1 = user_repository.create_user("alice", hash_password("secret"))
        user_2 = user_repository.create_user("bob", hash_password("secret"))

        report_1 = report_repository.create_report(
            ReportInput(name="Alice Report", content="A"),
            user_id=str(user_1.id),
        )
        report_2 = report_repository.create_report(
            ReportInput(name="Bob Report", content="B"),
            user_id=str(user_2.id),
        )

        user_1_reports = report_repository.list_reports(user_id=str(user_1.id))
        user_2_reports = report_repository.list_reports(user_id=str(user_2.id))

        assert len(user_1_reports) == 1
        assert user_1_reports[0].id == report_1.id
        assert len(user_2_reports) == 1
        assert user_2_reports[0].id == report_2.id

        # Cross-user access should return no report.
        assert (
            report_repository.get_report(report_id=report_1.id, user_id=str(user_2.id))
            is None
        )
    finally:
        connection.disconnect()


def test_report_router_lists_only_current_user_reports(tmp_path):
    connection, user_repository, report_repository = _setup_repositories(tmp_path)
    try:
        user_1 = user_repository.create_user("alice", hash_password("secret"))
        user_2 = user_repository.create_user("bob", hash_password("secret"))

        report_repository.create_report(
            ReportInput(name="Alice Report", content="A"),
            user_id=str(user_1.id),
        )
        report_repository.create_report(
            ReportInput(name="Bob Report", content="B"),
            user_id=str(user_2.id),
        )

        app = FastAPI()
        app.include_router(report_router)

        # Build app with a patched report repository and user #1 context.
        report_app_context = SimpleNamespace(container=_Container(report_repository))
        with patch("lunar_api.report.router.app_context", report_app_context):
            app.dependency_overrides[get_current_user] = (
                lambda: AuthenticatedUser(id=user_1.id, login=user_1.login)
            )
            client = TestClient(app)
            response = client.get("/report/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Alice Report"
    finally:
        connection.disconnect()
