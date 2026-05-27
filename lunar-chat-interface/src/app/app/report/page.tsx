// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { serverApiUrl } from "@/configuration";
import ReportsClientPage from "./components/reports-client-page";
import { Report } from "@/models/report";
import { Navbar } from "@/components/navbar";
import PageContainer from "@/components/page-container/page-container";
import { fetchWithServerAuth } from "@/lib/server-auth";

export default async function ReportPage() {
  if (!serverApiUrl) {
    console.error("Missing server API base URL");
    return null;
  }
  
  const response = await fetchWithServerAuth(`${serverApiUrl}/report`, {
    cache: "no-store",
    next: { revalidate: 0 },
  });
  
  if (!response.ok) {
    console.error("Error fetching reports:", response.statusText);
    return null;
  }
  
  const data = await response.json();
  
  const reports: Report[] = Array.isArray(data)
    ? data.map((report: Record<string, unknown>) => ({
        id: String(report.id ?? ""),
        name: String(report.name ?? report.id ?? "untitled"),
        title: String(report.name ?? "Untitled Report"),
        description: "",
        filename: String(report.name ?? "report.html"),
        createdAt: report.created_at ? String(report.created_at) : undefined,
        contentType: report.content_type ? String(report.content_type) as Report["contentType"] : undefined,
        contentTypeId: typeof report.content_type_id === "number" ? report.content_type_id : undefined,
      }))
    : [];

  return (
    <>
      <Navbar title="Agents" />
      <PageContainer>
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold text-foreground">Reports</h1>
        </div>
        <ReportsClientPage reports={reports} />
      </PageContainer>
    </>
  );
}
