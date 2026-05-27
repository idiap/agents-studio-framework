// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";
import { useState } from "react";
import { exportMarkdownToDocx } from "@/utils/exportToDocx";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ExportToDocButtonProps {
  reportId: string;
  reportContent: string | null;
}

const ExportToDocButton: React.FC<ExportToDocButtonProps> = ({
  reportId,
  reportContent,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const handleExportToDocx = async () => {
    if (!reportContent) return;
    setIsExporting(true);
    try {
      // Remove variable placeholders like {{variable_name}} but keep chart tags
      const contentWithoutVariables = reportContent.replace(
        /\{\{[^}]+\}\}/g,
        "[Chart/Visual Component]"
      );
      const filename = `${reportId}_${
        new Date().toISOString().split("T")[0]
      }.docx`;
      await exportMarkdownToDocx(contentWithoutVariables, filename);
    } catch (error) {
      console.error("Error exporting to DOCX:", error);
      alert("Failed to export report. Please try again.");
    } finally {
      setIsExporting(false);
    }
  };
  return (
    <Button
      onClick={handleExportToDocx}
      disabled={isExporting}
      title="Export to DOCX"
    >
      <Download className="w-4 h-4" />
      {isExporting ? "Exporting..." : "Export DOCX"}
    </Button>
  );
};

export default ExportToDocButton;
