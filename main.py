# SPDX-FileCopyrightText: Copyright © 2025 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Imen Ben Mahmoud <imen.benmahmoud@idiap.ch>
#
# SPDX-License-Identifier: GPL-3.0-only

from agents import Agent, Runner, set_default_openai_client, set_default_openai_api


import yaml
import logging
import os
from datetime import datetime
import json
from openai import AsyncOpenAI  # <-- must be async
from dotenv import load_dotenv
from pathlib import Path


from openai import OpenAI
from config import (
    enrichment_paths, inference_paths, writing_paths, arguments,
    reasoner_yaml,synthesis_paths, visualization_paths)

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Constants
PATH_REGISTRY = {
    "enrichment_paths": enrichment_paths,
    "inference_paths": inference_paths,
    "writing_paths": writing_paths,
    "synthesis_paths": synthesis_paths,
    "visualization_paths": visualization_paths
}

# ---------- Utilities ----------

def load_yaml(path):
    """Load YAML file and return both dict and raw text."""
    with open(path, "r") as f:
        yaml_text=f.read()
        cfg = yaml.safe_load(yaml_text)
    return cfg,yaml_text
    
def find_key_in_registry(key,dicts=None):
    """Search for a key across multiple config dictionaries and return the dict name and value."""
    registry = dicts or PATH_REGISTRY
    for dict_name, dictionary in registry.items():
        if key in dictionary:
            return dict_name, dictionary[key]
    
    return None, None

def save_output(content, stage_name, dir_path,argument_key,ext = ".txt"):
    """Save text or json with timestamp for traceability."""
    save_dir = dir_path / argument_key 
    os.makedirs(save_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


    file_path = save_dir / f"{stage_name}_{timestamp}{ext}"
        
    if ext == ".txt":
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    elif ext == ".json":
        real_json = json.loads(content)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(real_json, f, indent=2)
    logger.info(f"[SAVED] Output to {file_path}")
    return file_path

   
def get_output_name_from_stage(stage):
    """Return canonical output name for a stage (handles dict/string/list outputs)."""
    outputs = stage.get("outputs")
    if isinstance(outputs, dict):
        return next(iter(outputs.keys()), None)
    if isinstance(outputs, str) and outputs:
        return outputs
    if isinstance(outputs, list) and outputs:
        return outputs[0]
    return None

def resolve_context_variables(inputs, context):
    """Resolve variables from context in input dictionary."""
    if isinstance(inputs, str):
        if inputs.startswith("{$") and inputs.endswith("}"):
            context_key = inputs.strip("{}$")
            return context.get(context_key, "")
        return inputs 

    # If it's a dictionary
    elif isinstance(inputs, dict):
        return {k: resolve_context_variables(v, context) for k, v in inputs.items()}

    # If it's a list
    elif isinstance(inputs, list):
        return [resolve_context_variables(v, context) for v in inputs]

    return inputs

# ---------- Core Agent Runner ----------

def run_agent_from_yaml(stage,yaml_file, inputs, step_label,config,ext=".txt"):
    cfg, yaml_text = load_yaml(yaml_file)
    resolved_inputs = resolve_context_variables(stage.get("inputs", {}), inputs)
    agent = Agent(
        name=cfg["name"],
        instructions=yaml_text,
        model=config["model"],
    )
    
    input_text=json.dumps(resolved_inputs, indent=2)
    logger.info(f"\n[RUNNING] {cfg['name']} ({step_label})")
    logger.info(f"Inputs: {input_text[:300]}...\n")  
    result = Runner.run_sync(agent, input_text)
    logger.info(f"[DONE] {cfg['name']} → Output length: {len(result.final_output)}")

    save_output(result.final_output, step_label,config["results_dir"],config["argument_key"], ext=ext)
    return result.final_output
    
def handle_prompt_stage(stage, context, config):
    """Handle prompt-based stage processing."""
    prompt_template = stage["prompt"]
    resolved_inputs = resolve_context_variables(stage.get("inputs", {}), context)
    input_text = json.dumps(resolved_inputs, indent=2)
    
    agent = Agent(
        name=stage["name"],
        instructions=prompt_template,
        model=config["model"],
    )
    result = Runner.run_sync(agent, input_text)
    
    output_name = list(stage.get("outputs", {}).keys())[0]
    save_output(result.final_output, output_name, config["results_dir"], config["argument_key"])
    return output_name, result.final_output

def handle_handoff_stage(stage, context, config):
    """Handle handoff stage processing."""
    handoff_key = stage["handoff_key"]
    # search in all path dicts
    _, handoff_path = find_key_in_registry(handoff_key)
    
    output = run_agent_from_yaml(stage,handoff_path, context, stage["name"], config)
    output_name= get_output_name_from_stage(stage)
    
    return output_name, output

def handle_multi_path_stage(stage,config_group, context,config):
    paths = PATH_REGISTRY.get(config_group,{})
    results={}
    for key, path in paths.items():
        label=f"{stage['name']}-{key}"
        output = run_agent_from_yaml(stage,path, context, label, config)
        results[key] = output
    output_name= get_output_name_from_stage(stage)
    
    return output_name,results

def handle_visualization_stage(stage, context,config):
    handoff_key = stage["handoff_key"]
    _, yaml_path = find_key_in_registry(handoff_key)

    # run the visualization agent
    raw_output = run_agent_from_yaml(stage, yaml_path, context, stage["name"], config,ext=".json")

    output_name = get_output_name_from_stage(stage)
    return output_name, raw_output
    
def run_reasoner(yaml_file, argument_text, config,domain):
    reasoner_cfg, _ = load_yaml(yaml_file)
    context = {
        "ARGUMENT_TEXT": argument_text,
        "DOMAIN": domain
    }

    for stage in reasoner_cfg["stages"]:
        stage_name = stage["name"]
        logger.info(f"\n=== Step: {stage_name} ===")
        
        if "config_group" in stage:
            output_name, output_value = handle_multi_path_stage(stage, stage["config_group"], context, config)
        #----PROMPT STAGE----
        elif "prompt" in stage:
            output_name, output_value = handle_prompt_stage(stage, context,config)
            
        # visualization 
        elif stage.get("type") == "visualization":           
            output_name, output_value = handle_visualization_stage(stage, context,config)
            
        #----INFERENCE STAGE----
        elif "handoff_key" in stage:
            output_name, output_value = handle_handoff_stage(stage, context,config)
        
        context[output_name] = output_value         
        
    return context

       


def main():
    """pipeline entry point."""
    #configuration
    argument_key=os.getenv("argument_key","argument_1")
    results_dir=Path("outputs/")
    model = os.getenv("OPENAI_MODEL","gpt-5")
    
    config = {
        "argument_key": argument_key,
        "results_dir": results_dir,
        "model": model
    }
    argument_text=arguments[argument_key]

    logger.info("\n=== RUNNING REASONER PIPELINE ===\n")
    enriched_output = run_reasoner(
        reasoner_yaml,
        argument_text=argument_text,
        config=config,
        domain="law",
    )

    logger.info("\n=== PIPELINE COMPLETE ===\n")
    logger.info(f"Final context keys: {list(enriched_output.keys())}")
    
if __name__ == "__main__":
    main()

