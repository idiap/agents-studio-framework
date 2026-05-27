// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import Image from "next/image";
import ExportToDocButton from "./export-to-doc-button";
import EditReportButton from "./edit-report-button";
import ProvenanceButton from "./provenance-button";
import ReportContent from "./report-content";
import NoReportFound from "./no-report-found";
import HtmlReportContent from "./html-report-content";
import { serverApiUrl } from "@/configuration";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchWithServerAuth } from "@/lib/server-auth";

interface DatabaseReportProps {
  reportId: string;
  version?: number;
}

const DatabaseReport: React.FC<DatabaseReportProps> = async ({
  reportId,
  version,
}) => {
  const url =
    version !== undefined
      ? `${serverApiUrl}/report/${reportId}?version=${version}`
      : `${serverApiUrl}/report/${reportId}`;
  const response = await fetchWithServerAuth(url, {
    cache: "no-store",
    method: "GET",
  });
  if (!response.ok) {
    console.error("Error response:", response);
    throw new Error("Failed to load report");
  }
  const reportJson = await response.json();
  const content = reportJson.content;
  const contentType = reportJson.content_type;
  const currentVersion = reportJson.version;
  const isHistoricalVersion =
    version !== undefined && version !== currentVersion;

  if (!content) {
    return <NoReportFound />;
  }

  // Render HTML content in an iframe for isolation
  if (contentType === "html") {
    return <HtmlReportContent content={content} reportId={reportId} />;
  }

  // Render markdown/other content types with the standard report layout
  return (
    <div className="container mx-auto px-6 pb-6 max-w-4xl">
      {isHistoricalVersion && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-amber-800">
              You are viewing version {version} (current is v{currentVersion})
            </span>
          </div>
          <Link href={`/app/report/${reportId}`}>
            <Button variant="outline" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to current version
            </Button>
          </Link>
        </div>
      )}
      <div className="flex items-center mb-4">
        <ExportToDocButton reportId={reportId} reportContent={content} />
        {!isHistoricalVersion && (
          <>
            <EditReportButton reportId={reportId} />
            <ProvenanceButton reportId={reportId} />
          </>
        )}
        {isHistoricalVersion && <ProvenanceButton reportId={reportId} />}
      </div>
      <div className="bg-white shadow-lg rounded-lg">
        {process.env.NEXT_PUBLIC_WORKSPACE === "icebrook" && (
          <div className="border-b border-gray-200 bg-linear-to-r from-slate-50 to-gray-50 px-8 py-6">
            <div className="flex items-center justify-between">
              <div className="flex-1 flex items-center justify-center">
                <Image
                  src="/logo.png"
                  alt="Company Logo"
                  width={200}
                  height={60}
                  className="h-12 w-auto object-contain"
                  priority
                />
              </div>
            </div>
            <div className="text-center mt-4">
              <h1 className="text-2xl font-semibold text-gray-800">
                Investment Report
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Generated on {new Date().toLocaleDateString()}
              </p>
            </div>
          </div>
        )}
        <ReportContent reportContent={content} />
      </div>
    </div>
  );
};

export default DatabaseReport;
