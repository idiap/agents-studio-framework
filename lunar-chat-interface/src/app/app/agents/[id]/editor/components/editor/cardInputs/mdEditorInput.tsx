// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const MDEditor = dynamic(() => import("@uiw/react-md-editor"), { ssr: false });

interface MdEditorInputProps {
  inputKey: string;
  value: string;
  onChange: (value: string) => void;
}

export const MdEditorInput: React.FC<MdEditorInputProps> = ({
  inputKey,
  value,
  onChange,
}) => {
  const [open, setOpen] = useState(false);
  const [localValue, setLocalValue] = useState(value);

  useEffect(() => {
    if (!open) {
      document.body.style.overflow = 'unset'; // or 'scroll' or ''
    }
  }, [open]);

  const handleOpenChange = (isOpen: boolean) => {
    if (isOpen) {
      setLocalValue(value);
    }
    setOpen(isOpen);
  };

  const handleSave = () => {
    onChange(localValue);
    setOpen(false);
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium">{inputKey}</label>
      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogTrigger asChild>
          <Button variant="outline" className="w-full gap-2">
            Edit
          </Button>
        </DialogTrigger>
        <DialogContent className="min-w-[1000px] max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader className="flex flex-row items-center">
            <DialogTitle>Edit General Instructions</DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-auto min-h-[500px]" data-color-mode="light">
            <MDEditor
              value={localValue}
              onChange={(val) => setLocalValue(val || "")}
              height={500}
              hideToolbar={false}
            />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave}>Save</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MdEditorInput;
