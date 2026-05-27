// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { authOptions } from "@/app/api/auth/[...nextauth]/auth-options";
import { getServerSession } from "next-auth";

export const getServerAccessToken = async (): Promise<string | null> => {
  const session = await getServerSession(authOptions);
  const token = session?.accessToken;
  return typeof token === "string" && token.length > 0 ? token : null;
};

export const getAuthHeaders = async (
  headers?: HeadersInit,
): Promise<Headers> => {
  const result = new Headers(headers);
  const accessToken = await getServerAccessToken();

  if (accessToken) {
    result.set("Authorization", `Bearer ${accessToken}`);
  }

  return result;
};

export const fetchWithServerAuth = async (
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> => {
  const headers = await getAuthHeaders(init?.headers);
  return fetch(input, {
    ...init,
    headers,
  });
};
