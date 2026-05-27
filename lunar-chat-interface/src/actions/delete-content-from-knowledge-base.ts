// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server"

import { serverApiUrl } from "@/configuration"

export async function deleteContentFromKnowledgeBase(contentId: string) {
  if (!serverApiUrl) {
    throw new Error("Missing server API base URL")
  }

  try {
    const response = await fetch(`${serverApiUrl}/knowledge_base/content/${contentId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to delete file: ${response.status}`)
    }

    const data = await response.json()
    return { success: data.success, message: data.message }
  } catch (error) {
    console.error("Error deleting file:", error)
    throw error
  }
}
