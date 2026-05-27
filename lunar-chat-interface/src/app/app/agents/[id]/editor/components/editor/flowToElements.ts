// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Node as RFNode, Edge as RFEdge, MarkerType } from "@xyflow/react";
import dagre from "dagre";
import { ComponentModel } from "../../models/component";
import { FlowModel } from "../../models/flow";
import { NodeModel } from "../../models/node";

const NODE_WIDTH = 250;
const NODE_HEIGHT_BASE = 100;
const NODE_HEIGHT_PER_INPUT = 80;

const convertFlowToElements = (
  flow: FlowModel,
  components: ComponentModel[],
) => {
  const nodes: RFNode[] = [];
  const edges: RFEdge[] = [];

  const allNodes: NodeModel[] = [];

  function flatten(flowOrNodes: FlowModel | NodeModel[]) {
    console.log(">>>Flow:", flowOrNodes);
    if (Array.isArray(flowOrNodes)) {
      flowOrNodes.forEach((n) => allNodes.push(n));
    } else {
      flowOrNodes.nodes.forEach((item) => {
        if ("nodes" in item) flatten(item as FlowModel);
        else allNodes.push(item as NodeModel);
      });
    }
  }

  flatten(flow);

  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "LR", nodesep: 40, ranksep: 80 });
  g.setDefaultEdgeLabel(() => ({}));

  // Compute variable heights for each node
  const nodeHeights: Record<string, number> = {};
  allNodes.forEach((node) => {
    const numInputs = Object.keys(node.inputs).length;
    nodeHeights[node.id] = NODE_HEIGHT_BASE + NODE_HEIGHT_PER_INPUT * numInputs;
  });

  // Add nodes to dagre with variable height
  allNodes.forEach((node) => {
    g.setNode(node.id, { width: NODE_WIDTH, height: nodeHeights[node.id] });
  });

  allNodes.forEach((node) => {
    Object.values(node.inputs).forEach((val) => {
      const refs: string[] = [];
      const regex = /\$([A-Za-z0-9_]+)(?:\.([A-Za-z0-9_.]+))?/;
      if (typeof val === "string") {
        const match = val.match(regex);
        if (match) {
          refs.push(match[1]);
        }
      } else if (Array.isArray(val)) {
        val.forEach((item) => {
          if (typeof item === "string") {
            const match = item.match(regex);
            if (match) {
              refs.push(match[1]);
            }
          }
        });
      }
      refs.forEach((srcId) => {
        g.setEdge(srcId, node.id);
        edges.push({
          id: `e${srcId}-${node.id}`,
          source: srcId,
          target: node.id,
          targetHandle: Object.keys(node.inputs).find(
            (key) => node.inputs[key] === val,
          ),
          markerEnd: {
            type: MarkerType.Arrow,
            width: 16,
            height: 16,
          },
          animated: true,
        });
      });
    });
  });

  dagre.layout(g);

  allNodes.forEach((node) => {
    const component = components.find(
      (component) => component.token === node.component_token,
    );
    const dagreNode = g.node(node.id);
    nodes.push({
      id: node.id,
      type: "default",
      position: {
        x: dagreNode.x - NODE_WIDTH / 2,
        y: dagreNode.y - nodeHeights[node.id] / 2,
      },
      data: { node, component },
    });
  });

  return { nodes, edges };
};

export default convertFlowToElements;
