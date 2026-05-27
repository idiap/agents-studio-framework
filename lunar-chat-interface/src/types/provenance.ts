// SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
//
// SPDX-License-Identifier: GPL-3.0-only

export interface BundleHashInfo {
  sha256_nt_sorted: string;
  triple_count: number;
}

export interface Manifest {
  base_uri: string;
  flow_id: string;
  run_id: string;
  bundles: Record<string, string>;
  generated_at: string;
  bundle_hashes: Record<string, BundleHashInfo>;
}

export interface DataSource {
  id: string;
  uri: string;
  value: any;
  summary: string;
  is_external: boolean;
}

export interface RunInfo {
  started_at: string;
  ended_at: string;
  duration_s?: number | null;
}

export interface InputBinding {
  name: string;
  raw: any;
  kind: "step_output" | "flow_input" | "literal";
  ref?: string;
  field?: string;
  value?: any;
  value_summary?: string;
}

export interface LLMMetadata {
  model?: string | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  total_tokens?: number | null;
}

export interface StepTrustData {
  trust_index: number;
  confidence: number;
  band: "green" | "amber" | "red";
  risk: number;
  step_kind: "GEN" | "RET" | "DET" | "VER" | "HUM";
  depth: number;
  missingness: number;
  risk_factors: Record<string, any>;
  subscores: Record<string, number>;
  drivers: Record<string, any>[];
  actions: string[];
  summary: string;
  details: Record<string, any>;
}

export interface StepView {
  id: string;
  component: string;
  plan: Record<string, any>;
  depends_on: string[];
  flow_inputs_used: string[];
  run: RunInfo;
  inputs: InputBinding[];
  output: { value: any | null; summary: string };
  generative: boolean;
  llm_metadata?: LLMMetadata | null;
  uri?: string;
  // Trust score data
  trust?: StepTrustData | null;
}

export interface Edge {
  type: string;
  from_step: string;
  to_step: string;
  via?: string;
  field?: string;
}

export interface RecentOutput {
  step: string;
  ended_at: string;
  summary: string;
}

export interface WorkflowView {
  id: string;
  name: string;
  description?: string;
  status?: string;
  started_at?: string;
  completed_at?: string;
  uri?: string;
}

export interface ViewModel {
  base_uri: string;
  run_id: string;
  workflow: WorkflowView;
  data_sources: DataSource[];
  steps: StepView[];
  edges: Edge[];
  recent_outputs: RecentOutput[];
}

export interface StepTrustScore {
  step_id: string;
  trust_index: number;
  risk: number;
  kind: "GEN" | "RET" | "DET" | "VER" | "HUM";
  depth: number;
  missingness: number;
  band: "green" | "amber" | "red";
  risk_factors: Record<string, any>;
}

export interface TrustScoreData {
  trust_index: number;
  confidence: number;
  band: "green" | "amber" | "red";
  subscores: Record<string, number>;
  drivers: Record<string, any>[];
  actions: string[];
  summary: string;
  step_scores: Record<string, StepTrustScore>;
  details?: Record<string, any>;
}

export interface Provenance {
  manifest: Manifest;
  trig: string;
  view_model: ViewModel;
  trust_score?: TrustScoreData | null;
}
