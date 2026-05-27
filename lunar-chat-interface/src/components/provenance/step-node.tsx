// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { StepView } from "@/types/provenance";
import { Handle, Position } from "@xyflow/react";
import TrustBadge from "./trust-badge";

interface StepNodeData {
  step: StepView;
  [key: string]: unknown;
}

interface StepNodeProps {
  data: StepNodeData;
}

const StepNode: React.FC<StepNodeProps> = ({ data }) => {
  const { step } = data;
  const KIND_MAP: Record<string, string> = {
    GEN: "generative",
    RET: "retrieval",
    DET: "deterministic",
    VER: "verification",
    HUM: "human-reviewed",
  };
  const handleClick = () => {
    if ((data as any).onNodeClick) (data as any).onNodeClick();
  };

  const getBorderColor = () => {
    if (!step.trust?.band) return "border-gray-300";
    switch (step.trust.band) {
      case "green":
        return "border-green-400";
      case "red":
        return "border-red-400";
      case "amber":
        return "border-amber-400";
      default:
        return "border-gray-300";
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`cursor-pointer bg-white rounded-lg border-2 ${getBorderColor()} shadow-md p-4 w-62.5`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2 w-full">
          <div className="flex flex-1 items-center gap-2 min-w-0">
            <div className="w-2 h-2 rounded-full bg-primary-main" />
            <h4 className="font-semibold text-sm truncate">{step.id}</h4>
          </div>
          <div className="shrink-0">
            <TrustBadge
              trustIndex={step.trust?.trust_index}
              band={step.trust?.band}
            />
          </div>
        </div>

        <div className="text-xs text-muted-foreground">
          <div className="font-medium">{step.component}</div>
          {step.trust?.step_kind && (
            <div className="text-xs text-muted-foreground opacity-75">
              Kind:{" "}
              {KIND_MAP[step.trust.step_kind as string] || step.trust.step_kind}
            </div>
          )}
        </div>

        {step.run && step.run.duration_s !== null && (
          <div className="text-xs text-muted-foreground pt-2 border-t">
            <div>Duration: {step.run.duration_s?.toFixed(2)}s</div>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
};

export default StepNode;
