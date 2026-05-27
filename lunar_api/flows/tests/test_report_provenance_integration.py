# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for agent router provenance-to-report integration.

Tests the extract_reports_from_result and update_reports_with_provenance
helper functions that attach provenance data to reports.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import MagicMock
from lunarflow.result import Result

from lunar_api.flows.use_case.run_agent import (
    extract_reports_from_result,
    update_reports_with_provenance,
)
from lunar_api.report.model import Report
from lunar_api.flows.provenance.provenance_models import (
    ProvenanceData,
    Manifest,
    BundleHashInfo,
)


class TestExtractReportsFromResult:
    """Tests for extract_reports_from_result function."""

    def test_extract_report_objects(self):
        """Test extracting Report objects from result value."""
        report1 = Report(
            id=uuid4(),
            name="Report 1",
            content="# Content 1",
            created_at=datetime.now(),
        )
        report2 = Report(
            id=uuid4(),
            name="Report 2",
            content="# Content 2",
            created_at=datetime.now(),
        )

        result_value = {
            "step_1": Result(value="some string result"),
            "step_2": Result(value=report1),
            "step_3": Result(value={"key": "value"}),
            "generate_report": Result(value=report2),
        }

        reports = extract_reports_from_result(result_value)

        assert len(reports) == 2
        assert report1 in reports
        assert report2 in reports

    def test_extract_serialized_report_dicts(self):
        """Test extracting Report-like dicts from result value."""
        report_id = uuid4()
        now = datetime.now()

        result_value = {
            "step_1": Result(value="some result"),
            "generate_report": Result(
                value={
                    "id": str(report_id),
                    "name": "Serialized Report",
                    "content": "# Content",
                    "created_at": now.isoformat(),
                }
            ),
        }

        reports = extract_reports_from_result(result_value)

        assert len(reports) == 1
        assert reports[0].id == report_id
        assert reports[0].name == "Serialized Report"

    def test_extract_mixed_reports(self):
        """Test extracting both Report objects and serialized dicts."""
        report_obj = Report(
            id=uuid4(),
            name="Object Report",
            content="# Object",
            created_at=datetime.now(),
        )
        serialized_id = uuid4()

        result_value = {
            "step_1": Result(value=report_obj),
            "step_2": Result(
                value={
                    "id": str(serialized_id),
                    "name": "Dict Report",
                    "content": "# Dict",
                    "created_at": datetime.now().isoformat(),
                }
            ),
        }

        reports = extract_reports_from_result(result_value)

        assert len(reports) == 2

    def test_extract_no_reports(self):
        """Test returns empty list when no reports present."""
        result_value = {
            "step_1": Result(value="string result"),
            "step_2": Result(value={"key": "value"}),
            "step_3": Result(value=42),
            "step_4": Result(value=None),
        }

        reports = extract_reports_from_result(result_value)

        assert reports == []

    def test_extract_from_empty_result(self):
        """Test returns empty list for empty result."""
        reports = extract_reports_from_result({})

        assert reports == []

    def test_extract_from_non_dict_result(self):
        """Test returns empty list for non-dict result."""
        reports = extract_reports_from_result("not a dict")  # type: ignore

        assert reports == []

    def test_extract_ignores_invalid_report_dicts(self):
        """Test ignores dicts that don't match Report schema."""
        result_value = {
            "step_1": Result(
                value={
                    "id": "not-a-uuid",  # Invalid UUID
                    "name": "Bad Report",
                    "content": "# Content",
                    "created_at": datetime.now().isoformat(),
                },
            ),
            "step_2": Result(
                value={
                    "id": str(uuid4()),
                    "name": "Missing fields",  # Missing content and created_at
                }
            ),
            "step_3": Result(
                value={
                    "other": "structure",
                }
            ),
        }

        reports = extract_reports_from_result(result_value)

        assert len(reports) == 0

    def test_extract_with_uuid_object_id(self):
        """Test extracting dict with UUID object instead of string."""
        report_id = uuid4()

        result_value = {
            "step_1": Result(
                value={
                    "id": report_id,  # UUID object, not string
                    "name": "UUID Object Report",
                    "content": "# Content",
                    "created_at": datetime.now(),  # datetime object
                }
            ),
        }

        reports = extract_reports_from_result(result_value)

        assert len(reports) == 1
        assert reports[0].id == report_id


