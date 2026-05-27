// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Separator } from "@/components/ui/separator";
import { Navbar } from "@/components/navbar";
import { serverApiUrl } from "@/configuration";
import { TemplatesClient } from "./templates-client";
import PageContainer from "@/components/page-container/page-container";

interface Template {
  id: string;
  name: string;
  content: string;
  agent: string | null;
  created_at: string;
  updated_at: string;
}

async function getTemplates(): Promise<Template[]> {
  try {
    const response = await fetch(`${serverApiUrl}/templates`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Failed to fetch templates");
    }

    return response.json();
  } catch (error) {
    console.error("Failed to fetch templates:", error);
    return [];
  }
}

export default async function TemplatesPage() {
  const templates = await getTemplates();

  return (
    <>
      <Navbar title="Templates" />
      <PageContainer>
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold text-foreground">Templates</h1>
        </div>
        <div className="relative flex flex-col max-w-300 w-full gap-8 h-[calc(100%)] mb-0 mr-auto ml-auto">
          <div className="flex flex-col gap-4">
            <TemplatesClient initialTemplates={templates} />
            <Separator />
          </div>
        </div>
      </PageContainer>
    </>
  );
}
