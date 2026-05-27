# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only


"""Input inference utilities for lunarflow flows.

This module provides utilities to automatically infer AgentInputConfig
from flow definitions by analyzing node inputs for flow input references (&var).
"""

import re
from typing import Any, List, Mapping, Set

from lunarflow.flows import Flow

from lunar_api.flows.models import AgentInputConfig, InputType


# Regex to match flow input references: &variable_name
FLOW_INPUT_PATTERN = re.compile(r"&([A-Za-z_][A-Za-z0-9_]*)")


def _extract_flow_input_refs(value: Any, refs: Set[str]) -> None:
    """Recursively extract flow input references (&var) from a value."""
    if isinstance(value, str):
        matches = FLOW_INPUT_PATTERN.findall(value)
        refs.update(matches)
    elif isinstance(value, dict):
        for v in value.values():
            _extract_flow_input_refs(v, refs)
    elif isinstance(value, list):
        for item in value:
            _extract_flow_input_refs(item, refs)


def _infer_input_type(input_name: str) -> InputType:
    """Infer the input type based on naming conventions.

    Args:
        input_name: The name of the input parameter.

    Returns:
        The inferred InputType.
    """
    name_lower = input_name.lower()

    # Knowledge base field references
    if "kb_field" in name_lower or "field_id" in name_lower:
        return "knowledge-base-field"

    # Knowledge base references
    if "knowledge_base" in name_lower or "kb_id" in name_lower:
        return "knowledge-base"

    # Default to string
    return "string"


def _infer_label(input_name: str) -> str:
    """Generate a human-readable label from an input name.

    Args:
        input_name: The snake_case or camelCase input name.

    Returns:
        A human-readable label.
    """
    normalized_name = re.sub(r"(?<!^)(?=[A-Z])", "_", input_name)
    words = normalized_name.split("_")

    replacements = {
        "kb": "Knowledge Base",
        "id": "ID",
        "url": "URL",
    }

    label_parts = []
    for word in words:
        if not word:
            continue
        replacement = replacements.get(word.lower())
        label_parts.append(replacement if replacement else word.capitalize())

    return " ".join(label_parts)


def _is_optional_input(input_name: str) -> bool:
    """Determine if an input is likely optional based on naming conventions.

    Args:
        input_name: The name of the input parameter.

    Returns:
        True if the input appears to be optional.
    """
    optional_indicators = [
        "optional",
        "filter",
        "instructions",
        "config",
        "settings",
    ]
    name_lower = input_name.lower()
    return any(indicator in name_lower for indicator in optional_indicators)


def infer_inputs_from_flow(flow: Flow) -> List[AgentInputConfig]:
    """Infer AgentInputConfig list from a Flow by analyzing its nodes.

    This function scans all node inputs for flow input references (&var)
    and generates corresponding AgentInputConfig entries.

    Args:
        flow: The lunarflow Flow to analyze.

    Returns:
        List of inferred AgentInputConfig objects.
    """
    refs: Set[str] = set()

    # Extract all flow input references from all nodes
    for node in flow.get_nodes():
        if node.inputs:
            _extract_flow_input_refs(node.inputs, refs)

    # Convert to AgentInputConfig list
    inputs: List[AgentInputConfig] = []
    for ref_name in sorted(refs):  # Sort for deterministic order
        input_type = _infer_input_type(ref_name)
        label = _infer_label(ref_name)
        required = not _is_optional_input(ref_name)

        inputs.append(
            AgentInputConfig(
                id=ref_name,
                label=label,
                type=input_type,
                required=required,
            )
        )

    return inputs


def infer_inputs_from_content(content: Any) -> List[AgentInputConfig]:
    """Infer AgentInputConfig list from raw flow content mapping.

    This is used when flows are fetched from storage and only the serialized
    content is available.
    """
    refs: Set[str] = set()

    if not isinstance(content, Mapping):
        return []

    steps = content.get("steps")
    if not isinstance(steps, Mapping):
        return []

    for step in steps.values():
        if not isinstance(step, Mapping):
            continue
        step_inputs = step.get("inputs")
        if step_inputs is not None:
            _extract_flow_input_refs(step_inputs, refs)

    inputs: List[AgentInputConfig] = []
    for ref_name in sorted(refs):
        input_type = _infer_input_type(ref_name)
        label = _infer_label(ref_name)
        required = not _is_optional_input(ref_name)

        inputs.append(
            AgentInputConfig(
                id=ref_name,
                label=label,
                type=input_type,
                required=required,
            )
        )

    return inputs