class TestUpdateReportsWithProvenance:
    """Tests for update_reports_with_provenance function."""

    @pytest.fixture
    def sample_provenance(self):
        """Create sample provenance data for testing."""
        return ProvenanceData(
            manifest=Manifest(
                base_uri="http://example.com/prov/",
                flow_id="test_flow",
                run_id="run_123",
                bundles={"prospective": "http://example.com/prov/prospective"},
                generated_at=datetime.now(timezone.utc).isoformat(),
                bundle_hashes={
                    "prospective": BundleHashInfo(
                        sha256_nt_sorted="abc123",
                        triple_count=10,
                    )
                },
            ),
            trig="@prefix prov: <http://www.w3.org/ns/prov#> .",
            view_model=None,
        )

    @pytest.fixture
    def mock_repository(self):
        """Create mock report repository."""
        return MagicMock()

    def test_update_single_report(self, sample_provenance, mock_repository):
        """Test updating a single report with provenance."""
        report = Report(
            id=uuid4(),
            name="Test Report",
            content="# Content",
            created_at=datetime.now(),
        )
        mock_repository.update_report_with_provenance_and_content.return_value = report

        updated_ids = update_reports_with_provenance(
            reports=[report],
            provenance_data=sample_provenance,
            report_repository=mock_repository,
        )

        assert len(updated_ids) == 1
        assert updated_ids[0] == report.id
        mock_repository.update_report_with_provenance_and_content.assert_called_once()

    def test_update_multiple_reports(self, sample_provenance, mock_repository):
        """Test updating multiple reports with provenance."""
        reports = [
            Report(
                id=uuid4(),
                name=f"Report {i}",
                content=f"# Content {i}",
                created_at=datetime.now(),
            )
            for i in range(3)
        ]
        mock_repository.update_report_with_provenance_and_content.side_effect = reports

        updated_ids = update_reports_with_provenance(
            reports=reports,
            provenance_data=sample_provenance,
            report_repository=mock_repository,
        )

        assert len(updated_ids) == 3
        assert mock_repository.update_report_with_provenance_and_content.call_count == 3

    def test_update_empty_reports_list(self, sample_provenance, mock_repository):
        """Test updating empty list returns empty result."""
        updated_ids = update_reports_with_provenance(
            reports=[],
            provenance_data=sample_provenance,
            report_repository=mock_repository,
        )

        assert updated_ids == []
        mock_repository.update_report_with_provenance_and_content.assert_not_called()

    def test_update_handles_repository_failure(
        self, sample_provenance, mock_repository
    ):
        """Test gracefully handles repository errors."""
        report1 = Report(
            id=uuid4(),
            name="Report 1",
            content="# Content 1",
            created_at=datetime.now(),
        )
        report2 = Report(
            id=uuid4(),
            name="Report 2",
            content="# Content 2",
            created_at=datetime.now(),
        )

        # First call succeeds, second fails
        mock_repository.update_report_with_provenance_and_content.side_effect = [
            report1,
            Exception("Database error"),
        ]

        updated_ids = update_reports_with_provenance(
            reports=[report1, report2],
            provenance_data=sample_provenance,
            report_repository=mock_repository,
        )

        # Should still have first report updated
        assert len(updated_ids) == 1
        assert updated_ids[0] == report1.id

    def test_update_handles_not_found(self, sample_provenance, mock_repository):
        """Test handles case where report not found (returns None)."""
        report = Report(
            id=uuid4(),
            name="Test Report",
            content="# Content",
            created_at=datetime.now(),
        )
        mock_repository.update_report_with_provenance_and_content.return_value = None

        updated_ids = update_reports_with_provenance(
            reports=[report],
            provenance_data=sample_provenance,
            report_repository=mock_repository,
        )

        assert updated_ids == []

    def test_provenance_serialized_correctly(self, sample_provenance, mock_repository):
        """Test provenance is serialized as JSON-compatible dict."""
        report = Report(
            id=uuid4(),
            name="Test Report",
            content="# Content",
            created_at=datetime.now(),
        )
        mock_repository.update_report_with_provenance_and_content.return_value = report

        update_reports_with_provenance(
            reports=[report],
            provenance_data=sample_provenance,
            report_repository=mock_repository,
        )

        call_args = mock_repository.update_report_with_provenance_and_content.call_args
        provenance_dict = call_args.kwargs["provenance_data"]

        # Verify it's a dict with expected structure
        assert isinstance(provenance_dict, dict)
        assert "manifest" in provenance_dict
        assert "trig" in provenance_dict
        assert provenance_dict["manifest"]["flow_id"] == "test_flow"
