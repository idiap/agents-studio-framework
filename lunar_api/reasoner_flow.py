# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from pathlib import Path

from lunarflow.flows import Flow
from lunarflow.dsl.flow_compiler import FlowCompiler


def create_reasoner_flow_argumentation(
    enrichment_dir: Path = Path("./prompts/enrichment/"),
    inference_dir: Path = Path("./prompts/inference/"),
    writing_dir: Path = Path("./prompts/writing/"),
) -> Flow:
    compiler = FlowCompiler()
    agent_results = []
    enrichment_yamls = list(enrichment_dir.glob("*lunar.yaml"))
    inference_yamls = list(inference_dir.glob("*lunar.yaml"))
    writing_yamls = list(writing_dir.glob("*lunar.yaml"))
    report_yaml = list(Path("./report/").glob("*lunar.yaml"))
    all_yamls = enrichment_yamls + inference_yamls + writing_yamls + report_yaml

    for yaml_file in all_yamls:
        yaml_str = yaml_file.read_text()
        agent_results.append(compiler.load(yaml_str))

    flow = Flow(
        id="lunarflow_reasoner",
        name="Agent d'argumentation",
        description="Un flux d'agents de raisonnement pour enrichir une argumentation avec des informations pertinentes : agents d'enrichissement, d'inférence et de rédaction.",
        nodes=[result.node for result in agent_results],
    )
    return flow

def create_reasoner_flow_enriched_thesis(
    example_dir: Path = Path("./prompts/enrich_thesis/"),
    report_dir: Path = Path("./report/")
) -> Flow:
    compiler = FlowCompiler()
    agent_results = []
    all_yamls = list(example_dir.glob("*.yaml"))  + [report_dir / "report_enriched_thesis_lunar.yaml"]

    for yaml_file in all_yamls:
        yaml_str = yaml_file.read_text()
        agent_results.append(compiler.load(yaml_str))

    flow = Flow(
        id="lunarflow_reasoner_example",
        name="Agent enrichissement de thèse",
        description="Un agent pour enrichir une thèse avec des arguments structurés.",
        nodes=[result.node for result in agent_results],
    )
    return flow

def create_reasoner_class_support(
    class_support_dir: Path = Path("./prompts/class_support/"),
    report_dir: Path = Path("./report/")
) -> Flow:
    compiler = FlowCompiler()
    agent_results = []
    all_yamls = list(class_support_dir.glob("topic_to_lesson.yaml")) + [report_dir / "report_class_support_lunar.yaml"]
    for yaml_file in all_yamls:
        yaml_str = yaml_file.read_text()
        agent_results.append(compiler.load(yaml_str))

    flow = Flow(
        id="lunarflow_reasoner_class_support",
        name="Agent création de supports de cours",
        description="Un agent pour créer des supports de cours à partir d'un objectif global PER.",
        nodes=[result.node for result in agent_results],
    )
    return flow

reasoner_flow_argumentation = create_reasoner_flow_argumentation()
reasoner_flow_enrich_thesis= create_reasoner_flow_enriched_thesis()
reasoner_flow_class_support = create_reasoner_class_support()
