// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { serverApiUrl } from "@/configuration";
import { readFile } from "fs/promises";
import { join } from "path";

export async function POST(request: Request) {
  const body = await request.json();
  const { prompt, ai_model_id } = body;

  if (!prompt || !ai_model_id) {
    return new Response(
      JSON.stringify({ error: "prompt and ai_model_id are required" }),
      { status: 400, headers: { "Content-Type": "application/json" } },
    );
  }

  // Load the improvement template from the Markdown file
  const templatePath = join(
    process.cwd(),
    "src/app/app/prompts/[promptId]/prompt-improvement-template.md",
  );

  let template: string;
  try {
    template = await readFile(templatePath, "utf-8");
  } catch {
    return new Response(
      JSON.stringify({ error: "Failed to load improvement template" }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }

  // Compose the full prompt: system template + user prompt
  const fullPrompt = `${template}\n\n---\n\n## User Prompt to Improve\n\n${prompt}`;

  const response = await fetch(`${serverApiUrl}/prompts/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: fullPrompt,
      ai_model_id,
    }),
  });

  if (!response.ok) {
    return new Response(
      JSON.stringify({ error: "Failed to improve prompt" }),
      {
        status: response.status,
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  // Forward the SSE stream from the backend
  return new Response(response.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
