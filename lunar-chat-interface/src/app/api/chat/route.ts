// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { serverApiUrl } from "@/configuration";

export async function POST(req: Request) {
  try {
    const body = await req.text();

    const response = await fetch(`${serverApiUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body,
    });

    // Stream the SSE response back to the client
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        ...Object.fromEntries(response.headers.entries()),
      },
    });
  } catch (error) {
    console.error("Error proxying chat request:", error);
    return new Response(JSON.stringify({ error: "Failed to proxy request" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
