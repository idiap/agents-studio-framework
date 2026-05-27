// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { serverApiUrl } from "@/configuration";
import type {
  KnowledgeBase,
  KnowledgeBaseField,
} from "@/models/knowledge-base";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import UploadButton from "../components/upload-button";
import { DeleteContentButton } from "../components/delete-content-button";

type PageProps = {
  params: Promise<{
    id: string;
  }>;
};

const KnowledgeBaseDetailPage: React.FC<PageProps> = async ({ params }) => {
  const { id } = await params;

  if (!serverApiUrl) {
    throw new Error("Missing server API base URL");
  }

  // Fetch knowledge base details
  const knowledgeBaseResponse = await fetch(
    `${serverApiUrl}/knowledge_base/${id}`,
    {
      cache: "no-store",
      next: { revalidate: 0 },
    },
  );

  if (!knowledgeBaseResponse.ok) {
    if (knowledgeBaseResponse.status === 404) {
      notFound();
    }
    throw new Error(
      `Failed to fetch knowledge base: ${knowledgeBaseResponse.status}`,
    );
  }

  const kbData = await knowledgeBaseResponse.json();

  const knowledgeBase: KnowledgeBase = {
    id: kbData.id || id,
    name: kbData.name || "Untitled Knowledge Base",
    description: kbData.description || null,
    fields: kbData.fields || [],
  };

  // Fetch fields
  const fieldsResponse = await fetch(
    `${serverApiUrl}/knowledge_base/${id}/fields`,
    {
      cache: "no-store",
      next: { revalidate: 0 },
    },
  );

  if (!fieldsResponse.ok) {
    throw new Error(`Failed to fetch fields: ${fieldsResponse.status}`);
  }

  const fieldsData = await fieldsResponse.json();

  // The API returns Field objects with content array (not contents)
  const fieldsWithContents: KnowledgeBaseField[] = Array.isArray(fieldsData)
    ? fieldsData
    : [];

  const totalFiles = fieldsWithContents.reduce(
    (sum, field) => sum + (field.content_count || 0),
    0,
  );

  return (
    <div className="min-h-screen bg-background">
      <Navbar title="Knowledge base" />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <Link href="/app/knowledge-base">
              <Button variant="ghost" size="icon" className="h-9 w-9">
                <ArrowLeft className="h-5 w-5" />
                <span className="sr-only">Back to knowledge bases</span>
              </Button>
            </Link>
            <h1 className="text-3xl font-semibold text-foreground">
              {knowledgeBase.name}
            </h1>
          </div>
          {knowledgeBase.description && (
            <p className="ml-12 max-w-3xl text-muted-foreground">
              {knowledgeBase.description}
            </p>
          )}
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl">
                  Knowledge Base Contents
                </CardTitle>
                <CardDescription>
                  {totalFiles > 0
                    ? `${totalFiles} file${totalFiles > 1 ? "s" : ""} across ${
                        fieldsWithContents.length
                      } field${fieldsWithContents.length > 1 ? "s" : ""}`
                    : "No files uploaded yet"}
                </CardDescription>
              </div>
              <UploadButton kbId={id} fields={fieldsWithContents} />
            </div>
          </CardHeader>
          <CardContent className="pb-6">
            {fieldsWithContents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <p className="text-muted-foreground">
                  No fields found in this knowledge base.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {fieldsWithContents.map((field) => (
                  <div key={field.id} className="space-y-3">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold">{field.name}</h3>
                      <span className="text-sm text-muted-foreground">
                        ({field.content_count} file
                        {field.content_count !== 1 ? "s" : ""})
                      </span>
                    </div>

                    {field.content && field.content.length > 0 ? (
                      <div className="rounded-lg border">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Name</TableHead>
                              <TableHead className="w-17.5"></TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {field.content.map((contentSummary) => (
                              <TableRow key={contentSummary.id}>
                                <TableCell className="font-medium">
                                  {contentSummary.name}
                                </TableCell>
                                <TableCell>
                                  <DeleteContentButton
                                    contentId={contentSummary.id}
                                    fileName={contentSummary.name}
                                  />
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    ) : (
                      <div className="rounded-lg border border-dashed py-8 text-center">
                        <p className="text-sm text-muted-foreground">
                          No files in this field yet
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default KnowledgeBaseDetailPage;
