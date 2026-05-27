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

export default function AIModelsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("AI Models page error:", error);
  }, [error]);

  return (
    <div>
      <Navbar title="AI Models" />
      <div className="relative flex flex-col max-w-300 w-full gap-8 h-[calc(100%)] mb-0 mr-auto ml-auto">
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">AI Models</h1>
            <p className="text-muted-foreground">
              Manage your AI model configurations
            </p>
          </div>
          <Separator />
        </div>

        <Card className="border-destructive">
          <CardContent className="flex flex-col items-center justify-center py-12 gap-4">
            <AlertCircle className="w-12 h-12 text-destructive" />
            <div className="text-center">
              <h3 className="font-semibold text-lg">
                Something went wrong
              </h3>
              <p className="text-muted-foreground text-sm mt-1">
                {error.message || "Failed to load AI models"}
              </p>
            </div>
            <Button onClick={reset} variant="outline">
              Try again
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
