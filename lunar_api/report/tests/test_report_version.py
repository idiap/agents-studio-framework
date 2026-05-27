# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for Report version functionality - repository and router.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from lunar_api.auth.dependencies import get_current_user
from lunar_api.auth.model import AuthenticatedUser
from lunar_api.report.model import Report
from lunar_api.report.repository.report_repository import ReportRepository

TEST_AUTHENTICATED_USER = AuthenticatedUser(id=uuid4(), login="test-user")


def _build_router_client(router):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: TEST_AUTHENTICATED_USER
    return TestClient(app)


class TestReportVersionModel:
    """Tests for Report model version field."""

    def test_report_with_default_version(self):
        """Test Report model has default version of 1."""
        report = Report(
            id=uuid4(),
            name="Test Report",
            content="# Content",
            created_at=datetime.now(),
        )
        assert report.version == 1

    def test_report_with_explicit_version(self):
        """Test Report model with explicit version."""
        report = Report(
            id=uuid4(),
            name="Test Report",
            content="# Content",
            created_at=datetime.now(),
            version=5,
        )
        assert report.version == 5

    def test_report_to_dict_includes_version(self):
        """Test Report.to_dict() includes version field."""
        report = Report(
            id=uuid4(),
            name="Test Report",
            content="# Content",
            created_at=datetime.now(),
            version=3,
        )
        result = report.to_dict()
        assert "version" in result
        assert result["version"] == 3


