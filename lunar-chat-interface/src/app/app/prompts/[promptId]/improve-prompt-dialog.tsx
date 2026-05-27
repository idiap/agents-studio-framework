// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useState, useCallback, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2, Sparkles } from "lucide-react";
import { AIModelSelect, type AIModel } from "@/components/ai-model-select";
import { parseSSEStream } from "@/lib/sse-parser";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

interface ImprovePromptDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  aiModels: AIModel[];
  promptContent: string;
  onImproved: (improvedContent: string) => void;
}

export function ImprovePromptDialog({
  open,
  onOpenChange,
  aiModels,
  promptContent,
  onImproved,
}: ImprovePromptDialogProps) {
  const [selectedModelId, setSelectedModelId] = useState<string>(
    aiModels.length > 0 ? aiModels[0].id : "",
  );
  const [isImproving, setIsImproving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleCancel = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsImproving(false);
    setError(null);
    onOpenChange(false);
  }, [onOpenChange]);

  const handleConfirm = useCallback(async () => {
    if (!selectedModelId) {
      setError("Please select an AI model.");
      return;
    }

    if (!promptContent.trim()) {
      setError("Prompt content is empty. Nothing to improve.");
      return;
    }

    setError(null);
    setIsImproving(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let improvedContent = "";

    try {
      const response = await fetch(`${basePath}/api/prompts/improve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: promptContent,
          ai_model_id: selectedModelId,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body");
      }

      let streamError: Error | null = null;

      await parseSSEStream(reader, (event) => {
        if (event.type === "text-delta") {
          improvedContent += event.delta as string;
        } else if (event.type === "error") {
          streamError = new Error(event.error as string);
        }
      });

      if (streamError) {
        throw streamError;
      }

      if (improvedContent.trim()) {
        onImproved(improvedContent.trim());
        onOpenChange(false);
      } else {
        setError("The model returned an empty response. Please try again.");
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        // User cancelled — not an error
      } else {
        setError(err instanceof Error ? err.message : "An error occurred");
      }
    } finally {
      setIsImproving(false);
      abortControllerRef.current = null;
    }
  }, [promptContent, selectedModelId, onImproved, onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={isImproving ? undefined : onOpenChange}>
      <DialogContent showCloseButton={!isImproving}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-500" />
            Improve Prompt
          </DialogTitle>
          <DialogDescription>
            Select an AI model to analyze and improve your prompt. The improved
            version will replace the current content.
          </DialogDescription>
        </DialogHeader>

        <div className="py-2">
          <label className="text-sm font-medium mb-2 block">AI Model</label>
          <AIModelSelect
            models={aiModels}
            value={selectedModelId}
            onValueChange={setSelectedModelId}
            disabled={isImproving}
          />
        </div>

        {error && (
          <div className="p-3 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        {isImproving && (
          <div className="flex items-center gap-3 p-3 rounded-md bg-blue-50 border border-blue-200 text-blue-700 text-sm">
            <Loader2 className="w-4 h-4 animate-spin shrink-0" />
            <span>Improving your prompt… This may take a moment.</span>
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isImproving}
          >
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={isImproving}>
            {isImproving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Improving…
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Improve
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
