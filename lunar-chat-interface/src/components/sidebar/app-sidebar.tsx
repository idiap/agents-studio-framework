// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";
import {
  Bot,
  Brain,
  Database,
  FileText,
  LayoutTemplate,
  MessageCircleMore,
  Search,
  ScrollText,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import Link from "next/link";
import Image from "next/image";
import Logo from "@/assets/logo.png";
import clsx from "clsx";

interface SidebarItem {
  title: string;
  url: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

const items: SidebarItem[] = [];
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

console.log("NEXT_PUBLIC_WORKSPACE:", process.env.NEXT_PUBLIC_WORKSPACE);

if (process.env.NEXT_PUBLIC_WORKSPACE === "icebrook") {
  items.push({ title: "Agents", url: `${basePath}/app/agents`, icon: Bot });
  items.push({
    title: "Chat",
    url: `${basePath}/app/chat`,
    icon: MessageCircleMore,
  });
  items.push({
    title: "Knowledge Bases",
    url: `${basePath}/app/knowledge-base`,
    icon: Database,
  });
  items.push({
    title: "Reports",
    url: `${basePath}/app/report`,
    icon: FileText,
  });
  items.push({
    title: "Templates",
    url: `${basePath}/app/templates`,
    icon: LayoutTemplate,
  });
  items.push({
    title: "Prompts",
    url: `${basePath}/app/prompts`,
    icon: ScrollText,
  });
  items.push({
    title: "AI Models",
    url: `${basePath}/app/ai-models`,
    icon: Brain,
  });
}

if (process.env.NEXT_PUBLIC_WORKSPACE === "aurora") {
  items.push({
    title: "Chat",
    url: `${basePath}/app/chat`,
    icon: MessageCircleMore,
  });
  items.push({ title: "Search", url: `${basePath}/app/search`, icon: Search });
}

if (process.env.NEXT_PUBLIC_WORKSPACE === "argumentation-agent") {
  items.push({ title: "Agents", url: `${basePath}/app/agents`, icon: Bot });
  items.push({
    title: "Reports",
    url: `${basePath}/app/report`,
    icon: FileText,
  });
}

interface AppSidebarProps {
  contentGroups?: React.ReactNode;
}

export function AppSidebar({ contentGroups }: AppSidebarProps) {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  return (
    <Sidebar
      collapsible="icon"
      className={clsx(
        "sticky bg-white transition-all duration-300 ease-in-out",
        {
          "w-0 overflow-hidden": isCollapsed,
          "w-62": !isCollapsed,
        },
      )}
    >
      <SidebarHeader className="gap-4 flex-row items-center py-0 px-6 h-16.5 bg-white">
        <SidebarTrigger />
        <Link href={`${basePath}/`}>
          <Image
            src={Logo}
            width={128}
            height={64}
            alt="Lunar"
            className="align-middle h-16"
          />
        </Link>
      </SidebarHeader>

      <SidebarContent className="bg-white">
        <SidebarGroup>
          <SidebarGroupContent className="mt-10">
            <SidebarMenu className="gap-4">
              {items.map((item) => {
                const Icon = item.icon;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild tooltip={item.title}>
                      <a
                        href={item.url}
                        className="flex items-center gap-3 px-4 font-semibold text-link text-text-primary"
                      >
                        <Icon strokeWidth={2} className="w-6! h-6!" />
                        <span>{item.title}</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        {contentGroups}
      </SidebarContent>
    </Sidebar>
  );
}
