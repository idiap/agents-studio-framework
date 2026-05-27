// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { serverApiUrl } from "@/configuration";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export const deleteChatAction = async (chatId: string) => {
  const url = `${serverApiUrl}/chat/${chatId}`;
  const response = await fetch(url, { method: "DELETE" });
  if (!response.ok) {
    throw new Error("Failed to delete chat");
  }
  revalidatePath("/app/chat");
  redirect("/app/chat");
};
