// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import React from "react";
import NoReportFound from "./no-report-found";
import fs from "fs";
import path from "path";

interface StaticReportProps {
  reportId: string;
}

const StaticReport: React.FC<StaticReportProps> = async ({ reportId }) => {
  const reportsDir = path.join(
    process.cwd(),
    "src",
    "app",
    "app",
    "report",
    "reports",
    `${reportId}.html`
  );
  console.log("Static report path:", reportsDir);
  if (!fs.existsSync(reportsDir)) {
    return <NoReportFound />;
  }
  const content = fs.readFileSync(reportsDir, "utf-8");
  return (
    <div className="min-h-screen">
      <iframe
        key={reportId} // Force recreation when report changes
        srcDoc={content}
        className="w-full h-screen border-0"
        title={`Report: ${reportId}`}
        sandbox="allow-same-origin allow-scripts"
        style={{
          colorScheme: "initial",
          isolation: "isolate",
        }}
      />
    </div>
  );
};

export default StaticReport;
