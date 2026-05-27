// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import NextAuth from "next-auth"
import { authOptions } from "./auth-options"

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST }