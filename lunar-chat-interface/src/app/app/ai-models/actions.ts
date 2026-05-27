// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { revalidatePath } from "next/cache";
import { serverApiUrl } from "@/configuration";

export async function createAIModel(data: {
  name: string;
  provider: string;
  model_id: string;
  api_base?: string;
  api_version?: string;
  api_key: string;
  config?: Record<string, unknown>;
}) {
  if (!data.name?.trim()) {
    throw new Error("Model name is required");
  }
  if (!data.provider?.trim()) {
    throw new Error("Provider is required");
  }
  if (!data.model_id?.trim()) {
    throw new Error("Model ID is required");
  }
  if (!data.api_key?.trim()) {
    throw new Error("API key is required");
  }

  const response = await fetch(`${serverApiUrl}/ai-models/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: data.name.trim(),
      provider: data.provider.trim(),
      model_id: data.model_id.trim(),
      api_base: data.api_base?.trim() || null,
      api_version: data.api_version?.trim() || null,
      api_key: data.api_key,
      config: data.config || {},
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to create AI model");
  }

  const newModel = await response.json();
  revalidatePath("/app/ai-models");
  return newModel;
}

export async function deleteAIModel(modelId: string) {
  if (!modelId) {
    throw new Error("Model ID is required");
  }
  const response = await fetch(`${serverApiUrl}/ai-models/${modelId}`, {
    method: "DELETE",
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to delete AI model");
  }
  revalidatePath("/app/ai-models");
}

export async function updateAIModel(
  modelId: string,
  data: {
    name?: string;
    provider?: string;
    model_id?: string;
    api_base?: string;
    api_version?: string;
    config?: Record<string, unknown>;
  },
) {
  if (!modelId) {
    throw new Error("Model ID is required");
  }

  const response = await fetch(`${serverApiUrl}/ai-models/${modelId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to update AI model");
  }

  const updatedModel = await response.json();
  revalidatePath("/app/ai-models");
  revalidatePath(`/app/ai-models/${modelId}`);
  return updatedModel;
}
