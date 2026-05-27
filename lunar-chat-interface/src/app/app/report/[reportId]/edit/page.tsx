// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { notFound } from "next/navigation";
import { serverApiUrl } from "@/configuration";
import ReportEditor from "./components/report-editor";
import { fetchWithServerAuth } from "@/lib/server-auth";

interface ReportEditorPageProps {
  params: Promise<{
    reportId: string;
  }>;
}

interface Report {
  id: string;
  name: string;
  content: string;
  created_at: string;
  provenance_data?: Record<string, unknown> | null;
}

async function getReport(reportId: string): Promise<Report | null> {
  try {
    const response = await fetchWithServerAuth(`${serverApiUrl}/report/${reportId}`, {
      cache: "no-store",
      method: "GET",
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error("Failed to fetch report");
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching report:", error);
    throw error;
  }
}

export default async function ReportEditorPage({
  params,
}: ReportEditorPageProps) {
  const { reportId } = await params;
  const report = await getReport(reportId);

  if (!report) {
    notFound();
  }

  return (
    <ReportEditor
      reportId={reportId}
      initialName={report.name}
      initialContent={report.content}
    />
  );
}
