// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn, formatRelativeDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import {
  MessageCircle,
  Menu,
  Plus,
  ChevronLeft,
  ChevronRight,
  Trash2,
} from "lucide-react";
import React, { useState } from "react";
import { deleteChatAction } from "@/actions/delete-chat";

interface SidebarItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const sidebarItems: SidebarItem[] = [
  {
    title: "New Chat",
    href: "/app/chat",
    icon: Plus,
  },
];

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

interface SidebarComponentProps {
  chats: any[];
  onChatDeleted?: () => void;
  onDeleteChat?: (chatId: string) => Promise<void>;
}

export const ChatSidebar: React.FC<SidebarComponentProps> = ({ chats }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const pathname = usePathname();

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const deleteChat = async (chatId: string) => {
    try {
      await deleteChatAction(chatId);
    } catch (error) {
      console.error("Failed to delete chat:", error);
    }
  };

  return (
    <>
      <div className="hidden md:flex">
        <DesktopSidebar
          isCollapsed={sidebarCollapsed}
          onToggle={toggleSidebar}
          chats={chats}
          onDeleteChat={deleteChat}
        />
      </div>
      <div className="md:hidden fixed top-20 left-4 z-40">
        <MobileSidebar chats={chats} onDeleteChat={deleteChat} />
      </div>
    </>
  );
};

export function DesktopSidebar({
  isCollapsed,
  onToggle,
  chats,
  onDeleteChat,
}: SidebarProps & SidebarComponentProps) {
  const pathname = usePathname();
  const router = useRouter();
  return (
    <div
      className={cn(
        "flex flex-col h-full bg-gray-50 border-r transition-all duration-300",
        isCollapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex items-center justify-between p-4">
        {!isCollapsed && <h2 className="text-lg font-semibold">Chat</h2>}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="h-8 w-8 p-0"
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <Separator />

      <nav className="p-4 space-y-2">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Button
              key={item.href}
              variant={isActive ? "secondary" : "ghost"}
              className={cn("w-full justify-start", isCollapsed && "px-2")}
              onClick={() => {
                // Generate UUID locally - chat will be created when assistant responds
                const id = crypto.randomUUID();
                router.push(`/app/chat/${id}`);
              }}
            >
              <Icon className={cn("h-4 w-4", !isCollapsed && "mr-2")} />
              {!isCollapsed && item.title}
            </Button>
          );
        })}
      </nav>
      {!isCollapsed && (
        <>
          <div className="flex-1 flex flex-col p-4 min-h-0">
            <h4 className="text-sm font-medium text-gray-500 mb-2">
              Recent Conversations
            </h4>
            <div className="flex-1 space-y-1 overflow-y-auto">
              {chats &&
                chats.map((chat) => {
                  const isActiveChat = pathname === `/app/chat/${chat.id}`;
                  return (
                    <div key={chat.id} className="group relative">
                      <Button
                        variant={isActiveChat ? "secondary" : "ghost"}
                        className={cn(
                          "w-full justify-start text-sm pr-8",
                          isActiveChat && "bg-gray-200 text-gray-900",
                        )}
                        onClick={() => {
                          router.push(`/app/chat/${chat.id}`);
                        }}
                      >
                        <MessageCircle className="h-3 w-3 mr-2" />
                        <span className="flex flex-col items-start leading-tight">
                          <span className="truncate">
                            {chat.title || "Untitled Chat"}
                          </span>
                          <span className="text-xs text-text-secondary">
                            {formatRelativeDate(chat.updated_at)}
                          </span>
                        </span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100 hover:text-red-600"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onDeleteChat) {
                            onDeleteChat(chat.id);
                          }
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  );
                })}
              {!chats && (
                <p className="text-xs text-gray-400">No recent chats</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export const MobileSidebar: React.FC<SidebarComponentProps> = ({
  chats,
  onDeleteChat,
}) => {
  const pathname = usePathname();
  const router = useRouter();
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="md:hidden">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-64 p-0">
        <div className="flex flex-col h-full bg-gray-50">
          <div className="p-4">
            <h2 className="text-lg font-semibold">Chat</h2>
          </div>

          <Separator />

          <nav className="flex-1 p-4 space-y-2">
            {sidebarItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className="w-full justify-start"
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.title}
                  </Button>
                </Link>
              );
            })}
          </nav>

          <Separator />

          <div className="flex-1 flex flex-col p-4 min-h-0">
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              Recent Conversations
            </h3>
            <div className="flex-1 space-y-1 overflow-y-auto">
              {chats &&
                chats.map((chat) => {
                  const isActiveChat = pathname === `/app/chat/${chat.id}`;
                  return (
                    <div key={chat.id} className="group relative">
                      <Button
                        variant={isActiveChat ? "secondary" : "ghost"}
                        className={cn(
                          "w-full justify-start text-sm pr-8",
                          isActiveChat && "bg-gray-200 text-gray-900",
                        )}
                        onClick={() => {
                          router.push(`/app/chat/${chat.id}`);
                        }}
                      >
                        <MessageCircle className="h-3 w-3 mr-2" />
                        <span className="truncate">
                          {chat.title || "Untitled Chat"}
                        </span>
                        <span className="">
                          , {new Date(chat.updatedAt).toLocaleDateString()}
                        </span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100 hover:text-red-600"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onDeleteChat) {
                            onDeleteChat(chat.id);
                          }
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  );
                })}
              {!chats && (
                <p className="text-xs text-gray-400">No recent chats</p>
              )}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};
