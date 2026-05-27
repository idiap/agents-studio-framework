// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server"

import { serverApiUrl } from "@/configuration"
import { revalidatePath } from "next/cache"

export const deleteKnowledgeBaseAction = async (knowledgeBaseId: string) => {
  if (!knowledgeBaseId) {
    throw new Error("Knowledge base ID is required.")
  }

  if (!serverApiUrl) {
    throw new Error("Missing server API base URL")
  }

  const url = `${serverApiUrl}/knowledge_base/${knowledgeBaseId}`

  const response = await fetch(url, {
    method: "DELETE",
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Failed to delete knowledge base: ${errorText}`)
  }

  revalidatePath("/app/knowledge-base")
}
