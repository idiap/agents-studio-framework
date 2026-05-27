// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server"

import { serverApiUrl } from "@/configuration"
import { revalidatePath } from "next/cache"

export async function uploadContentToKnowledgeBase(
  kbId: string,
  fieldId: string,
  files: File[]
) {
  if (!serverApiUrl) {
    throw new Error("Missing server configuration")
  }

  if (!files || files.length === 0) {
    throw new Error("No files provided")
  }

  if (!kbId) {
    throw new Error("No knowledge base ID provided")
  }

  if (!fieldId) {
    throw new Error("No field ID provided")
  }

  const uploadFormData = new FormData()

  // Append all files to the FormData
  files.forEach((file) => {
    uploadFormData.append("files", file)
  })

  try {
    // Using the correct endpoint: POST /{kb_id}/content with kb_field_id as query parameter
    const url = new URL(`${serverApiUrl}/knowledge_base/${kbId}/content`)
    url.searchParams.append("kb_field_id", fieldId)

    const response = await fetch(url.toString(), {
      method: "POST",
      body: uploadFormData,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(errorText || `Upload failed with status ${response.status}`)
    }

    const result = await response.json()

    // Revalidate the knowledge base page to show the new files
    revalidatePath(`/app/knowledge-base/${kbId}`)

    return {
      success: result.success,
      message: result.message,
      uploadedFiles: result.uploaded_files,
      failedFiles: result.failed_files,
    }
  } catch (error) {
    console.error("Upload failed:", error)
    throw error
  }
}
