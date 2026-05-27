// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { serverApiUrl } from "@/configuration";
import { fetchWithServerAuth } from "@/lib/server-auth";

export async function runFlow(
  flow_id: string,
  input: Record<string, any>,
): Promise<any> {
  if (!serverApiUrl) {
    throw new Error("Server API URL is not configured");
  }

  try {
    const response = await fetchWithServerAuth(`${serverApiUrl}/flow/${flow_id}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to run flow ${flow_id}: ${response.status} - ${errorText}`,
      );
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error("Error running flow:", error);
    throw error;
  }
}
