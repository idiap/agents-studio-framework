// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Handle, Position } from "@xyflow/react"
import React from "react"

interface InputProps extends React.DetailedHTMLProps<React.HTMLAttributes<HTMLDivElement>, HTMLDivElement> {
  id?: string
}

const InputHandle: React.FC<InputProps> = ({ id, ...rest }) => {
  return <div {...rest}>
    <Handle type="target" position={Position.Left} id={id ?? '2'} className="-ml-6" isConnectableStart={false} />
  </div>
}

export default InputHandle
