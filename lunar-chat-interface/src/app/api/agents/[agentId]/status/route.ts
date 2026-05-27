// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { serverApiUrl } from "@/configuration";
import { getAuthHeaders } from "@/lib/server-auth";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ agentId: string }> },
) {
  try {
    const { agentId } = await params;
    if (!agentId) {
      return new Response(
        JSON.stringify({ error: `Unknown agent: ${agentId}` }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    const headers = await getAuthHeaders({
      "Content-Type": "application/json",
    });
    const response = await fetch(
      `${serverApiUrl}/flow/${agentId}/status`,
      {
        method: "GET",
        headers,
        cache: "no-store",
      },
    );

    if (!response.ok) {
      return new Response(
        JSON.stringify({ error: "Failed to fetch status from backend" }),
        {
          status: response.status,
          headers: { "Content-Type": "application/json" },
        },
      );
    }

    const data = await response.json();

    return new Response(JSON.stringify(data), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store, must-revalidate",
      },
    });
  } catch (error) {
    console.error("Error proxying agent status request:", error);
    return new Response(
      JSON.stringify({ error: "Failed to proxy status request" }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
}
