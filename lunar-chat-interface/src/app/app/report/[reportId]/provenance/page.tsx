// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { notFound } from "next/navigation";
import { serverApiUrl } from "@/configuration";
import { Provenance } from "@/types/provenance";
import { ProvenanceGraph } from "@/components/provenance/provenance-graph";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchWithServerAuth } from "@/lib/server-auth";

interface ReportProvenancePageProps {
  params: Promise<{
    reportId: string;
  }>;
}

interface ProvenanceResponse {
  report_id: string;
  manifest: Record<string, unknown>;
  view_model: Record<string, unknown>;
  versions: Array<{
    version: number;
    content: string;
    created_at: string;
    username: string;
    step_id?: string;
    note?: string;
    diff_stats?: Record<string, number>;
  }>;
}

async function getReportProvenance(
  reportId: string
): Promise<ProvenanceResponse | null> {
  try {
    const response = await fetchWithServerAuth(
      `${serverApiUrl}/report/${reportId}/provenance`,
      {
        cache: "no-store",
        method: "GET",
      }
    );

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error("Failed to fetch report provenance");
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching report provenance:", error);
    throw error;
  }
}

export default async function ReportProvenancePage({
  params,
}: ReportProvenancePageProps) {
  const { reportId } = await params;
  const provenanceData = await getReportProvenance(reportId);

  if (!provenanceData) {
    notFound();
  }

  // Convert to Provenance type for the graph component
  const provenance: Provenance = {
    manifest: {
      base_uri: (provenanceData.manifest.base_uri as string) || "",
      flow_id: (provenanceData.manifest.report_id as string) || reportId,
      run_id: (provenanceData.manifest.run_id as string) || "",
      bundles: {},
      generated_at: (provenanceData.manifest.created_at as string) || "",
      bundle_hashes: {},
    },
    trig: "",
    view_model:
      provenanceData.view_model as unknown as Provenance["view_model"],
  };

  const versions = provenanceData.versions || [];

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href={`/app/report/${reportId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Report
            </Button>
          </Link>
          <h1 className="text-2xl font-semibold text-gray-800">
            Report Provenance
          </h1>
        </div>
      </div>

      {/* Version History Summary */}
      <div className="bg-white shadow-lg rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Version History
        </h2>
        <div className="space-y-2">
          {versions.length === 0 ? (
            <p className="text-gray-500">No version history available</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Version
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Author
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Changes
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Note
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {versions.map((version) => (
                    <tr
                      key={version.version}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-2 whitespace-nowrap text-sm">
                        <Link
                          href={`/app/report/${reportId}?version=${version.version}`}
                          className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                        >
                          v{version.version}
                        </Link>
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                        {new Date(version.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                        {version.username}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                        {version.diff_stats ? (
                          <span>
                            <span className="text-green-600">
                              +{version.diff_stats.lines_added}
                            </span>
                            {" / "}
                            <span className="text-red-600">
                              -{version.diff_stats.lines_removed}
                            </span>
                          </span>
                        ) : (
                          <span className="text-gray-400">Initial</span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-500 max-w-xs truncate">
                        {version.note || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Provenance Graph */}
      <div className="bg-white shadow-lg rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Provenance Graph
        </h2>
        <ProvenanceGraph provenance={provenance} />
      </div>
    </div>
  );
}
