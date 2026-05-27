// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

export type ContentType = "markdown" | "html" | "latex";

export interface Report {
  id: string;
  name: string;
  title: string;
  description: string;
  filename: string;
  createdAt?: string;
  contentType?: ContentType;
  contentTypeId?: number;
}
