// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { serverApiUrl } from "@/configuration"
import { fetchWithServerAuth } from "@/lib/server-auth"

export const buildComparativeReportAction = async () => {
  const response = await fetchWithServerAuth(`${serverApiUrl}/report/comparative`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  })
  if (!response.ok) {
    throw new Error('Failed to build report')
  }
  const data = await response.json()
  return data
}
