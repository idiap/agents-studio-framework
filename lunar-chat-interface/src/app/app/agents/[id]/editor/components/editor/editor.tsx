// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Connection,
  Edge,
  Node as RFNode,
  MarkerType,
  ReactFlow,
  useReactFlow,
} from "@xyflow/react";
import { useCallback, useRef, useState } from "react";
import convertFlowToElements from "./flowToElements";
import { GenericCard, GenericCardProps } from "./genericCard/genericCard";
import { FlowModel } from "../../models/flow";
import { NodeModel } from "../../models/node";
import { ComponentModel } from "../../models/component";
import { useComponents } from "@/context/componentsContext";
import "@xyflow/react/dist/base.css";

const nodeTypes: Record<string, React.FC<GenericCardProps>> = {
  default: GenericCard,
};

interface EditorProps {
  initialFlow?: FlowModel;
}

const Editor: React.FC<EditorProps> = ({ initialFlow }) => {
  const { components } = useComponents();
  const reactFlowWrapper = useRef<HTMLDivElement | null>(null);
  const reactFlow = useReactFlow();
  const elementsFlow = initialFlow
    ? convertFlowToElements(initialFlow, components)
    : null;
  const [nodes, setNodes] = useState(elementsFlow?.nodes ?? []);
  const [edges, setEdges] = useState(elementsFlow?.edges ?? []);

  const onNodesChange = useCallback(
    (changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [setNodes]
  );
  const onEdgesChange = useCallback(
    (changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onConnect = useCallback((params: Edge | Connection) => {
    setEdges((eds) =>
      addEdge(
        {
          ...params,
          markerEnd: {
            type: MarkerType.Arrow,
            width: 16,
            height: 16,
          },
          animated: true,
        },
        eds
      )
    );
    setNodes((nds) =>
      nds.map((n: RFNode) => {
        if (n.id !== params.target) return n;
        const inputKey = params.targetHandle ?? "input";
        const originalNode: NodeModel = n.data["node"] as NodeModel;
        const updatedInputs = {
          ...originalNode.inputs,
          [inputKey]: `$${params.source}`,
        };

        return {
          ...n,
          data: {
            ...n.data,
            node: {
              ...originalNode,
              inputs: updatedInputs,
            },
          },
        };
      })
    );
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      if (reactFlowWrapper.current != null && reactFlow != null) {
        event.preventDefault();
        reactFlow.getViewport();
        const reactFlowBounds =
          reactFlowWrapper.current.getBoundingClientRect();
        const component = event.dataTransfer.getData("application/component");

        const position = reactFlow.screenToFlowPosition({
          x: event.clientX - 57.5,
          y: event.clientY - reactFlowBounds.top,
        });
        setNodes((nds) => {
          if (component != null && component.length > 0) {
            const parsedComponent: ComponentModel = JSON.parse(component);
            const lunarNode: NodeModel = {
              id: parsedComponent.token,
              component_token: parsedComponent.token,
              inputs: parsedComponent.inputs,
            };
            const newNodeElement = {
              id: parsedComponent.token,
              type: "default",
              position,
              data: {
                node: lunarNode,
                component: parsedComponent,
              },
            };
            return nds.concat(newNodeElement);
          }
          return nds;
        });
      }
    },
    [reactFlow]
  );

  return (
    <div className="w-full h-full" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onDrop={onDrop}
        onConnect={onConnect}
        onDragOver={onDragOver}
        fitView
        nodeTypes={nodeTypes}
      ></ReactFlow>
    </div>
  );
};

export default Editor;
