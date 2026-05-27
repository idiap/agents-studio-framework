// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { serverApiUrl } from "@/configuration";
import { revalidatePath } from "next/cache";
import { fetchWithServerAuth } from "@/lib/server-auth";

interface UpdateReportInput {
  reportId: string;
  name?: string;
  content?: string;
}

export async function updateReport({
  reportId,
  name,
  content,
}: UpdateReportInput) {
  try {
    const response = await fetchWithServerAuth(`${serverApiUrl}/report/${reportId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...(name !== undefined && { name }),
        ...(content !== undefined && { content }),
      }),
    });

    if (!response.ok) {
      return { success: false, error: "Failed to update report" };
    }

    const updatedReport = await response.json();

    // Revalidate the report page to show updated content
    revalidatePath(`/app/report/${reportId}`);

    return { success: true, data: updatedReport };
  } catch (error) {
    console.error("Error updating report:", error);
    return {
      success: false,
      error: "An error occurred while updating the report",
    };
  }
}
