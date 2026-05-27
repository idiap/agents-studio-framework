# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Pydantic models for provenance data structures.

These models define the schema for provenance data returned by the service,
ensuring type safety and validation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BundleHashInfo(BaseModel):
    """Information about a provenance bundle hash."""

    sha256_nt_sorted: str = Field(
        description="SHA256 hash of the bundle in N-Triples format"
    )
    triple_count: int = Field(description="Number of RDF triples in the bundle")


class Manifest(BaseModel):
    """Provenance manifest with bundle information."""

    base_uri: str = Field(description="Base URI for provenance entities")
    flow_id: str = Field(description="ID of the workflow")
    run_id: str = Field(description="ID of this execution run")
    bundles: Dict[str, str] = Field(description="Map of bundle names to their URIs")
    generated_at: str = Field(description="ISO timestamp when manifest was generated")
    bundle_hashes: Dict[str, BundleHashInfo] = Field(
        description="Hash information for each bundle"
    )


class DataSource(BaseModel):
    """Original data source (flow input)."""

    id: str = Field(description="Input parameter name")
    uri: str = Field(description="URI of the input entity")
    value: Any = Field(default=None, description="Actual input value")
    summary: str = Field(description="Human-readable summary of the value")
    is_external: bool = Field(
        description="Whether this appears to be an external resource reference"
    )


class RunInfo(BaseModel):
    """Runtime information for a step execution."""

    started_at: Optional[str] = Field(
        default=None, description="ISO timestamp when step started"
    )
    ended_at: Optional[str] = Field(
        default=None, description="ISO timestamp when step ended"
    )
    duration_s: Optional[float] = Field(default=None, description="Duration in seconds")


class InputBinding(BaseModel):
    """Input binding for a step showing data flow."""

    name: str = Field(description="Input parameter name")
    raw: Any = Field(description="Raw input specification")
    kind: str = Field(
        description="Type of binding: step_output, flow_input, or literal"
    )
    ref: Optional[str] = Field(default=None, description="Reference to step or input")
    field: Optional[str] = Field(
        default=None, description="Field path within referenced value"
    )
    value: Any = Field(default=None, description="Resolved input value")
    value_summary: Optional[str] = Field(
        default=None, description="Summary of the value"
    )


class StepOutput(BaseModel):
    """Output from a step execution."""

    value: Any = Field(default=None, description="Output value")
    summary: str = Field(description="Human-readable summary of output")


class LLMMetadata(BaseModel):
    """Metadata specific to LLM/generative steps."""

    model: Optional[str] = Field(
        default=None, description="Model name used (e.g., gpt-4o-2024-08-06)"
    )
    input_tokens: Optional[int] = Field(
        default=None, description="Number of input tokens consumed"
    )
    output_tokens: Optional[int] = Field(
        default=None, description="Number of output tokens generated"
    )
    total_tokens: Optional[int] = Field(default=None, description="Total tokens used")


class StepTrustData(BaseModel):
    """Trust scoring data for a single step."""

    trust_index: int = Field(description="Trust index for this step (0-100)")
    confidence: int = Field(description="Confidence in the trust score (0-100)")
    band: str = Field(description="Trust band (green, amber, red)")
    risk: float = Field(description="Risk score for this step (0-1)")
    step_kind: str = Field(
        description="Step classification kind (GEN, RET, DET, VER, HUM)"
    )
    depth: int = Field(description="Depth in the workflow graph")
    missingness: float = Field(description="Metadata missingness score (0-1)")
    risk_factors: Dict[str, Any] = Field(
        default_factory=dict, description="Breakdown of risk factors"
    )
    subscores: Dict[str, float] = Field(
        default_factory=dict, description="Detailed subscores"
    )
    drivers: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top risk drivers for this step"
    )
    actions: List[str] = Field(
        default_factory=list, description="Recommended actions for this step"
    )
    summary: str = Field(default="", description="Human-readable trust summary")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional trust scoring details"
    )


class StepView(BaseModel):
    """View of a workflow step with runtime information."""

    id: str = Field(description="Step identifier")
    component: str = Field(description="Component name or type")
    plan: Dict[str, Any] = Field(description="Step specification from workflow plan")
    depends_on: List[str] = Field(description="List of step IDs this step depends on")
    flow_inputs_used: List[str] = Field(
        description="List of flow input names used by this step"
    )
    run: RunInfo = Field(description="Runtime execution information")
    inputs: List[InputBinding] = Field(description="Input bindings")
    output: StepOutput = Field(description="Step output")
    uri: Optional[str] = Field(default=None, description="PROV-O URI for this activity")
    generative: bool = Field(
        default=False, description="Whether this is a generative/LLM step"
    )
    llm_metadata: Optional[LLMMetadata] = Field(
        default=None, description="LLM-specific metadata if generative"
    )
    # Trust score data (populated by trustprov service)
    trust: Optional[StepTrustData] = Field(
        default=None, description="Trust scoring data for this step"
    )


class Edge(BaseModel):
    """Dependency edge between steps."""

    type: str = Field(description="Edge type (e.g., dependsOn)")
    from_step: str = Field(description="Source step ID")
    to_step: str = Field(description="Target step ID")
    via: Optional[str] = Field(default=None, description="Input parameter name")
    field: Optional[str] = Field(default=None, description="Field path")

    model_config = ConfigDict(populate_by_name=True)


class RecentOutput(BaseModel):
    """Recent step output information."""

    step: str = Field(description="Step ID")
    ended_at: str = Field(description="ISO timestamp when step completed")
    summary: str = Field(description="Output summary")


