// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-64px)] gap-4">
      <h2 className="text-2xl font-semibold">Report Not Found</h2>
      <p className="text-muted-foreground">
        The report you&apos;re looking for doesn&apos;t exist or has been
        deleted.
      </p>
      <Button asChild>
        <Link href="/app/report">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Reports
        </Link>
      </Button>
    </div>
  );
}
