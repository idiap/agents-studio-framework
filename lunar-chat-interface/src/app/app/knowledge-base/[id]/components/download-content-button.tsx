// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client"

import { useState } from "react"
import { Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { downloadKnowledgeBaseContent } from "@/actions/download-knowledge-base-content"

type DownloadContentButtonProps = {
  contentId: string
  fileName: string
}

export function DownloadContentButton({ contentId, fileName }: DownloadContentButtonProps) {
  const [isDownloading, setIsDownloading] = useState(false)

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const { blob, filename } = await downloadKnowledgeBaseContent(contentId)

      // Create a download link and trigger it
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.success(`Downloaded ${filename}`)
    } catch (error) {
      console.error("Error downloading file:", error)
      toast.error("Failed to download file")
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      className="h-8 w-8"
      onClick={handleDownload}
      disabled={isDownloading}
    >
      <Download className="h-4 w-4 text-muted-foreground hover:text-foreground" />
      <span className="sr-only">Download {fileName}</span>
    </Button>
  )
}
