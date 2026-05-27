// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { revalidatePath } from "next/cache";
import { serverApiUrl } from "@/configuration";

export async function createTemplate(name: string) {
  if (!name?.trim()) {
    throw new Error("Template name is required");
  }
  const response = await fetch(`${serverApiUrl}/templates/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: name.trim(),
      content: "# New Template\n\nStart writing your template here...",
    }),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to create template");
  }
  const newTemplate = await response.json();
  revalidatePath("/app/templates");
  return newTemplate;
}

export async function deleteTemplate(templateId: string) {
  if (!templateId) {
    throw new Error("Template ID is required");
  }

  const response = await fetch(`${serverApiUrl}/templates/${templateId}`, {
    method: "DELETE",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to delete template");
  }

  revalidatePath("/app/templates");
}

export async function updateTemplate(
  templateId: string,
  data: { name: string; content: string }
) {
  if (!templateId) {
    throw new Error("Template ID is required");
  }

  if (!data.name?.trim()) {
    throw new Error("Template name is required");
  }

  const response = await fetch(`${serverApiUrl}/templates/${templateId}`, {
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
    throw new Error("Failed to update template");
  }

  const updatedTemplate = await response.json();
  revalidatePath("/app/templates");
  revalidatePath(`/app/templates/${templateId}`);
  return updatedTemplate;
}
