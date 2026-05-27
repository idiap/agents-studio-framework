// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import React, { Suspense } from "react";
import ReportLoading from "./components/report-loading";
import DatabaseReport from "./components/db-report";
import PageContainer from "@/components/page-container/page-container";
import { Navbar } from "@/components/navbar";

interface ReportPageProps {
  params: Promise<{
    reportId: string;
  }>;
  searchParams: Promise<{
    version?: string;
  }>;
}

const ReportPage: React.FC<ReportPageProps> = async ({
  params,
  searchParams,
}) => {
  const { reportId } = await params;
  const { version } = await searchParams;
  const versionNumber = version ? parseInt(version, 10) : undefined;

  return (
    <>
      <Navbar title="Report" />
      <PageContainer>
        <Suspense fallback={<ReportLoading />}>
          <DatabaseReport reportId={reportId} version={versionNumber} />
        </Suspense>
      </PageContainer>
    </>
  );
};

export default ReportPage;
