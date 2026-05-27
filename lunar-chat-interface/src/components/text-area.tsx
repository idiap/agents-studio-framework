// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { Textarea } from "@/components/ui/textarea"

export const SearchTextArea: React.FC<React.ComponentProps<"textarea">> = (props) => {
  return (
    <Textarea
      {...props}
      className="border-0 shadow-none focus:border-transparent focus:ring-0 focus:border-0 focus-visible:ring-0 focus-visible:outline-0 bg-transparent"
    />
  )
}
