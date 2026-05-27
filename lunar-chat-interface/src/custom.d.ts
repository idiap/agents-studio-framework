// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

/* eslint-disable @typescript-eslint/no-unused-vars */
import NextAuth, { DefaultSession } from "next-auth"

declare module "next-auth" {
  interface User {
    id: string
    login?: string
    accessToken?: string
  }

  interface Session {
    accessToken?: string
    provider?: string
    user: {
      id?: string
      login?: string
    } & DefaultSession["user"]
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string
    provider?: string
    userId?: string
    login?: string
  }
}

declare module "*.svg" {
  const content: React.FunctionComponent<React.SVGAttributes<SVGElement>>;
  export default content;
}
