# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for flow input inference."""

from unittest.mock import Mock

from lunar_api.flows.input_inference import (
    infer_inputs_from_content,
    infer_inputs_from_flow,
)


class TestInferInputsFromFlow:
    """Test inferring inputs from flow node references."""

    def test_infers_inputs_from_nested_node_inputs(self):
        """Test inferring inputs from nested dict and list values."""
        flow = Mock()
        flow.get_nodes.return_value = [
            Mock(
                inputs={
                    "prompt": "Analyze &argument",
                    "config": {
                        "knowledge_base": "&knowledge_base_id",
                        "fields": ["&kb_field_id", "&optional_instructions"],
                    },
                }
            )
        ]

        result = infer_inputs_from_flow(flow)

        assert [item.id for item in result] == [
            "argument",
            "kb_field_id",
            "knowledge_base_id",
            "optional_instructions",
        ]
        assert [item.label for item in result] == [
            "Argument",
            "Knowledge Base Field ID",
            "Knowledge Base ID",
            "Optional Instructions",
        ]
        assert [item.type for item in result] == [
            "string",
            "knowledge-base-field",
            "knowledge-base",
            "string",
        ]
        assert [item.required for item in result] == [True, True, True, False]


class TestInferInputsFromContent:
    """Test inferring inputs from serialized flow content."""

    def test_infers_inputs_from_serialized_steps(self):
        """Test serialized flow content is parsed consistently."""
        result = infer_inputs_from_content(
            {
                "steps": {
                    "step_1": {
                        "inputs": {
                            "question": "&argument",
                            "filters": ["&optional_filter", {"field": "&field_id"}],
                        }
                    }
                }
            }
        )

        assert [item.id for item in result] == [
            "argument",
            "field_id",
            "optional_filter",
        ]
        assert [item.type for item in result] == [
            "string",
            "knowledge-base-field",
            "string",
        ]
        assert [item.required for item in result] == [True, True, False]

    def test_returns_empty_list_for_invalid_content(self):
        """Test invalid content gracefully returns no inferred inputs."""
        assert infer_inputs_from_content(None) == []
        assert infer_inputs_from_content({}) == []
        assert infer_inputs_from_content({"steps": []}) == []