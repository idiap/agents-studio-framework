// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { UIMessage } from "ai";
import { Bar } from "react-chartjs-2";
import MarkdownOutput from "@/components/io/markdown-output/markdown-output";
import { Separator } from "@/components/ui/separator";
import { CategoryScale, Chart, BarElement, LinearScale } from "chart.js";
import ChatCollapsible from "./chat-collapsible";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircleIcon } from "lucide-react";

Chart.register(CategoryScale);
Chart.register(BarElement);
Chart.register(LinearScale);

type EventData<EventPayload> = {
  metadata: {
    id: string;
    name: string;
    token: string;
    error?: string;
  };
  payload: EventPayload;
};

type MessagePart = NonNullable<UIMessage["parts"]>[number];

interface AssistantMessagePartProps {
  messagePart: MessagePart;
  index: number;
  addToolResult: <TOOL extends string>({
    tool,
    toolCallId,
    output,
  }: {
    tool: TOOL;
    toolCallId: string;
    output: unknown;
  }) => Promise<void>;
}

const AssistantMessagePart: React.FC<AssistantMessagePartProps> = ({
  messagePart,
  index,
}) => {
  const data =
    "data" in messagePart ? (messagePart.data as EventData<any>) : null;
  switch (messagePart.type) {
    case "step-start":
      return index !== 0 ? (
        <Separator />
      ) : (
        <div style={{ marginTop: 16 }}></div>
      );
    case "text":
      return <MarkdownOutput content={messagePart.text} />;
    case "tool-Hybrid_Search":
      return (
        <ChatCollapsible title="Base Legal">
          <MarkdownOutput content={messagePart.output as string} />
        </ChatCollapsible>
      );
    case "data-log":
      return <></>;
    case "data-component-started":
      return (
        <h4 className="font-bold text-xs uppercase">{data!.metadata.name}</h4>
      );
    case "data-component-finished":
      if (data!.metadata.id === "chat_bar_chart") {
        const payload = data!.payload.result;
        return (
          <div key={index} className="h-125 m-4">
            <Bar
              width="100%"
              data={{
                labels: payload.labels || [],
                datasets: payload.datasets?.map((dataset: object) => ({
                  ...dataset,
                  backgroundColor: "#1E3257",
                })),
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
              }}
            />
          </div>
        );
      }
      return (
        <ChatCollapsible title="Component Result">
          <pre className="whitespace-pre-wrap wrap-break-word text-xs">
            <code>{JSON.stringify(data, null, 2)}</code>
          </pre>
        </ChatCollapsible>
      );
    case messagePart.type.match(/^tool-/)?.input: {
      if (!("input" in messagePart)) {
        throw new Error(
          `Tool part is missing input: ${JSON.stringify(messagePart)}`
        );
      }
      return (
        <ChatCollapsible
          title={`${messagePart.type
            .replace(/^tool-/, "")
            .replace(/_/g, " ")} tool was called`}
        >
          <pre className="whitespace-pre-wrap wrap-break-word text-xs">
            <code>{JSON.stringify(messagePart.input, null, 2)}</code>
          </pre>
        </ChatCollapsible>
      );
    }
    case "data-component-error":
      return (
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertTitle>Component Error</AlertTitle>
          <AlertDescription>
            <p>{data!.metadata.error}</p>
          </AlertDescription>
        </Alert>
      );
    case "data-flow-error":
      return (
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertTitle>Flow Error</AlertTitle>
          <AlertDescription>
            <p>{data!.metadata.error}</p>
          </AlertDescription>
        </Alert>
      );
    default:
      console.error("Unknown part type:", messagePart.type, messagePart);
  }
};

export default AssistantMessagePart;
