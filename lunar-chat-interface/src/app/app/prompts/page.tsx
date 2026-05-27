// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";
import { serverApiUrl } from "@/configuration";
import { PromptsClient } from "./prompts-client";
import PageContainer from "@/components/page-container/page-container";

interface DirectoryContents {
  directory: {
    id: string;
    name: string;
    parent_id: string | null;
  } | null;
  breadcrumb: {
    id: string;
    name: string;
    parent_id: string | null;
  }[];
  children: {
    id: string;
    name: string;
    type: "directory" | "prompt";
    created_at: string;
    updated_at: string;
  }[];
}

async function getRootContents(): Promise<DirectoryContents> {
  try {
    const response = await fetch(`${serverApiUrl}/prompts/root/contents`, {
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error("Failed to fetch root contents");
    }
    return response.json();
  } catch (error) {
    console.error("Failed to fetch root contents:", error);
    return { directory: null, breadcrumb: [], children: [] };
  }
}

export default async function PromptsPage() {
  const contents = await getRootContents();

  return (
    <>
      <Navbar title="Prompts" />
      <PageContainer>
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold text-foreground">Prompts</h1>
        </div>
        <div className="relative flex flex-col max-w-300 w-full gap-8 h-[calc(100%)] mb-0 mr-auto ml-auto">
          <div className="flex flex-col gap-4">
            <PromptsClient
              initialContents={contents}
              currentDirectoryId={null}
            />
          </div>
        </div>
      </PageContainer>
    </>
  );
}
