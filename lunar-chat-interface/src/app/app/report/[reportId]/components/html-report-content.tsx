// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

interface HtmlReportContentProps {
  content: string;
  reportId: string;
}

export default function HtmlReportContent({
  content,
  reportId,
}: HtmlReportContentProps) {
  return (
    <div className="min-h-screen">
      <iframe
        key={reportId}
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
}
