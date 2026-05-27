// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";
import { buildComparativeReportAction } from "@/actions/build-comparative-report-action";
import Button from "@/components/button";
import { useRouter } from "next/dist/client/components/navigation";
import { useState } from "react";

const BuildReportButton = () => {
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const getReportButtonText = () => {
    if (loading) return "Building Report...";
    if (report) return "Show report";
    return "Build Report";
  };

  const onReportButtonClick = async () => {
    setLoading(true);
    if (report) {
      router.push("/app/report/" + encodeURIComponent(report));
    } else {
      const report = await buildComparativeReportAction();
      setReport(report);
      setLoading(false);
    }
  };
  return (
    <Button onClick={onReportButtonClick} disabled={loading}>
      {getReportButtonText()}
    </Button>
  );
};

export default BuildReportButton;
