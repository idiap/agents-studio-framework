// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { DataSource } from "@/types/provenance";
import { Handle, Position } from "@xyflow/react";
import { Database } from "lucide-react";

interface DataSourceNodeData {
  dataSource: DataSource;
  [key: string]: unknown;
}

interface DataSourceNodeProps {
  data: DataSourceNodeData;
}

const DataSourceNode: React.FC<DataSourceNodeProps> = ({
  data,
}: {
  data: DataSourceNodeData;
}) => {
  const { dataSource } = data;
  const handleClick = () => {
    if ((data as any).onNodeClick) (data as any).onNodeClick();
  };

  return (
    <div
      onClick={handleClick}
      className="cursor-pointer bg-blue-50 rounded-lg border-2 border-blue-300 shadow-sm p-4 w-62.5"
    >
      <Handle type="source" position={Position.Right} className="w-3 h-3" />
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-600" />
          <h4 className="font-semibold text-sm text-blue-900">
            {dataSource.id}
          </h4>
        </div>

        <div className="text-xs text-blue-700 pt-2 border-t border-blue-200">
          <div className="font-medium">Value:</div>
          <div className="truncate">{dataSource.summary}</div>
        </div>
      </div>
    </div>
  );
};

export default DataSourceNode;
