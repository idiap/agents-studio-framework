// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { UIMessage } from "ai";
import { Fragment, ReactNode } from "react";

type MessagePart = NonNullable<UIMessage['parts']>[number];

interface AssistantMessageProps {
  message: UIMessage
  messagePartRender: (messagePart: MessagePart, index: number) => ReactNode
}

const AssistantMessage: React.FC<AssistantMessageProps> = ({
  message,
  messagePartRender,
}) => {
  return <div className="mb-12">
    {message.parts?.map((part, index) => <Fragment key={index}>
      {messagePartRender(part, index)}
    </Fragment>)}
  </div>
}

export default AssistantMessage
