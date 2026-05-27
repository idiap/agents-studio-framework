# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Trust Annotation Utility Module.

This module provides utilities for annotating report sections with trust index
information from component executions in Lunarflow workflows.

Annotation format:
<!-- lunar/component-id=<id> lunar/trust-start=<trust>/100 lunar/confidence=<conf> [other_data]-->
...content...
<!-- lunar/trust-end -->
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class TrustAnnotation:
    """Represents trust annotation data for a component section."""

    component_id: str
    trust_index: int
    confidence: int
    band: str = "amber"
    risk: float = 0.0
    step_kind: str = "DET"
    depth: int = 0
    missingness: float = 0.0

    def to_start_comment(self) -> str:
        """Generate the opening annotation comment."""
        parts = [
            f"lunar/component-id={self.component_id}",
            f"lunar/trust-start={self.trust_index}/100",
            f"lunar/confidence={self.confidence}",
            f"lunar/band={self.band}",
            f"lunar/risk={self.risk:.4f}",
            f"lunar/step-kind={self.step_kind}",
        ]
        return f"<!-- {' '.join(parts)} -->"

    @staticmethod
    def end_comment() -> str:
        """Return the closing annotation comment."""
        return "<!-- lunar/trust-end -->"


# Regex pattern for parsing trust annotations
TRUST_START_PATTERN = re.compile(
    r"<!--\s*"
    r"lunar/component-id=(\S+)\s+"
    r"lunar/trust-start=(\d+)/100\s+"
    r"lunar/confidence=(\d+)"
    r"(?:\s+lunar/band=(\S+))?"
    r"(?:\s+lunar/risk=([\d.]+))?"
    r"(?:\s+lunar/step-kind=(\S+))?"
    r".*?-->"
)
TRUST_END_PATTERN = re.compile(r"<!--\s*lunar/trust-end\s*-->")

# Pattern for matching template placeholders like {component_id} or {{component_id}}
TEMPLATE_PLACEHOLDER_PATTERN = re.compile(r"\{?\{([a-zA-Z_][a-zA-Z0-9_]*)\}?\}")


def parse_trust_annotation(
    text: str,
) -> Optional[Tuple[TrustAnnotation, str, int, int]]:
    """Parse a trust annotation from text.

    Args:
        text: The text to parse

    Returns:
        Tuple of (TrustAnnotation, annotated_content, start_pos, end_pos) or None
    """
    start_match = TRUST_START_PATTERN.search(text)
    if not start_match:
        return None

    end_match = TRUST_END_PATTERN.search(text, start_match.end())
    if not end_match:
        return None

    annotation = TrustAnnotation(
        component_id=start_match.group(1),
        trust_index=int(start_match.group(2)),
        confidence=int(start_match.group(3)),
        band=start_match.group(4) or "amber",
        risk=float(start_match.group(5)) if start_match.group(5) else 0.0,
        step_kind=start_match.group(6) or "DET",
    )

    content = text[start_match.end() : end_match.start()].strip()
    return annotation, content, start_match.start(), end_match.end()


def parse_all_trust_annotations(
    text: str,
) -> List[Tuple[TrustAnnotation, str, int, int]]:
    """Parse all trust annotations from text.

    Args:
        text: The text to parse

    Returns:
        List of (TrustAnnotation, annotated_content, start_pos, end_pos) tuples
    """
    results = []
    pos = 0

    while pos < len(text):
        result = parse_trust_annotation(text[pos:])
        if not result:
            break
        annotation, content, rel_start, rel_end = result
        results.append((annotation, content, pos + rel_start, pos + rel_end))
        pos = pos + rel_end

    return results


def strip_trust_annotations(text: str) -> str:
    """Remove all trust annotations from text, keeping only the content.

    This is useful for exporting to formats that don't support annotations.

    Args:
        text: The text with annotations

    Returns:
        Text with annotations stripped, content preserved
    """
    result = text

    # Replace all annotation blocks with just their content
    while True:
        start_match = TRUST_START_PATTERN.search(result)
        if not start_match:
            break

        end_match = TRUST_END_PATTERN.search(result, start_match.end())
        if not end_match:
            break

        # Extract just the content between tags
        content = result[start_match.end() : end_match.start()]
        # Replace the entire annotation block with just the content
        result = result[: start_match.start()] + content + result[end_match.end() :]

    return result


def annotate_component_output(
    component_id: str,
    content: str,
    trust_data: Dict[str, Any],
) -> str:
    """Annotate a component's output with trust information.

    Args:
        component_id: The ID of the component
        content: The component's output content
        trust_data: Trust data dictionary with keys like trust_index, confidence, etc.

    Returns:
        Content wrapped with trust annotation comments
    """
    annotation = TrustAnnotation(
        component_id=component_id,
        trust_index=trust_data.get("trust_index", 0),
        confidence=trust_data.get("confidence", 0),
        band=trust_data.get("band", "amber"),
        risk=trust_data.get("risk", 0.0),
        step_kind=trust_data.get("step_kind", "DET"),
        depth=trust_data.get("depth", 0),
        missingness=trust_data.get("missingness", 0.0),
    )

    return f"{annotation.to_start_comment()}\n{content}\n{annotation.end_comment()}"


def annotate_report_from_template(
    template: str,
    component_outputs: Dict[str, str],
    trust_scores: Dict[str, Dict[str, Any]],
) -> str:
    """Annotate a report by replacing template placeholders with annotated component outputs.

    Template placeholders can be either {component_id} or {{component_id}}.

    Args:
        template: The report template with placeholders
        component_outputs: Dictionary mapping component IDs to their output content
        trust_scores: Dictionary mapping component IDs to their trust data

    Returns:
        Report content with all component outputs annotated with trust information
    """
    result = template

    # Find all placeholders and replace them with annotated outputs
    for match in TEMPLATE_PLACEHOLDER_PATTERN.finditer(template):
        component_id = match.group(1)
        placeholder = match.group(0)

        if component_id in component_outputs:
            output = component_outputs[component_id]
            trust_data = trust_scores.get(component_id)

            # Only annotate if trust data is available
            if trust_data:
                annotated_output = annotate_component_output(
                    component_id, output, trust_data
                )
                result = result.replace(placeholder, annotated_output, 1)
            else:
                # No trust data - just replace with plain output
                result = result.replace(placeholder, output, 1)

    return result


def get_annotations_from_report(text: str) -> Dict[str, TrustAnnotation]:
    """Extract all trust annotations from a report as a dictionary.

    Args:
        text: The report text with annotations

    Returns:
        Dictionary mapping component IDs to their TrustAnnotation objects
    """
    annotations = parse_all_trust_annotations(text)
    return {ann.component_id: ann for ann, _, _, _ in annotations}
