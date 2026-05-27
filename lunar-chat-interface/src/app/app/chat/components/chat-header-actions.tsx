// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

'use client'

import AvatarDropdown from "@/components/avatar-dropdown";

const ChatHeaderActions: React.FC = () => {
  return <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
    <AvatarDropdown />
  </div>
}

export default ChatHeaderActions;
