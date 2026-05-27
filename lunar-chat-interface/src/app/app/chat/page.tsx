// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { randomUUID } from "crypto";
import { redirect } from "next/navigation";

export default async function Page() {
  // Generate UUID on the server side without creating chat in DB
  // Chat will only be created when assistant generates content
  const id = randomUUID();
  redirect(`chat/${id}`);
}

export const dynamic = "force-dynamic";
