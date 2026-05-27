// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

export default function TemplatesLoading() {
  return (
    <div>
      <Navbar title="Templates" />
      <div className="relative flex flex-col max-w-300 w-full gap-8 h-[calc(100%)] mb-0 mr-auto ml-auto p-6">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton className="h-9 w-48" />
              <Skeleton className="h-5 w-72" />
            </div>
            <Skeleton className="h-10 w-32" />
          </div>
          <Separator />
        </div>

        <div className="grid gap-4">
          <div className="flex items-center gap-4">
            <Skeleton className="h-10 w-80 max-w-sm" />
            <Skeleton className="h-5 w-24" />
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="border rounded-lg p-6 space-y-4">
                <div className="space-y-2">
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                </div>
                <div className="pt-4 border-t flex items-center justify-between">
                  <Skeleton className="h-4 w-24" />
                  <div className="flex gap-2">
                    <Skeleton className="h-8 w-16" />
                    <Skeleton className="h-8 w-8" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
