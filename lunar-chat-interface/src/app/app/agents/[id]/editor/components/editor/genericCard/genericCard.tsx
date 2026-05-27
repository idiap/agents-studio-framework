// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import {
  Handle,
  NodeProps,
  Position,
  useReactFlow,
  Node as XYFlowNode,
} from "@xyflow/react";
import GenericCardInput from "./genericCardInput";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import TemplateInput from "../cardInputs/TemplateInput";
import { ComponentModel } from "../../../models/component";
import { NodeModel } from "@/app/app/agents/[id]/editor/models/node";

export type Node = XYFlowNode<
  {
    component: ComponentModel;
    node: NodeModel;
  },
  "default"
>;

export type GenericCardProps = NodeProps<Node>;

export const GenericCard: React.FC<GenericCardProps> = ({ id, data }) => {
  const { setNodes } = useReactFlow();

  const handleChange =
    (key: string) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const raw = e.target.value.replace(/\$/g, "");
      let parsed: any = raw;
      try {
        parsed = JSON.parse(raw);
      } catch {}
      setNodes((nodes) => {
        return nodes.map((node) => {
          if (node.id !== id) return node;
          const lunarNode = (node as Node).data.node;
          lunarNode.inputs[key as keyof typeof lunarNode] = parsed;
          return {
            ...node,
            data: {
              component: node.data.component,
              node: lunarNode,
            },
          };
        });
      });
    };
  return (
    <Card className="w-62.5 border-0">
      <CardHeader>
        <CardTitle className="truncate">
          {data.component?.name ?? data.node.id}
        </CardTitle>
        {data.component && data.component.description && (
          <CardDescription>{data.component.description}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <form>
          <div className="flex flex-col gap-6">
            {data.node &&
              Object.entries(data.node.inputs).map(([key, value]) =>
                data.node.id === "report" && key === "template" ? (
                  <TemplateInput id={id} key={key} inputKey={key} />
                ) : (
                  <GenericCardInput
                    key={key}
                    inputKey={key}
                    value={value}
                    onChange={(e) => handleChange(key)(e)}
                  />
                ),
              )}
          </div>
        </form>
        <Handle
          type="source"
          position={Position.Right}
          className=""
          style={{ top: "50%" }}
        />
      </CardContent>
    </Card>
  );
};
