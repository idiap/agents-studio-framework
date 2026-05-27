// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use client";

import type { Flow } from "../page";
import { useRouter } from "next/navigation";
import AgentListItem from "./agent-list-item";

interface AgentsListProps {
  agents: Flow[];
}

export default function AgentsList({ agents }: AgentsListProps) {
  const router = useRouter();

  const handleAgentClick = (agent: Flow) => {
    router.push(`/app/agents/${agent.id}`);
  };

  return (
    <div className="w-full">
      <div className="flex flex-col divide-y rounded-md">
        {agents.map((agent) => (
          <AgentListItem
            key={agent.id}
            flow={agent}
            onClick={() => handleAgentClick(agent)}
          />
        ))}
      </div>
    </div>
  );
}
