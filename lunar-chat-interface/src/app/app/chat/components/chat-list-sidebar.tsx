// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useRouter, usePathname } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn, formatRelativeDate } from "@/lib/utils";
import DeleteChatButton from "./delete-chat-button";
import { SidebarGroup, SidebarGroupLabel } from "@/components/ui/sidebar";

interface Chat {
  id: string;
  title: string;
  updated_at: string;
}

interface ChatListSidebarProps {
  chats: Chat[];
}

export default function ChatListSidebar({ chats }: ChatListSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [hoveredChatId, setHoveredChatId] = useState<string | null>(null);

  return (
    <SidebarGroup className="">
      <SidebarGroupLabel className="uppercase font-bold text-[#1E3257]/60">
        Recent conversations
      </SidebarGroupLabel>
      <div key={"new-chat"} className="relative">
        <Button
          variant={"ghost"}
          className={cn(
            "w-full justify-start text-sm py-2 px-4 h-12 hover:bg-[#1E3257]/4",
          )}
          onClick={() => {
            router.push(`/app/chat`);
          }}
        >
          <span className="truncate font-heading font-medium text-link ">
            New Chat
          </span>
        </Button>
      </div>
      {chats &&
        chats.map((chat) => {
          const isActiveChat = pathname === `/app/chat/${chat.id}`;
          return (
            <div
              key={chat.id}
              className="relative"
              onMouseEnter={() => setHoveredChatId(chat.id)}
              onMouseLeave={() => setHoveredChatId(null)}
            >
              <Button
                variant={isActiveChat ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-start text-sm py-2 px-4 h-12",
                  isActiveChat && "bg-[#1E3257]/4 text-gray-900",
                )}
                onClick={() => {
                  router.push(`/app/chat/${chat.id}`);
                }}
              >
                <span className="flex flex-col items-start leading-tight">
                  <span className="truncate font-heading font-medium text-link">
                    {chat.title || "Untitled Chat"}
                  </span>
                  <span className="text-xs text-[#0D181C]/30 font-bold">
                    {formatRelativeDate(chat.updated_at)}
                  </span>
                </span>
              </Button>
              <DeleteChatButton
                chatId={chat.id}
                isVisible={hoveredChatId === chat.id}
              />
            </div>
          );
        })}
      {!chats && <p className="text-xs text-gray-400">No recent chats</p>}
    </SidebarGroup>
  );
}
