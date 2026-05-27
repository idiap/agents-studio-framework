// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Navbar } from "@/components/navbar";
import AgentsList from "./components/agents-list";
import PageContainer from "@/components/page-container/page-container";
import { getFlows, Flow, FlowInput, InputType } from "@/actions/get-flows";
import CreateAgentButton from "./components/create-agent-button";

export type { InputType, FlowInput, Flow };
export const dynamic = "force-dynamic";

const AgentsPage: React.FC = async () => {
  const agents = await getFlows();

  return (
    <>
      <Navbar title="Agents" />
      <PageContainer>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-3xl font-semibold text-foreground">Agents</h1>
          <CreateAgentButton />
        </div>
        <AgentsList agents={agents} />
      </PageContainer>
    </>
  );
};

export default AgentsPage;
