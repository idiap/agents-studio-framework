// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { NextRequest, NextResponse } from "next/server";
import { serverApiUrl } from "@/configuration";
import { getAuthHeaders } from "@/lib/server-auth";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ reportId: string }> }
) {
  try {
    const { reportId } = await params;

    const headers = await getAuthHeaders();
    const response = await fetch(`${serverApiUrl}/report/${reportId}`, {
      cache: "no-store",
      method: "GET",
      headers,
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: "Failed to fetch report from backend" },
        { status: response.status }
      );
    }

    const report = await response.json();
    return NextResponse.json(report);
  } catch (error) {
    console.error("Error fetching report:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ reportId: string }> }
) {
  try {
    const { reportId } = await params;
    const body = await request.json();

    const headers = await getAuthHeaders({
      "Content-Type": "application/json",
    });
    const response = await fetch(`${serverApiUrl}/report/${reportId}`, {
      method: "PUT",
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: "Failed to update report" },
        { status: response.status }
      );
    }

    const report = await response.json();
    return NextResponse.json(report);
  } catch (error) {
    console.error("Error updating report:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ reportId: string }> }
) {
  try {
    const { reportId } = await params;

    const headers = await getAuthHeaders();
    const response = await fetch(`${serverApiUrl}/report/${reportId}`, {
      method: "DELETE",
      headers,
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: "Failed to delete report" },
        { status: response.status }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error deleting report:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
