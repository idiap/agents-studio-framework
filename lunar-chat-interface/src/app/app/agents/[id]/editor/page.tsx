// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { ReactFlowProvider } from "@xyflow/react";
import { FlowModel } from "./models/flow";
import RunButton from "./components/run";
import SaveButton from "./components/save";
import Editor from "./components/editor/editor";
import { ComponentsProvider } from "@/context/componentsContext";
import { serverApiUrl } from "@/configuration";
import { fetchWithServerAuth } from "@/lib/server-auth";

export default async function EditorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const flow = await fetchWithServerAuth(
    `${serverApiUrl}/flow/${(await params).id}?definition=true`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    },
  );
  if (!flow.ok) {
    throw new Error(`Failed to fetch flow: ${flow.statusText}`);
  }
  const initialFlowModel: FlowModel = await flow.json();
  console.log(">>>Fetched flow successfully", initialFlowModel);

  return (
    <div className="w-full h-full">
      <ComponentsProvider>
        <ReactFlowProvider>
          <div className="absolute right-0 m-2 z-10 flex gap-2">
            <RunButton
              flowId={initialFlowModel.id}
              flowName={initialFlowModel.name}
            />
            <SaveButton
              flowId={initialFlowModel.id}
              flowName={initialFlowModel.name}
            />
          </div>
          <Editor initialFlow={initialFlowModel} />
        </ReactFlowProvider>
      </ComponentsProvider>
    </div>
  );
}
