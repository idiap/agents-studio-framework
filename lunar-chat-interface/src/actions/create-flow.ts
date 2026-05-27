// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { serverApiUrl } from "@/configuration";
import { fetchWithServerAuth } from "@/lib/server-auth";

export type CreateFlowResult = {
  success: boolean;
  message?: string;
  flow?: Record<string, unknown>;
};

export async function createFlow(
  formData: FormData,
): Promise<CreateFlowResult> {
  if (!serverApiUrl) {
    throw new Error("Server API URL is not configured");
  }

  const response = await fetchWithServerAuth(`${serverApiUrl}/flow/create_agent`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    return {
      success: false,
      message: `Failed to create flow: ${response.status} - ${errorText}`,
    };
  }

  const flow = await response.json();
  return { success: true, flow };
}
