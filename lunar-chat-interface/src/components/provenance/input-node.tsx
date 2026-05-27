// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { InputBinding } from "@/types/provenance";
import { Handle, Position } from "@xyflow/react";
import { FileInput } from "lucide-react";

export interface InputNodeData {
  input: InputBinding;
  stepId: string;
  [key: string]: unknown;
}

interface InputNodeProps {
  data: InputNodeData;
}

const InputNode: React.FC<InputNodeProps> = ({ data }) => {
  const { input } = data;
  const handleClick = () => {
    if ((data as any).onNodeClick) (data as any).onNodeClick();
  };

  return (
    <div
      onClick={handleClick}
      className="cursor-pointer bg-green-50 rounded-lg border-2 border-green-300 shadow-sm p-3 w-50"
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <FileInput className="w-3 h-3 text-green-600" />
          <h4 className="font-semibold text-xs text-green-900">{input.name}</h4>
        </div>
        <div className="text-xs text-green-700">
          <div className="italic">{input.kind}</div>
          {input.value_summary && (
            <div className="truncate mt-1">{input.value_summary}</div>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
};

export default InputNode;
