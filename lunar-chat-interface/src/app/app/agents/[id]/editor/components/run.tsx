// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client"
import Button from "@/components/button";
import { Dialog, DialogClose, DialogContent, DialogFooter, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useReactFlow } from "@xyflow/react";
import { LoaderCircleIcon, Play } from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";
import convertElementsToFlow from "./editor/elementsToFlow";

interface RunButtonProps {
  flowId: string;
  flowName: string;
}

const RunButton: React.FC<RunButtonProps> = ({ flowId, flowName }) => {
  const reactFlow = useReactFlow();
  const nodes = reactFlow.getNodes();
  const edges = reactFlow.getEdges();
  const flow = convertElementsToFlow({ nodes, edges }, { id: flowId, name: flowName });

  const flowInputSet = new Set<string>();
  nodes.forEach(node => {
    const nodeData = node.data?.node;
    if (nodeData && typeof nodeData === 'object' && 'inputs' in nodeData && nodeData.inputs) {
      Object.values(nodeData.inputs).forEach(val => {
        if (typeof val === 'string' && val.startsWith('&')) {
          flowInputSet.add(val.replaceAll('&', ''));
        } else if (Array.isArray(val)) {
          val.forEach(item => {
            if (typeof item === 'string' && item.startsWith('&')) {
              flowInputSet.add(item.replaceAll('&', ''));
            }
          });
        }
      });
    }
  });
  const flowInputs = Array.from(flowInputSet);

  const [inputValues, setInputValues] = useState<Record<string, string>>({});

  const [loading, setLoading] = useState(false);

  const handleInputChange = (name: string, value: string) => {
    setInputValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // await runFlowAction(flow.id, inputValues);
      toast.success("Flow ran successfully!");
    } catch (error) {
      console.error("Error running flow:", error);
      toast.error("Failed to run flow.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="default" disabled={loading}>
            {loading ? <LoaderCircleIcon className="animate-spin" /> : <Play strokeWidth={2.5} />} Run Flow
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[425px]">
          <DialogTitle>Provide Flow Inputs</DialogTitle>
          <form
            onSubmit={handleSubmit}
          >
            {flowInputs.map((name) => (
              <div key={name} className="mb-3">
                <label>
                  {name.replaceAll('&', '').replaceAll('_', ' ').replace(/^\w/, c => c.toUpperCase())}:
                </label>
                <Input
                  type="text"
                  value={inputValues[name] || ''}
                  onChange={e => handleInputChange(name, e.target.value)}
                  required
                />
              </div>
            ))}
            <DialogFooter>
              <DialogClose asChild>
                <Button type="button" variant="default">
                  Cancel
                </Button>
              </DialogClose>
              <Button type="submit" variant="primary" disabled={loading}>
                Run
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
};
export default RunButton;