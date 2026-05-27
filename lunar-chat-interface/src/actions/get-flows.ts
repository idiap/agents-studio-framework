// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

"use server";

import { serverApiUrl } from "@/configuration";
import { fetchWithServerAuth } from "@/lib/server-auth";

export type InputType = "string" | "knowledge-base" | "knowledge-base-field";

export interface FlowInput {
  id: string;
  label: string;
  type: InputType;
  required: boolean;
}

export interface Flow {
  id: string;
  name: string;
  description: string | null;
  inputs: FlowInput[];
}

function normalizeFlowInput(rawInput: unknown): FlowInput | null {
  if (!rawInput || typeof rawInput !== "object") {
    return null;
  }

  const candidate = rawInput as Partial<FlowInput>;
  const type = candidate.type;

  if (
    typeof candidate.id !== "string" ||
    typeof candidate.label !== "string" ||
    (type !== "string" &&
      type !== "knowledge-base" &&
      type !== "knowledge-base-field")
  ) {
    return null;
  }

  return {
    id: candidate.id,
    label: candidate.label,
    type,
    required: candidate.required !== false,
  };
}

function normalizeFlow(rawFlow: unknown): Flow {
  const candidate =
    rawFlow && typeof rawFlow === "object"
      ? (rawFlow as Partial<Flow>)
      : ({} as Partial<Flow>);

  const inputs = Array.isArray(candidate.inputs)
    ? candidate.inputs
        .map((input) => normalizeFlowInput(input))
        .filter((input): input is FlowInput => input !== null)
    : [];

  return {
    id: typeof candidate.id === "string" ? candidate.id : "",
    name: typeof candidate.name === "string" ? candidate.name : "Untitled Flow",
    description:
      typeof candidate.description === "string" ? candidate.description : null,
    inputs,
  };
}

export async function getFlows(): Promise<Flow[]> {
  if (!serverApiUrl) {
    throw new Error("Server API URL is not configured");
  }

  try {
    const response = await fetchWithServerAuth(`${serverApiUrl}/flow/list`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to fetch flows: ${response.status} - ${errorText}`,
      );
    }

    const flows = await response.json();
    return Array.isArray(flows) ? flows.map(normalizeFlow) : [];
  } catch (error) {
    console.error("Error fetching flows:", error);
    throw error;
  }
}

export async function getFlowById(id: string): Promise<Flow | null> {
  if (!serverApiUrl) {
    throw new Error("Server API URL is not configured");
  }

  try {
    const response = await fetchWithServerAuth(`${serverApiUrl}/flow/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to fetch flow: ${response.status} - ${errorText}`,
      );
    }

    const flow = await response.json();
    return normalizeFlow(flow);
  } catch (error) {
    console.error("Error fetching flow by id:", error);
    throw error;
  }
}
