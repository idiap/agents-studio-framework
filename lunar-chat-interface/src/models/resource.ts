// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

export interface Resource {
  external_reference: string
  resource_type: string
  content: string
}

export interface ResourceHighlight {
  resource_external_reference: string
  highlight: string
}