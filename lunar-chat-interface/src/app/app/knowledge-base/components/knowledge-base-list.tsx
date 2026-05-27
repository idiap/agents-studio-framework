// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { KnowledgeBase } from "@/models/knowledge-base";
import { ListItem } from "@/components/list-item";
import { DeleteButton } from "@/components/delete-button";
import { deleteKnowledgeBaseAction } from "@/actions/delete-knowledge-base";
import { Database } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface KnowledgeBaseListProps {
  knowledgeBases: KnowledgeBase[];
  error?: string | null;
}

export default function KnowledgeBaseList({
  knowledgeBases,
  error,
}: KnowledgeBaseListProps) {
  if (error) {
    return (
      <Card className="flex flex-col items-center justify-center py-12">
        <CardContent className="text-center space-y-2">
          <p className="text-sm text-destructive">{error}</p>
          <p className="text-sm text-muted-foreground">
            Please try again in a few moments.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!knowledgeBases || knowledgeBases.length === 0) {
    return (
      <Card className="flex flex-col items-center justify-center py-12">
        <CardContent className="text-center space-y-2">
          <p className="text-sm text-muted-foreground">
            No knowledge bases have been created yet.
          </p>
          <p className="text-sm text-muted-foreground">
            Create a knowledge base to start organizing your documents.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div>
      {knowledgeBases.map((kb) => (
        <KnowledgeBaseListItem key={kb.id} knowledgeBase={kb} />
      ))}
    </div>
  );
}

function KnowledgeBaseListItem({
  knowledgeBase,
}: {
  knowledgeBase: KnowledgeBase;
}) {
  return (
    <ListItem
      title={knowledgeBase.name}
      description={knowledgeBase.description}
      href={`/app/knowledge-base/${knowledgeBase.id}`}
      icon={<Database className="w-4 h-4 text-white" />}
      actions={
        <DeleteButton
          title="Delete Knowledge Base"
          description={`Are you sure you want to delete "${knowledgeBase.name}"? This action cannot be undone and will permanently remove the knowledge base and all its associated data.`}
          onDelete={() => deleteKnowledgeBaseAction(knowledgeBase.id)}
          successMessage="Knowledge base deleted successfully"
          errorMessage="Failed to delete knowledge base"
        />
      }
    />
  );
}
