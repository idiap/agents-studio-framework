// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
      <FileQuestion className="w-16 h-16 text-muted-foreground" />
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-2">Directory Not Found</h2>
        <p className="text-muted-foreground mb-6">
          The directory you&apos;re looking for doesn&apos;t exist or has been
          deleted.
        </p>
        <Button asChild>
          <Link href="/app/prompts">Back to Prompts</Link>
        </Button>
      </div>
    </div>
  );
}
