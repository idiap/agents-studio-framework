// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { revalidatePath } from "next/cache";
import { serverApiUrl } from "@/configuration";
import { fetchWithServerAuth } from "@/lib/server-auth";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export async function deleteReportAction(reportId: string) {
  if (!serverApiUrl) {
    throw new Error("Server API URL is not configured");
  }

  const response = await fetchWithServerAuth(
    `${serverApiUrl}/report/${reportId}`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    },
  );

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ message: "Failed to delete report" }));
    throw new Error(error.message || "Failed to delete report");
  }

  revalidatePath(`${basePath}/app/report`);
  return await response.json();
}
