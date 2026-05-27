// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Report } from "@/models/report";
import { Calendar } from "lucide-react";

interface ReportCardProps {
  report: Report;
  onViewDetails?: (reportId: string) => void;
}

export function ReportCard({ report, onViewDetails }: ReportCardProps) {
  const handleViewDetails = () => {
    if (onViewDetails) {
      onViewDetails(report.filename);
    }
  };

  return (
    <Card
      className="hover:shadow-md transition-shadow cursor-pointer group flex flex-col h-full"
      onClick={handleViewDetails}
    >
      <CardHeader className="flex-1">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <CardTitle className="text-lg group-hover:text-primary transition-colors">
              {report.title}
            </CardTitle>
            <CardDescription className="line-clamp-2">
              {report.description}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      {report.createdAt && (
        <CardFooter className="mt-auto">
          <div className="flex items-center justify-between pt-2 border-t w-full">
            <div className="flex items-center text-xs text-muted-foreground">
              <>
                <Calendar className="w-3 h-3 mr-1" />
                {new Date(report.createdAt).toLocaleDateString()} •{" "}
                {new Date(report.createdAt).toLocaleTimeString()}
              </>
            </div>
          </div>
        </CardFooter>
      )}
    </Card>
  );
}
