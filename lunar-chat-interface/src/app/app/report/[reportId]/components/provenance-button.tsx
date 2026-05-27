// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { Button } from "@/components/ui/button";
import { FileSearch } from "lucide-react";
import Link from "next/link";

interface ProvenanceButtonProps {
  reportId: string;
}

export default function ProvenanceButton({ reportId }: ProvenanceButtonProps) {
  return (
    <Link href={`/app/report/${reportId}/provenance`}>
      <Button variant="outline" className="flex items-center gap-2 ml-2">
        <FileSearch className="w-4 h-4" />
        Provenance
      </Button>
    </Link>
  );
}
