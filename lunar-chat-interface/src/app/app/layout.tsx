// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { getServerSession } from "next-auth";
import { authOptions } from "../api/auth/[...nextauth]/auth-options";
import { redirect } from "next/navigation";
import { SidebarProvider } from "@/components/ui/sidebar";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions);
  if (session?.accessToken == null) {
    redirect("/login");
  }
  return (
    <SidebarProvider>
      <div className="w-full bg-white flex flex-col min-h-screen">
        {children}
      </div>
    </SidebarProvider>
  );
}
