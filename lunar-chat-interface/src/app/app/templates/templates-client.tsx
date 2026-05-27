// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Plus, FileText } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { createTemplate, deleteTemplate } from "./actions";
import { ListItem } from "@/components/list-item";
import { DeleteButton } from "@/components/delete-button";

interface Template {
  id: string;
  name: string;
  content: string;
  agent: string | null;
  created_at: string;
  updated_at: string;
}

interface TemplatesClientProps {
  initialTemplates: Template[];
}

export function TemplatesClient({ initialTemplates }: TemplatesClientProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [newTemplateName, setNewTemplateName] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  const handleCreateTemplate = async () => {
    if (!newTemplateName.trim()) return;

    startTransition(async () => {
      try {
        const created = await createTemplate(newTemplateName.trim());
        setNewTemplateName("");
        setIsCreateDialogOpen(false);
        if (created && created.id) {
          router.push(`/app/templates/${created.id}`);
        }
      } catch (error) {
        alert("Failed to create template. Please try again.");
      }
    });
  };

  const filteredTemplates = initialTemplates.filter((template) =>
    template.name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <>
      <div className="grid gap-4">
        <div className="flex items-center gap-4 justify-between">
          <Input
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
          <div className="flex items-center justify-between">
            <Dialog
              open={isCreateDialogOpen}
              onOpenChange={setIsCreateDialogOpen}
            >
              <DialogTrigger asChild>
                <Button disabled={isPending}>
                  <Plus className="w-4 h-4 mr-2" />
                  New Template
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Template</DialogTitle>
                  <DialogDescription>
                    Enter a name for your new template. You can edit the content
                    after creation.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Template Name</Label>
                    <Input
                      id="name"
                      value={newTemplateName}
                      onChange={(e) => setNewTemplateName(e.target.value)}
                      placeholder="Enter template name..."
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleCreateTemplate();
                        }
                      }}
                      disabled={isPending}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setIsCreateDialogOpen(false)}
                    disabled={isPending}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreateTemplate}
                    disabled={isPending || !newTemplateName.trim()}
                  >
                    {isPending ? "Creating..." : "Create Template"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <div>
          {filteredTemplates.map((template) => (
            <ListItem
              key={template.id}
              title={template.name}
              description={template.content.substring(0, 100) + (template.content.length > 100 ? "..." : "")}
              date={template.updated_at}
              href={`/app/templates/${template.id}`}
              icon={<FileText className="w-4 h-4 text-white" />}
              actions={
                <DeleteButton
                  title="Delete Template"
                  description={`Are you sure you want to delete "${template.name}"? This action cannot be undone.`}
                  onDelete={() => deleteTemplate(template.id)}
                  successMessage="Template deleted successfully"
                  errorMessage="Failed to delete template"
                />
              }
            />
          ))}
        </div>
      </div>

      {filteredTemplates.length === 0 && searchTerm && (
        <Card className="flex flex-col items-center justify-center py-12">
          <CardContent className="text-center">
            <h3 className="text-lg font-semibold mb-2">No templates found</h3>
            <p className="text-muted-foreground mb-4">
              No templates match your search criteria.
            </p>
            <Button variant="outline" onClick={() => setSearchTerm("")}>
              Clear Search
            </Button>
          </CardContent>
        </Card>
      )}

      {initialTemplates.length === 0 && !searchTerm && (
        <Card className="flex flex-col items-center justify-center py-12">
          <CardContent className="text-center">
            <h3 className="text-lg font-semibold mb-2">No templates yet</h3>
            <p className="text-muted-foreground mb-4">
              Get started by creating your first template
            </p>
            <Button
              onClick={() => setIsCreateDialogOpen(true)}
              disabled={isPending}
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Template
            </Button>
          </CardContent>
        </Card>
      )}
    </>
  );
}
