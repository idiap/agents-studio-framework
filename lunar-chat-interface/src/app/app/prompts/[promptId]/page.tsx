// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { notFound } from "next/navigation";
import { serverApiUrl } from "@/configuration";
import PromptEditor from "./prompt-editor";
import type { AIModel } from "@/components/ai-model-select";

interface PromptEditorPageProps {
  params: Promise<{
    promptId: string;
  }>;
}

interface Prompt {
  id: string;
  name: string;
  content: string | null;
  directory_id: string | null;
  created_at: string;
  updated_at: string;
}

async function getPrompt(promptId: string): Promise<Prompt | null> {
  try {
    const response = await fetch(`${serverApiUrl}/prompts/${promptId}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error("Failed to fetch prompt");
    }

    return response.json();
  } catch (error) {
    console.error("Failed to fetch prompt:", error);
    throw error;
  }
}

async function getAIModels(): Promise<AIModel[]> {
  try {
    const response = await fetch(`${serverApiUrl}/ai-models/`, {
      cache: "no-store",
    });
    if (!response.ok) {
      return [];
    }
    return response.json();
  } catch (error) {
    console.error("Failed to fetch AI models:", error);
    return [];
  }
}

export default async function PromptEditorPage({
  params,
}: PromptEditorPageProps) {
  const { promptId } = await params;
  const [prompt, aiModels] = await Promise.all([
    getPrompt(promptId),
    getAIModels(),
  ]);

  if (!prompt) {
    notFound();
  }

  return <PromptEditor prompt={prompt} aiModels={aiModels} />;
}
