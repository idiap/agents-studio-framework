// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { notFound } from "next/navigation";
import { serverApiUrl } from "@/configuration";
import TemplateEditor from "./template-editor";

interface TemplateEditorPageProps {
  params: Promise<{
    templateId: string;
  }>;
}

interface Template {
  id: string;
  name: string;
  content: string;
  agent: string | null;
  created_at: string;
  updated_at: string;
}

async function getTemplate(templateId: string): Promise<Template | null> {
  try {
    const response = await fetch(`${serverApiUrl}/templates/${templateId}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error("Failed to fetch template");
    }

    return response.json();
  } catch (error) {
    console.error("Failed to fetch template:", error);
    throw error;
  }
}

export default async function TemplateEditorPage({
  params,
}: TemplateEditorPageProps) {
  const { templateId } = await params;
  const template = await getTemplate(templateId);

  if (!template) {
    notFound();
  }

  return <TemplateEditor template={template} />;
}
