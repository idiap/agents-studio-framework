// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { useState } from "react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronRight } from "lucide-react";

interface ChatCollapsibleProps {
  title: string;
  children: React.ReactNode;
}

const ChatCollapsible: React.FC<ChatCollapsibleProps> = ({ title, children }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (<Collapsible open={isOpen} onOpenChange={setIsOpen}>
    <CollapsibleTrigger className="flex items-center gap-2 p-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors">
      {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      {title}
    </CollapsibleTrigger>
    <CollapsibleContent>
      <div className="bg-gray-100 p-4 rounded-md mt-2 mb-4">
        {children}
      </div>
    </CollapsibleContent>
  </Collapsible>)
}

export default ChatCollapsible;
