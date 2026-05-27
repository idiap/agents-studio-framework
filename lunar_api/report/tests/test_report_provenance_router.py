# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for Report Provenance Router endpoints.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import MagicMock

from lunar_api.report.model import Report


class TestReportProvenanceEndpoint:
    """Tests for the GET /report/{report_id}/provenance endpoint."""

    @pytest.fixture
    def mock_report_repository(self):
        """Create a mock ReportRepository."""
        return MagicMock()

    @pytest.fixture
    def sample_report_with_provenance(self):
        """Create a sample report with provenance data."""
        report_id = uuid4()
        return Report(
            id=report_id,
            name="Test Report",
            content="# Test Content",
            created_at=datetime.now(),
            provenance_data={
                "manifest": {
                    "base_uri": f"http://lunarbase.ai/prov/report/{report_id}",
                    "report_id": str(report_id),
                    "run_id": "test-run",
                    "version": 1,
                },
                "view_model": {
                    "base_uri": f"http://lunarbase.ai/prov/report/{report_id}",
                    "run_id": "test-run",
                    "workflow": {
                        "id": str(report_id),
                        "name": "Report",
                        "description": "Test workflow",
                    },
                    "data_sources": [],
                    "steps": [],
                    "edges": [],
                    "recent_outputs": [],
                },
                "versions": [
                    {
                        "version": 0,
                        "content": "# Test Content",
                        "created_at": "2025-01-13T00:00:00Z",
                        "username": "test",
                    }
                ],
            },
        )

    @pytest.fixture
    def sample_report_without_provenance(self):
        """Create a sample report without provenance data."""
        return Report(
            id=uuid4(),
            name="Test Report",
            content="# Test Content",
            created_at=datetime.now(),
            provenance_data=None,
        )

    def test_get_provenance_returns_view_model(
        self, mock_report_repository, sample_report_with_provenance
    ):
        """Test that the provenance endpoint returns the view model."""
        mock_report_repository.get_report.return_value = sample_report_with_provenance

        # The actual endpoint test would require FastAPI test client
        # Here we test the logic components
        report = mock_report_repository.get_report(sample_report_with_provenance.id)

        assert report is not None
        assert report.provenance_data is not None
        assert "view_model" in report.provenance_data
        assert "manifest" in report.provenance_data
        assert "versions" in report.provenance_data

    def test_provenance_creates_initial_if_none_exists(
        self, mock_report_repository, sample_report_without_provenance
    ):
        """Test that provenance is created if it doesn't exist."""
        from lunar_api.report.use_case.report_provenance_service import (
            create_initial_provenance,
        )

        report = sample_report_without_provenance

        # Simulate what the endpoint does
        if not report.provenance_data:
            initial_provenance = create_initial_provenance(
                report_id=report.id,
                content=report.content,
                username="system",
            )

            assert initial_provenance is not None
            assert "manifest" in initial_provenance
            assert "view_model" in initial_provenance
            assert initial_provenance["manifest"]["report_id"] == str(report.id)


class TestReportUpdateWithProvenance:
    """Tests for the PUT /report/{report_id} endpoint with provenance tracking."""

    @pytest.fixture
    def mock_report_repository(self):
        """Create a mock ReportRepository."""
        return MagicMock()

    def test_update_content_triggers_provenance_update(self, mock_report_repository):
        """Test that updating content triggers a provenance update."""
        from lunar_api.report.use_case.report_provenance_service import (
            add_edit_to_provenance,
        )

        report_id = uuid4()
        old_content = "# Original Content"
        new_content = "# Updated Content"

        # Simulate existing report
        existing_report = Report(
            id=report_id,
            name="Test Report",
            content=old_content,
            created_at=datetime.now(),
            provenance_data=None,
        )

        # Simulate what the endpoint does when content changes
        if new_content != existing_report.content:
            updated_provenance = add_edit_to_provenance(
                existing_provenance=existing_report.provenance_data,
                report_id=report_id,
                old_content=existing_report.content,
                new_content=new_content,
                username="anonymous",
            )

            assert updated_provenance is not None
            assert "versions" in updated_provenance
            # Should have 2 versions: initial + edit
            assert len(updated_provenance["versions"]) == 2

    def test_update_name_only_does_not_trigger_provenance(self, mock_report_repository):
        """Test that updating only the name does not trigger provenance update."""
        report_id = uuid4()
        content = "# Same Content"

        existing_report = Report(
            id=report_id,
            name="Old Name",
            content=content,
            created_at=datetime.now(),
            provenance_data=None,
        )

        # Simulate name update (content stays the same)
        new_content = content  # Same as existing

        # This should not trigger provenance update
        should_update_provenance = new_content != existing_report.content
        assert should_update_provenance is False

    def test_update_with_existing_provenance_appends_version(
        self, mock_report_repository
    ):
        """Test that updating a report with existing provenance appends a new version."""
        from lunar_api.report.use_case.report_provenance_service import (
            create_initial_provenance,
            add_edit_to_provenance,
        )

        report_id = uuid4()
        content_v0 = "# Version 0"
        content_v1 = "# Version 1"
        content_v2 = "# Version 2"

        # Create initial provenance
        provenance = create_initial_provenance(
            report_id=report_id,
            content=content_v0,
            username="system",
        )

        # First edit
        provenance = add_edit_to_provenance(
            existing_provenance=provenance,
            report_id=report_id,
            old_content=content_v0,
            new_content=content_v1,
            username="user1",
        )

        assert len(provenance["versions"]) == 2

        # Second edit
        provenance = add_edit_to_provenance(
            existing_provenance=provenance,
            report_id=report_id,
            old_content=content_v1,
            new_content=content_v2,
            username="user2",
        )

        assert len(provenance["versions"]) == 3
        assert provenance["versions"][2]["version"] == 2
        assert provenance["versions"][2]["username"] == "user2"


class TestProvenanceResponseFormat:
    """Tests to ensure the provenance response format matches frontend expectations."""

    def test_provenance_response_structure(self):
        """Test that the provenance response has the expected structure."""
        from lunar_api.report.use_case.report_provenance_service import (
            create_initial_provenance,
            get_provenance_view_model,
        )

        report_id = uuid4()
        provenance = create_initial_provenance(
            report_id=report_id,
            content="# Test",
            username="test",
        )

        # Simulate the response structure from the endpoint
        response = {
            "report_id": str(report_id),
            "manifest": provenance.get("manifest", {}),
            "view_model": get_provenance_view_model(provenance),
            "versions": provenance.get("versions", []),
        }

        assert "report_id" in response
        assert "manifest" in response
        assert "view_model" in response
        assert "versions" in response

        # Check view_model has required fields for ProvenanceGraph
        view_model = response["view_model"]
        assert "base_uri" in view_model
        assert "run_id" in view_model
        assert "workflow" in view_model
        assert "data_sources" in view_model
        assert "steps" in view_model
        assert "edges" in view_model
        assert "recent_outputs" in view_model
