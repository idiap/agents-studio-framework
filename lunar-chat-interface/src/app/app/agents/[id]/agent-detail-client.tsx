// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Bot,
  ArrowLeft,
  Play,
  Loader2,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
  ChevronDown,
  Network,
  StopCircle,
} from "lucide-react";
import type { Flow } from "../page";
import type { KnowledgeBase } from "@/models/knowledge-base";
import RunAgentModal from "./components/run-agent-modal";
import { useAgentStatus } from "@/hooks/use-agent-status";
import MarkdownOutput from "@/components/io/markdown-output/markdown-output";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProvenanceGraph } from "@/components/provenance/provenance-graph";
import { AgentStatusIndicator } from "../components/agent-status-indicator";
import Button from "@/components/button";
import { getFlowById } from "@/actions/get-flows";

interface AgentDetailClientProps {
  flow: Flow;
  knowledgeBases: KnowledgeBase[];
}

const getEventIcon = (type: string) => {
  const t = (type || "").toLowerCase();
  if (t.includes("error") || t.includes("failed")) return AlertCircle;
  if (t.includes("finished") || t.includes("completed")) return CheckCircle2;
  if (t.includes("started") || t.includes("running")) return CheckCircle2;
  if (t.includes("warning")) return AlertTriangle;
  if (t.includes("info") || t.includes("update")) return Info;
  return CheckCircle2;
};

