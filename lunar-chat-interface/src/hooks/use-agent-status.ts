// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { Provenance } from "@/types/provenance";
import { useEffect, useState, useCallback, useRef } from "react";

export type AgentStatus =
  | "idle"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface EventLogEntry {
  type: string;
  timestamp: string;
  payload: any;
  metadata: Record<string, any>;
}

export interface ComponentResult {
  value: any;
  event_log: EventLogEntry[] | null;
  error: string | null;
}

export interface FlowResult {
  [componentName: string]: ComponentResult;
}

export interface ExecutionResult {
  status: AgentStatus;
  started_at?: string;
  completed_at?: string;
  progress?: string;
  error: string | null;
  result?: FlowResult;
  event_log?: EventLogEntry[];
  metadata?: {
    input_field_id?: string;
    output_field_id?: string;
  };
}

export interface TaskResult {
  execution_result: ExecutionResult;
  provenance: Provenance;
}

export interface TaskInfo {
  status: AgentStatus;
  started_at?: string;
  completed_at?: string;
  progress?: string;
  error?: string;
  metadata?: Record<string, any>;
  result?: TaskResult;
}

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function useAgentStatus(agentId: string) {
  const [status, setStatus] = useState<TaskInfo>({ status: "idle" });
  const [isLoading, setIsLoading] = useState(true);
  const [isCancelling, setIsCancelling] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!agentId) return;

    try {
      const response = await fetch(`${basePath}/api/agents/${agentId}/status`, {
        cache: "no-store",
      });

      if (response.ok) {
        const data = await response.json();
        console.log(">>>", data);
        setStatus(data);
      } else {
        setStatus({ status: "idle" });
      }
    } catch (error) {
      console.error(`Error fetching status for ${agentId}:`, error);
      setStatus({ status: "idle" });
    } finally {
      setIsLoading(false);
    }
  }, [agentId]);

  const cancelAgent = useCallback(async (): Promise<boolean> => {
    if (!agentId) return false;

    setIsCancelling(true);
    try {
      const response = await fetch(`${basePath}/api/agents/${agentId}/cancel`, {
        method: "POST",
      });

      if (response.ok) {
        await fetchStatus();
        return true;
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error(`Failed to cancel agent ${agentId}:`, errorData);
        return false;
      }
    } catch (error) {
      console.error(`Error cancelling agent ${agentId}:`, error);
      return false;
    } finally {
      setIsCancelling(false);
    }
  }, [agentId, fetchStatus]);

  // Poll every 2 seconds
  useEffect(() => {
    if (!agentId) {
      setIsLoading(false);
      return;
    }

    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, 2000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [agentId, fetchStatus]);

  return {
    status,
    isLoading,
    isCancelling,
    cancelAgent,
    refresh: fetchStatus,
  };
}
