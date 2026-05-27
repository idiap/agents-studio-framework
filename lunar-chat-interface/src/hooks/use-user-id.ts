// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { useSession } from "next-auth/react"
import { useEffect, useState } from "react"

export const useUserId = (): string | null => {
  const { data: session, status } = useSession()
  const [userId, setUserId] = useState<string | null>(null)

  useEffect(() => {
    if (status === "unauthenticated" || status === "loading") {
      setUserId(null)
    } else {
      setUserId(session?.user?.id ?? session?.user?.email ?? null)
    }
  }, [status, session])

  return userId
}
