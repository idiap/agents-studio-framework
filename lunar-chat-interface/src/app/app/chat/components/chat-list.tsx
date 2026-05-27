// SPDX-FileCopyrightText: Copyright © 2024 Lunarbase (https://lunarbase.ai/) <contact@lunarbase.ai>
//
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-or-later

"use client"
import { UIMessage } from "ai"
import "./chat.css"
import { ReactNode } from "react"

interface ChatListProps {
  messages: UIMessage[]
  outputLabels: Record<string, string[]>
  renderItem: (message: UIMessage, index: number) => ReactNode
}

const ChatList: React.FC<ChatListProps> = ({ messages, renderItem }) => {
  return <div
    className="mt-auto flex flex-col"
  >
    {messages.map((message, index) => (
      <div key={index} className={message.role === 'user' ? 'self-end' : ''}>
        {renderItem(message, index)}
      </div>
    ))}
  </div>
}

export default ChatList
