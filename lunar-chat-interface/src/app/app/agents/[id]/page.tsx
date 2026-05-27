// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";
import { serverApiUrl } from "@/configuration";
import type { KnowledgeBase } from "@/models/knowledge-base";
import { notFound } from "next/navigation";
import AgentDetailClient from "./agent-detail-client";
import { getFlowById } from "@/actions/get-flows";
import PageContainer from "@/components/page-container/page-container";

export const dynamic = "force-dynamic";

interface AgentPageProps {
  params: Promise<{ id: string }>;
}

const AgentPage: React.FC<AgentPageProps> = async ({ params }) => {
  const { id } = await params;

  const flow = await getFlowById(id);

  if (!flow) {
    notFound();
  }

  let knowledgeBases: KnowledgeBase[] = [];

  // Fetch knowledge bases for the modal form
  if (!serverApiUrl) {
    console.error("Missing server API base URL");
  } else {
    try {
      const response = await fetch(`${serverApiUrl}/knowledge_base`, {
        cache: "no-store",
        next: { revalidate: 0 },
      });

      if (response.ok) {
        const responseJson = await response.json();

        if (Array.isArray(responseJson)) {
          knowledgeBases = responseJson.map((rawKb: any, index: number) => {
            const id =
              typeof rawKb.id === "string"
                ? rawKb.id
                : typeof rawKb.id === "number"
                  ? String(rawKb.id)
                  : `kb-${index}`;

            const name =
              typeof rawKb.name === "string" && rawKb.name.trim().length > 0
                ? rawKb.name.trim()
                : "Untitled knowledge base";

            const description =
              typeof rawKb.description === "string" &&
              rawKb.description.trim().length > 0
                ? rawKb.description.trim()
                : null;

            const fields = Array.isArray(rawKb.fields) ? rawKb.fields : [];

            return {
              id,
              name,
              description,
              fields,
            };
          });
        }
      } else {
        console.error(`Failed to fetch knowledge bases: ${response.status}`);
      }
    } catch (error) {
      console.error("Error fetching knowledge bases:", error);
    }
  }

  return (
    <>
      <Navbar title={flow.name} />
      <PageContainer>
        <AgentDetailClient flow={flow} knowledgeBases={knowledgeBases} />
      </PageContainer>
    </>
  );
};

export default AgentPage;
