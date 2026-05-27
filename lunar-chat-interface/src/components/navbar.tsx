// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";
import Link from "next/link";
import Image from "next/image";
import Logo from "@/assets/logo.png";
import { Button } from "@/components/ui/button";
import { SidebarTrigger, useSidebar } from "./ui/sidebar";
import { LogOut } from "lucide-react";
import { signOut } from "next-auth/react";
import { basePath } from "@/configuration";
import React from "react";

const NAVBAR_HEIGHT = "h-16";

interface NavbarProps {
  title: string | React.ReactNode;
}

export const Navbar: React.FC<NavbarProps> = ({ title }) => {
  const { state } = useSidebar();
  const isSidebarCollapsed = state === "expanded";

  return (
    <div className="w-full">
      <div
        className={`sticky top-0 z-50 grid w-full grid-cols-[10.25rem_1fr_10.25rem] items-center bg-white/50 px-4 backdrop-blur-md ${NAVBAR_HEIGHT}`}
      >
        <div
          className={`flex h-16 items-center gap-2 overflow-hidden transition-all duration-300 ease-in-out ${isSidebarCollapsed ? "opacity-0 pointer-events-none" : "opacity-100"}`}
          aria-hidden={isSidebarCollapsed}
        >
          <SidebarTrigger />
          <Link href="/">
            <Image
              src={Logo}
              width={128}
              height={64}
              alt="Lunar"
              className="align-middle h-16"
            />
          </Link>
        </div>
        <div className="flex justify-center px-4">
          <div className="font-semibold text-sm text-text-primary">{title}</div>
        </div>
        <div className="flex justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={() => signOut({ callbackUrl: `${basePath}/login` })}
          >
            <LogOut className="h-4 w-4" />
            Log out
          </Button>
        </div>
      </div>
    </div>
  );
};
