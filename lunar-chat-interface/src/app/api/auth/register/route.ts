// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { NextRequest, NextResponse } from "next/server";
import { serverApiUrl } from "@/configuration";

export async function POST(request: NextRequest) {
  if (!serverApiUrl) {
    return NextResponse.json(
      { error: "Server API URL is not configured" },
      { status: 500 },
    );
  }

  try {
    const body = await request.json();

    const response = await fetch(`${serverApiUrl}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json().catch(() => ({}));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Error registering user:", error);
    return NextResponse.json({ error: "Failed to register user" }, { status: 500 });
  }
}
