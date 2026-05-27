// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Edit, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useReactFlow } from "@xyflow/react";
import { Node } from "../genericCard/genericCard";

interface Template {
  id: string;
  name: string;
  content: string;
}

interface TemplateInputProps {
  id: string;
  inputKey?: string;
}

const TemplateInput: React.FC<TemplateInputProps> = ({ id, inputKey }) => {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const { setNodes } = useReactFlow();

  const extractVariablesFromTemplate = (templateContent: string): string[] => {
    const variableRegex = /\{(\w+)\}/g;
    const variables = new Set<string>();
    let match;

    while ((match = variableRegex.exec(templateContent)) !== null) {
      variables.add(match[1]);
    }

    return Array.from(variables);
  };

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);
    const selectedTemplate = templates.find((t) => t.id === templateId);
    if (selectedTemplate) {
      const variables = extractVariablesFromTemplate(selectedTemplate.content);

      setNodes((nodes) =>
        nodes.map((node) => {
          if (node.id !== id) return node;
          const lunarNode = (node as Node).data.node;

          // Update template content
          lunarNode.inputs["template"] = selectedTemplate.content;

          // Remove old template variables (those starting with variables that are no longer in the template)
          const currentKeys = Object.keys(lunarNode.inputs);
          const oldVariableKeys = currentKeys.filter(
            (key) => key !== "template" && !variables.includes(key)
          );
          oldVariableKeys.forEach((key) => {
            delete lunarNode.inputs[key];
          });

          // Add new template variables with empty string defaults if they don't exist
          variables.forEach((variable) => {
            if (!(variable in lunarNode.inputs)) {
              lunarNode.inputs[variable] = "";
            }
          });

          return {
            ...node,
            data: {
              component: node.data.component,
              node: lunarNode,
            },
          };
        })
      );
    }
  };

  useEffect(() => {
    fetch("/api/templates")
      .then((res) => res.json())
      .then((data) => {
        setTemplates(data);
        const templateInput = data.node
          ? Object.entries(data.node.inputs).find(([key]) => key === "template")
          : null;
        if (templateInput) {
          const currentContent = templateInput[1];
          const matchingTemplate = data.find(
            (t: Template) => t.content === currentContent
          );
          if (matchingTemplate) {
            setSelectedTemplateId(matchingTemplate.id);
          }
        }
      })
      .catch((err) => console.error("Failed to fetch templates:", err));
  }, []);

  return (
    <div key={inputKey} className="grid w-full gap-2">
      <Label htmlFor={`template-select-${id}`}>Template</Label>
      <Select value={selectedTemplateId} onValueChange={handleTemplateSelect}>
        <SelectTrigger id={`template-select-${id}`}>
          <SelectValue placeholder="Select a template" />
        </SelectTrigger>
        <SelectContent>
          {templates.map((template) => (
            <SelectItem key={template.id} value={template.id}>
              {template.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <div className="flex flex-col gap-2 mt-1">
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="flex-1"
          onClick={() => router.push("/app/templates")}
        >
          <Plus className="w-3 h-3 mr-1" />
          New Template
        </Button>
        {selectedTemplateId && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => router.push(`/app/templates/${selectedTemplateId}`)}
          >
            <Edit className="w-3 h-3 mr-1" />
            Edit Template
          </Button>
        )}
      </div>
    </div>
  );
};

export default TemplateInput;
