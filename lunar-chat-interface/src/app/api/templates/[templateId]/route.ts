// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { NextRequest, NextResponse } from 'next/server'
import { serverApiUrl } from '@/configuration'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ templateId: string }> }
) {
  try {
    const { templateId } = await params

    const response = await fetch(`${serverApiUrl}/templates/${templateId}`, {
      cache: 'no-store',
      method: 'GET',
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch template from backend' },
        { status: response.status }
      )
    }

    const template = await response.json()
    return NextResponse.json(template)
  } catch (error) {
    console.error('Error fetching template:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ templateId: string }> }
) {
  try {
    const { templateId } = await params
    const body = await request.json()

    const response = await fetch(`${serverApiUrl}/templates/${templateId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to update template' },
        { status: response.status }
      )
    }

    const template = await response.json()
    return NextResponse.json(template)
  } catch (error) {
    console.error('Error updating template:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ templateId: string }> }
) {
  try {
    const { templateId } = await params

    const response = await fetch(`${serverApiUrl}/templates/${templateId}`, {
      method: 'DELETE',
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to delete template' },
        { status: response.status }
      )
    }

    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error('Error deleting template:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
