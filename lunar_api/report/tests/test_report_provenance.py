# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for Report model and ReportRepository with provenance data support.
"""

import json
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import MagicMock
from typing import Any, Dict

from lunar_api.report.model import Report, ReportInput, ReportUpdate
from lunar_api.report.repository.report_repository import (
    ReportRepository,
    _parse_provenance_data,
)


class TestReportModel:
    """Tests for Report model with provenance data."""

    def test_report_with_provenance_data(self):
        """Test Report model includes provenance_data field."""
        report_id = uuid4()
        now = datetime.now()
        provenance = {"manifest": {"flow_id": "test_flow"}, "view_model": {}}

        report = Report(
            id=report_id,
            name="Test Report",
            content="# Report Content",
            created_at=now,
            provenance_data=provenance,
        )

        assert report.id == report_id
        assert report.name == "Test Report"
        assert report.content == "# Report Content"
        assert report.created_at == now
        assert report.provenance_data == provenance
        assert report.provenance_data is not None
        assert report.provenance_data["manifest"]["flow_id"] == "test_flow"

    def test_report_without_provenance_data(self):
        """Test Report model works without provenance_data."""
        report_id = uuid4()
        now = datetime.now()

        report = Report(
            id=report_id,
            name="Test Report",
            content="# Report Content",
            created_at=now,
        )

        assert report.id == report_id
        assert report.provenance_data is None

    def test_report_to_dict_with_provenance(self):
        """Test Report.to_dict() includes provenance_data."""
        report_id = uuid4()
        now = datetime.now()
        provenance = {"manifest": {"flow_id": "test_flow"}}

        report = Report(
            id=report_id,
            name="Test Report",
            content="# Content",
            created_at=now,
            provenance_data=provenance,
        )

        result = report.to_dict()

        assert result["id"] == str(report_id)
        assert result["name"] == "Test Report"
        assert result["content"] == "# Content"
        assert result["created_at"] == now.isoformat()
        assert result["provenance_data"] == provenance

    def test_report_to_dict_without_provenance(self):
        """Test Report.to_dict() handles None provenance_data."""
        report_id = uuid4()
        now = datetime.now()

        report = Report(
            id=report_id,
            name="Test Report",
            content="# Content",
            created_at=now,
        )

        result = report.to_dict()

        assert result["provenance_data"] is None


class TestReportUpdate:
    """Tests for ReportUpdate model with provenance_data."""

    def test_report_update_with_provenance_data(self):
        """Test ReportUpdate can include provenance_data."""
        provenance = {"manifest": {"flow_id": "test"}}

        update = ReportUpdate(provenance_data=provenance)

        assert update.provenance_data == provenance
        assert update.name is None
        assert update.content is None

    def test_report_update_without_provenance_data(self):
        """Test ReportUpdate works without provenance_data."""
        update = ReportUpdate(name="Updated Name")

        assert update.name == "Updated Name"
        assert update.provenance_data is None


class TestParseProvenanceData:
    """Tests for the _parse_provenance_data helper function."""

    def test_parse_dict_provenance(self):
        """Test parsing provenance data that is already a dict."""
        provenance: Dict[str, Any] = {"manifest": {"flow_id": "test_flow"}}
        result = _parse_provenance_data(provenance)
        assert result == provenance

    def test_parse_json_string_provenance(self):
        """Test parsing provenance data from JSON string."""
        provenance = {"manifest": {"flow_id": "test_flow"}}
        json_str = json.dumps(provenance)
        result = _parse_provenance_data(json_str)
        assert result == provenance

    def test_parse_none_provenance(self):
        """Test parsing None provenance data."""
        result = _parse_provenance_data(None)
        assert result is None

    def test_parse_invalid_json_string(self):
        """Test parsing invalid JSON string returns None."""
        result = _parse_provenance_data("not valid json")
        assert result is None

    def test_parse_empty_dict(self):
        """Test parsing empty dict provenance."""
        result = _parse_provenance_data({})
        assert result == {}


class TestReportRepository:
    """Tests for ReportRepository with provenance data support."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock PostgresConnection."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_connection):
        """Create a ReportRepository with mocked connection."""
        return ReportRepository(sql_database_connection=mock_connection)

    def test_create_report(self, repository, mock_connection):
        """Test create_report calls execute with correct query."""
        report_id = uuid4()
        now = datetime.now()

        mock_connection.execute.return_value = (
            str(report_id),
            "Test Report",
            "# Content",
            now,
            None,
            1,  # version
        )

        report_input = ReportInput(name="Test Report", content="# Content")
        result = repository.create_report(report_input)

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        assert "INSERT INTO reports" in call_args.kwargs["query"]
        assert (
            "RETURNING id, name, content, created_at, provenance_data, version"
            in call_args.kwargs["query"]
        )
        assert result.name == "Test Report"

    def test_get_report(self, repository, mock_connection):
        """Test get_report retrieves report with provenance data."""
        report_id = uuid4()
        now = datetime.now()
        provenance = {"manifest": {"flow_id": "test"}}

        mock_connection.execute.return_value = (
            str(report_id),
            "Test Report",
            "# Content",
            now,
            provenance,
            1,  # version
        )

        result = repository.get_report(report_id)

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        assert (
            "SELECT id, name, content, created_at, provenance_data, version"
            in call_args.kwargs["query"]
        )
        assert result is not None
        assert result.provenance_data == provenance

    def test_get_report_not_found(self, repository, mock_connection):
        """Test get_report returns None for non-existent report."""
        mock_connection.execute.return_value = None

        result = repository.get_report(uuid4())

        assert result is None

    def test_list_reports(self, repository, mock_connection):
        """Test list_reports retrieves reports with provenance data."""
        report_id = uuid4()
        now = datetime.now()
        provenance = {"manifest": {"flow_id": "test"}}

        mock_connection.execute.return_value = [
            (str(report_id), "Report 1", "# Content 1", now, provenance, 2),
            (str(uuid4()), "Report 2", "# Content 2", now, None, 1),
        ]

        result = repository.list_reports(limit=10)

        assert len(result) == 2
        assert result[0].provenance_data == provenance
        assert result[0].version == 2
        assert result[1].provenance_data is None
        assert result[1].version == 1

    def test_update_provenance_data(self, repository, mock_connection):
        """Test update_provenance_data updates report with provenance."""
        report_id = uuid4()
        now = datetime.now()
        provenance = {
            "manifest": {"flow_id": "test_flow", "run_id": "run_123"},
            "view_model": {"steps": []},
        }

        mock_connection.execute.return_value = (
            str(report_id),
            "Test Report",
            "# Content",
            now,
            provenance,
            1,  # version
        )

        result = repository.update_provenance_data(report_id, provenance)

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args
        assert "UPDATE reports" in call_args.kwargs["query"]
        assert "SET provenance_data = %s" in call_args.kwargs["query"]
        assert (
            "RETURNING id, name, content, created_at, provenance_data, version"
            in call_args.kwargs["query"]
        )
        assert result is not None
        assert result.provenance_data == provenance

    def test_update_provenance_data_not_found(self, repository, mock_connection):
        """Test update_provenance_data returns None for non-existent report."""
        mock_connection.execute.return_value = None

        result = repository.update_provenance_data(uuid4(), {"test": "data"})

        assert result is None

    def test_delete_report(self, repository, mock_connection):
        """Test delete_report deletes report correctly."""
        report_id = uuid4()

        mock_connection.execute.return_value = None

        result = repository.delete_report(report_id)

        mock_connection.execute.assert_called_once()
        assert result is True
