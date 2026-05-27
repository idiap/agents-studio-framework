# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for Report Provenance Service - tracks edits to reports and updates provenance data.
"""

from uuid import uuid4

from lunar_api.report.use_case.report_provenance_service import (
    create_initial_provenance,
    add_edit_to_provenance,
    get_provenance_view_model,
)


class TestCreateInitialProvenance:
    """Tests for create_initial_provenance function."""

    def test_create_initial_provenance_basic(self):
        """Test creating initial provenance for a new report."""
        report_id = uuid4()
        content = "# My Report\n\nThis is the content."

        result = create_initial_provenance(
            report_id=report_id,
            content=content,
            username="test_user",
        )

        assert result is not None
        assert "manifest" in result
        assert "view_model" in result
        assert "versions" in result

        # Check manifest
        manifest = result["manifest"]
        assert manifest["report_id"] == str(report_id)
        assert manifest["version"] == 0
        assert "created_at" in manifest

        # Check view_model
        view_model = result["view_model"]
        assert "base_uri" in view_model
        assert "run_id" in view_model
        assert "workflow" in view_model
        assert "data_sources" in view_model
        assert "steps" in view_model
        assert len(view_model["steps"]) == 1
        assert view_model["steps"][0]["id"] == "report_creation"

        # Check versions
        versions = result["versions"]
        assert len(versions) == 1
        assert versions[0]["version"] == 0
        assert versions[0]["content"] == content
        assert versions[0]["username"] == "test_user"

    def test_create_initial_provenance_with_long_content(self):
        """Test creating initial provenance with content that exceeds summary length."""
        report_id = uuid4()
        content = "# " + "x" * 1000  # Long content

        result = create_initial_provenance(
            report_id=report_id,
            content=content,
            username="test_user",
        )

        # Content in version should be full
        assert result["versions"][0]["content"] == content
        # Summary in output should be truncated
        assert len(result["view_model"]["steps"][0]["output"]["value"]) <= 500


class TestAddEditToProvenance:
    """Tests for add_edit_to_provenance function."""

    def test_add_edit_without_existing_provenance(self):
        """Test adding an edit when no provenance exists yet."""
        report_id = uuid4()
        old_content = "# My Report\n\nOriginal content."
        new_content = "# My Report\n\nUpdated content with more text."

        result = add_edit_to_provenance(
            existing_provenance=None,
            report_id=report_id,
            old_content=old_content,
            new_content=new_content,
            username="editor_user",
            note="Fixed typo",
        )

        assert result is not None
        assert "manifest" in result
        assert "view_model" in result
        assert "versions" in result

        # Should have created initial + added edit
        versions = result["versions"]
        assert len(versions) == 2
        assert versions[0]["version"] == 0
        assert versions[0]["content"] == old_content
        assert versions[1]["version"] == 1
        assert versions[1]["content"] == new_content
        assert versions[1]["username"] == "editor_user"
        assert versions[1]["note"] == "Fixed typo"

    def test_add_edit_with_existing_provenance(self):
        """Test adding an edit to existing provenance."""
        report_id = uuid4()
        old_content = "# My Report\n\nOriginal content."
        new_content = "# My Report\n\nUpdated content."

        # Create initial provenance
        existing_provenance = create_initial_provenance(
            report_id=report_id,
            content=old_content,
            username="creator",
        )

        # Add an edit
        result = add_edit_to_provenance(
            existing_provenance=existing_provenance,
            report_id=report_id,
            old_content=old_content,
            new_content=new_content,
            username="editor",
            note="First edit",
        )

        versions = result["versions"]
        assert len(versions) == 2
        assert versions[1]["version"] == 1
        assert versions[1]["username"] == "editor"
        assert "diff_stats" in versions[1]

    def test_add_multiple_edits(self):
        """Test adding multiple sequential edits."""
        report_id = uuid4()
        content_v0 = "# Report v0"
        content_v1 = "# Report v1"
        content_v2 = "# Report v2"

        # Create initial
        provenance = create_initial_provenance(
            report_id=report_id,
            content=content_v0,
            username="creator",
        )

        # First edit
        provenance = add_edit_to_provenance(
            existing_provenance=provenance,
            report_id=report_id,
            old_content=content_v0,
            new_content=content_v1,
            username="editor1",
        )

        # Second edit
        provenance = add_edit_to_provenance(
            existing_provenance=provenance,
            report_id=report_id,
            old_content=content_v1,
            new_content=content_v2,
            username="editor2",
        )

        versions = provenance["versions"]
        assert len(versions) == 3
        assert versions[0]["version"] == 0
        assert versions[1]["version"] == 1
        assert versions[2]["version"] == 2
        assert versions[2]["username"] == "editor2"

        # Check manifest is updated
        assert provenance["manifest"]["version"] == 2
        assert provenance["manifest"]["last_modified_by"] == "editor2"

    def test_add_edit_creates_edges(self):
        """Test that adding an edit creates proper dependency edges."""
        report_id = uuid4()
        old_content = "Original"
        new_content = "Updated"

        existing = create_initial_provenance(
            report_id=report_id,
            content=old_content,
            username="creator",
        )

        result = add_edit_to_provenance(
            existing_provenance=existing,
            report_id=report_id,
            old_content=old_content,
            new_content=new_content,
            username="editor",
        )

        edges = result["view_model"]["edges"]
        assert len(edges) == 1
        assert edges[0]["type"] == "dependsOn"
        assert edges[0]["from"] == "report_creation"
        assert edges[0]["to"] == "manual_edit_1"

    def test_diff_stats_are_computed(self):
        """Test that diff statistics are computed correctly."""
        report_id = uuid4()
        old_content = "Line 1\nLine 2\nLine 3"
        new_content = "Line 1\nModified Line 2\nLine 3\nNew Line 4"

        result = add_edit_to_provenance(
            existing_provenance=None,
            report_id=report_id,
            old_content=old_content,
            new_content=new_content,
            username="editor",
        )

        # Get the edit version's diff stats
        edit_version = result["versions"][-1]
        assert "diff_stats" in edit_version
        stats = edit_version["diff_stats"]
        assert "lines_added" in stats
        assert "lines_removed" in stats
        assert "chars_before" in stats
        assert "chars_after" in stats


class TestGetProvenanceViewModel:
    """Tests for get_provenance_view_model function."""

    def test_get_view_model_from_provenance(self):
        """Test extracting view model from provenance data."""
        report_id = uuid4()
        provenance = create_initial_provenance(
            report_id=report_id,
            content="# Test",
            username="test",
        )

        result = get_provenance_view_model(provenance)

        assert result is not None
        assert "base_uri" in result
        assert "run_id" in result
        assert "workflow" in result
        assert "steps" in result

    def test_get_view_model_from_none(self):
        """Test extracting view model when provenance is None."""
        result = get_provenance_view_model(None)
        assert result is None

    def test_get_view_model_from_empty_dict(self):
        """Test extracting view model when provenance is empty dict."""
        result = get_provenance_view_model({})
        assert result is None


class TestProvenanceViewModelStructure:
    """Tests to ensure the view model structure matches frontend expectations."""

    def test_view_model_has_required_fields(self):
        """Test that the view model has all fields required by ProvenanceGraph component."""
        report_id = uuid4()
        provenance = create_initial_provenance(
            report_id=report_id,
            content="# Test Report",
            username="test_user",
        )

        view_model = provenance["view_model"]

        # Required top-level fields
        assert "base_uri" in view_model
        assert "run_id" in view_model
        assert "workflow" in view_model
        assert "data_sources" in view_model
        assert "steps" in view_model
        assert "edges" in view_model
        assert "recent_outputs" in view_model

        # Workflow structure
        workflow = view_model["workflow"]
        assert "id" in workflow
        assert "name" in workflow
        assert "description" in workflow

        # Step structure
        step = view_model["steps"][0]
        assert "id" in step
        assert "component" in step
        assert "plan" in step
        assert "depends_on" in step
        assert "flow_inputs_used" in step
        assert "run" in step
        assert "inputs" in step
        assert "output" in step
        assert "uri" in step

        # Data source structure
        data_source = view_model["data_sources"][0]
        assert "id" in data_source
        assert "uri" in data_source
        assert "value" in data_source
        assert "summary" in data_source
        assert "is_external" in data_source

    def test_step_input_binding_structure(self):
        """Test that step input bindings have the correct structure."""
        report_id = uuid4()
        old_content = "# Original"
        new_content = "# Modified"

        provenance = create_initial_provenance(
            report_id=report_id,
            content=old_content,
            username="creator",
        )
        provenance = add_edit_to_provenance(
            existing_provenance=provenance,
            report_id=report_id,
            old_content=old_content,
            new_content=new_content,
            username="editor",
        )

        # Get the edit step
        edit_step = provenance["view_model"]["steps"][1]
        input_binding = edit_step["inputs"][0]

        assert "name" in input_binding
        assert "raw" in input_binding
        assert "kind" in input_binding
        assert "ref" in input_binding
        assert "value_summary" in input_binding
