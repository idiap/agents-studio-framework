// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import Image from "next/image";
import logo from "@/assets/logo.png";
import { Button } from "../ui/button";
import { useRouter } from "next/navigation";
import { ComponentModel } from "@/app/app/agents/[id]/editor/models/component";
import { useComponents } from "@/context/componentsContext";

const EditorSidebar: React.FC = () => {
  const route = useRouter();
  const { components } = useComponents();
  const onDragStart = (
    event: React.DragEvent<HTMLLIElement>,
    component: ComponentModel,
  ) => {
    if (event.dataTransfer != null) {
      event.dataTransfer.setData(
        "application/component",
        JSON.stringify(component),
      );
      event.dataTransfer.effectAllowed = "move";
    }
  };
  return (
    <Sidebar>
      <SidebarHeader>
        <Button
          variant="ghost"
          className="h-12.5 cursor-pointer p-2"
          onClick={() => route.push("/")}
        >
          <Image src={logo} alt="Lunar" width={130} className="mr-auto" />
        </Button>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Components</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {components.map((component) => (
                <SidebarMenuItem
                  key={component.token}
                  onDragStart={(e) => onDragStart(e, component)}
                  draggable
                >
                  <SidebarMenuButton asChild className="cursor-pointer">
                    <div>
                      <p className="overflow-hidden w-full text-ellipsis whitespace-nowrap block">
                        {component.name}
                      </p>
                    </div>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
};

export default EditorSidebar;
