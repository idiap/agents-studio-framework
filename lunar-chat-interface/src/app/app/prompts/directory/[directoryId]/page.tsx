// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";
import { serverApiUrl } from "@/configuration";
import { PromptsClient } from "../../prompts-client";
import PageContainer from "@/components/page-container/page-container";
import { notFound } from "next/navigation";

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

interface DirectoryPageProps {
  params: Promise<{
    directoryId: string;
  }>;
}

async function getDirectoryContents(
  directoryId: string,
): Promise<DirectoryContents | null> {
  try {
    const response = await fetch(
      `${serverApiUrl}/prompts/directories/${directoryId}/contents`,
      {
        cache: "no-store",
      },
    );
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error("Failed to fetch directory contents");
    }
    return response.json();
  } catch (error) {
    console.error("Failed to fetch directory contents:", error);
    throw error;
  }
}

export default async function DirectoryPage({ params }: DirectoryPageProps) {
  const { directoryId } = await params;
  const contents = await getDirectoryContents(directoryId);

  if (!contents) {
    notFound();
  }

  const dirName = contents.directory?.name ?? "Directory";

  return (
    <>
      <Navbar title={dirName} />
      <PageContainer>
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold text-foreground">{dirName}</h1>
        </div>
        <div className="relative flex flex-col max-w-300 w-full gap-8 h-[calc(100%)] mb-0 mr-auto ml-auto">
          <div className="flex flex-col gap-4">
            <PromptsClient
              initialContents={contents}
              currentDirectoryId={directoryId}
            />
          </div>
        </div>
      </PageContainer>
    </>
  );
}
