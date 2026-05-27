// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { NodeModel } from "./node";

export interface FlowModel {
  id: string;
  name: string;
  description?: string;
  nodes: Array<NodeModel | FlowModel>;
}