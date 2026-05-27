// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { serverApiUrl } from "@/configuration";
import type {
  KnowledgeBase,
  KnowledgeBaseField,
} from "@/models/knowledge-base";
import KnowledgeBaseList from "./components/knowledge-base-list";
import CreateKnowledgeBaseButton from "./components/create-knowledge-base-button";
import PageContainer from "@/components/page-container/page-container";

const KnowledgeBasePage: React.FC = async () => {
  let knowledgeBases: KnowledgeBase[] = [];
  const errorMessage: string | null = null;
  if (!serverApiUrl) {
    throw new Error("Missing server API base URL");
  }
  const response = await fetch(`${serverApiUrl}/knowledge_base`, {
    cache: "no-store",
    next: { revalidate: 0 },
  });
  if (!response.ok) {
    throw new Error(`Failed with status ${response.status}`);
  }
  type KnowledgeBaseApiResponse = {
    id?: string | number;
    name?: string | null;
    description?: string | null;
    propositionMetadataSchemas?: unknown[] | null;
  };

  const responseJson = (await response.json()) as unknown;

  if (!Array.isArray(responseJson)) {
    throw new Error("Unexpected knowledge base list response.");
  }

  const payload = responseJson as KnowledgeBaseApiResponse[];

  knowledgeBases = payload.map((rawKb, index) => {
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

    const propositionMetadataSchemasRaw = Array.isArray(
      rawKb.propositionMetadataSchemas,
    )
      ? rawKb.propositionMetadataSchemas
      : [];

    const fields = propositionMetadataSchemasRaw.map((schema, schemaIndex) => {
      const typedSchema = (schema ?? {}) as KnowledgeBaseField;
      const idValue = typedSchema.id;

      return {
        ...typedSchema,
        id:
          typeof idValue === "string"
            ? idValue
            : typeof idValue === "number"
              ? String(idValue)
              : `schema-${index}-${schemaIndex}`,
      };
    });

    return {
      id,
      name,
      description,
      fields,
    };
  });

  return (
    <>
      <Navbar title="Knowledge Bases" />
      <PageContainer>
        <div className="flex gap-2 justify-between">
          <h1 className="text-3xl font-semibold text-foreground">
            Knowledge Bases
          </h1>
          <CreateKnowledgeBaseButton />
        </div>
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 py-10">
          {errorMessage ?? null}
          <KnowledgeBaseList
            knowledgeBases={knowledgeBases}
            error={errorMessage}
          />
        </div>
      </PageContainer>
    </>
  );
};

export default KnowledgeBasePage;
