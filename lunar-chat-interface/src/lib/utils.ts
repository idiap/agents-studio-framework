// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const parseUtcDate = (value: string): Date | null => {
  if (!value) {
    return null
  }

  const trimmed = value.trim()
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(trimmed)
  const normalized = hasTimezone
    ? trimmed
    : `${trimmed.replace(" ", "T")}Z`

  const timestamp = Date.parse(normalized)

  if (Number.isNaN(timestamp)) {
    return null
  }

  return new Date(timestamp)
}

export const formatRelativeDate = (isoDate: string) => {
  try {
    const formatter = new Intl.RelativeTimeFormat(undefined, {
      numeric: "auto",
    })
    const now = Date.now()
    const parsedDate = parseUtcDate(isoDate) ?? new Date(isoDate)
    const then = parsedDate.getTime()

    if (Number.isNaN(then)) {
      throw new Error(`Unable to parse date: ${isoDate}`)
    }

    const diff = then - now
    const diffMinutes = Math.round(diff / (1000 * 60))
    const diffHours = Math.round(diff / (1000 * 60 * 60))
    const diffDays = Math.round(diff / (1000 * 60 * 60 * 24))

    if (Math.abs(diffMinutes) < 60) {
      return formatter.format(diffMinutes, "minute")
    }
    if (Math.abs(diffHours) < 48) {
      return formatter.format(diffHours, "hour")
    }
    return formatter.format(diffDays, "day")
  } catch (error) {
    console.error("Error formatting date", error)
    const parsedDate = parseUtcDate(isoDate)
    return (parsedDate ?? new Date(isoDate)).toLocaleString(undefined, {
      timeZone: "UTC",
    })
  }
}
