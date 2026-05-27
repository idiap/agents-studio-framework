// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import Chat from "../components/chat";
import { UIMessage } from "ai";
import { serverApiUrl } from "@/configuration";

export default async function ChatPage(props: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await props.params;
  const url = `${serverApiUrl}/chat/${id}`;
  const response = await fetch(url, { method: "GET" });

  let chat = null;
  if (response.ok) {
    chat = await response.json();
  }

  const uiMessages: UIMessage[] = Array.isArray(chat?.content?.messages)
    ? chat.content.messages.map((msg: any) => {
        return {
          id: msg.id,
          role: msg.role,
          parts: Array.isArray(msg.parts)
            ? msg.parts.map((part: any) => {
                if (part.type === "text") {
                  return { type: "text", text: part.text };
                }
                if (
                  typeof part.type === "string" &&
                  part.type.startsWith("tool-")
                ) {
                  return { ...part };
                }
                if (
                  part.type === "data-component-started" ||
                  part.type === "data-component-finished"
                ) {
                  return {
                    type: part.type,
                    data: part.data,
                  };
                }
                return part;
              })
            : [],
          text: msg.text ?? "",
          created_at: msg.created_at,
          metadata: msg.metadata || {},
        };
      })
    : [];

  return (
    <div className="flex flex-col w-full h-full p-6">
      <div className="flex flex-col max-w-[800px] w-full gap-8 h-full mx-auto">
        <Chat id={id} initialMessages={uiMessages} />
      </div>
    </div>
  );
}
