// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use server'

import { serverApiUrl } from "@/configuration"
import { fetchWithServerAuth } from "@/lib/server-auth"

export const buildReportAction = async (context?: string): Promise<string> => {
  const url = `${serverApiUrl}/report`
  const response = await fetchWithServerAuth(url, {
    method: 'POST',
    body: JSON.stringify({
      context
    }),
    headers: {
      'Content-Type': 'application/json',
    },
  })
  const data = await response.json()
  return data
}
