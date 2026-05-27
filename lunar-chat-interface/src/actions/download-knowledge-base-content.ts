// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server"

import { serverApiUrl } from "@/configuration"

export async function downloadKnowledgeBaseContent(contentId: string) {
  if (!serverApiUrl) {
    throw new Error("Missing server API base URL")
  }

  try {
    const response = await fetch(`${serverApiUrl}/knowledge_base/content/${contentId}/download`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("File not found")
      }
      throw new Error(`Failed to download file: ${response.status}`)
    }

    // Get the file content as blob
    const blob = await response.blob()
    
    // Get filename from Content-Disposition header
    const contentDisposition = response.headers.get("Content-Disposition")
    let filename = "download"
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    return {
      blob,
      filename,
      contentType: response.headers.get("Content-Type") || "application/octet-stream",
    }
  } catch (error) {
    console.error("Error downloading file:", error)
    throw error
  }
}
