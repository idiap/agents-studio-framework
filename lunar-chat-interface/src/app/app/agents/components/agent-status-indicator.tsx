// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import {
  Loader2,
  CheckCircle2,
  XCircle,
  Circle,
  StopCircle,
} from "lucide-react";
import type { AgentStatus } from "@/hooks/use-agent-status";

interface AgentStatusIndicatorProps {
  status: AgentStatus;
  className?: string;
}

const getStatusConfig = (status: AgentStatus) => {
  switch (status) {
    case "running":
      return {
        label: "Agent Running",
        icon: Loader2,
        iconClass: "animate-spin text-blue-500",
      };
    case "completed":
      return {
        label: "Completed",
        icon: CheckCircle2,
        iconClass: "text-green-500",
      };
    case "failed":
      return {
        label: "Failed",
        icon: XCircle,
        iconClass: "text-red-500",
      };
    case "cancelled":
      return {
        label: "Cancelled",
        icon: StopCircle,
        iconClass: "text-orange-500",
      };
    case "idle":
    default:
      return {
        label: "Idle",
        icon: Circle,
        iconClass: "text-gray-400",
      };
  }
};

export const AgentStatusIndicator = ({
  status,
  className = "",
}: AgentStatusIndicatorProps) => {
  const statusConfig = getStatusConfig(status);
  const StatusIcon = statusConfig.icon;

  return (
    <div
      className={`flex items-center gap-1.5 text-xs font-bold uppercase ${className}`}
    >
      <span>{statusConfig.label}</span>
      <StatusIcon
        strokeWidth={3}
        className={`w-4 h-4 ${statusConfig.iconClass}`}
      />
    </div>
  );
};
