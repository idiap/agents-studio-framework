# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for agent configuration models."""

from lunar_api.flows.models import AgentInputConfig, AgentConfig


class TestAgentInputConfig:
    """Test AgentInputConfig dataclass."""

    def test_create_with_required_fields(self):
        """Test creating an AgentInputConfig with required fields."""
        config = AgentInputConfig(
            id="test_input",
            label="Test Input",
            type="string",
        )
        assert config.id == "test_input"
        assert config.label == "Test Input"
        assert config.type == "string"
        assert config.required is True  # default value

    def test_create_with_optional_required_false(self):
        """Test creating an AgentInputConfig with required=False."""
        config = AgentInputConfig(
            id="optional_input",
            label="Optional Input",
            type="string",
            required=False,
        )
        assert config.required is False

    def test_create_with_knowledge_base_field_type(self):
        """Test creating an AgentInputConfig with knowledge-base-field type."""
        config = AgentInputConfig(
            id="kb_field",
            label="Knowledge Base Field",
            type="knowledge-base-field",
            required=True,
        )
        assert config.type == "knowledge-base-field"

    def test_create_with_knowledge_base_type(self):
        """Test creating an AgentInputConfig with knowledge-base type."""
        config = AgentInputConfig(
            id="kb",
            label="Knowledge Base",
            type="knowledge-base",
            required=True,
        )
        assert config.type == "knowledge-base"


class TestAgentConfig:
    """Test AgentConfig dataclass."""

    def test_create_with_no_inputs(self):
        """Test creating an AgentConfig with no inputs."""
        config = AgentConfig(
            id="test_agent",
            name="Test Agent",
            description="A test agent",
        )
        assert config.id == "test_agent"
        assert config.name == "Test Agent"
        assert config.description == "A test agent"
        assert config.inputs == []

    def test_create_with_inputs(self):
        """Test creating an AgentConfig with inputs."""
        inputs = [
            AgentInputConfig(
                id="input1",
                label="Input 1",
                type="string",
                required=True,
            ),
            AgentInputConfig(
                id="input2",
                label="Input 2",
                type="knowledge-base-field",
                required=False,
            ),
        ]
        config = AgentConfig(
            id="test_agent",
            name="Test Agent",
            description="A test agent",
            inputs=inputs,
        )
        assert len(config.inputs) == 2
        assert config.inputs[0].id == "input1"
        assert config.inputs[1].id == "input2"

    def test_to_dict(self):
        """Test converting AgentConfig to dictionary."""
        inputs = [
            AgentInputConfig(
                id="input1",
                label="Input 1",
                type="string",
                required=True,
            ),
            AgentInputConfig(
                id="input2",
                label="Input 2",
                type="knowledge-base-field",
                required=False,
            ),
        ]
        config = AgentConfig(
            id="test_agent",
            name="Test Agent",
            description="A test agent",
            inputs=inputs,
        )
        result = config.to_dict()

        assert result["id"] == "test_agent"
        assert result["name"] == "Test Agent"
        assert result["description"] == "A test agent"
        assert len(result["inputs"]) == 2
        assert result["inputs"][0] == {
            "id": "input1",
            "label": "Input 1",
            "type": "string",
            "required": True,
        }
        assert result["inputs"][1] == {
            "id": "input2",
            "label": "Input 2",
            "type": "knowledge-base-field",
            "required": False,
        }

    def test_to_dict_with_empty_inputs(self):
        """Test converting AgentConfig with no inputs to dictionary."""
        config = AgentConfig(
            id="empty_agent",
            name="Empty Agent",
            description="An agent with no inputs",
        )
        result = config.to_dict()

        assert result["id"] == "empty_agent"
        assert result["name"] == "Empty Agent"
        assert result["description"] == "An agent with no inputs"
        assert result["inputs"] == []
