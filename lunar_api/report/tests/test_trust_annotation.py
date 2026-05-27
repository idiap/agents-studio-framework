# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for Trust Annotation Utility Module.
"""

from lunar_api.report.utils.trust_annotation import (
    TrustAnnotation,
    parse_trust_annotation,
    parse_all_trust_annotations,
    strip_trust_annotations,
    annotate_component_output,
    annotate_report_from_template,
    get_annotations_from_report,
)


class TestTrustAnnotation:
    """Tests for TrustAnnotation dataclass."""

    def test_to_start_comment_basic(self):
        """Test generating start comment with basic fields."""
        annotation = TrustAnnotation(
            component_id="test_component",
            trust_index=85,
            confidence=90,
        )
        comment = annotation.to_start_comment()

        assert "lunar/component-id=test_component" in comment
        assert "lunar/trust-start=85/100" in comment
        assert "lunar/confidence=90" in comment
        assert comment.startswith("<!--")
        assert comment.endswith("-->")

    def test_to_start_comment_with_all_fields(self):
        """Test generating start comment with all fields."""
        annotation = TrustAnnotation(
            component_id="complex_component",
            trust_index=75,
            confidence=80,
            band="amber",
            risk=0.25,
            step_kind="GEN",
            depth=2,
            missingness=0.1,
        )
        comment = annotation.to_start_comment()

        assert "lunar/component-id=complex_component" in comment
        assert "lunar/trust-start=75/100" in comment
        assert "lunar/confidence=80" in comment
        assert "lunar/band=amber" in comment
        assert "lunar/risk=0.2500" in comment
        assert "lunar/step-kind=GEN" in comment

    def test_end_comment(self):
        """Test end comment is static."""
        assert TrustAnnotation.end_comment() == "<!-- lunar/trust-end -->"


class TestParseTrustAnnotation:
    """Tests for parse_trust_annotation function."""

    def test_parse_basic_annotation(self):
        """Test parsing a basic trust annotation."""
        text = """Some text before
<!-- lunar/component-id=my_component lunar/trust-start=94/100 lunar/confidence=60 -->
This is the annotated content
<!-- lunar/trust-end -->
Some text after"""

        result = parse_trust_annotation(text)
        assert result is not None

        annotation, content, start_pos, end_pos = result
        assert annotation.component_id == "my_component"
        assert annotation.trust_index == 94
        assert annotation.confidence == 60
        assert "This is the annotated content" in content

    def test_parse_annotation_with_all_attributes(self):
        """Test parsing annotation with all attributes."""
        text = """<!-- lunar/component-id=gen_step lunar/trust-start=70/100 lunar/confidence=80 lunar/band=amber lunar/risk=0.30 lunar/step-kind=GEN -->
Generated content here
<!-- lunar/trust-end -->"""

        result = parse_trust_annotation(text)
        assert result is not None

        annotation, content, start_pos, end_pos = result
        assert annotation.component_id == "gen_step"
        assert annotation.trust_index == 70
        assert annotation.confidence == 80
        assert annotation.band == "amber"
        assert annotation.risk == 0.30
        assert annotation.step_kind == "GEN"
        assert "Generated content here" in content

    def test_parse_no_annotation(self):
        """Test parsing text without annotation returns None."""
        text = "This is just regular text without any annotations."
        result = parse_trust_annotation(text)
        assert result is None

    def test_parse_incomplete_annotation(self):
        """Test parsing incomplete annotation (missing end tag) returns None."""
        text = """<!-- lunar/component-id=test lunar/trust-start=50/100 lunar/confidence=50 -->
Content without end tag"""
        result = parse_trust_annotation(text)
        assert result is None


class TestParseAllTrustAnnotations:
    """Tests for parse_all_trust_annotations function."""

    def test_parse_multiple_annotations(self):
        """Test parsing multiple annotations in sequence."""
        text = """# Report

<!-- lunar/component-id=first_component lunar/trust-start=90/100 lunar/confidence=85 -->
First component output
<!-- lunar/trust-end -->

Some text between

