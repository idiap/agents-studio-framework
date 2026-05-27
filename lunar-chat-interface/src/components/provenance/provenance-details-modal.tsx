// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogHeader,
  DialogClose,
} from "@/components/ui/dialog";
import { Shield } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SelectedItem } from "./provenance-graph";

interface ProvenanceDetailsModalProps {
  selected: SelectedItem;
  setSelected: (selected: ProvenanceDetailsModalProps["selected"]) => void;
}

const ProvenanceDetailsModal = ({
  selected,
  setSelected,
}: ProvenanceDetailsModalProps) => {
  const KIND_MAP: Record<string, string> = {
    GEN: "generative",
    RET: "retrieval",
    DET: "deterministic",
    VER: "verification",
    HUM: "human-reviewed",
  };

  const bandColorClass = (band?: string) => {
    switch (band) {
      case "green":
        return "bg-green-600";
      case "red":
        return "bg-red-600";
      case "amber":
        return "bg-amber-600";
      default:
        return "bg-slate-400";
    }
  };
  return (
    <Dialog open={!!selected} onOpenChange={(v) => !v && setSelected(null)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {selected
              ? `${
                  (selected.kind || "").charAt(0).toUpperCase() +
                  (selected.kind || "").slice(1)
                } details`
              : "Details"}
          </DialogTitle>
          <DialogDescription>
            More information about the selected node.
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-80 mt-2">
          <div className="space-y-4">
            {selected?.kind === "step" && (
              <div>
                <div className="font-semibold">Step ID</div>
                <div className="mono">{selected.payload.id}</div>
                <div className="mt-2 font-semibold">Component</div>
                <div className="mono">{selected.payload.component}</div>

                {/* Trust Score Section */}
                {selected.payload.trust?.trust_index !== null &&
                  selected.payload.trust?.trust_index !== undefined && (
                    <div className="mt-4 p-3 rounded-lg border bg-slate-50">
                      <div className="font-semibold mb-2 flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Trust
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">
                            Trust Index:
                          </span>{" "}
                          <span className="font-medium">
                            {selected.payload.trust.trust_index}/100
                          </span>
                        </div>

                        {/* kind */}
                        <div className="flex items-center gap-2">
                          <div>
                            <span className="text-muted-foreground">Kind:</span>{" "}
                            <span className="font-medium">
                              {KIND_MAP[selected.payload.trust.step_kind] ||
                                selected.payload.trust.step_kind ||
                                ""}
                            </span>
                          </div>
                        </div>

                        {/* Confidence */}
                        {selected.payload.trust.confidence !== null &&
                          selected.payload.trust.confidence !== undefined && (
                            <div>
                              <span className="text-muted-foreground">
                                Confidence:
                              </span>{" "}
                              <span className="font-medium">
                                {typeof selected.payload.trust.confidence ===
                                "number"
                                  ? selected.payload.trust.confidence > 1
                                    ? `${selected.payload.trust.confidence}`
                                    : `${(
                                        selected.payload.trust.confidence * 100
                                      ).toFixed(2)}%`
                                  : String(selected.payload.trust.confidence)}
                              </span>
                            </div>
                          )}

                        {/* Missingness */}
                        {selected.payload.trust.missingness !== null &&
                          selected.payload.trust.missingness !== undefined && (
                            <div>
                              <span className="text-muted-foreground">
                                Missingness:
                              </span>{" "}
                              <span className="font-medium">
                                {typeof selected.payload.trust.missingness ===
                                "number"
                                  ? `${(
                                      selected.payload.trust.missingness * 100
                                    ).toFixed(2)}%`
                                  : String(selected.payload.trust.missingness)}
                              </span>
                            </div>
                          )}

                        {selected.payload.trust.risk !== null &&
                          selected.payload.trust.risk !== undefined && (
                            <div>
                              <span className="text-muted-foreground">
                                Risk:
                              </span>{" "}
                              <span className="font-medium">
                                {(selected.payload.trust.risk * 100).toFixed(2)}
                                %
                              </span>
                            </div>
                          )}

                        {/* Trust summary */}
                        {selected.payload.trust.summary && (
                          <div className="col-span-2 mt-2 text-sm">
                            <div className="text-muted-foreground">
                              Summary:
                            </div>
                            <div className="font-medium">
                              <span
                                aria-hidden
                                className={`inline-block w-3 h-3 mr-2 rounded-full ${bandColorClass(
                                  selected.payload.trust.band
                                )}`}
                              />
                              {selected.payload.trust.summary}
                            </div>
                          </div>
                        )}

                        {/* Actions */}
                        {Array.isArray(selected.payload.trust.actions) && (
                          <div className="col-span-2 mt-2">
                            <div className="text-muted-foreground">
                              Actions:
                            </div>
                            <div className="mt-1 flex flex-wrap gap-2">
                              {selected.payload.trust.actions.length > 0 ? (
                                selected.payload.trust.actions.map(
                                  (a: any, i: number) => (
                                    <button
                                      key={i}
                                      className="px-2 py-1 rounded bg-slate-100 text-sm"
                                      onClick={() => {
                                        if (typeof a === "string") {
                                          try {
                                            window.open(a, "_blank");
                                          } catch (e) {
                                            /* ignore */
                                          }
                                        }
                                      }}
                                    >
                                      {typeof a === "string"
                                        ? a
                                        : JSON.stringify(a)}
                                    </button>
                                  )
                                )
                              ) : (
                                <p>No suggested actions</p>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                <div className="mt-2 font-semibold">Run info</div>
                <pre className="bg-muted p-2 rounded text-sm whitespace-pre-wrap wrap-break-word break-all">
                  {JSON.stringify(selected.payload.run || {}, null, 2)}
                </pre>

                <div className="mt-2 font-semibold">Inputs</div>
                <pre className="bg-muted p-2 rounded text-sm whitespace-pre-wrap wrap-break-word break-all">
                  {JSON.stringify(selected.payload.inputs || [], null, 2)}
                </pre>

                <div className="mt-2 font-semibold">Output</div>
                <pre className="bg-muted p-2 rounded text-sm whitespace-pre-wrap wrap-break-word break-all">
                  {JSON.stringify(selected.payload.output || {}, null, 2)}
                </pre>
              </div>
            )}

            {selected?.kind === "data_source" && (
              <div>
                <div className="font-semibold">Data Source ID</div>
                <div className="mono">{selected.payload.id}</div>
                <div className="mt-2 font-semibold">Summary</div>
                <div className="mono">{selected.payload.summary}</div>
                <div className="mt-2 font-semibold">Value</div>
                <pre className="bg-muted p-2 rounded text-sm whitespace-pre-wrap wrap-break-wordword break-all">
                  {JSON.stringify(selected.payload.value ?? null, null, 2)}
                </pre>
              </div>
            )}

            {selected?.kind === "input" && (
              <div>
                <div className="font-semibold">Input name</div>
                <div className="mono">{selected.payload.input.name}</div>
                <div className="mt-2 font-semibold">Kind</div>
                <div className="mono">{selected.payload.input.kind}</div>
                <div className="mt-2 font-semibold">Value summary</div>
                <div className="mono wrap-break-word break-all whitespace-normal">
                  {selected.payload.input.value_summary}
                </div>
                <div className="mt-2 font-semibold">Raw binding</div>
                <pre className="bg-muted p-2 rounded text-sm whitespace-pre-wrap wrap-break-word break-all">
                  {JSON.stringify(
                    selected.payload.input.raw ?? selected.payload.input,
                    null,
                    2
                  )}
                </pre>
              </div>
            )}

            {selected?.kind === "output" && (
              <div>
                <div className="font-semibold">Step</div>
                <div className="mono">{selected.payload.stepId}</div>
                <div className="mt-2 font-semibold">Output</div>
                <pre className="bg-muted p-2 rounded text-sm whitespace-pre-wrap wrap-break-word break-all">
                  {JSON.stringify(selected.payload.output ?? null, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="mt-4 flex justify-end">
          <DialogClose className="btn">Close</DialogClose>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ProvenanceDetailsModal;
