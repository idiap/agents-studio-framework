// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import * as React from "react";
import { useSelectedLayoutSegments } from "next/navigation";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import { SidebarInset } from "@/components/ui/sidebar";

type AgentsLayoutClientProps = {
  children: React.ReactNode;
};

export default function AgentsLayoutClient({
  children,
}: AgentsLayoutClientProps) {
  const segments = useSelectedLayoutSegments();
  const disableAgentsLayout = segments.includes("editor");

  if (disableAgentsLayout) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen">
      <AppSidebar />
      <SidebarInset>{children}</SidebarInset>
    </div>
  );
}
