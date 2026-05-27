// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client'
import { ReactNode } from "react"

interface ChatListItemProps {
  userMessage: ReactNode
  assistantMessage: ReactNode
  role: string
}

const ChatListItem: React.FC<ChatListItemProps> = ({
  userMessage,
  assistantMessage,
  role,
}) => {
  switch (role) {
    case 'user':
      return <>{userMessage}</>
    case 'assistant':
      return <>{assistantMessage}</>
    case 'system':
      return <></>
    default:
      throw new Error(`Unknown message role: ${role}`)
  }
}

export default ChatListItem
