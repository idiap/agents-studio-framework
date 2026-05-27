// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Plus, Brain } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { createAIModel, deleteAIModel } from "./actions";
import { ListItem } from "@/components/list-item";
import { DeleteButton } from "@/components/delete-button";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";

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

interface AIModelsClientProps {
  initialModels: AIModel[];
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

export function AIModelsClient({ initialModels }: AIModelsClientProps) {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newProvider, setNewProvider] = useState("");
  const [newModelId, setNewModelId] = useState("");
  const [newApiBase, setNewApiBase] = useState("");
  const [newApiVersion, setNewApiVersion] = useState("");
  const [newApiKey, setNewApiKey] = useState("");
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  const resetForm = () => {
    setNewName("");
    setNewProvider("");
    setNewModelId("");
    setNewApiBase("");
    setNewApiVersion("");
    setNewApiKey("");
  };

  const handleCreate = async () => {
    if (
      !newName.trim() ||
      !newProvider.trim() ||
      !newModelId.trim() ||
      !newApiKey.trim()
    ) {
      toast.error("Please fill in all required fields");
      return;
    }

    startTransition(async () => {
      try {
        const created = await createAIModel({
          name: newName.trim(),
          provider: newProvider,
          model_id: newModelId.trim(),
          api_base: newApiBase.trim() || undefined,
          api_version: newApiVersion.trim() || undefined,
          api_key: newApiKey,
        });
        resetForm();
        setIsCreateOpen(false);
        toast.success("AI model created successfully");
        if (created && created.id) {
          router.push(`/app/ai-models/${created.id}`);
        }
      } catch {
        toast.error("Failed to create AI model. Please try again.");
      }
    });
  };

  return (
    <>
      <div className="flex justify-end">
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button disabled={isPending}>
              <Plus className="w-4 h-4 mr-2" />
              Create AI Model
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Create New AI Model</DialogTitle>
              <DialogDescription>
                Configure a new AI model connection. The API key will be
                encrypted and stored securely.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  placeholder="e.g. GPT-4 Production"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="provider">Provider *</Label>
                <Select value={newProvider} onValueChange={setNewProvider}>
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
                <Label htmlFor="model_id">Model ID *</Label>
                <Input
                  id="model_id"
                  placeholder="e.g. gpt-4, claude-3-opus"
                  value={newModelId}
                  onChange={(e) => setNewModelId(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="api_key">API Key *</Label>
                <Input
                  id="api_key"
                  type="password"
                  placeholder="Enter API key"
                  value={newApiKey}
                  onChange={(e) => setNewApiKey(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="api_base">API Base URL</Label>
                <Input
                  id="api_base"
                  placeholder="e.g. https://api.openai.com/v1"
                  value={newApiBase}
                  onChange={(e) => setNewApiBase(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="api_version">API Version</Label>
                <Input
                  id="api_version"
                  placeholder="e.g. 2024-02-01"
                  value={newApiVersion}
                  onChange={(e) => setNewApiVersion(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  resetForm();
                  setIsCreateOpen(false);
                }}
                disabled={isPending}
              >
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={isPending}>
                {isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Separator />

      {initialModels.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Brain className="w-12 h-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-muted-foreground">
            No AI models configured
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            Create your first AI model to get started.
          </p>
        </div>
      ) : (
        <div className="flex flex-col">
          {initialModels.map((model) => (
            <ListItem
              key={model.id}
              title={model.name}
              description={`${model.provider} · ${model.model_id}`}
              date={model.created_at}
              href={`/app/ai-models/${model.id}`}
              icon={<Brain className="w-4 h-4 text-white" />}
              actions={
                <DeleteButton
                  title="Delete AI Model"
                  description={`Are you sure you want to delete "${model.name}"? This action cannot be undone.`}
                  onDelete={() => deleteAIModel(model.id)}
                  successMessage="AI model deleted successfully"
                  errorMessage="Failed to delete AI model"
                />
              }
            />
          ))}
        </div>
      )}
    </>
  );
}