<!-- lunar/component-id=second_component lunar/trust-start=75/100 lunar/confidence=70 -->
Second component output
<!-- lunar/trust-end -->
"""

        results = parse_all_trust_annotations(text)
        assert len(results) == 2

        first_ann, first_content, _, _ = results[0]
        assert first_ann.component_id == "first_component"
        assert first_ann.trust_index == 90
        assert "First component output" in first_content

        second_ann, second_content, _, _ = results[1]
        assert second_ann.component_id == "second_component"
        assert second_ann.trust_index == 75
        assert "Second component output" in second_content

    def test_parse_no_annotations(self):
        """Test parsing text with no annotations returns empty list."""
        text = "Just regular markdown content."
        results = parse_all_trust_annotations(text)
        assert results == []


class TestStripTrustAnnotations:
    """Tests for strip_trust_annotations function."""

    def test_strip_single_annotation(self):
        """Test stripping a single annotation."""
        text = """# Title

<!-- lunar/component-id=test lunar/trust-start=85/100 lunar/confidence=90 -->
Content to keep
<!-- lunar/trust-end -->

Footer"""

        result = strip_trust_annotations(text)

        assert "Content to keep" in result
        assert "lunar/component-id" not in result
        assert "lunar/trust-start" not in result
        assert "lunar/trust-end" not in result
        assert "# Title" in result
        assert "Footer" in result

    def test_strip_multiple_annotations(self):
        """Test stripping multiple annotations."""
        text = """<!-- lunar/component-id=first lunar/trust-start=90/100 lunar/confidence=90 -->
First content
<!-- lunar/trust-end -->

<!-- lunar/component-id=second lunar/trust-start=80/100 lunar/confidence=80 -->
Second content
<!-- lunar/trust-end -->"""

        result = strip_trust_annotations(text)

        assert "First content" in result
        assert "Second content" in result
        assert "lunar/component-id" not in result
        assert result.count("lunar/trust-end") == 0

    def test_strip_no_annotations(self):
        """Test stripping from text without annotations returns original."""
        text = "No annotations here."
        result = strip_trust_annotations(text)
        assert result == text


class TestAnnotateComponentOutput:
    """Tests for annotate_component_output function."""

    def test_annotate_basic_output(self):
        """Test annotating a basic component output."""
        result = annotate_component_output(
            component_id="my_component",
            content="# Analysis\n\nSome markdown content",
            trust_data={
                "trust_index": 85,
                "confidence": 90,
                "band": "green",
                "risk": 0.15,
                "step_kind": "DET",
            },
        )

        assert "lunar/component-id=my_component" in result
        assert "lunar/trust-start=85/100" in result
        assert "lunar/confidence=90" in result
        assert "# Analysis" in result
        assert "Some markdown content" in result
        assert "lunar/trust-end" in result

    def test_annotate_with_minimal_trust_data(self):
        """Test annotating with minimal trust data (uses defaults)."""
        result = annotate_component_output(
            component_id="simple",
            content="Simple content",
            trust_data={"trust_index": 50, "confidence": 60},
        )

        assert "lunar/component-id=simple" in result
        assert "lunar/trust-start=50/100" in result
        assert "Simple content" in result


class TestAnnotateReportFromTemplate:
    """Tests for annotate_report_from_template function."""

    def test_annotate_single_placeholder(self):
        """Test annotating template with single placeholder."""
        template = """# Report

{analysis_output}

## Conclusion
"""
        component_outputs = {
            "analysis_output": "This is the analysis result.",
        }
        trust_scores = {
            "analysis_output": {
                "trust_index": 80,
                "confidence": 85,
                "band": "green",
                "risk": 0.2,
                "step_kind": "GEN",
            },
        }

        result = annotate_report_from_template(
            template=template,
            component_outputs=component_outputs,
            trust_scores=trust_scores,
        )

        assert "# Report" in result
        assert "## Conclusion" in result
        assert "This is the analysis result." in result
        assert "lunar/component-id=analysis_output" in result
        assert "lunar/trust-start=80/100" in result

    def test_annotate_double_brace_placeholder(self):
        """Test annotating template with {{placeholder}} syntax."""
        template = """# Report

