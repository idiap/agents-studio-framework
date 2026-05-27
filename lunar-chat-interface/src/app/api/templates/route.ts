// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { NextRequest, NextResponse } from 'next/server'
import { serverApiUrl } from '@/configuration'

export async function GET() {
  try {
    const response = await fetch(`${serverApiUrl}/templates`, {
      cache: 'no-store',
      method: 'GET',
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch templates from backend' },
        { status: response.status }
      )
    }

    const templates = await response.json()
    return NextResponse.json(templates)
  } catch (error) {
    console.error('Error fetching templates:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(`${serverApiUrl}/templates`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to create template' },
        { status: response.status }
      )
    }

    const template = await response.json()
    return NextResponse.json(template, { status: 201 })
  } catch (error) {
    console.error('Error creating template:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
