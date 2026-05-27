// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

/**
 * Prompt variable utilities.
 *
 * Variables are declared using `{variableName}` syntax.
 * Rules:
 *  - Must start with a letter (a-z, A-Z)
 *  - May contain letters, digits (0-9) and underscores (_)
 *  - Case-sensitive
 *  - Escaped braces `{{` / `}}` are ignored
 */

const VARIABLE_RE = /(?<!\{)\{([A-Za-z][A-Za-z0-9_]*)\}(?!\})/g;

/**
 * Extract all unique variable names from a prompt template string.
 */
export function extractVariables(template: string): string[] {
  const seen = new Set<string>();
  let match: RegExpExecArray | null;
  // Reset lastIndex because the regex is global
  VARIABLE_RE.lastIndex = 0;
  while ((match = VARIABLE_RE.exec(template)) !== null) {
    seen.add(match[1]);
  }
  return Array.from(seen);
}
