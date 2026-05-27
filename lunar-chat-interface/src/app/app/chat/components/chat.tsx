// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";
import ChatInput from "./chat-input";
import ChatList from "./chat-list";
import { useState } from "react";
import { SessionProvider } from "next-auth/react";
import { useChat } from "@ai-sdk/react";
import ChatListItem from "./chat-list-item";
import UserMessage from "./user-message";
import AssistantMessage from "./assistant-message";
import AssistantMessagePart from "./assistant-message-part";
import { DefaultChatTransport, UIMessage } from "ai";
import SendButton from "@/components/send-button";
import Button from "@/components/button";
import { buildReportAction } from "@/actions/build-report-action";
import { useRouter } from "next/navigation";
import { Database } from "lucide-react";

interface ChatProps {
  id: string;
  initialMessages: UIMessage[];
}

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const Chat: React.FC<ChatProps> = (props) => {
  return (
    <SessionProvider>
      <ChatContent {...props} />
    </SessionProvider>
  );
};

const scrollToBottom = () => {
  setTimeout(() => {
    const scroller = document.getElementById("scroller");
    scroller?.scrollTo({
      top: scroller.scrollHeight,
      behavior: "smooth",
    });
  }, 50);
};

const ChatContent: React.FC<ChatProps> = ({ id, initialMessages }) => {
  const [input, setInput] = useState("");
  const [options, setOptions] = useState<Record<string, boolean>>({
    knowledge_base: true,
  });
  const defaultTransport = new DefaultChatTransport({
    api: "/api/chat",
  });
  const { messages, sendMessage, addToolResult, status } = useChat({
    id,
    messages: initialMessages,
    transport: defaultTransport,
    experimental_throttle: 50,
    onData: ({ data, type }) => {
      console.log(">>>onData", { data, type });
      // Handle data-chat-id event when server generates a new chat ID
      if (
        data &&
        typeof data === "object" &&
        "type" in data &&
        data.type === "data-chat-id"
      ) {
        const newChatId = (data as any).chatId;
        if (newChatId && id === "new-chat") {
          // Replace the URL without reloading the page
          router.replace(`${basePath}/app/chat/${newChatId}`);
        }
      }
    },
    onError: (e) => {
      console.error(">>> Chat error", e);
    },
    onToolCall: (tool) => {
      console.log(">>> Tool call", tool);
    },
  });
  console.log("Messages:", messages);
  const [outputLabelsById, setOutputLabelsById] = useState<
    Record<string, string[]>
  >({});
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const onSubmit = (
    e?: {
      preventDefault?: () => void;
    },
    chatRequestOptions?: any,
  ) => {
    scrollToBottom();
    const outputLabelsByIdCopy = { ...outputLabelsById };
    setOutputLabelsById(outputLabelsByIdCopy);
    try {
      const activeOptions = Object.fromEntries(
        Object.entries(options).filter(([, isActive]) => isActive),
      );
      sendMessage({
        text: input,
        metadata: chatRequestOptions?.body?.options || activeOptions,
      });
      setInput("");
    } catch (e) {
      console.error(e);
    }
  };

  const handleOptionToggle = (optionId: string, isActive: boolean) => {
    setOptions((prev) => ({
      ...prev,
      [optionId]: isActive,
    }));
  };

  const availableOptions =
    process.env.NEXT_PUBLIC_WORKSPACE === "aurora"
      ? [
          {
            id: "knowledge_base",
            label: "Repository 1",
            icon: Database,
            isActive: options.knowledge_base,
          },
          {
            id: "knowledge_base_2",
            label: "Repository 2",
            icon: Database,
            isActive: options.knowledge_base_2,
          },
        ]
      : [
          {
            id: "knowledge_base",
            label: "Knowledge Base",
            icon: Database,
            isActive: options.knowledge_base,
          },
        ];

  const getReportButtonText = () => {
    if (loading) return "Building Report...";
    if (report) return "Show report";
    return "Build Report";
  };

  const onReportButtonClick = async () => {
    setLoading(true);
    if (report) {
      router.push(`${basePath}/app/report/` + encodeURIComponent(report));
    } else {
      const report = await buildReportAction(
        messages.reduce(
          (acc, message) =>
            acc +
            message.parts.map((part) =>
              part.type === "text" ? part.text : "",
            ),
          "\n",
        ),
      );
      setReport(report);
      setLoading(false);
    }
  };

  const actionButtons =
    process.env.NEXT_PUBLIC_WORKSPACE === "aurora"
      ? [
          <SendButton
            key="send-button"
            onSubmit={onSubmit}
            value={input}
            loading={status === "submitted" || status === "streaming"}
            autoFocus={true}
            options={Object.fromEntries(
              Object.entries(options).filter(([, isActive]) => isActive),
            )}
          />,
          <Button
            key="build-report-button"
            onClick={onReportButtonClick}
            disabled={loading}
          >
            {getReportButtonText()}
          </Button>,
        ]
      : [
          <SendButton
            key="send-button"
            onSubmit={onSubmit}
            value={input}
            loading={status === "submitted" || status === "streaming"}
            autoFocus={true}
            options={Object.fromEntries(
              Object.entries(options).filter(([, isActive]) => isActive),
            )}
          />,
          <Button
            key="build-report-button"
            onClick={onReportButtonClick}
            disabled={loading}
          >
            {getReportButtonText()}
          </Button>,
        ];

  return (
    <>
      <SessionProvider>
        {/* <ChatHeader workflows={workflows} setSelectedWorkflowIds={setSelectedWorkflowIds} selectedWorkflowIds={selectedWorkflowIds} /> */}
        {messages.length > 0 ? (
          <ChatList
            messages={messages}
            outputLabels={outputLabelsById}
            renderItem={(message, index) => (
              <ChatListItem
                userMessage={<UserMessage message={message} />}
                assistantMessage={
                  <AssistantMessage
                    messagePartRender={(messagePart, messagePartIndex) => (
                      <AssistantMessagePart
                        messagePart={messagePart}
                        index={messagePartIndex}
                        addToolResult={addToolResult}
                      />
                    )}
                    message={message}
                  />
                }
                role={message.role}
                key={index}
              />
            )}
          />
        ) : (
          <h1 className="mt-[30vh] text-center text-subtitle font-medium font-heading">
            What will we discover today?
          </h1>
        )}
        <ChatInput
          handleSubmit={onSubmit}
          actionButtons={actionButtons}
          input={input}
          handleInputChange={(e) => setInput(e.target.value)}
          availableOptions={availableOptions}
          onOptionToggle={handleOptionToggle}
        />
      </SessionProvider>
    </>
  );
};

export default Chat;
