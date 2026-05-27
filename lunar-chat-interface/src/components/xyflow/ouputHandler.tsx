// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Handle, Position } from "@xyflow/react"

interface OutputHandleProps {
  name: string
}

const OutputHandle: React.FC<OutputHandleProps> = ({ name }) => {
  return <div className="relative">
    <p className="text-right">{name}</p>
    <Handle type="source" position={Position.Right} id={'1'} className="-mr-6" isConnectableEnd={false} />
  </div>
}

export default OutputHandle