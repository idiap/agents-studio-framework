// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Report editor error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-64px)] gap-4">
      <h2 className="text-2xl font-semibold">Something went wrong!</h2>
      <p className="text-muted-foreground">
        Failed to load the report editor. Please try again.
      </p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
