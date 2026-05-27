// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { authOptions } from "@/app/api/auth/[...nextauth]/auth-options";
import { getServerSession } from "next-auth";

export const getUserId = async (): Promise<string | null> => {
  const session = await getServerSession(authOptions);
  return session?.user?.id ?? null;
}