class TestReportRepositoryVersion:
    """Tests for ReportRepository version-related functionality."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock PostgresConnection."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_connection):
        """Create a ReportRepository with mocked connection."""
        return ReportRepository(sql_database_connection=mock_connection)

    def test_create_report_sets_version_1(self, repository, mock_connection):
        """Test create_report sets version to 1."""
        from lunar_api.report.model import ReportInput

        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Test Report",
            "# Content",
            now,
            None,  # provenance_data
            1,  # version
        )

        result = repository.create_report(
            ReportInput(name="Test Report", content="# Content")
        )

        assert result.version == 1
        call_args = mock_connection.execute.call_args
        query = call_args.kwargs["query"]
        assert "INSERT INTO reports" in query
        assert "version" in query

    def test_get_report_returns_version(self, repository, mock_connection):
        """Test get_report returns version field."""
        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Test Report",
            "# Content",
            now,
            None,  # provenance_data
            3,  # version
        )

        result = repository.get_report(report_id)

        assert result is not None
        assert result.version == 3

    def test_update_report_increments_version(self, repository, mock_connection):
        """Test update_report increments version when flag is set."""
        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Updated Name",
            "# Updated Content",
            now,
            None,
            2,  # incremented version
        )

        result = repository.update_report(
            report_id=report_id,
            content="# Updated Content",
            increment_version=True,
        )

        assert result is not None
        call_args = mock_connection.execute.call_args
        query = call_args.kwargs["query"]
        assert "version = version + 1" in query

    def test_update_report_no_increment_by_default(self, repository, mock_connection):
        """Test update_report does not increment version by default."""
        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Updated Name",
            "# Content",
            now,
            None,
            1,
        )

        result = repository.update_report(
            report_id=report_id,
            name="Updated Name",
        )

        assert result is not None
        call_args = mock_connection.execute.call_args
        query = call_args.kwargs["query"]
        assert "version = version + 1" not in query

    def test_get_report_version_returns_current(self, repository, mock_connection):
        """Test get_report_version returns current report when version matches."""
        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Test Report",
            "# Current Content",
            now,
            None,
            2,  # current version
        )

        result = repository.get_report_version(report_id, version=2)

        assert result is not None
        assert result.version == 2
        assert result.content == "# Current Content"

    def test_get_report_version_returns_historical(self, repository, mock_connection):
        """Test get_report_version returns historical version from provenance."""
        report_id = uuid4()
        now = datetime.now()
        provenance_data = {
            "versions": [
                {
                    "version": 0,
                    "content": "# Initial Content",
                    "created_at": "2026-01-01T10:00:00",
                },
                {
                    "version": 1,
                    "content": "# V1 Content",
                    "created_at": "2026-01-02T10:00:00",
                },
            ]
        }

        mock_connection.execute.return_value = (
            str(report_id),
            "Test Report",
            "# Current Content",
            now,
            provenance_data,
            2,  # current version
        )

        result = repository.get_report_version(report_id, version=1)

        assert result is not None
        assert result.version == 1
        assert result.content == "# V1 Content"

    def test_get_report_version_returns_none_for_invalid_version(
        self, repository, mock_connection
    ):
        """Test get_report_version returns None for non-existent version."""
        report_id = uuid4()
        now = datetime.now()
        provenance_data = {
            "versions": [
                {"version": 0, "content": "# Initial Content"},
            ]
        }

        mock_connection.execute.return_value = (
            str(report_id),
            "Test Report",
            "# Current Content",
            now,
            provenance_data,
            1,
        )

        result = repository.get_report_version(report_id, version=99)

        assert result is None

    def test_get_report_version_returns_none_without_provenance(
        self, repository, mock_connection
    ):
        """Test get_report_version returns None when no provenance exists for old version."""
        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Test Report",
            "# Current Content",
            now,
            None,  # no provenance data
            2,
        )

        result = repository.get_report_version(report_id, version=1)

        assert result is None


class TestReportRouterVersion:
    """Tests for report router version query parameter."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock ReportRepository."""
        return MagicMock()

    def test_get_report_with_version_param(self, mock_repository):
        """Test GET /report/{report_id}?version=N returns specific version."""

        report_id = uuid4()
        now = datetime.now()

        mock_report = Report(
            id=report_id,
            name="Test Report",
            content="# V1 Content",
            created_at=now,
            version=1,
        )
        mock_repository.get_report_version.return_value = mock_report

        with patch("lunar_api.report.router.app_context") as mock_app_context:
            mock_app_context.container.get.return_value = mock_repository

            from lunar_api.report.router import router
            client = _build_router_client(router)

            response = client.get(f"/report/{report_id}?version=1")

            assert response.status_code == 200
            data = response.json()
            assert data["version"] == 1
            assert data["content"] == "# V1 Content"
            mock_repository.get_report_version.assert_called_once_with(
                report_id=report_id,
                version=1,
                user_id=str(TEST_AUTHENTICATED_USER.id),
            )

    def test_get_report_without_version_param(self, mock_repository):
        """Test GET /report/{report_id} without version returns current."""

        report_id = uuid4()
        now = datetime.now()

        mock_report = Report(
            id=report_id,
            name="Test Report",
            content="# Current Content",
            created_at=now,
            version=3,
        )
        mock_repository.get_report.return_value = mock_report

        with patch("lunar_api.report.router.app_context") as mock_app_context:
            mock_app_context.container.get.return_value = mock_repository

            from lunar_api.report.router import router
            client = _build_router_client(router)

            response = client.get(f"/report/{report_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["version"] == 3
            mock_repository.get_report.assert_called_once_with(
                report_id=report_id,
                user_id=str(TEST_AUTHENTICATED_USER.id),
            )

    def test_get_report_version_not_found(self, mock_repository):
        """Test GET /report/{report_id}?version=N returns 404 for invalid version."""

        report_id = uuid4()
        mock_repository.get_report_version.return_value = None

        with patch("lunar_api.report.router.app_context") as mock_app_context:
            mock_app_context.container.get.return_value = mock_repository

            from lunar_api.report.router import router
            client = _build_router_client(router)

            response = client.get(f"/report/{report_id}?version=99")

            assert response.status_code == 404
            assert "version 99 not found" in response.json()["detail"]

    def test_update_report_increments_version_on_content_change(self, mock_repository):
        """Test PUT /report/{report_id} increments version when content changes."""

        report_id = uuid4()
        now = datetime.now()

        current_report = Report(
            id=report_id,
            name="Test Report",
            content="# Original Content",
            created_at=now,
            version=1,
        )

        updated_report = Report(
            id=report_id,
            name="Test Report",
            content="# New Content",
            created_at=now,
            version=2,
        )

        mock_repository.get_report.return_value = current_report
        mock_repository.update_report.return_value = updated_report
        mock_repository.update_provenance_data.return_value = updated_report

        with patch("lunar_api.report.router.app_context") as mock_app_context:
            mock_app_context.container.get.return_value = mock_repository

            from lunar_api.report.router import router
            client = _build_router_client(router)

            response = client.put(
                f"/report/{report_id}",
                json={"content": "# New Content"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["version"] == 2

            # Verify increment_version was set to True
            mock_repository.update_report.assert_called_once()
            call_kwargs = mock_repository.update_report.call_args.kwargs
            assert call_kwargs["increment_version"] is True

    def test_update_report_does_not_increment_on_name_only_change(
        self, mock_repository
    ):
        """Test PUT /report/{report_id} does not increment version for name-only change."""

        report_id = uuid4()
        now = datetime.now()

        current_report = Report(
            id=report_id,
            name="Original Name",
            content="# Content",
            created_at=now,
            version=1,
        )

        updated_report = Report(
            id=report_id,
            name="New Name",
            content="# Content",
            created_at=now,
            version=1,  # version unchanged
        )

        mock_repository.get_report.return_value = current_report
        mock_repository.update_report.return_value = updated_report

        with patch("lunar_api.report.router.app_context") as mock_app_context:
            mock_app_context.container.get.return_value = mock_repository

            from lunar_api.report.router import router
            client = _build_router_client(router)

            response = client.put(
                f"/report/{report_id}",
                json={"name": "New Name"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["version"] == 1

            # Verify increment_version was set to False
            mock_repository.update_report.assert_called_once()
            call_kwargs = mock_repository.update_report.call_args.kwargs
            assert call_kwargs["increment_version"] is False

    def test_list_reports_includes_version(self, mock_repository):
        """Test GET /report/ returns reports with version field."""

        now = datetime.now()
        mock_reports = [
            Report(
                id=uuid4(),
                name="Report 1",
                content="# Content 1",
                created_at=now,
                version=3,
            ),
            Report(
                id=uuid4(),
                name="Report 2",
                content="# Content 2",
                created_at=now,
                version=1,
            ),
        ]
        mock_repository.list_reports.return_value = mock_reports

        with patch("lunar_api.report.router.app_context") as mock_app_context:
            mock_app_context.container.get.return_value = mock_repository

            from lunar_api.report.router import router
            client = _build_router_client(router)

            response = client.get("/report/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["version"] == 3
            assert data[1]["version"] == 1
