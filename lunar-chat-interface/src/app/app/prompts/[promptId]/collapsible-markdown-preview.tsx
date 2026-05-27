// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import React, { useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { ChevronDown, ChevronRight } from "lucide-react";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";

const MarkdownPreview = dynamic(() => import("@uiw/react-markdown-preview"), {
  ssr: false,
});

/**
 * Extend the default sanitization schema to allow className on code/span
 * (needed for syntax highlighting) while still stripping unknown tags
 * like <short>, <one>, <paste>, <optional>.
 */
const sanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    code: [...(defaultSchema.attributes?.code ?? []), "className"],
    span: [...(defaultSchema.attributes?.span ?? []), "className", "style"],
  },
};

/** Shared props applied to every MarkdownPreview instance */
const sharedPreviewProps = {
  rehypePlugins: [[rehypeSanitize, sanitizeSchema]] as never[],
  style: {
    backgroundColor: "transparent",
    fontSize: "14px",
  },
};

/**
 * A rotating palette of section colors.
 * Each h2 section gets a color from this list (cycling).
 */
const SECTION_COLORS = [
  "#6366f1", // indigo
  "#f59e0b", // amber
  "#10b981", // emerald
  "#ef4444", // red
  "#8b5cf6", // violet
  "#3b82f6", // blue
  "#ec4899", // pink
  "#14b8a6", // teal
  "#f97316", // orange
  "#84cc16", // lime
];

interface MarkdownSection {
  title: string;
  content: string;
  color: string;
}

/**
 * Parse markdown content into sections split by ## headings.
 * Content before the first ## heading is treated as a preamble (rendered directly).
 */
function parseMarkdownSections(markdown: string): {
  preamble: string;
  sections: MarkdownSection[];
} {
  const lines = markdown.split("\n");
  let preamble = "";
  const sections: MarkdownSection[] = [];
  let currentSection: { title: string; lines: string[] } | null = null;
  let colorIndex = 0;

  for (const line of lines) {
    // Match lines that start with exactly "## " (h2 headings)
    const h2Match = line.match(/^##\s+(.+)$/);

    if (h2Match) {
      // Flush previous section
      if (currentSection) {
        sections.push({
          title: currentSection.title,
          content: currentSection.lines.join("\n").trim(),
          color: SECTION_COLORS[colorIndex % SECTION_COLORS.length],
        });
        colorIndex++;
      }

      currentSection = {
        title: h2Match[1].trim(),
        lines: [],
      };
    } else if (currentSection) {
      currentSection.lines.push(line);
    } else {
      preamble += line + "\n";
    }
  }

  // Flush last section
  if (currentSection) {
    sections.push({
      title: currentSection.title,
      content: currentSection.lines.join("\n").trim(),
      color: SECTION_COLORS[colorIndex % SECTION_COLORS.length],
    });
  }

  return { preamble: preamble.trim(), sections };
}

function CollapsibleSection({
  section,
  defaultOpen = true,
}: {
  section: MarkdownSection;
  defaultOpen?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div
      className="mb-3 rounded-lg border overflow-hidden"
      style={{ borderColor: `${section.color}30` }}
    >
      {/* Collapsible trigger */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-full flex items-center gap-2 px-4 py-3 text-left transition-colors hover:bg-gray-50"
        style={{ backgroundColor: `${section.color}08` }}
      >
        <span
          className="flex items-center justify-center w-5 h-5 rounded transition-transform"
          style={{ color: section.color }}
        >
          {isOpen ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </span>
        <span
          className="font-semibold text-base"
          style={{ color: section.color }}
        >
          {section.title}
        </span>
      </button>

      {/* Collapsible content */}
      {isOpen && (
        <div className="flex">
          {/* Colored bar */}
          <div
            className="w-1 shrink-0"
            style={{ backgroundColor: section.color }}
          />

          {/* Markdown content */}
          <div
            className="flex-1 px-4 py-3 min-w-0 overflow-hidden [&_pre]:overflow-x-auto [&_pre]:max-w-full"
            data-color-mode="light"
          >
            {section.content ? (
              <MarkdownPreview
                source={section.content}
                {...sharedPreviewProps}
              />
            ) : (
              <p className="text-sm text-muted-foreground italic">
                No content in this section.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface CollapsibleMarkdownPreviewProps {
  source: string;
}

export default function CollapsibleMarkdownPreview({
  source,
}: CollapsibleMarkdownPreviewProps) {
  const { preamble, sections } = useMemo(
    () => parseMarkdownSections(source),
    [source],
  );

  // If there are no h2 sections, render as a regular markdown preview
  if (sections.length === 0) {
    return (
      <div
        className="h-full p-4 overflow-hidden [&_pre]:overflow-x-auto [&_pre]:max-w-full"
        data-color-mode="light"
      >
        <MarkdownPreview source={source} {...sharedPreviewProps} />
      </div>
    );
  }

  return (
    <div className="p-4 overflow-hidden">
      {/* Preamble (content before the first ## heading) */}
      {preamble && (
        <div
          className="mb-4 overflow-hidden [&_pre]:overflow-x-auto [&_pre]:max-w-full"
          data-color-mode="light"
        >
          <MarkdownPreview source={preamble} {...sharedPreviewProps} />
        </div>
      )}

      {/* Collapsible sections */}
      {sections.map((section, index) => (
        <CollapsibleSection key={index} section={section} />
      ))}
    </div>
  );
}
