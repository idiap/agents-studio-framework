// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  model_id: string;
  api_base: string | null;
  api_version: string | null;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface AIModelSelectProps {
  models: AIModel[];
  value: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
  triggerClassName?: string;
  disabled?: boolean;
}

export function AIModelSelect({
  models,
  value,
  onValueChange,
  placeholder = "Select a model...",
  triggerClassName = "flex-1 h-9",
  disabled = false,
}: AIModelSelectProps) {
  return (
    <Select value={value} onValueChange={onValueChange} disabled={disabled}>
      <SelectTrigger className={triggerClassName}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {models.map((model) => (
          <SelectItem key={model.id} value={model.id}>
            <span className="font-medium">{model.name}</span>
            <span className="text-muted-foreground ml-1.5 text-xs">
              {model.provider}/{model.model_id}
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
