// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Node as RFNode, Edge as RFEdge } from '@xyflow/react';

export interface FlowModel {
  id: string;
  name: string;
  description?: string;
  nodes: Array<NodeModel>;
}

export interface NodeModel {
  id: string;
  component_token: string;
  inputs: Record<string, any>;
}

const convertElementsToFlow = (
  elements: { nodes: RFNode[]; edges: RFEdge[] },
  meta: { id: string; name: string; description?: string }
): FlowModel => {
  const reconstructedNodes: NodeModel[] = elements.nodes.map(n => {
    const original = n.data.node as NodeModel;
    return {
      id: original.id,
      component_token: original.component_token,
      inputs: { ...original.inputs },
    };
  });

  return {
    id: meta.id,
    name: meta.name,
    description: meta.description,
    nodes: reconstructedNodes,
  };
};

export default convertElementsToFlow;
