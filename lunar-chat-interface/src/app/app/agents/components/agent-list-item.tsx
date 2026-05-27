// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Bot, Trash2 } from "lucide-react";
import { useAgentStatus } from "@/hooks/use-agent-status";
import type { Flow } from "@/app/app/agents/page";
import { deleteFlow } from "@/actions/delete-flow";
import { toast } from "sonner";
import { useState, useTransition } from "react";
import { AgentStatusIndicator } from "./agent-status-indicator";

interface AgentListItemProps {
  flow: Flow;
  onClick?: () => void;
}

export default function AgentListItem({ flow, onClick }: AgentListItemProps) {
  const router = useRouter();
  const { status } = useAgentStatus(flow.id);
  const [open, setOpen] = useState(false);
  const [isPending, startTransition] = useTransition();

  const handleClick = () => {
    if (onClick) return onClick();
    router.push(`/app/agents/${flow.id}`);
  };

  const handleDelete = () => {
    startTransition(async () => {
      try {
        const result = await deleteFlow(flow.id);
        if (result.success) {
          toast.success("Agent deleted successfully");
          setOpen(false);
          router.refresh();
        } else {
          toast.error(result.message || "Failed to delete agent");
        }
      } catch (error) {
        console.error("Error deleting agent:", error);
        toast.error("An error occurred while deleting the agent");
      }
    });
  };

  return (
    <div
      className="flex items-center justify-between p-4 hover:bg-accent cursor-pointer"
      onClick={handleClick}
      role="button"
    >
      <div className="flex items-start gap-4 w-full">
        <div className="flex flex-col gap-1 items-start w-full">
          <div className="flex items-center w-full">
            <div className="p-1 bg-linear-to-r from-primary-main to-primary-light rounded-sm mr-3">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <h3 className="font-medium text-base mr-auto">{flow.name}</h3>
            <AgentStatusIndicator status={status.status} />
            <AlertDialog open={open} onOpenChange={setOpen}>
              <AlertDialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8"
                  onClick={(event) => event.stopPropagation()}
                >
                  <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                  <span className="sr-only">Delete agent</span>
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete agent</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to delete this agent? This action
                    cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel disabled={isPending}>
                    Cancel
                  </AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleDelete}
                    disabled={isPending}
                  >
                    {isPending ? "Deleting..." : "Delete"}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {flow.description}
          </p>
        </div>
      </div>
    </div>
  );
}
