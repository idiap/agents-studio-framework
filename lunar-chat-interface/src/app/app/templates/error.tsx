// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Navbar } from "@/components/navbar";
import { Separator } from "@/components/ui/separator";
import { AlertCircle } from "lucide-react";

export default function TemplatesError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Templates page error:", error);
  }, [error]);

  return (
    <div>
      <Navbar title="Template" />
      <div className="relative flex flex-col max-w-300 w-full gap-8 h-[calc(100%)] mb-0 mr-auto ml-auto">
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Templates</h1>
            <p className="text-muted-foreground">
              Create and manage your document templates
            </p>
          </div>
          <Separator />
        </div>

        <Card className="flex flex-col items-center justify-center py-12">
          <CardContent className="text-center space-y-4">
            <AlertCircle className="w-12 h-12 text-destructive mx-auto" />
            <div>
              <h3 className="text-lg font-semibold mb-2">
                Something went wrong
              </h3>
              <p className="text-muted-foreground mb-4">
                Failed to load templates. Please try again.
              </p>
            </div>
            <div className="flex gap-2 justify-center">
              <Button onClick={reset}>Try Again</Button>
              <Button
                variant="outline"
                onClick={() => (window.location.href = "/app")}
              >
                Go Home
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
