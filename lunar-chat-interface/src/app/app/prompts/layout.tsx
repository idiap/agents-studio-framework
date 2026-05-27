// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { AppSidebar } from "@/components/sidebar/app-sidebar";
import { SidebarInset } from "@/components/ui/sidebar";

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      <AppSidebar />
      <SidebarInset>{children}</SidebarInset>
    </div>
  );
}
