// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Bot, Play, Loader2 } from "lucide-react";
import type { Flow } from "@/app/app/agents/page";
import { useAgentStatus } from "@/hooks/use-agent-status";
import { AgentStatusIndicator } from "./agent-status-indicator";

interface AgentCardProps {
  flow: Flow;
  onRun?: (flow: Flow) => void;
}

export function AgentCard({ flow, onRun }: AgentCardProps) {
  const { status, isLoading } = useAgentStatus(flow.id);

  const handleRun = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onRun && status.status !== "running") {
      onRun(flow);
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer group flex flex-col h-full">
      <CardHeader className="flex-1">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary" />
              <CardTitle className="text-lg group-hover:text-primary transition-colors">
                {flow.name}
              </CardTitle>
            </div>
            <CardDescription className="line-clamp-2">
              {flow.description}
            </CardDescription>

            {/* Status */}
            <div className="pt-2">
              <AgentStatusIndicator status={status.status} />
            </div>

            {/* Progress or Error Message */}
            {status.status === "running" && status.progress && (
              <p className="text-xs text-muted-foreground pt-1">
                {status.progress}
              </p>
            )}
            {status.status === "failed" && status.error && (
              <p
                className="text-xs text-red-500 pt-1 line-clamp-2"
                title={status.error}
              >
                Error: {status.error}
              </p>
            )}
            {status.status === "completed" && status.completed_at && (
              <p className="text-xs text-muted-foreground pt-1">
                Completed {new Date(status.completed_at).toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>
      </CardHeader>
      {onRun && (
        <CardFooter className="mt-auto">
          <div className="flex items-center justify-between pt-2 border-t w-full">
            <Button
              variant="default"
              size="sm"
              onClick={handleRun}
              disabled={status.status === "running" || isLoading}
              className="text-xs"
            >
              {status.status === "running" ? (
                <>
                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 mr-1" />
                  Run Agent
                </>
              )}
            </Button>
          </div>
        </CardFooter>
      )}
    </Card>
  );
}
