// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import React, { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Save, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { updateAIModel } from "../actions";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Navbar } from "@/components/navbar";
import PageContainer from "@/components/page-container/page-container";

interface AIModel {
  id: string;
  name: string;
  provider: string;
  model_id: string;
  api_base: string | null;
  api_version: string | null;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface AIModelEditorProps {
  model: AIModel;
}

const PROVIDERS = [
  "openai",
  "azure",
  "anthropic",
  "google",
  "cohere",
  "mistral",
  "huggingface",
  "ollama",
  "other",
];

function AIModelEditor({ model }: AIModelEditorProps) {
  const [name, setName] = useState(model.name);
  const [provider, setProvider] = useState(model.provider);
  const [modelId, setModelId] = useState(model.model_id);
  const [apiBase, setApiBase] = useState(model.api_base ?? "");
  const [apiVersion, setApiVersion] = useState(model.api_version ?? "");
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const router = useRouter();

  const handleSave = useCallback(async () => {
    if (!hasChanges) return;

    setSaving(true);
    try {
      await updateAIModel(model.id, {
        name,
        provider,
        model_id: modelId,
        api_base: apiBase || undefined,
        api_version: apiVersion || undefined,
      });
      setHasChanges(false);
      toast.success("AI model updated successfully");
    } catch (error) {
      console.error("Failed to save AI model:", error);
      toast.error("Failed to save AI model. Please try again.");
    } finally {
      setSaving(false);
    }
  }, [model.id, name, provider, modelId, apiBase, apiVersion, hasChanges]);

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

  const markChanged = () => setHasChanges(true);

  return (
    <>
      <Navbar title="AI Model Details" />
      <PageContainer>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/app/ai-models")}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <h1 className="text-2xl font-semibold text-foreground">
              {model.name}
            </h1>
          </div>
          <div className="flex items-center gap-4">
            {hasChanges && !saving && (
              <span className="text-sm text-orange-500">Unsaved changes</span>
            )}
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

        <Separator />

        <div className="grid gap-6">
          <div className="grid gap-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                markChanged();
              }}
              placeholder="Model name"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="provider">Provider</Label>
            <Select
              value={provider}
              onValueChange={(value) => {
                setProvider(value);
                markChanged();
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a provider" />
              </SelectTrigger>
              <SelectContent>
                {PROVIDERS.map((p) => (
                  <SelectItem key={p} value={p}>
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="model_id">Model ID</Label>
            <Input
              id="model_id"
              value={modelId}
              onChange={(e) => {
                setModelId(e.target.value);
                markChanged();
              }}
              placeholder="e.g. gpt-4, claude-3-opus"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="api_key">API Key</Label>
            <Input
              id="api_key"
              value="••••••••••••••••"
              disabled
              className="bg-muted"
            />
            <p className="text-xs text-muted-foreground">
              API keys cannot be viewed or edited after creation for security
              reasons.
            </p>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="api_base">API Base URL</Label>
            <Input
              id="api_base"
              value={apiBase}
              onChange={(e) => {
                setApiBase(e.target.value);
                markChanged();
              }}
              placeholder="e.g. https://api.openai.com/v1"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="api_version">API Version</Label>
            <Input
              id="api_version"
              value={apiVersion}
              onChange={(e) => {
                setApiVersion(e.target.value);
                markChanged();
              }}
              placeholder="e.g. 2024-02-01"
            />
          </div>

          {Object.keys(model.config).length > 0 && (
            <div className="grid gap-2">
              <Label>Configuration</Label>
              <pre className="bg-muted p-4 rounded-md text-sm overflow-auto">
                {JSON.stringify(model.config, null, 2)}
              </pre>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
            <div>
              <span className="font-medium">Created:</span>{" "}
              {new Date(model.created_at).toLocaleString()}
            </div>
            <div>
              <span className="font-medium">Updated:</span>{" "}
              {new Date(model.updated_at).toLocaleString()}
            </div>
          </div>
        </div>
      </PageContainer>
    </>
  );
}

export default AIModelEditor;
