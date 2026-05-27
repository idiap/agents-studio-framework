// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { serverApiUrl } from "@/configuration";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import ChatListSidebar from "./components/chat-list-sidebar";

export const dynamic = "force-dynamic";

interface Chat {
  id: string;
  title: string;
  updated_at: string;
}

export default async function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const url = `${serverApiUrl}/chat`;
  const response = await fetch(url, {
    cache: "no-store",
  });
  const chats: Chat[] = await response.json();

  return (
    <div className="flex h-screen">
      <AppSidebar contentGroups={<ChatListSidebar chats={chats} />} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
