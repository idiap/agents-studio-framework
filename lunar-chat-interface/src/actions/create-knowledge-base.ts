// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server"

import { serverApiUrl } from "@/configuration"
import { revalidatePath } from "next/cache"

export type PropositionMetadataSchemaInput = {
  field_name: string
  field_description: string
}

export type FileMetadataSchemaInput = {
  field_name: string
  field_description: string
}

export interface CreateKnowledgeBaseInput {
  name: string
  description?: string | null
  proposition_metadata_schemas?: PropositionMetadataSchemaInput[]
  file_metadata_schemas?: FileMetadataSchemaInput[]
}

export interface KnowledgeBaseApiResponse {
  id: string
  name: string
  description: string | null
  created_at?: string | null
  createdAt?: string | null
  files_count?: number | null
  file_count?: number | null
  filesCount?: number | null
  proposition_metadata_schemas?: PropositionMetadataSchemaInput[] | null
}

export const createKnowledgeBaseAction = async (
  input: CreateKnowledgeBaseInput,
) => {
  const name = input.name?.trim()
  const description = input.description?.trim()
  const propositionMetadataSchemas = input.proposition_metadata_schemas?.map(schema => ({
    ...(schema ?? {}),
  }))
  const fileMetadataSchemas = input.file_metadata_schemas?.map(schema => ({
    ...(schema ?? {}),
  }))

  if (!name) {
    throw new Error("Knowledge base name is required.")
  }

  if (!serverApiUrl) {
    throw new Error("Missing server API base URL")
  }

  const response = await fetch(`${serverApiUrl}/knowledge_base`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name,
      description: description ?? null,
      proposition_metadata_schemas: propositionMetadataSchemas,
      file_metadata_schemas: fileMetadataSchemas,
    }),
    cache: "no-store",
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || `Request failed with status ${response.status}`)
  }

  const knowledgeBase = (await response.json()) as KnowledgeBaseApiResponse

  revalidatePath("/app/knowledge-base")

  return knowledgeBase
}
