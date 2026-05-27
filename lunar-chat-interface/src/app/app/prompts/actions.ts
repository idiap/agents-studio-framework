// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { revalidatePath } from "next/cache";
import { serverApiUrl } from "@/configuration";

export async function createPrompt(
  name: string,
  directoryId: string | null = null,
) {
  if (!name?.trim()) {
    throw new Error("Prompt name is required");
  }
  const response = await fetch(`${serverApiUrl}/prompts/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: name.trim(),
      content: "# New Prompt\n\nStart writing your prompt here...",
      directory_id: directoryId,
    }),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to create prompt");
  }
  const newPrompt = await response.json();
  revalidatePath("/app/prompts");
  return newPrompt;
}

export async function deletePrompt(promptId: string) {
  if (!promptId) {
    throw new Error("Prompt ID is required");
  }
  const response = await fetch(`${serverApiUrl}/prompts/${promptId}`, {
    method: "DELETE",
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to delete prompt");
  }
  revalidatePath("/app/prompts");
}

export async function updatePrompt(
  promptId: string,
  data: { name: string; content: string },
) {
  if (!promptId) {
    throw new Error("Prompt ID is required");
  }
  if (!data.name?.trim()) {
    throw new Error("Prompt name is required");
  }
  const response = await fetch(`${serverApiUrl}/prompts/${promptId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: data.name.trim(),
      content: data.content,
    }),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to update prompt");
  }
  const updatedPrompt = await response.json();
  revalidatePath("/app/prompts");
  revalidatePath(`/app/prompts/${promptId}`);
  return updatedPrompt;
}

export async function createDirectory(
  name: string,
  parentId: string | null = null,
) {
  if (!name?.trim()) {
    throw new Error("Directory name is required");
  }
  const response = await fetch(`${serverApiUrl}/prompts/directories`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: name.trim(),
      parent_id: parentId,
    }),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to create directory");
  }
  const newDir = await response.json();
  revalidatePath("/app/prompts");
  return newDir;
}

export async function deleteDirectory(directoryId: string) {
  if (!directoryId) {
    throw new Error("Directory ID is required");
  }
  const response = await fetch(
    `${serverApiUrl}/prompts/directories/${directoryId}`,
    {
      method: "DELETE",
      cache: "no-store",
    },
  );
  if (!response.ok) {
    throw new Error("Failed to delete directory");
  }
  revalidatePath("/app/prompts");
}

export async function moveDirectory(
  directoryId: string,
  parentId: string | null,
) {
  if (!directoryId) {
    throw new Error("Directory ID is required");
  }
  const response = await fetch(
    `${serverApiUrl}/prompts/directories/${directoryId}/move`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ parent_id: parentId }),
      cache: "no-store",
    },
  );
  if (!response.ok) {
    throw new Error("Failed to move directory");
  }
  revalidatePath("/app/prompts");
}

export async function movePrompt(
  promptId: string,
  directoryId: string | null,
) {
  if (!promptId) {
    throw new Error("Prompt ID is required");
  }
  const response = await fetch(`${serverApiUrl}/prompts/${promptId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ directory_id: directoryId }),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to move prompt");
  }
  revalidatePath("/app/prompts");
}
