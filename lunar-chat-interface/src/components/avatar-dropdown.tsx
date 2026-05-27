// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut, User } from "lucide-react";
import { signOut, useSession } from "next-auth/react";
import { basePath } from "@/configuration";

const AvatarDropdown: React.FC = () => {
  const session = useSession();
  const userImagePath = session.data?.user?.image;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <div className="ml-auto cursor-pointer">
          <Avatar>
            <AvatarImage
              src={userImagePath || ""}
              alt="profile"
              referrerPolicy="no-referrer"
            />
            <AvatarFallback>
              <User className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>
        </div>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onClick={() => signOut({ callbackUrl: `${basePath}/` })}
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default AvatarDropdown;
