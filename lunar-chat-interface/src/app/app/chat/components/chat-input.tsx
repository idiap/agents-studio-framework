// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client"

import { ChatRequestOptions } from "ai"
import { SearchTextArea } from "@/components/text-area";
import { ReactNode, useState } from "react";
import { Toggle } from "@/components/ui/toggle";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { X, Plus } from "lucide-react";

interface ChatOption {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  isActive: boolean
}

interface ChatInputProps {
  actionButtons: ReactNode[]
  handleSubmit: (event?: {
    preventDefault?: () => void;
  }, chatRequestOptions?: ChatRequestOptions) => void
  input: string
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement> | React.ChangeEvent<HTMLTextAreaElement>) => void
  availableOptions: ChatOption[]
  onOptionToggle: (optionId: string, isActive: boolean) => void
}

const ChatInput: React.FC<ChatInputProps> = ({
  actionButtons,
  handleSubmit,
  input,
  handleInputChange,
  availableOptions,
  onOptionToggle,
}) => {
  const [isHovered, setIsHovered] = useState<string | null>(null);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  const activeOptions = availableOptions.filter(option => option.isActive);
  const inactiveOptions = availableOptions.filter(option => !option.isActive);

  // Create options object for submission
  const options = activeOptions.reduce((acc, option) => {
    acc[option.id] = true;
    return acc;
  }, {} as Record<string, boolean>);

  const handleAddOption = (optionId: string) => {
    onOptionToggle(optionId, true);
    setIsPopoverOpen(false);
  };

  const handleRemoveOption = (optionId: string) => {
    onOptionToggle(optionId, false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e, { body: { options } });
    }
  }
  return <div className="sticky bottom-0 z-10 right-0 left-0 w-full bg-white">
    <div style={{ backgroundColor: "#ffffff" }} className="flex flex-col p-4 w-full bg-transparent overflow-hidden shadow-lg border-[1px] rounded-lg mb-10">
      <SearchTextArea value={input} onChange={handleInputChange} onKeyDown={handleKeyDown} placeholder='Search' />
      <div className="flex items-center mt-1 gap-2">
        {inactiveOptions.length > 0 && (
          <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8">
                <Plus className="w-4 h-4" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-48 p-2" align="start">
              {inactiveOptions.map((option) => {
                const IconComponent = option.icon;
                return (
                  <Button
                    key={option.id}
                    variant="ghost"
                    className="w-full justify-start"
                    onClick={() => handleAddOption(option.id)}
                  >
                    <IconComponent className="w-4 h-4 mr-2" />
                    {option.label}
                  </Button>
                );
              })}
            </PopoverContent>
          </Popover>
        )}

        {activeOptions.map((option) => {
          const IconComponent = option.icon;
          return (
            <Toggle
              key={option.id}
              pressed={true}
              onPressedChange={() => handleRemoveOption(option.id)}
              className="bg-background-highlight"
              onMouseEnter={() => setIsHovered(option.id)}
              onMouseLeave={() => setIsHovered(null)}
            >
              {isHovered === option.id ? (
                <X className="w-4 h-4" />
              ) : (
                <IconComponent className="w-4 h-4" />
              )}
              {option.label}
            </Toggle>
          );
        })}
        <div className="ml-auto" />
        {actionButtons}
      </div>
    </div>
  </div>
}

export default ChatInput
