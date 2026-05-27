// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Save, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { updateReport } from "../actions";
import "@uiw/react-md-editor/markdown-editor.css";
import "@uiw/react-markdown-preview/markdown.css";

// Dynamically import MDEditor to avoid SSR issues
const MDEditor = dynamic(() => import("@uiw/react-md-editor"), { ssr: false });

interface ReportEditorProps {
  reportId: string;
  initialName: string;
  initialContent: string;
}

export default function ReportEditor({
  reportId,
  initialName,
  initialContent,
}: ReportEditorProps) {
  const [name, setName] = useState(initialName);
  const [content, setContent] = useState(initialContent);
  const [hasChanges, setHasChanges] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  const handleSave = useCallback(async () => {
    if (!hasChanges) return;

    startTransition(async () => {
      const result = await updateReport({
        reportId,
        name,
        content,
      });

      if (result.success) {
        setHasChanges(false);
        setLastSaved(new Date());
      } else {
        console.error("Failed to save:", result.error);
      }
    });
  }, [reportId, name, content, hasChanges]);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
    setHasChanges(true);
  };

  const handleContentChange = (value: string | undefined) => {
    setContent(value || "");
    setHasChanges(true);
  };

  // Keyboard shortcut for save
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleSave]);

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b bg-white">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/app/report/${reportId}`)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Report
          </Button>
          <Input
            value={name}
            onChange={handleNameChange}
            className="text-xl font-semibold border-none shadow-none focus-visible:ring-0 w-[300px]"
            placeholder="Report name..."
          />
        </div>
        <div className="flex items-center gap-4">
          {lastSaved && (
            <span className="text-sm text-muted-foreground">
              Last saved: {lastSaved.toLocaleTimeString()}
            </span>
          )}
          {hasChanges && !isPending && (
            <span className="text-sm text-orange-500">Unsaved changes</span>
          )}
          <Button
            onClick={handleSave}
            disabled={isPending || !hasChanges}
            size="sm"
          >
            {isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden" data-color-mode="light">
        <MDEditor
          value={content}
          onChange={handleContentChange}
          height="100%"
          preview="live"
          visibleDragbar={false}
        />
      </div>
    </div>
  );
}
