# SPDX-FileCopyrightText: Copyright © 2025 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Imen Ben Mahmoud <imen.benmahmoud@idiap.ch>
#
# SPDX-License-Identifier: GPL-3.0-only

import asyncio
from pathlib import Path
import os

from dotenv import load_dotenv
from config import arguments

from lunarflow.flows import Flow
from lunarflow.context import InMemoryContext
from lunarflow.runner import PythonRunner
from lunarflow.dsl.flow_compiler import FlowCompiler




def save_results(result, config):
    argument_key = config["argument_key"]
    results_dir = config["results_dir"]
    save_path = results_dir / argument_key
    os.makedirs(save_path, exist_ok=True)
    for key, value in result.value.items():
        content = value.value if value.value is not None else ""
        with open(f"{save_path}/{key}.txt","w") as f:
            f.write(content)
    
    
    

def create_flow():
    
    compiler = FlowCompiler()
    agent_results = []
# look for yaml files in the current directory
    enrichment_yamls = list(Path("./prompts/enrichment/").glob("*lunar.yaml")) 
    inference_yamls = list(Path("./prompts/inference/").glob("*lunar.yaml"))
    writing_yamls = list(Path("./prompts/writing/").glob("*lunar.yaml"))
    report_yaml = list(Path("./prompts/report/").glob("*lunar.yaml"))
    all_yamls = enrichment_yamls+ inference_yamls + writing_yamls + report_yaml

# load each yaml file and compile it into a flow node
    for index,file in enumerate(all_yamls):
        yaml_str = file.read_text()
        agent_results.append(compiler.load(yaml_str))

    flow = Flow(
        id="reasoner_flow",
        name="reasoner_flow",
        description="A flow to run multiple agents on an argument.",
        nodes=[ result.node for result in agent_results]
    )
    return flow

    
def main():
    """pipeline entry point."""
    load_dotenv()
    #configuration
    argument_key=os.getenv("argument_key","argument_1")
    argument_text=arguments[argument_key]
    results_dir=Path("outputs/")
    config = {
        "argument_key": argument_key,
        "results_dir": results_dir,
    }
    flow = create_flow()
    
    # Create a PythonRunner instance and run the flow
    context = InMemoryContext()
    runner = PythonRunner(context=context)
    inputs = {"argument": argument_text}
        
    result = asyncio.run(runner.run(flow, inputs=inputs))

    print("Flow Execution Completed.", result)
    
    save_results(result, config)
        
if __name__ == "__main__":
    main()
