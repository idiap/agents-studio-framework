# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from rdflib import Dataset, Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD
from lunarflow.flows import Flow
from .parsers import ExecutionLog, index_events, flow_start_event, flow_finish_event
from .prov_dataset import PROV, Namespaces, add_bundle_header, dt_literal
from .embedding import embed_json
from .utils import safe_id, find_step_refs, find_flow_input_refs

LUNAR = Namespace(
    "urn:lunar:prov:"
)  # will be overridden by base namespace in exporter if desired


def mint(ns: Namespace, *parts: str) -> URIRef:
    return URIRef(
        str(ns) + "/".join([p.strip("/") for p in parts if p is not None and p != ""])
    )


def build_prov_dataset(
    workflow: Flow,
    log: ExecutionLog,
    base_uri: str,
    embed_values: bool = True,
    max_embed_bytes: Optional[int] = None,
    emit_redacted: bool = False,
) -> Tuple[Dataset, Dict[str, Any]]:
    """Build an rdflib Dataset with:
    - prospective bundle (prov:Bundle)
    - retrospective bundle (prov:Bundle)
    - optional redacted bundle (prov:Bundle)

    Returns (dataset, manifest_like_dict_without_hashes).
    """
    ns = Namespaces(base=Namespace(base_uri.rstrip("/") + "/"))
    ds = Dataset()
    prov = PROV

    flow_id = workflow.get_id()
    run_id = safe_id(f"{flow_id}-{log.started_at}")

    # Bundle IRIs
    b_pro = URIRef(str(ns.base) + "bundle/prospective")
    b_ret = URIRef(str(ns.base) + f"bundle/retrospective/{run_id}")
    b_red = (
        URIRef(str(ns.base) + f"bundle/redacted/{run_id}") if emit_redacted else None
    )

    g_pro = ds.graph(b_pro)
    g_ret = ds.graph(b_ret)
    g_red = ds.graph(b_red) if b_red else None

    # Headers
    add_bundle_header(g_pro, b_pro)
    add_bundle_header(g_ret, b_ret)
    if g_red is not None and b_red is not None:
        add_bundle_header(g_red, b_red)

    # Custom terms
    EX = ns.base
    dependsOn = URIRef(str(EX) + "dependsOn")
    partOf = URIRef(str(EX) + "partOf")
    generativeProperty = URIRef(str(EX) + "generative")
    modelProperty = URIRef(str(EX) + "model")
    inputTokensProperty = URIRef(str(EX) + "inputTokens")
    outputTokensProperty = URIRef(str(EX) + "outputTokens")
    totalTokensProperty = URIRef(str(EX) + "totalTokens")

    # Local helpers for bounded embedding
    def _add_meta(g: Graph, subj: URIRef, meta: Any) -> None:
        if not meta:
            return
        g.add(
            (
                subj,
                URIRef(str(ns.base) + "sha256"),
                Literal(str(meta.sha256), datatype=XSD.string),
            )
        )
        g.add(
            (
                subj,
                URIRef(str(ns.base) + "byteLength"),
                Literal(int(meta.byte_length), datatype=XSD.integer),
            )
        )
        g.add(
            (
                subj,
                URIRef(str(ns.base) + "truncated"),
                Literal(True, datatype=XSD.boolean),
            )
        )

    # ===== Prospective (plan) =====
    plan_workflow = URIRef(str(EX) + f"plan/workflow/{safe_id(flow_id)}")
    g_pro.add((plan_workflow, RDF.type, prov.Plan))
    g_pro.add((plan_workflow, RDF.type, prov.Entity))
    g_pro.add((plan_workflow, RDFS.label, Literal(workflow.get_name() or flow_id)))
    if workflow.get_description():
        g_pro.add(
            (
                plan_workflow,
                URIRef(str(RDFS) + "comment"),
                Literal(workflow.get_description()),
            )
        )

    steps_collection = URIRef(str(EX) + f"plan/workflow/{safe_id(flow_id)}/steps")
    g_pro.add((steps_collection, RDF.type, prov.Collection))
    g_pro.add((steps_collection, RDF.type, prov.Entity))
    g_pro.add(
        (steps_collection, prov.hadMember, plan_workflow)
    )  # include workflow in collection too

    # Convert nodes to steps dict for processing
    import json

    flow_dict = json.loads(workflow.to_json())
    steps = {}
    for node in flow_dict.get("nodes", []):
        node_id = node.get("id", "")
        steps[node_id] = node

    step_plans: Dict[str, URIRef] = {}
    for step_id, spec in steps.items():
        sp = URIRef(str(EX) + f"plan/step/{safe_id(step_id)}")
        step_plans[step_id] = sp
        g_pro.add((sp, RDF.type, prov.Plan))
        g_pro.add((sp, RDF.type, prov.Entity))
        g_pro.add((sp, RDFS.label, Literal(step_id)))
        g_pro.add((steps_collection, prov.hadMember, sp))
        # Keep a compact structured value for plan (useful for reconstruction)
        if embed_values:
            lit, meta = embed_json(spec, max_bytes=max_embed_bytes)
            g_pro.add((sp, prov.value, lit))
            _add_meta(g_pro, sp, meta)
        # Dependency discovery from $refs in inputs
        inputs = (spec.get("inputs") or {}) if isinstance(spec, dict) else {}
        for _, v in inputs.items() if isinstance(inputs, dict) else []:
            for ref_step, _field in find_step_refs(v):
                if ref_step in steps:
                    g_pro.add(
                        (
                            sp,
                            dependsOn,
                            URIRef(str(EX) + f"plan/step/{safe_id(ref_step)}"),
                        )
                    )

    g_pro.add((plan_workflow, prov.hadMember, steps_collection))

    # ===== Retrospective (run) =====
    # Agents
    engine = URIRef(str(EX) + "agent/lunar_engine")
    g_ret.add((engine, RDF.type, prov.SoftwareAgent))
    g_ret.add((engine, RDFS.label, Literal("Lunar Engine")))

    openai_agent = URIRef(str(EX) + "agent/openai")
    g_ret.add((openai_agent, RDF.type, prov.SoftwareAgent))
    g_ret.add((openai_agent, RDFS.label, Literal("OpenAI")))

    # Flow activity
    ev_start = flow_start_event(log.event_log)
    ev_end = flow_finish_event(log.event_log)
    flow_act = URIRef(str(EX) + f"run/{run_id}/activity/flow")
    g_ret.add((flow_act, RDF.type, prov.Activity))
    g_ret.add((flow_act, RDFS.label, Literal(f"flow:{flow_id}")))
    if ev_start and ev_start.get("timestamp"):
        g_ret.add((flow_act, prov.startedAtTime, dt_literal(ev_start["timestamp"])))
    if ev_end and ev_end.get("timestamp"):
        g_ret.add((flow_act, prov.endedAtTime, dt_literal(ev_end["timestamp"])))
    g_ret.add((flow_act, prov.wasAssociatedWith, engine))

    # Flow inputs as entities
    flow_inputs = ((ev_start or {}).get("payload") or {}).get("inputs") or {}
    input_entities: Dict[str, URIRef] = {}
    if isinstance(flow_inputs, dict):
        for k, v in flow_inputs.items():
            ent = URIRef(str(EX) + f"run/{run_id}/entity/input/{safe_id(k)}")
            input_entities[k] = ent
            g_ret.add((ent, RDF.type, prov.Entity))
            g_ret.add((ent, RDFS.label, Literal(f"input:{k}")))
            if embed_values:
                lit, meta = embed_json(v, max_bytes=max_embed_bytes)
                g_ret.add((ent, prov.value, lit))
                _add_meta(g_ret, ent, meta)
            g_ret.add((flow_act, prov.used, ent))

    # Step activities and outputs
    step_events = index_events(log.event_log)
    step_acts: Dict[str, URIRef] = {}
    step_outs: Dict[str, URIRef] = {}

    # Pre-mint output entities for all steps (so 'used' can reference them)
    for step_id in steps.keys():
        out_ent = URIRef(str(EX) + f"run/{run_id}/entity/output/{safe_id(step_id)}")
        step_outs[step_id] = out_ent

    for step_id, spec in steps.items():
        act = URIRef(str(EX) + f"run/{run_id}/activity/step/{safe_id(step_id)}")
        step_acts[step_id] = act
        g_ret.add((act, RDF.type, prov.Activity))
        g_ret.add((act, RDFS.label, Literal(f"step:{step_id}")))
        g_ret.add((act, partOf, flow_act))
        g_ret.add((act, prov.wasAssociatedWith, engine))

        # Determine if this is a generative/LLM step
        is_llm_step = isinstance(spec, dict) and spec.get("kind") == "llm"

        # Set generative flag (true for LLM nodes, false otherwise)
        g_ret.add(
            (act, generativeProperty, Literal(bool(is_llm_step), datatype=XSD.boolean))
        )

        # If step is LLM/openai, associate also with openai agent
        if is_llm_step:
            provider = spec.get("provider")
            if provider == "openai":
                g_ret.add((act, prov.wasAssociatedWith, openai_agent))

        # Times from events
        se = step_events.get(step_id, {})
        if se.get("step:started") and se["step:started"].get("timestamp"):
            g_ret.add(
                (act, prov.startedAtTime, dt_literal(se["step:started"]["timestamp"]))
            )
        if se.get("step:finished") and se["step:finished"].get("timestamp"):
            g_ret.add(
                (act, prov.endedAtTime, dt_literal(se["step:finished"]["timestamp"]))
            )

        # Extract token usage and model from step result if this is an LLM step
        if is_llm_step:
            # Try to get from step:result event first, then from step:finished
            res_evt = se.get("step:result")
            if not res_evt:
                # If no separate result event, try to extract from step:finished
                finished_evt = se.get("step:finished")
                if finished_evt:
                    payload = finished_evt.get("payload") or {}
                    if isinstance(payload, dict):
                        result_data = payload.get("result") or {}
                        if isinstance(result_data, dict):
                            res_evt = {"payload": result_data}

            if res_evt:
                payload = res_evt.get("payload") or {}
                if isinstance(payload, dict):
                    value = payload.get("value")
                    if isinstance(value, dict):
                        # Extract model information
                        model = value.get("model")
                        if model:
                            g_ret.add(
                                (
                                    act,
                                    modelProperty,
                                    Literal(str(model), datatype=XSD.string),
                                )
                            )

                        # Extract token usage
                        usage = value.get("usage")
                        if isinstance(usage, dict):
                            input_tokens = usage.get("input")
                            output_tokens = usage.get("output")
                            total_tokens = usage.get("total")

                            if input_tokens is not None:
                                g_ret.add(
                                    (
                                        act,
                                        inputTokensProperty,
                                        Literal(
                                            int(input_tokens), datatype=XSD.integer
                                        ),
                                    )
                                )
                            if output_tokens is not None:
                                g_ret.add(
                                    (
                                        act,
                                        outputTokensProperty,
                                        Literal(
                                            int(output_tokens), datatype=XSD.integer
                                        ),
                                    )
                                )
                            if total_tokens is not None:
                                g_ret.add(
                                    (
                                        act,
                                        totalTokensProperty,
                                        Literal(
                                            int(total_tokens), datatype=XSD.integer
                                        ),
                                    )
                                )

        # Link to plan via mentionOf/asInBundle (PROV Links)
        plan_mention = URIRef(
            str(EX) + f"run/{run_id}/entity/plan_mention/{safe_id(step_id)}"
        )
        g_ret.add((plan_mention, RDF.type, prov.Plan))
        g_ret.add((plan_mention, RDF.type, prov.Entity))
        g_ret.add((plan_mention, RDFS.label, Literal(f"plan_mention:{step_id}")))
        g_ret.add(
            (
                plan_mention,
                prov.mentionOf,
                URIRef(str(EX) + f"plan/step/{safe_id(step_id)}"),
            )
        )
        g_ret.add((plan_mention, prov.asInBundle, b_pro))
        g_ret.add((act, prov.hadPlan, plan_mention))

        # Determine used entities from workflow inputs mapping
        inputs = (spec.get("inputs") or {}) if isinstance(spec, dict) else {}
        if isinstance(inputs, dict):
            for _, v in inputs.items():
                # step refs
                for ref_step, _field in find_step_refs(v):
                    if ref_step in step_outs:
                        g_ret.add((act, prov.used, step_outs[ref_step]))
                        # also add control-flow edge
                        if ref_step in step_acts:
                            g_ret.add((act, prov.wasInformedBy, step_acts[ref_step]))
                # flow input refs
                for var in find_flow_input_refs(v):
                    if var in input_entities:
                        g_ret.add((act, prov.used, input_entities[var]))

        # Activity generates its output entity
        out_ent = step_outs[step_id]
        g_ret.add((out_ent, RDF.type, prov.Entity))
        g_ret.add((out_ent, RDFS.label, Literal(f"output:{step_id}")))
        g_ret.add((out_ent, prov.wasGeneratedBy, act))

        # Attach value from step:result if present
        if embed_values:
            res_evt = se.get("step:result")
            if res_evt:
                payload = res_evt.get("payload") or {}
                value = payload.get("value") if isinstance(payload, dict) else None
                if value is not None:
                    lit, meta = embed_json(value, max_bytes=max_embed_bytes)
                    g_ret.add((out_ent, prov.value, lit))
                    _add_meta(g_ret, out_ent, meta)

        # Redacted bundle mirrors structure, links alternates
        if g_red is not None:
            g_red.add((act, RDF.type, prov.Activity))
            g_red.add((act, RDFS.label, Literal(f"step:{step_id}")))
            g_red.add((act, partOf, flow_act))
            g_red.add((act, prov.wasAssociatedWith, engine))
            if se.get("step:started") and se["step:started"].get("timestamp"):
                g_red.add(
                    (
                        act,
                        prov.startedAtTime,
                        dt_literal(se["step:started"]["timestamp"]),
                    )
                )
            if se.get("step:finished") and se["step:finished"].get("timestamp"):
                g_red.add(
                    (
                        act,
                        prov.endedAtTime,
                        dt_literal(se["step:finished"]["timestamp"]),
                    )
                )
            # output entity (no prov:value)
            red_out = URIRef(
                str(EX) + f"run/{run_id}/entity/output_redacted/{safe_id(step_id)}"
            )
            g_red.add((red_out, RDF.type, prov.Entity))
            g_red.add((red_out, RDFS.label, Literal(f"output_redacted:{step_id}")))
            g_red.add((red_out, prov.wasGeneratedBy, act))
            # relate full ↔ redacted
            g_ret.add((out_ent, prov.alternateOf, red_out))
            g_red.add((red_out, prov.alternateOf, out_ent))

    # Top-level manifest-ish info (hashes computed separately)
    manifest = {
        "base_uri": base_uri,
        "flow_id": flow_id,
        "run_id": run_id,
        "bundles": {
            "prospective": str(b_pro),
            "retrospective": str(b_ret),
            **({"redacted": str(b_red)} if b_red else {}),
        },
    }
    return ds, manifest
