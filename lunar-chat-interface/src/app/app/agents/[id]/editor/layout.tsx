// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import AppSidebar from "@/components/sidebar/appSidebar";
import { ReactFlowProvider } from "@xyflow/react";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/app/api/auth/[...nextauth]/auth-options";
import { ComponentModel } from "./models/component";
import { ComponentsProvider } from "@/context/componentsContext";
import { serverApiUrl } from "@/configuration";
import { getAuthHeaders } from "@/lib/server-auth";

interface ComponentIndexResponse {
  components: ComponentModel[];
  total: number;
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await getServerSession(authOptions);
  if (session?.accessToken == null) {
    redirect("/login");
  }
  const headers = await getAuthHeaders({
    "Content-Type": "application/json",
  });
  const components = await fetch(`${serverApiUrl}/component/index`, {
    method: "GET",
    headers,
  });
  if (!components.ok) {
    throw new Error(`Failed to fetch components: ${components.statusText}`);
  }
  const initialComponents: ComponentIndexResponse = await components.json();
  console.log("Fetched components:", initialComponents);
  return (
    <div className="w-full h-full">
      <ReactFlowProvider>
        <ComponentsProvider initialComponents={initialComponents.components}>
          <AppSidebar />
          <main className="w-full h-full">{children}</main>
        </ComponentsProvider>
      </ReactFlowProvider>
    </div>
  );
}
