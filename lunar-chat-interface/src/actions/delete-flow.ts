// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { serverApiUrl } from "@/configuration";
import { fetchWithServerAuth } from "@/lib/server-auth";

export type DeleteFlowResult = {
  success: boolean;
  message?: string;
};

export async function deleteFlow(flowId: string): Promise<DeleteFlowResult> {
  if (!serverApiUrl) {
    throw new Error("Server API URL is not configured");
  }

  const response = await fetchWithServerAuth(`${serverApiUrl}/flow/${flowId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    return {
      success: false,
      message: `Failed to delete flow: ${response.status} - ${errorText}`,
    };
  }

  return { success: true };
}
