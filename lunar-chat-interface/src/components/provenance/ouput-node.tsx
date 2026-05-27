// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Handle, Position } from "@xyflow/react";
import { FileOutput } from "lucide-react";

interface OutputNodeData {
  output: { value: any | null; summary: string };
  stepId: string;
  [key: string]: unknown;
}

interface OutputNodeProps {
  data: OutputNodeData;
}

const OutputNode: React.FC<OutputNodeProps> = ({ data }) => {
  const { output } = data;

  const getOutputDisplay = () => {
    if (output?.summary) {
      return output.summary;
    }
    if (output?.value !== null && output?.value !== undefined) {
      const valueStr =
        typeof output.value === "string"
          ? output.value
          : JSON.stringify(output.value);
      return valueStr.length > 100
        ? valueStr.substring(0, 100) + "..."
        : valueStr;
    }
    return "No output";
  };

  return (
    <div
      onClick={() => (data as any).onNodeClick && (data as any).onNodeClick()}
      className="cursor-pointer bg-purple-50 rounded-lg border-2 border-purple-300 shadow-sm p-3 w-50"
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <FileOutput className="w-3 h-3 text-purple-600" />
          <h4 className="font-semibold text-xs text-purple-900">Output</h4>
        </div>
        <div className="text-xs text-purple-700">
          <div className="truncate">{getOutputDisplay()}</div>
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
};

export default OutputNode;
