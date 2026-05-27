// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

export default function PromptsLoading() {
  return (
    <div>
      <Navbar title="Prompts" />
      <div className="relative flex flex-col max-w-300 w-full gap-8 h-[calc(100%)] mb-0 mr-auto ml-auto p-6">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton className="h-9 w-48" />
              <Skeleton className="h-5 w-72" />
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-10 w-36" />
              <Skeleton className="h-10 w-32" />
            </div>
          </div>
          <Separator />
        </div>

        <div className="grid gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 p-4">
              <Skeleton className="h-8 w-8 rounded-sm" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-48" />
              </div>
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-8" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
