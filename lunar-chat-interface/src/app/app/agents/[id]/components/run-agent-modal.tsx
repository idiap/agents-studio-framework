// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Flow, FlowInput } from "../../page";
import type { KnowledgeBase } from "@/models/knowledge-base";
import { toast } from "sonner";
import { runFlow } from "@/actions/run-flow";

interface RunAgentModalProps {
  flow: Flow;
  knowledgeBases: KnowledgeBase[];
  isOpen: boolean;
  onClose: () => void;
  onConfirm?: (agentId: string, inputs: Record<string, any>) => void;
  isRunning?: boolean;
  onAgentStarted?: () => void;
  isLoadingInputs?: boolean;
}

export default function RunAgentModal({
  flow,
  knowledgeBases,
  isOpen,
  onClose,
  onConfirm,
  isRunning = false,
  onAgentStarted,
  isLoadingInputs = false,
}: RunAgentModalProps) {
  const [inputValues, setInputValues] = useState<Record<string, any>>({});
  const [selectedKbForFields, setSelectedKbForFields] = useState<
    Record<string, string>
  >({});
  const flowInputs = Array.isArray(flow.inputs) ? flow.inputs : [];

  const handleInputChange = (inputId: string, value: any) => {
    setInputValues((prev) => ({
      ...prev,
      [inputId]: value,
    }));
  };

  const handleKbForFieldChange = (inputId: string, kbId: string) => {
    setSelectedKbForFields((prev) => ({
      ...prev,
      [inputId]: kbId,
    }));
    setInputValues((prev) => ({
      ...prev,
      [inputId]: undefined,
    }));
  };

  const handleConfirm = async () => {
    // Ensure all inputValues keys are present, set optional to empty string if not changed
    const allInputs: Record<string, any> = { ...inputValues };
    flowInputs.forEach((input) => {
      if (!(input.id in allInputs)) {
        allInputs[input.id] = input.required ? undefined : "";
      }
    });
    const allRequiredFilled = flowInputs
      .filter((input) => input.required)
      .every((input) => {
        const value = allInputs[input.id];
        return value !== undefined && value !== null && value !== "";
      });

    if (allRequiredFilled) {
      try {
        await runFlow(flow.id, allInputs);
        toast.success("Agent started successfully");
      } catch (error) {
        console.error("Error running agent:", error);
        toast.error("Failed to start agent");
        return;
      }
      onAgentStarted?.();
      if (onConfirm) {
        onConfirm(flow.id, allInputs);
      }
      onClose();
      setInputValues({});
      setSelectedKbForFields({});
    }
  };

  const handleClose = () => {
    setInputValues({});
    setSelectedKbForFields({});
    onClose();
  };

  const isConfirmDisabled =
    isLoadingInputs ||
    flowInputs
      .filter((input) => input.required)
      .some((input) => {
        const value = inputValues[input.id];
        return value === undefined || value === null || value === "";
      }) ||
    isRunning;

  const renderInput = (input: FlowInput) => {
    switch (input.type) {
      case "string":
        return (
          <Input
            id={input.id}
            placeholder={`Enter ${input.label.toLowerCase()}`}
            value={inputValues[input.id] || ""}
            onChange={(e) => handleInputChange(input.id, e.target.value)}
          />
        );

      case "knowledge-base":
        return (
          <Select
            value={inputValues[input.id] || ""}
            onValueChange={(value) => handleInputChange(input.id, value)}
          >
            <SelectTrigger id={input.id}>
              <SelectValue placeholder="Select a knowledge base" />
            </SelectTrigger>
            <SelectContent>
              {knowledgeBases.length === 0 ? (
                <div className="py-6 text-center text-sm text-muted-foreground">
                  No knowledge bases available
                </div>
              ) : (
                knowledgeBases.map((kb) => (
                  <SelectItem key={kb.id} value={kb.id}>
                    {kb.name}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        );

      case "knowledge-base-field":
        const selectedKbId = selectedKbForFields[input.id];
        const selectedKb = knowledgeBases.find((kb) => kb.id === selectedKbId);
        const fields = selectedKb?.fields || [];

        return (
          <div className="grid gap-2">
            <Select
              value={selectedKbId || ""}
              onValueChange={(value) => handleKbForFieldChange(input.id, value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a knowledge base" />
              </SelectTrigger>
              <SelectContent>
                {knowledgeBases.length === 0 ? (
                  <div className="py-6 text-center text-sm text-muted-foreground">
                    No knowledge bases available
                  </div>
                ) : (
                  knowledgeBases.map((kb) => (
                    <SelectItem key={kb.id} value={kb.id}>
                      {kb.name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>

            {selectedKbId && (
              <Select
                value={inputValues[input.id] || ""}
                onValueChange={(value) => handleInputChange(input.id, value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a field" />
                </SelectTrigger>
                <SelectContent>
                  {fields.length === 0 ? (
                    <div className="py-6 text-center text-sm text-muted-foreground">
                      No fields available in this knowledge base
                    </div>
                  ) : (
                    fields.map((field) => (
                      <SelectItem
                        key={field.id || field.name}
                        value={field.id || field.name || ""}
                      >
                        {field.name || "Unnamed field"}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-175 max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Run {flow.name}</DialogTitle>
          <DialogDescription>
            Configure the agent run by providing the required inputs.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4">
          {isLoadingInputs ? (
            <p className="text-sm text-muted-foreground">
              Loading agent inputs...
            </p>
          ) : flowInputs.length > 0 ? (
            flowInputs.map((input) => (
              <div key={input.id} className="grid gap-2">
                <Label htmlFor={input.id}>
                  {input.label}
                  {input.required && (
                    <span className="text-destructive ml-1">*</span>
                  )}
                </Label>
                {renderInput(input)}
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">
              No inputs are available for this agent yet.
            </p>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            {"Close"}
          </Button>
          <Button onClick={handleConfirm} disabled={isConfirmDisabled}>
            {isRunning ? "Running..." : "Run"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
