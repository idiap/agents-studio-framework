// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { deleteChatAction } from "@/actions/delete-chat";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface DeleteChatButtonProps {
  chatId: string;
  isVisible: boolean;
}

const DeleteChatButton: React.FC<DeleteChatButtonProps> = ({ chatId, isVisible }) => {
  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn(
        "absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0 transition-opacity hover:bg-red-100 hover:text-red-600",
        isVisible ? "opacity-100" : "opacity-0"
      )}
      onClick={(e) => {
        e.stopPropagation();
        deleteChatAction(chatId);
      }}
    >
      <Trash2 className="h-3 w-3" />
    </Button>
  );
};

export default DeleteChatButton;
