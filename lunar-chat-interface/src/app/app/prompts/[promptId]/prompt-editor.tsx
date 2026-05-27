// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import React, {
  useState,
  useCallback,
  useEffect,
  useRef,
  useMemo,
} from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Navbar } from "@/components/navbar";
import { extractVariables } from "@/lib/prompt-variables";
import {
  ArrowLeft,
  Save,
  Loader2,
  Eye,
  Pencil,
  Play,
  Square,
  Copy,
  Check,
  Sparkles,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { updatePrompt } from "../actions";
import "@uiw/react-md-editor/markdown-editor.css";
import "@uiw/react-markdown-preview/markdown.css";
import CollapsibleMarkdownPreview from "./collapsible-markdown-preview";
import { AIModelSelect, type AIModel } from "@/components/ai-model-select";
import { ImprovePromptDialog } from "./improve-prompt-dialog";
import { parseSSEStream } from "@/lib/sse-parser";
import remarkBreaks from "remark-breaks";

const MDEditor = dynamic(() => import("@uiw/react-md-editor"), { ssr: false });
const MarkdownPreview = dynamic(() => import("@uiw/react-markdown-preview"), {
  ssr: false,
});

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

interface Prompt {
  id: string;
  name: string;
  content: string | null;
  directory_id: string | null;
  created_at: string;
  updated_at: string;
}

interface PromptEditorProps {
  prompt: Prompt;
  aiModels: AIModel[];
}

function PromptEditor({ prompt, aiModels }: PromptEditorProps) {
  const [name, setName] = useState(prompt.name);
  const [content, setContent] = useState(prompt.content ?? "");
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [previewMode, setPreviewMode] = useState<"edit" | "preview">("edit");
  const router = useRouter();

  // Run prompt state
  const [selectedModelId, setSelectedModelId] = useState<string>(
    aiModels.length > 0 ? aiModels[0].id : "",
  );
  const [output, setOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [showImproveDialog, setShowImproveDialog] = useState(false);
  const [variableValues, setVariableValues] = useState<Record<string, string>>(
    {},
  );
  const abortControllerRef = useRef<AbortController | null>(null);
  const outputEndRef = useRef<HTMLDivElement>(null);

  // Detect variables in prompt content
  const detectedVariables = useMemo(() => extractVariables(content), [content]);

  // Keep variableValues in sync: remove stale keys, add new ones with empty defaults
  useEffect(() => {
    setVariableValues((prev) => {
      const next: Record<string, string> = {};
      for (const name of detectedVariables) {
        next[name] = prev[name] ?? "";
      }
      return next;
    });
  }, [detectedVariables]);

  const backUrl = prompt.directory_id
    ? `/app/prompts/directory/${prompt.directory_id}`
    : "/app/prompts";

  const handleSave = useCallback(async () => {
    if (!hasChanges) return;

    setSaving(true);
    try {
      await updatePrompt(prompt.id, { name, content });
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to save prompt:", error);
      alert("Failed to save prompt. Please try again.");
    } finally {
      setSaving(false);
    }
  }, [prompt.id, name, content, hasChanges]);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
    setHasChanges(true);
  };

  const handleContentChange = (value: string | undefined) => {
    setContent(value || "");
    setHasChanges(true);
  };

  const handleStop = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsRunning(false);
  }, []);

  const handleRun = useCallback(async () => {
    if (!selectedModelId) {
      setRunError("Please select an AI model first.");
      return;
    }

    if (!content.trim()) {
      setRunError("Prompt content is empty.");
      return;
    }

    setOutput("");
    setRunError(null);
    setIsRunning(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch(`${basePath}/api/prompts/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: content,
          ai_model_id: selectedModelId,
          variables: detectedVariables.length > 0 ? variableValues : undefined,
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

      await parseSSEStream(reader, (event) => {
        if (event.type === "text-delta") {
          setOutput((prev) => prev + (event.delta as string));
        } else if (event.type === "error") {
          setRunError(event.error as string);
        }
      });
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        // User cancelled, not an error
      } else {
        setRunError(err instanceof Error ? err.message : "An error occurred");
      }
    } finally {
      setIsRunning(false);
      abortControllerRef.current = null;
    }
  }, [content, selectedModelId, detectedVariables, variableValues]);

  const handleCopy = useCallback(async () => {
    if (!output) return;
    await navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [output]);

  const handleImproved = useCallback((improvedContent: string) => {
    setContent(improvedContent);
    setHasChanges(true);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleSave]);

  // Auto-scroll output to bottom
  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [output]);

  return (
    <div className="flex flex-col h-screen">
      <Navbar
        title={
          <Input
            value={name}
            onChange={handleNameChange}
            className="text-xl font-semibold border-none shadow-none focus-visible:ring-0 w-75"
            placeholder="Prompt name..."
          />
        }
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header bar */}
        <div className="flex items-center justify-between px-6 py-2 border-b border-t bg-white">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push(backUrl)}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </div>
          <div className="flex items-center gap-4">
            {hasChanges && !saving && (
              <span className="text-sm text-orange-500">Unsaved changes</span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowImproveDialog(true)}
              disabled={isImproving || !content.trim()}
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Improve Prompt
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                setPreviewMode((prev) => (prev === "edit" ? "preview" : "edit"))
              }
            >
              {previewMode === "edit" ? (
                <>
                  <Eye className="w-4 h-4 mr-2" />
                  Preview
                </>
              ) : (
                <>
                  <Pencil className="w-4 h-4 mr-2" />
                  Edit
                </>
              )}
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || !hasChanges}
              size="sm"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Split panel: Editor + Output */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left panel — Markdown editor / preview */}
          <div
            className="flex-1 min-w-0 overflow-hidden h-full overflow-y-scroll"
            data-color-mode="light"
          >
            {previewMode === "preview" ? (
              <CollapsibleMarkdownPreview source={content} />
            ) : (
              <div
                className={`h-full ${isImproving ? "pointer-events-none opacity-50" : ""}`}
              >
                <MDEditor
                  value={content}
                  onChange={handleContentChange}
                  height="100%"
                  preview="edit"
                  hideToolbar
                  visibleDragbar={false}
                />
              </div>
            )}
          </div>

          {/* Right panel — Run & output */}
          <div className="w-120 shrink-0 flex flex-col border-l bg-gray-50">
            {/* Run controls */}
            <div className="flex items-center gap-2 px-4 py-3 border-b bg-white">
              <AIModelSelect
                models={aiModels}
                value={selectedModelId}
                onValueChange={setSelectedModelId}
              />

              {isRunning ? (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={handleStop}
                  className="shrink-0"
                >
                  <Square className="w-4 h-4 mr-1.5" />
                  Stop
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={handleRun}
                  disabled={!selectedModelId || !content.trim()}
                  className="shrink-0"
                >
                  <Play className="w-4 h-4 mr-1.5" />
                  Run
                </Button>
              )}
            </div>

            {/* Variable inputs */}
            {detectedVariables.length > 0 && (
              <div className="px-4 py-3 border-b bg-white space-y-3">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Variables
                </p>
                {detectedVariables.map((name) => (
                  <div key={name} className="space-y-1">
                    <Label htmlFor={`var-${name}`} className="text-sm">
                      {name}
                    </Label>
                    <Input
                      id={`var-${name}`}
                      placeholder={`Enter value for {${name}}`}
                      value={variableValues[name] ?? ""}
                      onChange={(e) =>
                        setVariableValues((prev) => ({
                          ...prev,
                          [name]: e.target.value,
                        }))
                      }
                      disabled={isRunning}
                      className="h-8 text-sm"
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Output area */}
            <div className="flex-1 overflow-y-auto">
              <div className="p-4">
                {runError && (
                  <div className="mb-3 p-3 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm">
                    {runError}
                  </div>
                )}

                {!output && !isRunning && !runError && (
                  <div className="text-sm text-muted-foreground text-center mt-8">
                    Select a model and click <strong>Run</strong> to execute
                    your prompt.
                  </div>
                )}

                {(output || isRunning) && (
                  <div className="relative">
                    {output && !isRunning && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute top-0 right-0 h-7 w-7 z-10"
                        onClick={handleCopy}
                      >
                        {copied ? (
                          <Check className="w-3.5 h-3.5 text-green-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </Button>
                    )}
                    <div className="pr-8" data-color-mode="light">
                      <MarkdownPreview
                        source={output}
                        remarkPlugins={[remarkBreaks]}
                        style={{
                          backgroundColor: "transparent",
                          fontSize: "14px",
                        }}
                        components={{
                          table: ({ children }) => (
                            <div className="overflow-x-auto w-full">
                              <table className="min-w-full border-collapse">
                                {children}
                              </table>
                            </div>
                          ),
                        }}
                      />
                      {isRunning && (
                        <span className="inline-block w-2 h-4 bg-foreground/70 animate-pulse ml-0.5" />
                      )}
                    </div>
                    <div ref={outputEndRef} />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <ImprovePromptDialog
        open={showImproveDialog}
        onOpenChange={(open) => {
          setShowImproveDialog(open);
          setIsImproving(false);
        }}
        aiModels={aiModels}
        promptContent={content}
        onImproved={handleImproved}
      />
    </div>
  );
}

export default PromptEditor;
