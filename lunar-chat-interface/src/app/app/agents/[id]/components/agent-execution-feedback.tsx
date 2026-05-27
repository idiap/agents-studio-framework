// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client'

import { Fragment } from 'react'
import type { UIMessage } from 'ai'
import AssistantMessagePart from '@/app/app/chat/components/assistant-message-part'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'

interface AgentExecutionFeedbackProps {
  messages: UIMessage[]
  isStreaming: boolean
  error: Error | null
  onComplete?: () => void
}

export default function AgentExecutionFeedback({
  messages,
  isStreaming,
  error,
}: AgentExecutionFeedbackProps) {
  const hasContent = messages.length > 0 || isStreaming || error

  if (!hasContent) {
    return (
      <div className="flex items-center justify-center p-8 text-muted-foreground">
        <p>Agent output will appear here...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Streaming status indicator */}
      {isStreaming && (
        <Alert className="border-blue-200 bg-blue-50">
          <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
          <AlertDescription className="text-blue-900">
            Agent is running...
          </AlertDescription>
        </Alert>
      )}

      {/* Error display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error.message}
          </AlertDescription>
        </Alert>
      )}

      {/* Completion indicator */}
      {!isStreaming && !error && messages.length > 0 && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-900">
            Agent execution completed
          </AlertDescription>
        </Alert>
      )}

      {/* Messages output */}
      <ScrollArea className="h-[400px] w-full rounded-md border p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className="space-y-2">
              {message.parts?.map((part, index) => (
                <Fragment key={index}>
                  <AssistantMessagePart
                    messagePart={part}
                    index={index}
                    addToolResult={async () => {
                      // No-op for agent execution - we don't need interactive tool results
                    }}
                  />
                </Fragment>
              ))}
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
