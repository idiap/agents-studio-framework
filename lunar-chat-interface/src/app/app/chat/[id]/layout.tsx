// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white flex flex-col h-screen">
      <Navbar title="Chat" />
      <div id="scroller" className="overflow-y-scroll h-[calc(100vh-62px)]">
        {children}
        <div id="anchor" className="h-0"></div>
      </div>
    </div>
  );
}