{{data_summary}}

End"""
        component_outputs = {
            "data_summary": "Summary of the data.",
        }
        trust_scores = {
            "data_summary": {
                "trust_index": 90,
                "confidence": 95,
            },
        }

        result = annotate_report_from_template(
            template=template,
            component_outputs=component_outputs,
            trust_scores=trust_scores,
        )

        assert "Summary of the data." in result
        assert "lunar/component-id=data_summary" in result

    def test_annotate_multiple_placeholders(self):
        """Test annotating template with multiple placeholders."""
        template = """# Report

## Section 1
{first_output}

## Section 2
{second_output}
"""
        component_outputs = {
            "first_output": "First analysis",
            "second_output": "Second analysis",
        }
        trust_scores = {
            "first_output": {"trust_index": 85, "confidence": 90},
            "second_output": {"trust_index": 70, "confidence": 75},
        }

        result = annotate_report_from_template(
            template=template,
            component_outputs=component_outputs,
            trust_scores=trust_scores,
        )

        assert "First analysis" in result
        assert "Second analysis" in result
        assert "lunar/component-id=first_output" in result
        assert "lunar/component-id=second_output" in result

    def test_annotate_missing_trust_score(self):
        """Test that missing trust score skips annotation."""
        template = "{component}"
        component_outputs = {"component": "Output"}
        trust_scores = {}  # No trust score provided

        result = annotate_report_from_template(
            template=template,
            component_outputs=component_outputs,
            trust_scores=trust_scores,
        )

        # Should not add annotation when trust score is missing
        assert "lunar/trust-start" not in result
        assert "lunar/trust-end" not in result
        assert "Output" in result


class TestGetAnnotationsFromReport:
    """Tests for get_annotations_from_report function."""

    def test_get_annotations_dict(self):
        """Test extracting annotations as a dictionary."""
        text = """<!-- lunar/component-id=comp_a lunar/trust-start=90/100 lunar/confidence=85 -->
Content A
<!-- lunar/trust-end -->

<!-- lunar/component-id=comp_b lunar/trust-start=75/100 lunar/confidence=70 -->
Content B
<!-- lunar/trust-end -->"""

        annotations = get_annotations_from_report(text)

        assert "comp_a" in annotations
        assert "comp_b" in annotations
        assert annotations["comp_a"].trust_index == 90
        assert annotations["comp_b"].trust_index == 75

    def test_get_empty_annotations(self):
        """Test getting annotations from text without any."""
        annotations = get_annotations_from_report("No annotations")
        assert annotations == {}


class TestRoundTrip:
    """Tests for annotation round-trip (annotate then strip)."""

    def test_annotate_and_strip_recovers_original(self):
        """Test that annotating and then stripping recovers original content."""
        original_content = "# Analysis\n\nThis is some analysis text."
        trust_data = {"trust_index": 85, "confidence": 90}

        annotated = annotate_component_output(
            component_id="test",
            content=original_content,
            trust_data=trust_data,
        )

        stripped = strip_trust_annotations(annotated)

        # The content should be preserved (may have slight whitespace differences)
        assert original_content.strip() in stripped.strip()

    def test_complex_report_round_trip(self):
        """Test round-trip for a complex report with multiple annotations."""
        template = """# Report

## Analysis
{analysis}

## Summary
{summary}
"""
        outputs = {
            "analysis": "Detailed analysis here.",
            "summary": "Brief summary here.",
        }
        trust_scores = {
            "analysis": {"trust_index": 80, "confidence": 85},
            "summary": {"trust_index": 90, "confidence": 95},
        }

        annotated = annotate_report_from_template(
            template=template,
            component_outputs=outputs,
            trust_scores=trust_scores,
        )

        # Verify annotations exist
        assert "lunar/component-id=analysis" in annotated
        assert "lunar/component-id=summary" in annotated

        # Strip and verify content preserved
        stripped = strip_trust_annotations(annotated)
        assert "# Report" in stripped
        assert "Detailed analysis here." in stripped
        assert "Brief summary here." in stripped
        assert "lunar/component-id" not in stripped
