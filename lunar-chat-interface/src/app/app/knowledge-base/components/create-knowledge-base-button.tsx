// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client"

import { useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { createKnowledgeBaseAction } from "@/actions/create-knowledge-base"
import type { PropositionMetadataSchemaInput, FileMetadataSchemaInput } from "@/actions/create-knowledge-base"

const propositionSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string(),
})

const fileMetadataSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string(),
})

const formSchema = z.object({
  name: z.string().min(1, "Knowledge base name is required"),
  description: z.string(),
  propositionMetadataSchemas: z.array(propositionSchema),
  fileMetadataSchemas: z.array(fileMetadataSchema),
})

type FormValues = z.infer<typeof formSchema>

const CreateKnowledgeBaseButton: React.FC = () => {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [isOpen, setIsOpen] = useState(false)

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      propositionMetadataSchemas: [],
      fileMetadataSchemas: [],
    },
  })

  const resetForm = () => {
    form.reset()
  }

  const onSubmit = (values: FormValues) => {
    startTransition(async () => {
      try {
        const propositionMetadataSchemas: PropositionMetadataSchemaInput[] | undefined =
          values.propositionMetadataSchemas.length > 0
            ? values.propositionMetadataSchemas
              .filter(schema => schema.name.trim().length > 0)
              .map(schema => ({
                field_name: schema.name.trim(),
                field_description: schema.description.trim().length > 0
                  ? schema.description.trim()
                  : "",
              }))
            : undefined

        const fileMetadataSchemas: FileMetadataSchemaInput[] | undefined =
          values.fileMetadataSchemas.length > 0
            ? values.fileMetadataSchemas
              .filter(schema => schema.name.trim().length > 0)
              .map(schema => ({
                field_name: schema.name.trim(),
                field_description: schema.description.trim().length > 0
                  ? schema.description.trim()
                  : "",
              }))
            : undefined

        await createKnowledgeBaseAction({
          name: values.name,
          description: values.description && values.description.length > 0
            ? values.description
            : undefined,
          proposition_metadata_schemas: propositionMetadataSchemas,
          file_metadata_schemas: fileMetadataSchemas,
        })

        toast("Knowledge base created", {
          description: `${values.name} is ready to use.`,
        })

        resetForm()
        setIsOpen(false)
        router.refresh()
      } catch (error) {
        console.error("Failed to create knowledge base", error)
        toast("Create failed", {
          description:
            error instanceof Error ? error.message : "Unexpected error occurred.",
        })
      }
    })
  }

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      resetForm()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>New Knowledge Base</Button>
      </DialogTrigger>
      <DialogContent showCloseButton={!isPending}>
        <Form {...form}>
          <form className="space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>Create knowledge base</DialogTitle>
              <DialogDescription>
                Add a new knowledge base to organize your documents.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Regulatory insights"
                        autoFocus
                        disabled={isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Description <span className="text-muted-foreground">(optional)</span>
                    </FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Summaries for compliance documents and legal research."
                        rows={3}
                        disabled={isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
                disabled={isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default CreateKnowledgeBaseButton
