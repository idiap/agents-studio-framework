# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""Agent configuration models for the Icebrook platform."""

from dataclasses import dataclass, field
from typing import List, Literal


InputType = Literal["string", "knowledge-base", "knowledge-base-field"]


@dataclass
class AgentInputConfig:
    """Configuration for an agent input field."""

    id: str
    label: str
    type: InputType
    required: bool = True


@dataclass
class AgentConfig:
    """Configuration for an agent, including its flow and input metadata."""

    id: str
    name: str
    description: str
    inputs: List[AgentInputConfig] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert the agent config to a dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "inputs": [
                {
                    "id": inp.id,
                    "label": inp.label,
                    "type": inp.type,
                    "required": inp.required,
                }
                for inp in self.inputs
            ],
        }
