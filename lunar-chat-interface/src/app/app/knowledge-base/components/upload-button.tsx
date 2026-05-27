// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client"

import { useRef, useState, type ChangeEvent } from "react"
import { useRouter } from "next/navigation"
import { Loader2, Upload } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { uploadContentToKnowledgeBase } from "@/actions/upload-content-to-knowledge-base"
import type { KnowledgeBaseField } from "@/models/knowledge-base"

interface UploadButtonProps {
  kbId: string
  fields: KnowledgeBaseField[]
}

const UploadButton = ({ kbId, fields }: UploadButtonProps) => {
  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [selectedFieldId, setSelectedFieldId] = useState<string>("")
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])

  const openFilePicker = () => {
    inputRef.current?.click()
  }

  const resetForm = () => {
    if (inputRef.current) {
      inputRef.current.value = ""
    }
    setSelectedFiles([])
    setSelectedFieldId("")
  }

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files) {
      setSelectedFiles(Array.from(files))
    }
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast("No files selected", {
        description: "Please select at least one file to upload.",
      })
      return
    }

    if (!selectedFieldId) {
      toast("No field selected", {
        description: "Please select a field for the files.",
      })
      return
    }

    setIsUploading(true)

    try {
      const result = await uploadContentToKnowledgeBase(kbId, selectedFieldId, selectedFiles)
      if (result.success) {
        toast("Upload complete", {
          description: result.message,
        })
      } else {
        toast("Upload completed with errors", {
          description: `${result.uploadedFiles.length} file(s) uploaded, ${result.failedFiles.length} failed.`,
        })
      }

      setIsOpen(false)
      resetForm()
      router.refresh()
    } catch (error) {
      console.error("Upload failed", error)
      toast("Upload failed", {
        description:
          error instanceof Error ? error.message : "Unexpected error occurred.",
      })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button className="inline-flex h-9 items-center gap-2">
          <Upload className="h-4 w-4" />
          Upload PDFs
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Upload Files</DialogTitle>
          <DialogDescription>
            Select a field and choose one or more PDF files to upload to this knowledge base.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="field">Knowledge Base Field</Label>
            <Select value={selectedFieldId} onValueChange={setSelectedFieldId}>
              <SelectTrigger id="field">
                <SelectValue placeholder="Select a field" />
              </SelectTrigger>
              <SelectContent>
                {fields.length === 0 ? (
                  <div className="p-2 text-sm text-muted-foreground">
                    No fields available
                  </div>
                ) : (
                  fields.map((field) => (
                    <SelectItem key={field.id} value={field.id}>
                      {field.name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="file">PDF Files</Label>
            <input
              ref={inputRef}
              id="file"
              type="file"
              accept="application/pdf"
              multiple
              className="hidden"
              onChange={handleFileChange}
            />
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={openFilePicker}
                className="flex-1"
              >
                {selectedFiles.length > 0
                  ? `${selectedFiles.length} file(s) selected`
                  : "Choose files"}
              </Button>
            </div>
            {selectedFiles.length > 0 && (
              <div className="max-h-32 overflow-y-auto text-xs text-muted-foreground space-y-1">
                {selectedFiles.map((file, index) => (
                  <div key={index}>
                    {file.name} ({(file.size / 1024).toFixed(2)} KB)
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={() => {
              setIsOpen(false)
              resetForm()
            }}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={isUploading || selectedFiles.length === 0 || !selectedFieldId}
          >
            {isUploading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isUploading ? "Uploading..." : "Upload"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default UploadButton