class WorkflowView(BaseModel):
    """View of the workflow metadata."""

    id: str = Field(description="Workflow identifier")
    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    status: Optional[str] = Field(default=None, description="Execution status")
    started_at: Optional[str] = Field(
        default=None, description="ISO timestamp when workflow started"
    )
    completed_at: Optional[str] = Field(
        default=None, description="ISO timestamp when workflow completed"
    )
    uri: Optional[str] = Field(default=None, description="PROV-O URI for this plan")


class ViewModel(BaseModel):
    """Complete view model for provenance visualization."""

    base_uri: str = Field(description="Base URI for provenance entities")
    run_id: str = Field(description="Execution run identifier")
    workflow: WorkflowView = Field(description="Workflow information")
    data_sources: List[DataSource] = Field(description="Original data sources")
    steps: List[StepView] = Field(description="Workflow steps with runtime info")
    edges: List[Edge] = Field(description="Dependency edges")
    recent_outputs: List[RecentOutput] = Field(description="Most recent step outputs")


class StepTrustScore(BaseModel):
    """Trust score for a single step."""

    step_id: str = Field(description="Step identifier")
    trust_index: int = Field(description="Trust index (0-100)")
    risk: float = Field(description="Risk score (0-1)")
    kind: str = Field(description="Step kind (GEN, RET, DET, VER, HUM)")
    depth: int = Field(description="Depth in the workflow graph")
    missingness: float = Field(description="Metadata missingness score (0-1)")
    band: str = Field(description="Trust band (green, amber, red)")
    risk_factors: Dict[str, Any] = Field(
        default_factory=dict, description="Breakdown of risk factors"
    )


class TrustScoreData(BaseModel):
    """Trust score data for the entire workflow execution."""

    trust_index: int = Field(description="Overall trust index (0-100)")
    confidence: int = Field(description="Confidence in the trust score (0-100)")
    band: str = Field(description="Trust band (green, amber, red)")
    subscores: Dict[str, float] = Field(
        default_factory=dict, description="Detailed subscores"
    )
    drivers: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top risk drivers"
    )
    actions: List[str] = Field(default_factory=list, description="Recommended actions")
    summary: str = Field(default="", description="Human-readable summary")
    step_scores: Dict[str, StepTrustScore] = Field(
        default_factory=dict, description="Per-step trust scores"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional scoring details"
    )


class ProvenanceData(BaseModel):
    """Complete provenance data including manifest, RDF, and view model."""

    manifest: Manifest = Field(description="Provenance manifest")
    trig: str = Field(description="RDF data in TriG format")
    view_model: Optional[ViewModel] = Field(
        default=None, description="View model for UI rendering"
    )
    trust_score: Optional[TrustScoreData] = Field(
        default=None, description="Trust score data for the workflow execution"
    )


# ============================================================================
# TrustProv Types (used by the trustprov scoring package)
# ============================================================================

# Re-export RunInfo as StepRun for trustprov compatibility
StepRun = RunInfo


class Step(BaseModel):
    """
    Unified representation of a workflow/provenance activity (a "step").

    This is the *primary unit* of scoring. A Trust Index is computed for a target
    output by extracting the ancestor subgraph of steps that contributed to it.

    Fields are intentionally permissive:
        - `component`, `inputs`, `output`, `uri` vary across systems.
        - `depends_on` is a simple and robust way to represent lineage when
          explicit provenance edges are unavailable.

    Derived fields:
        - `kind`: coarse taxonomy used by the scoring model:
          "GEN" | "RET" | "DET" | "VER" | "HUM"
        - `depth`: distance to the target within the ancestor subgraph.
        - `risk`: per-step risk contribution (0..1).
        - `missingness`: per-step metadata missingness (0..1).
    """

    id: str
    component: Optional[str] = None
    generative: bool = False
    plan: Optional[Dict[str, Any]] = None

    # Inputs/outputs can be dicts or free-form. We normalize common cases in io.py.
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output: Any = None

    # Optional URI for PROV-O style linking.
    uri: Optional[str] = None

    # Lightweight lineage: list of step ids this step depends on (parents).
    depends_on: List[str] = Field(default_factory=list)

    # Runtime & LLM metadata.
    run: StepRun = Field(default_factory=StepRun)
    llm: LLMMetadata = Field(default_factory=LLMMetadata)

    # Derived / computed fields (filled during scoring).
    kind: Optional[str] = None
    depth: int = 0
    risk: float = 0.0
    missingness: float = 0.0

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=False,  # Allow field assignments without validation
    )


class Workflow(BaseModel):
    """
    Parsed workflow description (YAML).

    The workflow file is optional: provenance alone can be enough.
    When provided, it helps classification (e.g., marking LLM steps as generative
    even if the provenance doesn't flag them explicitly).
    """

    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ProvenanceRun(BaseModel):
    """
    Container for a single run's parsed provenance.

    Attributes:
        run_id: Run identifier (if provided).
        base_uri: Optional base URI for entity/step identifiers (PROV-O style).
        steps: Mapping from step id -> Step.
        edges: Optional explicit edge list. Many runs will use `depends_on` only.
        recent_outputs: Optional summary of "what was produced" for UIs.
        raw: The full loaded JSON object (useful for debugging adapters).
    """

    run_id: Optional[str] = None
    base_uri: Optional[str] = None
    steps: Dict[str, Step] = Field(default_factory=dict)
    edges: List[Edge] = Field(default_factory=list)
    recent_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None


class TrustReport(BaseModel):
    """
    Final scoring output.

    trust_index and confidence are integers in [0, 100] for easy human consumption.
    Subscores are floats in [0, 1] to keep internal math simple.
    """

    target: str
    trust_index: int
    band: str
    confidence: int
    subscores: Dict[str, float]
    drivers: List[Dict[str, Any]]
    actions: List[str]
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
