// SPDX-FileCopyrightText: Copyright © 2024 Lunarbase (https://lunarbase.ai/) <contact@lunarbase.ai>
//
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-or-later

"use client"

import { ChatRequestOptions } from "ai"
import React from "react"
import Button from "./button"
import { LoaderIcon, SendHorizonal } from "lucide-react"

interface SendButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
  onSubmit: (event?: {
    preventDefault?: () => void;
  }, chatRequestOptions?: ChatRequestOptions) => void
  loading: boolean
  options?: any
}

const SendButton: React.FC<SendButtonProps> = ({ value, onSubmit, loading, options, ...props }) => {

  const handleClick = () => {
    onSubmit(undefined, { body: { options } });
  };

  return <Button
    variant='primary'
    onClick={handleClick}
    disabled={loading || value === ''}
    {...props}
  >
    Send
    {loading
      ? <LoaderIcon className="animate-spin" />
      : <SendHorizonal className="text-lg" strokeWidth={3} />
    }
  </Button>
}

export default SendButton
