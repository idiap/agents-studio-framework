// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { serverApiUrl } from "@/configuration";

export async function POST(request: Request) {
  const body = await request.json();

  const response = await fetch(`${serverApiUrl}/prompts/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    return new Response(JSON.stringify({ error: "Failed to run prompt" }), {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
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
