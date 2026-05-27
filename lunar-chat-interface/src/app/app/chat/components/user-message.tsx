// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

import { UIMessage } from "ai"

interface UserMessageProps {
  message: UIMessage
}

const UserMessage: React.FC<UserMessageProps> = ({ message }) => {
  return <div className="lunar-user-message mb-6" style={{
    backgroundColor: '#1E3257',
    paddingTop: 8,
    paddingBottom: 8,
    paddingLeft: 16,
    paddingRight: 16,
    borderRadius: 8,
    alignSelf: 'end',
    display: 'inline-block',
    position: 'relative'
  }}>
    {message.parts?.map((part, index) => part.type === "text" ? <p key={index} style={{ color: '#fff' }}>{part.text}</p> : <></>)}
  </div>
}

export default UserMessage
