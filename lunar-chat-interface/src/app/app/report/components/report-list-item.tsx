// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Report } from "@/models/report";
import { ListItem } from "@/components/list-item";
import { DeleteButton } from "@/components/delete-button";
import { deleteReportAction } from "@/actions/delete-report";
import { FileText, FileCode, FileType } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface ReportListItemProps {
  report: Report;
}

function getContentTypeIcon(contentType?: string) {
  switch (contentType) {
    case "html":
      return <FileCode className="w-4 h-4 text-white" />;
    case "markdown":
      return <FileText className="w-4 h-4 text-white" />;
    case "latex":
      return <FileType className="w-4 h-4 text-white" />;
    default:
      return <FileText className="w-4 h-4 text-white" />;
  }
}

export default function ReportListItem({ report }: ReportListItemProps) {
  return (
    <ListItem
      title={report.name}
      description={
        <div className="flex items-center gap-2">
          <span>{report.description}</span>
          {report.contentType && (
            <Badge variant="outline">{report.contentType.toUpperCase()}</Badge>
          )}
        </div>
      }
      date={report.createdAt}
      href={`/app/report/${report.id}`}
      icon={getContentTypeIcon(report.contentType)}
      actions={
        <DeleteButton
          title="Delete Report"
          description={`Are you sure you want to delete "${report.name}"? This action cannot be undone.`}
          onDelete={() => deleteReportAction(report.id)}
          successMessage="Report deleted successfully"
          errorMessage="Failed to delete report"
        />
      }
    />
  );
}
