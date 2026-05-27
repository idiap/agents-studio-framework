# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for Report update functionality - repository and router.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from lunar_api.auth.dependencies import get_current_user
from lunar_api.auth.model import AuthenticatedUser
from lunar_api.report.model import Report, ReportUpdate
from lunar_api.report.repository.report_repository import ReportRepository

TEST_AUTHENTICATED_USER = AuthenticatedUser(id=uuid4(), login="test-user")


def _build_router_client(router):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: TEST_AUTHENTICATED_USER
    return TestClient(app)


class TestReportUpdateModel:
    """Tests for ReportUpdate model."""

    def test_report_update_with_name_only(self):
        """Test ReportUpdate with name only."""
        update = ReportUpdate(name="Updated Name")

        assert update.name == "Updated Name"
        assert update.content is None
        assert update.provenance_data is None

    def test_report_update_with_content_only(self):
        """Test ReportUpdate with content only."""
        update = ReportUpdate(content="# Updated Content")

        assert update.name is None
        assert update.content == "# Updated Content"
        assert update.provenance_data is None

    def test_report_update_with_name_and_content(self):
        """Test ReportUpdate with both name and content."""
        update = ReportUpdate(name="Updated Name", content="# Updated Content")

        assert update.name == "Updated Name"
        assert update.content == "# Updated Content"
        assert update.provenance_data is None

    def test_report_update_empty(self):
        """Test ReportUpdate with no fields set."""
        update = ReportUpdate()

        assert update.name is None
        assert update.content is None
        assert update.provenance_data is None


