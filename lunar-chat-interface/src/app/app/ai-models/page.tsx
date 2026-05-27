// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";
import { serverApiUrl } from "@/configuration";
import PageContainer from "@/components/page-container/page-container";
import { AIModelsClient } from "./ai-models-client";

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

async function getAIModels(): Promise<AIModel[]> {
  try {
    const response = await fetch(`${serverApiUrl}/ai-models/`, {
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error("Failed to fetch AI models");
    }
    return response.json();
  } catch (error) {
    console.error("Failed to fetch AI models:", error);
    return [];
  }
}

export default async function AIModelsPage() {
  const models = await getAIModels();

  return (
    <>
      <Navbar title="AI Models" />
      <PageContainer>
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold text-foreground">AI Models</h1>
          <p className="text-muted-foreground">
            Manage your AI model configurations
          </p>
        </div>
        <AIModelsClient initialModels={models} />
      </PageContainer>
    </>
  );
}