export default function AgentDetailClient({
  flow,
  knowledgeBases,
}: AgentDetailClientProps) {
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [runFlowConfig, setRunFlowConfig] = useState(flow);
  const [isLoadingFlowConfig, setIsLoadingFlowConfig] = useState(false);
  const [activeTab, setActiveTab] = useState<"reasoning" | "provenance">(
    "reasoning",
  );
  const { status, isLoading, cancelAgent, isCancelling } = useAgentStatus(
    flow.id,
  );

  useEffect(() => {
    setRunFlowConfig(flow);
  }, [flow]);

  const handleCancelClick = async () => {
    await cancelAgent();
  };

  const handleBack = () => {
    router.push("/app/agents");
  };

  const handleRunClick = async () => {
    setIsModalOpen(true);
    setIsLoadingFlowConfig(true);

    try {
      const latestFlow = await getFlowById(flow.id);
      if (latestFlow) {
        setRunFlowConfig(latestFlow);
      }
    } catch (error) {
      console.error("Error refreshing flow configuration:", error);
    } finally {
      setIsLoadingFlowConfig(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleConfirmRun = async (
    agentId: string,
    inputs: Record<string, any>,
  ) => {
    setIsModalOpen(false);
  };

  const handleEdit = () => {
    router.push(`/app/agents/${flow.id}/editor`);
  };

  const handleDownloadTrig = () => {
    if (!status.result?.provenance?.trig) return;

    const blob = new Blob([status.result.provenance.trig], {
      type: "application/trig",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${flow.id}-provenance-${status.result.provenance.manifest.run_id}.trig`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <div className="flex items-center gap-4 px-3.5">
        <Button variant="ghost" onClick={handleBack} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Agents
        </Button>
      </div>

      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-linear-to-r from-primary-main to-primary-light rounded-lg">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-medium">{flow.name}</h3>
            </div>
            <CardDescription className="text-body">
              {flow.description}
            </CardDescription>
          </div>
          <Button onClick={handleEdit} variant="outline">
            Edit Agent
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Status Section */}
        <Card className="p-4 rounded-lg border shadow-[0_4px_20px_0_rgba(30,50,87,0.1)]">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <AgentStatusIndicator
                status={status.status}
                className="text-base"
              />

              {status.status === "running" && status.progress && (
                <p className="text-sm text-muted-foreground">
                  {status.progress}
                </p>
              )}

              {status.status === "failed" && status.error && (
                <p className="text-sm text-red-600">Error: {status.error}</p>
              )}

              {status.status === "completed" && status.completed_at && (
                <p className="text-sm text-muted-foreground">
                  {new Date(status.completed_at).toLocaleString()}
                </p>
              )}
            </div>

            <div className="flex gap-2">
              {status.status === "running" ? (
                <Button
                  onClick={handleCancelClick}
                  variant="outline"
                  disabled={isCancelling}
                >
                  {isCancelling ? (
                    <>
                      Cancelling...
                      <Loader2
                        className="w-4 h-4 ml-2 animate-spin"
                        strokeWidth={2}
                      />
                    </>
                  ) : (
                    <>
                      <StopCircle className="w-4 h-4 ml-2" strokeWidth={3} />
                      Cancel
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  variant="primary"
                  onClick={handleRunClick}
                  disabled={isLoading}
                >
                  Run Agent
                  <Play className="w-4 h-4 ml-2" strokeWidth={2} />
                </Button>
              )}
            </div>
          </div>
        </Card>

        <Separator className="my-8" />

        {/* Reasoning Log & Provenance Section */}
        {status.result?.execution_result?.event_log &&
          status.result.execution_result.event_log.length > 0 && (
            <Tabs
              value={activeTab}
              onValueChange={(v) =>
                setActiveTab(v as "reasoning" | "provenance")
              }
              className="space-y-4"
            >
              <TabsList className="grid w-full grid-cols-2 mb-10">
                <TabsTrigger value="reasoning" className="gap-2 cursor-pointer">
                  <Info className="w-4 h-4" />
                  Reasoning Log
                </TabsTrigger>
                <TabsTrigger
                  value="provenance"
                  className="gap-2 cursor-pointer"
                  disabled={!status.result?.provenance}
                >
                  <Network className="w-4 h-4" />
                  Provenance Graph
                </TabsTrigger>
              </TabsList>

              <TabsContent value="reasoning" className="space-y-4">
                <div className="gap-2 mb-10">
                  <h3 className="text-lg font-medium">Reasoning Log</h3>
                  <p className="text-muted-foreground">
                    {status.result.execution_result.event_log.length} events
                  </p>
                </div>

                {status.result.execution_result.event_log.map(
                  (event, index) => {
                    const eventTypeColor =
                      event.type.includes("error") ||
                      event.type.includes("failed")
                        ? "text-red-600 bg-red-50 border-red-200"
                        : event.type.includes("finished") ||
                            event.type.includes("completed")
                          ? "text-green-600 bg-green-50 border-green-200"
                          : event.type.includes("started")
                            ? "text-primary-main"
                            : "text-primary-main";

                    const EventIcon = getEventIcon(event.type);
                    const eventIconColor =
                      eventTypeColor.split(" ")[0] || "text-gray-600";

                    return (
                      <div key={index} className="space-y-8">
                        <div className="flex flex-col items-start justify-between mb-8">
                          <div className="w-full flex justify-between">
                            <div className="flex flex-col items-start gap-2">
                              <div className="flex items-center gap-2">
                                <EventIcon
                                  className={`w-4 h-4 ${eventIconColor}`}
                                  strokeWidth={3}
                                />
                                <p className="uppercase font-bold text-xs">
                                  {event.type}{" "}
                                  {event.metadata.name &&
                                  event.metadata.name !== ""
                                    ? "• " + event.metadata.name
                                    : ""}
                                </p>
                              </div>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {new Date(event.timestamp).toLocaleString()}
                            </div>
                          </div>
                          <div className="w-full">
                            {event.metadata.description ? (
                              <p className="text-xs font-medium">
                                {event.metadata.description}
                              </p>
                            ) : null}

                            {/* Custom rendering for step:started */}
                            {event.type === "step:started" &&
                              event.payload?.inputs && (
                                <div className="mt-2 space-y-2">
                                  {Object.entries(
                                    event.payload.inputs as Record<string, any>,
                                  ).map(([key, value]) => {
                                    return (
                                      <div key={key} className="space-y-1">
                                        {typeof value === "string" ? (
                                          <Collapsible>
                                            <CollapsibleTrigger className="flex items-center gap-1 text-xs hover:underline group text-primary/60">
                                              View {key}
                                              <ChevronDown className="w-3 h-3 transition-transform group-data-[state=open]:rotate-180" />
                                            </CollapsibleTrigger>
                                            <CollapsibleContent>
                                              <div className="text-sm bg-white p-3 rounded border mt-2">
                                                <MarkdownOutput
                                                  content={value}
                                                />
                                              </div>
                                            </CollapsibleContent>
                                          </Collapsible>
                                        ) : (
                                          <Collapsible>
                                            <CollapsibleTrigger className="flex items-center gap-1 text-xs hover:underline group text-primary/60">
                                              View {key}
                                              <ChevronDown className="w-3 h-3 transition-transform group-data-[state=open]:rotate-180" />
                                            </CollapsibleTrigger>
                                            <CollapsibleContent>
                                              <pre className="whitespace-pre-wrap mt-2 text-xs overflow-x-auto bg-white p-2 rounded border">
                                                {JSON.stringify(value, null, 2)}
                                              </pre>
                                            </CollapsibleContent>
                                          </Collapsible>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              )}

                            {/* Custom rendering for step:finished with llm-node */}
                            {event.type === "step:finished" &&
                              event.metadata?.token === "llm-node" &&
                              event.payload?.result?.value?.content && (
                                <Collapsible className="mt-2">
                                  <CollapsibleTrigger className="flex items-center gap-1 text-xs hover:underline group text-primary/60">
                                    View Result
                                    <ChevronDown className="w-3 h-3 transition-transform group-data-[state=open]:rotate-180" />
                                  </CollapsibleTrigger>
                                  <CollapsibleContent>
                                    <div className="text-sm bg-white p-3 rounded border mt-2">
                                      <MarkdownOutput
                                        content={
                                          event.payload.result.value.content
                                        }
                                      />
                                    </div>
                                  </CollapsibleContent>
                                </Collapsible>
                              )}

                            {/* Default payload rendering for other cases */}
                            {event.type !== "step:started" &&
                              !(
                                event.type === "step:finished" &&
                                event.metadata?.token === "llm-node"
                              ) &&
                              event.payload &&
                              typeof event.payload === "object" &&
                              Object.keys(event.payload).length > 0 && (
                                <Collapsible className="mt-2">
                                  <CollapsibleTrigger className="flex items-center gap-1 text-xs hover:underline group text-primary/60">
                                    View payload
                                    <ChevronDown className="w-3 h-3 transition-transform group-data-[state=open]:rotate-180" />
                                  </CollapsibleTrigger>
                                  <CollapsibleContent>
                                    <pre className="whitespace-pre-wrap mt-2 text-xs overflow-x-auto bg-white p-2 rounded border">
                                      {JSON.stringify(event.payload, null, 2)}
                                    </pre>
                                  </CollapsibleContent>
                                </Collapsible>
                              )}

                            {event.metadata?.error && (
                              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                            )}
                          </div>
                        </div>
                        {status.result?.execution_result.event_log?.length &&
                          index <
                            status.result.execution_result.event_log.length -
                              1 && <div className="my-2" />}
                      </div>
                    );
                  },
                )}
              </TabsContent>

              <TabsContent value="provenance">
                {status.result?.provenance && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 justify-between">
                      <div>
                        <h3 className="text-lg font-medium">
                          Provenance Graph
                        </h3>

                        <p className="text-muted-foreground">
                          {status.result.provenance.view_model.steps.length}{" "}
                          steps
                        </p>
                      </div>
                      <Button onClick={handleDownloadTrig} variant="outline">
                        Download TriG
                      </Button>
                    </div>
                    <ProvenanceGraph provenance={status.result.provenance} />
                  </div>
                )}
              </TabsContent>
            </Tabs>
          )}
      </CardContent>

      <RunAgentModal
        flow={runFlowConfig}
        knowledgeBases={knowledgeBases}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onConfirm={handleConfirmRun}
        isLoadingInputs={isLoadingFlowConfig}
      />
    </>
  );
}
