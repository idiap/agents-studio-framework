// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import React, { useState, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Save, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { updateTemplate } from "../actions";
import "@uiw/react-md-editor/markdown-editor.css";
import "@uiw/react-markdown-preview/markdown.css";

// Dynamically import MDEditor to avoid SSR issues
const MDEditor = dynamic(() => import("@uiw/react-md-editor"), { ssr: false });

interface Template {
  id: string;
  name: string;
  content: string;
  agent: string | null;
  created_at: string;
  updated_at: string;
}

interface TemplateEditorProps {
  template: Template;
}

function TemplateEditor({ template }: TemplateEditorProps) {
  const [name, setName] = useState(template.name);
  const [content, setContent] = useState(template.content);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const router = useRouter();

  const handleSave = useCallback(async () => {
    if (!hasChanges) return;

    setSaving(true);
    try {
      await updateTemplate(template.id, { name, content });
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to save template:", error);
      alert("Failed to save template. Please try again.");
    } finally {
      setSaving(false);
    }
  }, [template.id, name, content, hasChanges]);

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
    setHasChanges(true);
  };

  const handleContentChange = (value: string | undefined) => {
    setContent(value || "");
    setHasChanges(true);
  };

  // Keyboard shortcut for save (Cmd/Ctrl + S)
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
            onClick={() => router.push("/app/templates")}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <Input
            value={name}
            onChange={handleNameChange}
            className="text-xl font-semibold border-none shadow-none focus-visible:ring-0 w-[300px]"
            placeholder="Template name..."
          />
        </div>
        <div className="flex items-center gap-4">
          {hasChanges && !saving && (
            <span className="text-sm text-orange-500">Unsaved changes</span>
          )}
          <Button
            onClick={handleSave}
            disabled={saving || !hasChanges}
            size="sm"
          >
            {saving ? (
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

export default TemplateEditor;
