// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { serverApiUrl } from "@/configuration";
import { getAuthHeaders } from "@/lib/server-auth";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ agentId: string }> },
) {
  try {
    const { agentId } = await params;
    if (!agentId) {
      return new Response(JSON.stringify({ error: `Agent ID is required` }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const headers = await getAuthHeaders({
      "Content-Type": "application/json",
    });
    const response = await fetch(`${serverApiUrl}/flow/${agentId}/cancel`, {
      method: "POST",
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return new Response(
        JSON.stringify({
          error: errorData.detail || "Failed to cancel agent",
          status: response.status,
        }),
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
      },
    });
  } catch (error) {
    console.error("Error cancelling agent:", error);
    return new Response(JSON.stringify({ error: "Failed to cancel agent" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
