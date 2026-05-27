// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ReportsFilters } from "@/app/app/report/components/reports-filters";
import { useState, useMemo } from "react";
import { Report } from "@/models/report";
import ReportListItem from "./report-list-item";

interface ReportsClientPageProps {
  reports: Report[];
}

export default function ReportsClientPage({ reports }: ReportsClientPageProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [sortBy, setSortBy] = useState("newest");

  // Filter and sort reports based on state
  const filteredReports = useMemo(() => {
    let filtered = [...reports];

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(
        (report) =>
          report.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          report.description.toLowerCase().includes(searchTerm.toLowerCase()),
      );
    }

    // Filter by type
    if (filterType !== "all") {
      filtered = filtered.filter((report) => {
        const title = report.title.toLowerCase();
        switch (filterType) {
          case "market":
            return title.includes("market") || title.includes("analysis");
          case "portfolio":
            return title.includes("portfolio") || title.includes("performance");
          case "risk":
            return title.includes("risk") || title.includes("assessment");
          case "comparative":
            return (
              title.includes("comparative") || title.includes("comparison")
            );
          default:
            return true;
        }
      });
    }

    // Sort reports
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "newest":
          return parseInt(b.filename) - parseInt(a.filename);
        case "oldest":
          return parseInt(a.filename) - parseInt(b.filename);
        case "title":
          return a.title.localeCompare(b.title);
        case "type":
          return a.title.localeCompare(b.title);
        default:
          return 0;
      }
    });

    return filtered;
  }, [reports, searchTerm, filterType, sortBy]);

  return (
    <div className="relative flex flex-col max-w-300 w-full gap-8 h-[calc(100%)] mb-0 mr-auto ml-auto pt-4">
      <div className="grid gap-4">
        <ReportsFilters
          onSearchChange={setSearchTerm}
          onFilterChange={setFilterType}
          onSortChange={setSortBy}
          totalReports={filteredReports.length}
        />
        <div className="gap-4">
          {filteredReports.map((report) => (
            <ReportListItem key={report.id} report={report} />
          ))}
        </div>
      </div>

      {filteredReports.length === 0 && searchTerm && (
        <Card className="flex flex-col items-center justify-center py-12">
          <CardContent className="text-center">
            <h3 className="text-lg font-semibold mb-2">No reports found</h3>
            <p className="text-muted-foreground mb-4">
              No reports match your search criteria. Try adjusting your filters.
            </p>
            <Button
              variant="outline"
              onClick={() => {
                setSearchTerm("");
                setFilterType("all");
              }}
            >
              Clear Filters
            </Button>
          </CardContent>
        </Card>
      )}

      {filteredReports.length === 0 && !searchTerm && reports.length === 0 && (
        <Card className="flex flex-col items-center justify-center py-12">
          <CardContent className="text-center">
            <h3 className="text-lg font-semibold mb-2">No reports yet</h3>
            <p className="text-muted-foreground mb-4">
              Get started by generating your first report
            </p>
            <Button>Generate Report</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
