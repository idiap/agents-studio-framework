// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import {
  Provenance,
  StepView,
  DataSource,
  InputBinding,
} from "@/types/provenance";
import {
  ReactFlow,
  Node,
  Edge,
  MarkerType,
  Background,
  Controls,
} from "@xyflow/react";
import { useMemo, useState } from "react";
import "@xyflow/react/dist/style.css";
import ProvenanceDetailsModal from "./provenance-details-modal";
import InputNode from "./input-node";
import DataSourceNode from "./data-source-node";
import OutputNode from "./ouput-node";
import StepNode from "./step-node";

export type SelectedItem =
  | { kind: "step"; payload: StepView }
  | { kind: "data_source"; payload: DataSource }
  | { kind: "input"; payload: { input: InputBinding; stepId: string } }
  | { kind: "output"; payload: { output: any; stepId: string } }
  | null;

interface ProvenanceGraphProps {
  provenance: Provenance;
}

function convertProvenanceToElements(
  provenance: Provenance,
  onNodeClick?: (payload: { kind: string; payload: any }) => void
): {
  nodes: Node[];
  edges: Edge[];
} {
  const { view_model } = provenance;
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const COLUMN_WIDTH = 350;
  const BASE_STEP_HEIGHT = 100; // Base height for a step with no inputs
  const INPUT_VERTICAL_SPACING = 120; // Spacing between input nodes
  const STEP_PADDING = 50; // Padding between steps
  const DATA_SOURCE_COLUMN = 0;
  const INPUT_COLUMN = 1;
  const STEP_COLUMN = 2;
  const OUTPUT_COLUMN = 3;

  // 1. Add data source nodes (leftmost column)
  const dataSourceSpacing = 150;
  view_model.data_sources.forEach((dataSource, index) => {
    nodes.push({
      id: dataSource.id,
      type: "dataSourceNode",
      position: {
        x: DATA_SOURCE_COLUMN * COLUMN_WIDTH,
        y: index * dataSourceSpacing,
      },
      data: {
        dataSource,
        onNodeClick: onNodeClick
          ? () => onNodeClick({ kind: "data_source", payload: dataSource })
          : undefined,
      },
    });
  });

  // 2. Add step nodes, inputs, and outputs
  let currentY = 0;
  view_model.steps.forEach((step) => {
    const stepY = currentY;
    const inputCount = step.inputs.length || 1;
    const stepHeight = Math.max(
      BASE_STEP_HEIGHT,
      inputCount * INPUT_VERTICAL_SPACING
    );
    currentY += stepHeight + STEP_PADDING;
    step.inputs.forEach((input, inputIndex) => {
      const inputNodeId = `${step.id}-input-${inputIndex}`;
      nodes.push({
        id: inputNodeId,
        type: "inputNode",
        position: {
          x: INPUT_COLUMN * COLUMN_WIDTH,
          y: stepY + inputIndex * INPUT_VERTICAL_SPACING,
        },
        data: {
          input,
          stepId: step.id,
          onNodeClick: onNodeClick
            ? () =>
                onNodeClick({
                  kind: "input",
                  payload: { input, stepId: step.id },
                })
            : undefined,
        },
      });

      edges.push({
        id: `edge-${inputNodeId}-to-${step.id}`,
        source: inputNodeId,
        target: step.id,
        type: "smoothstep",
        animated: false,
        markerEnd: { type: MarkerType.Arrow, width: 16, height: 16 },
      });

      if (input.kind === "flow_input" && input.ref) {
        const dataSourceId = view_model.data_sources.find(
          (ds) => ds.id === input.ref
        )?.id;
        if (dataSourceId) {
          edges.push({
            id: `edge-${dataSourceId}-to-${inputNodeId}`,
            source: dataSourceId,
            target: inputNodeId,
            type: "smoothstep",
            animated: true,
            markerEnd: { type: MarkerType.Arrow, width: 16, height: 16 },
          });
        }
      }

      if (input.kind === "step_output" && input.ref) {
        const sourceOutputId = `${input.ref}-output`;
        edges.push({
          id: `edge-${sourceOutputId}-to-${inputNodeId}`,
          source: sourceOutputId,
          target: inputNodeId,
          type: "smoothstep",
          animated: true,
          label: input.field,
          markerEnd: { type: MarkerType.Arrow, width: 16, height: 16 },
        });
      }
    });

    // Add step node
    nodes.push({
      id: step.id,
      type: "stepNode",
      position: { x: STEP_COLUMN * COLUMN_WIDTH, y: stepY },
      data: {
        step,
        onNodeClick: onNodeClick
          ? () => onNodeClick({ kind: "step", payload: step })
          : undefined,
      },
    });

    // Add output node for the step
    const outputNodeId = `${step.id}-output`;
    nodes.push({
      id: outputNodeId,
      type: "outputNode",
      position: { x: OUTPUT_COLUMN * COLUMN_WIDTH, y: stepY },
      data: {
        output: step.output,
        stepId: step.id,
        onNodeClick: onNodeClick
          ? () =>
              onNodeClick({
                kind: "output",
                payload: { output: step.output, stepId: step.id },
              })
          : undefined,
      },
    });

    // Connect step to output
    edges.push({
      id: `edge-${step.id}-to-${outputNodeId}`,
      source: step.id,
      target: outputNodeId,
      type: "smoothstep",
      animated: false,
      markerEnd: { type: MarkerType.Arrow, width: 16, height: 16 },
    });
  });

  return { nodes, edges };
}

const nodeTypes = {
  stepNode: StepNode,
  dataSourceNode: DataSourceNode,
  inputNode: InputNode,
  outputNode: OutputNode,
};

export function ProvenanceGraph({ provenance }: ProvenanceGraphProps) {
  const [selected, setSelected] = useState<SelectedItem>(null);

  const { nodes, edges } = useMemo(
    () =>
      convertProvenanceToElements(provenance, (payload) => {
        setSelected(payload as any);
      }),
    [provenance]
  );

  return (
    <div className="w-full h-150 border rounded-lg bg-gray-50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        maxZoom={1.5}
      >
        <Background />
        <Controls />
      </ReactFlow>
      <ProvenanceDetailsModal selected={selected} setSelected={setSelected} />
    </div>
  );
}