class TestReportRepositoryUpdate:
    """Tests for ReportRepository.update_report method."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock PostgresConnection."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_connection):
        """Create a ReportRepository with mocked connection."""
        return ReportRepository(sql_database_connection=mock_connection)

    def test_update_report_name_only(self, repository, mock_connection):
        """Test update_report with name only."""
        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Updated Name",
            "# Original Content",
            now,
            None,
            1,  # version
        )

        result = repository.update_report(report_id=report_id, name="Updated Name")

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        query = call_args.kwargs["query"]
        assert "UPDATE reports" in query
        assert "name = %s" in query
        assert "content = %s" not in query
        assert (
            "RETURNING id, name, content, created_at, provenance_data, version" in query
        )
        assert result is not None
        assert result.name == "Updated Name"

    def test_update_report_content_only(self, repository, mock_connection):
        """Test update_report with content only."""
        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Original Name",
            "# Updated Content",
            now,
            None,
            1,  # version
        )

        result = repository.update_report(
            report_id=report_id, content="# Updated Content"
        )

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        query = call_args.kwargs["query"]
        assert "UPDATE reports" in query
        assert "content = %s" in query
        assert "name = %s" not in query
        assert result is not None
        assert result.content == "# Updated Content"

    def test_update_report_name_and_content(self, repository, mock_connection):
        """Test update_report with both name and content."""
        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Updated Name",
            "# Updated Content",
            now,
            {"manifest": {"flow_id": "test"}},
            2,  # version
        )

        result = repository.update_report(
            report_id=report_id,
            name="Updated Name",
            content="# Updated Content",
        )

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        query = call_args.kwargs["query"]
        values = call_args.kwargs["values"]
        assert "UPDATE reports" in query
        assert "name = %s" in query
        assert "content = %s" in query
        # Check values order: name first, then content, then report_id
        assert values[0] == "Updated Name"
        assert values[1] == "# Updated Content"
        assert values[2] == str(report_id)
        assert result is not None
        assert result.name == "Updated Name"
        assert result.content == "# Updated Content"
        assert result.provenance_data == {"manifest": {"flow_id": "test"}}

    def test_update_report_no_fields(self, repository, mock_connection):
        """Test update_report with no fields returns existing report."""
        report_id = uuid4()
        now = datetime.now()

        # Mock get_report call (called when no updates provided)
        mock_connection.execute.return_value = (
            str(report_id),
            "Original Name",
            "# Original Content",
            now,
            None,
            1,  # version
        )

        result = repository.update_report(report_id=report_id)

        # Should call get_report instead of update
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        query = call_args.kwargs["query"]
        assert "SELECT" in query  # get_report uses SELECT
        assert result is not None
        assert result.name == "Original Name"

    def test_update_report_not_found(self, repository, mock_connection):
        """Test update_report returns None for non-existent report."""
        mock_connection.execute.return_value = None

        result = repository.update_report(report_id=uuid4(), name="Updated Name")

        assert result is None

    def test_update_report_preserves_provenance_data(self, repository, mock_connection):
        """Test update_report preserves existing provenance data."""
        report_id = uuid4()
        now = datetime.now()
        provenance = {
            "manifest": {"flow_id": "test_flow", "run_id": "run_123"},
            "view_model": {"steps": []},
        }

        mock_connection.execute.return_value = (
            str(report_id),
            "Updated Name",
            "# Original Content",
            now,
            provenance,
            1,  # version
        )

        result = repository.update_report(report_id=report_id, name="Updated Name")

        assert result is not None
        assert result.provenance_data == provenance
        # Verify we didn't update provenance_data
        call_args = mock_connection.execute.call_args
        query = call_args.kwargs["query"]
        assert "provenance_data = %s" not in query.split("WHERE")[0]


class TestReportRouterUpdate:
    """Tests for the report router update endpoint."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock ReportRepository."""
        return MagicMock()

    def test_update_report_endpoint_success(self, mock_repository):
        """Test PUT /report/{report_id} returns updated report."""

        report_id = uuid4()
        now = datetime.now()

        # Mock the current report (before update)
        current_report = Report(
            id=report_id,
            name="Original Name",
            content="# Original Content",
            created_at=now,
            version=1,
            provenance_data=None,
        )

        mock_report = Report(
            id=report_id,
            name="Updated Name",
            content="# Updated Content",
            created_at=now,
            version=2,
            provenance_data=None,
        )
        mock_repository.get_report.return_value = current_report
        mock_repository.update_report.return_value = mock_report
        mock_repository.update_provenance_data.return_value = mock_report

        with patch("lunar_api.report.router.app_context") as mock_app_context:
            mock_app_context.container.get.return_value = mock_repository

            from lunar_api.report.router import router
            client = _build_router_client(router)

            response = client.put(
                f"/report/{report_id}",
                json={"name": "Updated Name", "content": "# Updated Content"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"
            assert data["content"] == "# Updated Content"

    def test_update_report_endpoint_not_found(self, mock_repository):
        """Test PUT /report/{report_id} returns 404 for non-existent report."""

        report_id = uuid4()
        mock_repository.get_report.return_value = None

        with patch("lunar_api.report.router.app_context") as mock_app_context:
            mock_app_context.container.get.return_value = mock_repository

            from lunar_api.report.router import router
            client = _build_router_client(router)

            response = client.put(
                f"/report/{report_id}",
                json={"name": "Updated Name"},
            )

            assert response.status_code == 404
            assert response.json()["detail"] == "Report not found"

    def test_update_report_endpoint_partial_update(self, mock_repository):
        """Test PUT /report/{report_id} with only name."""

        report_id = uuid4()
        now = datetime.now()

        # Mock the current report (before update) - name change only, no content change
        current_report = Report(
            id=report_id,
            name="Original Name",
            content="# Original Content",
            created_at=now,
            version=1,
            provenance_data=None,
        )

        mock_report = Report(
            id=report_id,
            name="Updated Name",
            content="# Original Content",
            created_at=now,
            version=1,
            provenance_data=None,
        )
        mock_repository.get_report.return_value = current_report
        mock_repository.update_report.return_value = mock_report

        with patch("lunar_api.report.router.app_context") as mock_app_context:
            mock_app_context.container.get.return_value = mock_repository

            from lunar_api.report.router import router
            client = _build_router_client(router)

            response = client.put(
                f"/report/{report_id}",
                json={"name": "Updated Name"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"
            # Repository was called with name but not content
            mock_repository.update_report.assert_called_once()
            call_kwargs = mock_repository.update_report.call_args.kwargs
            assert call_kwargs["name"] == "Updated Name"
            assert call_kwargs["content"] is None
