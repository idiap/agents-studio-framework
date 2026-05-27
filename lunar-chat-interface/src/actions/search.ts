// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { AxiosResponse } from "axios"
import auroraApi from "../app/api/auroraApi"
import { ResourceHighlight } from "../models/resource"

export const searchResourceAction = async (query: string) => {
  const { data } = await auroraApi.get<unknown, AxiosResponse<ResourceHighlight[]>>(`/search?query=${query}`)
  return data
}
