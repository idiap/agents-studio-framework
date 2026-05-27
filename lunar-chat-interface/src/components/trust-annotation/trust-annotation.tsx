// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import React, { ReactNode } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Shield, ShieldAlert, ShieldCheck } from "lucide-react";

/**
 * Trust annotation data parsed from markdown comments.
 */
export interface TrustAnnotationData {
  componentId: string;
  trustIndex: number;
  confidence: number;
  band?: "green" | "amber" | "red";
  risk?: number;
  stepKind?: string;
}

/**
 * Parsed annotation block with content.
 */
export interface ParsedAnnotation {
  annotation: TrustAnnotationData;
  content: string;
  startPos: number;
  endPos: number;
}

// Regex patterns for parsing trust annotations
const TRUST_START_PATTERN =
  /<!--\s*lunar\/component-id=(\S+)\s+lunar\/trust-start=(\d+)\/100\s+lunar\/confidence=(\d+)(?:\s+lunar\/band=(\S+))?(?:\s+lunar\/risk=([\d.]+))?(?:\s+lunar\/step-kind=(\S+))?.*?-->/g;
const TRUST_END_PATTERN = /<!--\s*lunar\/trust-end\s*-->/g;

/**
 * Parse a single trust annotation from text.
 */
function parseAnnotationBlock(
  text: string,
  startMatch: RegExpMatchArray,
  startIndex: number
): ParsedAnnotation | null {
  // Find the corresponding end tag
  const afterStart = text.slice(startIndex + startMatch[0].length);
  const endMatch = afterStart.match(/<!--\s*lunar\/trust-end\s*-->/);

  if (!endMatch || endMatch.index === undefined) {
    return null;
  }

  const contentStart = startIndex + startMatch[0].length;
  const contentEnd = contentStart + endMatch.index;
  const content = text.slice(contentStart, contentEnd).trim();

  return {
    annotation: {
      componentId: startMatch[1],
      trustIndex: parseInt(startMatch[2], 10),
      confidence: parseInt(startMatch[3], 10),
      band: (startMatch[4] as "green" | "amber" | "red") || "amber",
      risk: startMatch[5] ? parseFloat(startMatch[5]) : undefined,
      stepKind: startMatch[6] || undefined,
    },
    content,
    startPos: startIndex,
    endPos: contentEnd + endMatch[0].length,
  };
}

/**
 * Parse all trust annotations from text.
 */
export function parseAllAnnotations(text: string): ParsedAnnotation[] {
  const results: ParsedAnnotation[] = [];
  const startPattern = new RegExp(TRUST_START_PATTERN.source, "g");

  let match;
  while ((match = startPattern.exec(text)) !== null) {
    const parsed = parseAnnotationBlock(text, match, match.index);
    if (parsed) {
      results.push(parsed);
      // Skip past this block to avoid nested matching issues
      startPattern.lastIndex = parsed.endPos;
    }
  }

  return results;
}

/**
 * Strip all trust annotations from text, keeping only the content.
 */
export function stripAnnotations(text: string): string {
  let result = text;

  // Keep replacing until no more annotations found
  let prevLength = -1;
  while (result.length !== prevLength) {
    prevLength = result.length;
    const annotations = parseAllAnnotations(result);
    if (annotations.length === 0) break;

    // Replace from end to start to preserve indices
    for (let i = annotations.length - 1; i >= 0; i--) {
      const { content, startPos, endPos } = annotations[i];
      result = result.slice(0, startPos) + content + result.slice(endPos);
    }
  }

  return result;
}

/**
 * Get the trust band color for styling.
 */
function getBandColor(band: "green" | "amber" | "red" | undefined): string {
  switch (band) {
    case "green":
      return "text-green-600 bg-green-50 border-green-200";
    case "red":
      return "text-red-600 bg-red-50 border-red-200";
    case "amber":
    default:
      return "text-amber-600 bg-amber-50 border-amber-200";
  }
}

/**
 * Get the shield icon based on trust band.
 */
function getShieldIcon(band: "green" | "amber" | "red" | undefined) {
  switch (band) {
    case "green":
      return <ShieldCheck className="w-4 h-4" />;
    case "red":
      return <ShieldAlert className="w-4 h-4" />;
    case "amber":
    default:
      return <Shield className="w-4 h-4" />;
  }
}

interface TrustIndicatorButtonProps {
  annotation: TrustAnnotationData;
}

/**
 * An icon button that opens a modal with trust information.
 */
export const TrustIndicatorButton: React.FC<TrustIndicatorButtonProps> = ({
  annotation,
}) => {
  const bandColor = getBandColor(annotation.band);
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className={`absolute -left-8 top-0 rounded-full p-1 border ${bandColor} opacity-70 hover:opacity-100 transition-opacity`}
          aria-label="View trust indicators"
        >
          {getShieldIcon(annotation.band)}
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getShieldIcon(annotation.band)}
            Trust Indicators
          </DialogTitle>
          <DialogDescription>
            Details for this annotated section.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <span className="text-gray-500">Component:</span>
            <p className="font-mono text-xs">{annotation.componentId}</p>

            <span className="text-gray-500">Trust:</span>
            <p className={bandColor.split(" ")[0]}>
              {annotation.trustIndex}/100
            </p>

            <span className="text-gray-500">Confidence:</span>
            <p>{annotation.confidence}%</p>

            {annotation.stepKind && (
              <>
                <span className="text-gray-500">Step Type:</span>
                <p className="font-mono text-xs">{annotation.stepKind}</p>
              </>
            )}

            {annotation.risk !== undefined && (
              <>
                <span className="text-gray-500">Risk:</span>
                <p>{(annotation.risk * 100).toFixed(1)}%</p>
              </>
            )}
          </div>
          <div
            className={`text-xs px-2 py-1 rounded ${bandColor} inline-block`}
          >
            {annotation.band === "green"
              ? "High Trust"
              : annotation.band === "red"
              ? "Low Trust - Review Recommended"
              : "Moderate Trust"}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

interface TrustAnnotatedSectionProps {
  annotation: TrustAnnotationData;
  children: ReactNode;
}

/**
 * A wrapper component that adds trust visualization to a section.
 */
export const TrustAnnotatedSection: React.FC<TrustAnnotatedSectionProps> = ({
  annotation,
  children,
}) => {
  const bandColor = getBandColor(annotation.band);

  return (
    <div className="relative">
      <div className="absolute -left-3.5 top-0 bottom-0 w-8 flex items-start pt-1 z-10">
        <TrustIndicatorButton annotation={annotation} />
      </div>
      {children}
    </div>
  );
};

export default TrustAnnotatedSection;
