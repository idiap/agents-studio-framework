# SPDX-FileCopyrightText: Copyright © 2025 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Imen Ben Mahmoud <imen.benmahmoud@idiap.ch>
#
# SPDX-License-Identifier: GPL-3.0-only

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent

Prompts_path = ROOT / "prompts"

def load_arguments(path: Path = ROOT / "arguments.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
        
        
arguments = load_arguments()

reasoner_yaml =ROOT / "reasoner_agent.yaml"
prompts_paths = ROOT / "prompts"
enrichment_paths = {
    "assumption": prompts_paths / "enrichment" / "assumption_harvester.yaml",
    "constitutional": prompts_paths / "enrichment" / "constitutional_alignment_harvester.yaml",
    "definition": prompts_paths / "enrichment" / "definition_harvest.yaml",
    "ethical": prompts_paths / "enrichment" / "ethical_stance_harvester.yaml"
}
inference_paths = {
    "walton" : prompts_paths / "inference" / "walton_scheme_harvester.yaml"
}

writing_paths = { 
    "detailed_logical" : prompts_paths / "writing" / "ias_detailed_logical.yaml",
    "emotional_political" : prompts_paths / "writing" / "ias_emotional_political.yaml",
    "logical_rhetorical" : prompts_paths / "writing" / "ias_logical_rhetorical.yaml"
}

synthesis_paths = {
    "synthesis" : prompts_paths / "writing" / "integrated_argument_synthesizer.yaml",
    "auditor" : prompts_paths / "writing" / "ias_argument_quality_auditor.yaml"
}

visualization_paths = {
    "graph" : prompts_paths / "visualization" / "visualization.yaml"
}

