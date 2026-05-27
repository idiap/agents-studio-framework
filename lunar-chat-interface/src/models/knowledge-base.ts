// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

export interface KnowledgeBase {
  id: string
  name: string
  description: string | null
  fields: KnowledgeBaseField[]
}

export interface KnowledgeBaseFile {
  id: string
  name: string
  contentType: string
  size: number
  createdAt: string
}

export interface KnowledgeBaseField {
  id: string
  name: string
  knowledge_base_id: string
  type: number
  content: KnowledgeBaseContentSummary[]
  content_count: number
}

export interface KnowledgeBaseContentSummary {
  id: string
  name: string
}

export interface KnowledgeBaseContent {
  id: string
  name: string
  knowledge_base_field_id: string
  content?: string | ArrayBuffer
  created_at?: string
  size?: number
}
