// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import React from "react";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import InputHandle from "@/components/xyflow/inputHandle";

interface GenericCardInputProps {
  inputKey: string;
  value: unknown;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
}

interface GenericCardTextInputProps extends GenericCardInputProps {
  value: string;
}

const CardTextInput: React.FC<GenericCardTextInputProps> = ({ inputKey, value, onChange }) => {
  return (
    <div className="flex flex-col gap-2 nodrag nowheel">
      {value.length > 100 ? (
        <Textarea
          id={inputKey}
          value={String(value)}
          onChange={onChange}
          className="max-h-[200px] overflow-y-auto"
        />
      ) : (
        <Input
          id={inputKey}
          type="text"
          value={String(value)}
          onChange={onChange}
          className="w-full"
        />
      )}
    </div>
  );
};

const GenericCardInput: React.FC<GenericCardInputProps> = ({ inputKey, value, onChange }) => {
  const isVariable = typeof value === "string" && value.startsWith("$");
  const isArray = Array.isArray(value);
  if (isArray) {
    return (
      <div className="flex flex-col gap-2 nodrag nowheel">
        {!isVariable && !isArray && <Label htmlFor={inputKey}>{inputKey}</Label>}
        {value.map((item, index) => (
          <GenericCardInput
            key={`${inputKey}-${index}`}
            inputKey={`${inputKey}[${index}]`}
            value={item}
            onChange={onChange}
          />
        ))}
      </div>
    );
  }
  const displayValue = typeof value === "object" ? JSON.stringify(value) : String(value);
  return (
    <div className="flex flex-col gap-2 nodrag nowheel">
      {!isVariable && <Label htmlFor={inputKey}>{inputKey}</Label>}

      <div className="relative flex flex-1 flex-col">
        <InputHandle id={inputKey} />
        {isVariable ? (
          <Label htmlFor={inputKey}>{inputKey}</Label>
        ) : (
          <CardTextInput
            inputKey={inputKey}
            value={displayValue}
            onChange={onChange}
          />
        )}
      </div>
    </div>
  );
};

export default GenericCardInput;
