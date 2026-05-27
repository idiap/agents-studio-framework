// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { createFlow } from "@/actions/create-flow";

export default function CreateAgentButton() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleSubmit = () => {
    if (!file) {
      toast.error("Please select a YAML file");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    startTransition(async () => {
      try {
        const result = await createFlow(formData);
        if (result.success) {
          toast.success("Agent created successfully");
          setOpen(false);
          setFile(null);
          router.refresh();
        } else {
          toast.error(result.message || "Failed to create agent");
        }
      } catch (error) {
        console.error("Error creating agent:", error);
        toast.error("An error occurred while creating the agent");
      }
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default" className="gap-2">
          <Plus className="h-4 w-4" />
          New agent
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create agent</DialogTitle>
          <DialogDescription>
            Upload a Lunarflow YAML file to create a new agent.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Input
            type="file"
            accept=".yaml,.yml"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <p className="text-xs text-muted-foreground">
            Accepted formats: .yaml, .yml
          </p>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isPending || !file}>
            {isPending ? "Uploading..." : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
