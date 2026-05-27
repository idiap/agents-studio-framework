// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client"
import Button from "@/components/button"
import { useReactFlow } from "@xyflow/react";
import { LoaderIcon, Save } from "lucide-react"
import { useState } from "react";
import convertElementsToFlow from "./editor/elementsToFlow";

interface SaveButtonProps {
  flowId: string;
  flowName: string;
}

const SaveButton: React.FC<SaveButtonProps> = ({ flowId, flowName }) => {
  const [loading, setLoading] = useState(false);
  const reactFlow = useReactFlow();
  const onSave = async () => {
    setLoading(true);
    try {
      const nodes = reactFlow.getNodes();
      const edges = reactFlow.getEdges();
      const flow = convertElementsToFlow({ nodes, edges }, { id: flowId, name: flowName });
      // await saveFlow(flowId, flow);
    } catch (error) {
      console.error("Failed to save flow:", error);
    } finally {
      setLoading(false);
    }
  }

  return <Button variant="default" className="cursor-pointer" onClick={onSave} disabled={loading}>
    {loading ? <LoaderIcon /> : <><Save strokeWidth={2.5} /> Save</>}
  </Button>
}

export default SaveButton
