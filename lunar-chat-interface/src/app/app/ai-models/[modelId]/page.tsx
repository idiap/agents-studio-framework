// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { notFound } from "next/navigation";
import { serverApiUrl } from "@/configuration";
import AIModelEditor from "./ai-model-editor";

interface AIModelEditorPageProps {
  params: Promise<{
    modelId: string;
  }>;
}

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

async function getAIModel(modelId: string): Promise<AIModel | null> {
  try {
    const response = await fetch(`${serverApiUrl}/ai-models/${modelId}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error("Failed to fetch AI model");
    }

    return response.json();
  } catch (error) {
    console.error("Failed to fetch AI model:", error);
    throw error;
  }
}

export default async function AIModelEditorPage({
  params,
}: AIModelEditorPageProps) {
  const { modelId } = await params;
  const model = await getAIModel(modelId);

  if (!model) {
    notFound();
  }

  return <AIModelEditor model={model} />;
}
