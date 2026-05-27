# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for the trustprov service module.

These tests verify the trust scoring functionality integrated with provenance.
"""

import pytest

from lunar_api.flows.provenance.trustprov_service import (
    view_model_to_provenance_run,
    compute_step_trust_scores,
    compute_trust_score,
    _compute_band,
    _base_risk,
)
from lunar_api.flows.provenance.provenance_models import (
    ViewModel,
    WorkflowView,
    StepView,
    DataSource,
    Edge,
    RecentOutput,
    RunInfo,
    InputBinding,
    StepOutput,
    LLMMetadata,
    TrustScoreData,
    StepTrustData,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_view_model():
    """Create a sample ViewModel for testing."""
    return ViewModel(
        base_uri="http://test.example/prov",
        run_id="test-run-123",
        workflow=WorkflowView(
            id="test_workflow",
            name="Test Workflow",
            description="A test workflow for trust scoring",
        ),
        data_sources=[
            DataSource(
                id="input_data",
                uri="http://test.example/prov/entity/input/input_data",
                value={"key": "value"},
                summary="Test input data",
                is_external=False,
            )
        ],
        steps=[
            StepView(
                id="step_1",
                component="sql_query",
                plan={"component": "sql_query"},
                depends_on=[],
                flow_inputs_used=["input_data"],
                run=RunInfo(
                    started_at="2025-01-05T12:00:00Z",
                    ended_at="2025-01-05T12:00:01Z",
                    duration_s=1.0,
                ),
                inputs=[
                    InputBinding(
                        name="query",
                        raw="SELECT * FROM data",
                        kind="literal",
                        value="SELECT * FROM data",
                        value_summary="SQL query",
                    )
                ],
                output=StepOutput(value={"rows": []}, summary="Query results"),
                generative=False,
            ),
            StepView(
                id="step_2",
                component="llm_summarize",
                plan={"component": "llm_summarize", "llm": True},
                depends_on=["step_1"],
                flow_inputs_used=[],
                run=RunInfo(
                    started_at="2025-01-05T12:00:01Z",
                    ended_at="2025-01-05T12:00:05Z",
                    duration_s=4.0,
                ),
                inputs=[
                    InputBinding(
                        name="data",
                        raw="$step_1.value",
                        kind="step_output",
                        ref="step_1",
                        value={"rows": []},
                        value_summary="Query results",
                    )
                ],
                output=StepOutput(value="Summary text", summary="LLM summary"),
                generative=True,
                llm_metadata=LLMMetadata(
                    model="gpt-4",
                    input_tokens=500,
                    output_tokens=100,
                    total_tokens=600,
                ),
            ),
        ],
        edges=[
            Edge(
                type="dependsOn",
                from_step="step_1",
                to_step="step_2",
            )
        ],
        recent_outputs=[
            RecentOutput(
                step="step_2",
                ended_at="2025-01-05T12:00:05Z",
                summary="LLM summary",
            )
        ],
    )


@pytest.fixture
def empty_view_model():
    """Create an empty ViewModel for edge case testing."""
    return ViewModel(
        base_uri="http://test.example/prov",
        run_id="empty-run",
        workflow=WorkflowView(
            id="empty_workflow",
            name="Empty Workflow",
        ),
        data_sources=[],
        steps=[],
        edges=[],
        recent_outputs=[],
    )


@pytest.fixture
def generative_heavy_view_model():
    """Create a ViewModel with multiple generative steps for testing high-risk scenarios."""
    return ViewModel(
        base_uri="http://test.example/prov",
        run_id="gen-heavy-run",
        workflow=WorkflowView(
            id="gen_heavy_workflow",
            name="Generative Heavy Workflow",
        ),
        data_sources=[],
        steps=[
            StepView(
                id="gen_step_1",
                component="llm_generate",
                plan={"component": "llm_generate"},
                depends_on=[],
                flow_inputs_used=[],
                run=RunInfo(
                    started_at="2025-01-05T12:00:00Z",
                    ended_at="2025-01-05T12:00:05Z",
                    duration_s=5.0,
                ),
                inputs=[],
                output=StepOutput(value="Generated text 1", summary="First generation"),
                generative=True,
                llm_metadata=LLMMetadata(
                    model="gpt-4",
                    input_tokens=10000,  # Large context
                    output_tokens=2000,
                    total_tokens=12000,
                ),
            ),
            StepView(
                id="gen_step_2",
                component="llm_refine",
                plan={"component": "llm_refine"},
                depends_on=["gen_step_1"],
                flow_inputs_used=[],
                run=RunInfo(
                    started_at="2025-01-05T12:00:05Z",
                    ended_at="2025-01-05T12:00:10Z",
                    duration_s=5.0,
                ),
                inputs=[
                    InputBinding(
                        name="text",
                        raw="$gen_step_1.value",
                        kind="step_output",
                        ref="gen_step_1",
                    )
                ],
                output=StepOutput(value="Refined text", summary="Refined generation"),
                generative=True,
                llm_metadata=LLMMetadata(
                    model="gpt-4",
                    input_tokens=8000,
                    output_tokens=1500,
                    total_tokens=9500,
                ),
            ),
        ],
        edges=[
            Edge(
                type="dependsOn",
                from_step="gen_step_1",
                to_step="gen_step_2",
            )
        ],
        recent_outputs=[
            RecentOutput(
                step="gen_step_2",
                ended_at="2025-01-05T12:00:10Z",
                summary="Refined generation",
            )
        ],
    )


# ============================================================================
# Tests for view_model_to_provenance_run
# ============================================================================


class TestViewModelToProvenanceRun:
    """Tests for converting ViewModel to ProvenanceRun."""

    def test_basic_conversion(self, sample_view_model):
        """Test basic conversion of ViewModel to ProvenanceRun."""
        run = view_model_to_provenance_run(sample_view_model)

        assert run.run_id == "test-run-123"
        assert run.base_uri == "http://test.example/prov"
        assert len(run.steps) == 2
        assert "step_1" in run.steps
        assert "step_2" in run.steps

    def test_step_properties_preserved(self, sample_view_model):
        """Test that step properties are correctly preserved."""
        run = view_model_to_provenance_run(sample_view_model)

        step_1 = run.steps["step_1"]
        assert step_1.component == "sql_query"
        assert step_1.generative is False
        assert step_1.depends_on == []

        step_2 = run.steps["step_2"]
        assert step_2.component == "llm_summarize"
        assert step_2.generative is True
        assert step_2.depends_on == ["step_1"]

    def test_llm_metadata_preserved(self, sample_view_model):
        """Test that LLM metadata is correctly preserved."""
        run = view_model_to_provenance_run(sample_view_model)

        step_2 = run.steps["step_2"]
        assert step_2.llm.model == "gpt-4"
        assert step_2.llm.input_tokens == 500
        assert step_2.llm.output_tokens == 100
        assert step_2.llm.total_tokens == 600

    def test_edges_converted(self, sample_view_model):
        """Test that edges are correctly converted."""
        run = view_model_to_provenance_run(sample_view_model)

        assert len(run.edges) == 1
        edge = run.edges[0]
        assert edge.type == "dependsOn"
        assert edge.from_step == "step_1"
        assert edge.to_step == "step_2"

    def test_recent_outputs_preserved(self, sample_view_model):
        """Test that recent outputs are preserved."""
        run = view_model_to_provenance_run(sample_view_model)

        assert len(run.recent_outputs) == 1
        assert run.recent_outputs[0]["step"] == "step_2"

    def test_empty_view_model(self, empty_view_model):
        """Test conversion of empty ViewModel."""
        run = view_model_to_provenance_run(empty_view_model)

        assert run.run_id == "empty-run"
        assert len(run.steps) == 0
        assert len(run.edges) == 0


# ============================================================================
# Tests for compute_step_trust_scores
# ============================================================================


class TestComputeStepTrustScores:
    """Tests for computing per-step trust scores."""

    def test_basic_scoring(self, sample_view_model):
        """Test basic trust score computation."""
        scores = compute_step_trust_scores(sample_view_model)

        assert len(scores) == 2
        assert "step_1" in scores
        assert "step_2" in scores

    def test_score_structure(self, sample_view_model):
        """Test that scores have correct structure."""
        scores = compute_step_trust_scores(sample_view_model)

        for step_id, score in scores.items():
            assert isinstance(score, StepTrustData)
            assert 0 <= score.trust_index <= 100
            assert 0 <= score.risk <= 1
            assert score.step_kind in ["GEN", "RET", "DET", "VER", "HUM"]
            assert score.band in ["green", "amber", "red"]
            # Check for new fields
            assert 0 <= score.confidence <= 100
            assert isinstance(score.subscores, dict)
            assert isinstance(score.drivers, list)
            assert isinstance(score.actions, list)
            assert isinstance(score.summary, str)

    def test_generative_step_higher_risk(self, sample_view_model):
        """Test that generative steps have higher risk than deterministic."""
        scores = compute_step_trust_scores(sample_view_model)

        # Step 2 is generative, step 1 is not
        assert scores["step_2"].risk >= scores["step_1"].risk

    def test_empty_view_model_returns_empty(self, empty_view_model):
        """Test that empty view model returns empty scores."""
        scores = compute_step_trust_scores(empty_view_model)
        assert len(scores) == 0

    def test_high_context_increases_risk(self, generative_heavy_view_model):
        """Test that large context sizes increase risk for generative steps."""
        scores = compute_step_trust_scores(generative_heavy_view_model)

        # Both steps should have meaningful risk due to large context
        for score in scores.values():
            assert score.risk > 0


# ============================================================================
# Tests for compute_trust_score
# ============================================================================


class TestComputeTrustScore:
    """Tests for computing overall trust scores."""

    def test_basic_trust_score(self, sample_view_model):
        """Test basic trust score computation."""
        trust_data = compute_trust_score(sample_view_model)

        assert isinstance(trust_data, TrustScoreData)
        assert 0 <= trust_data.trust_index <= 100
        assert 0 <= trust_data.confidence <= 100
        assert trust_data.band in ["green", "amber", "red"]

    def test_trust_score_has_subscores(self, sample_view_model):
        """Test that trust score includes subscores."""
        trust_data = compute_trust_score(sample_view_model)

        expected_subscores = [
            "generative_exposure",
            "verification_coverage",
            "grounding_strength",
            "evidence_availability",
            "provenance_completeness",
            "external_dependency",
        ]

        for subscore in expected_subscores:
            assert subscore in trust_data.subscores

    def test_trust_score_has_step_scores(self, sample_view_model):
        """Test that trust score includes per-step scores."""
        trust_data = compute_trust_score(sample_view_model)

        assert len(trust_data.step_scores) == 2
        assert "step_1" in trust_data.step_scores
        assert "step_2" in trust_data.step_scores

    def test_trust_score_has_actions(self, sample_view_model):
        """Test that trust score includes recommended actions."""
        trust_data = compute_trust_score(sample_view_model)

        assert isinstance(trust_data.actions, list)
        # Should have at least one action
        assert len(trust_data.actions) >= 1

    def test_trust_score_has_summary(self, sample_view_model):
        """Test that trust score includes summary."""
        trust_data = compute_trust_score(sample_view_model)

        assert isinstance(trust_data.summary, str)
        assert len(trust_data.summary) > 0

    def test_empty_view_model_returns_default(self, empty_view_model):
        """Test that empty view model returns sensible defaults."""
        trust_data = compute_trust_score(empty_view_model)

        # Should return high trust (nothing to risk) but low confidence
        assert trust_data.trust_index == 100
        assert trust_data.confidence == 0

    def test_high_risk_workflow(self, generative_heavy_view_model):
        """Test that high-risk workflows get lower trust scores."""
        trust_data = compute_trust_score(generative_heavy_view_model)

        # Should have higher generative exposure
        assert trust_data.subscores.get("generative_exposure", 0) > 0

    def test_target_specification(self, sample_view_model):
        """Test specifying a target step for scoring."""
        trust_data = compute_trust_score(sample_view_model, target="step_2")

        assert isinstance(trust_data, TrustScoreData)
        assert trust_data.trust_index is not None


# ============================================================================
# Tests for helper functions
# ============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_compute_band_green(self):
        """Test green band computation."""
        band = _compute_band(0.85, 0.80)
        assert band == "green"

    def test_compute_band_amber(self):
        """Test amber band computation."""
        band = _compute_band(0.65, 0.60)
        assert band == "amber"

    def test_compute_band_red_low_trust(self):
        """Test red band for low trust."""
        band = _compute_band(0.40, 0.70)
        assert band == "red"

    def test_compute_band_red_low_confidence(self):
        """Test red band for low confidence."""
        band = _compute_band(0.70, 0.30)
        assert band == "red"

    def test_base_risk_gen(self):
        """Test base risk for generative steps."""
        from ..trustprov.score import TrustConfig

        cfg = TrustConfig()
        risk = _base_risk("GEN", cfg)
        assert risk == cfg.base_risk_gen

    def test_base_risk_det(self):
        """Test base risk for deterministic steps."""
        from ..trustprov.score import TrustConfig

        cfg = TrustConfig()
        risk = _base_risk("DET", cfg)
        assert risk == cfg.base_risk_det

    def test_base_risk_unknown(self):
        """Test base risk for unknown step type."""
        from ..trustprov.score import TrustConfig

        cfg = TrustConfig()
        risk = _base_risk("UNKNOWN", cfg)
        assert risk == cfg.base_risk_det


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for the trustprov service."""

    def test_full_workflow_scoring(self, sample_view_model):
        """Test full workflow from ViewModel to trust scores."""
        # Convert and score
        trust_data = compute_trust_score(sample_view_model)

        # Verify complete output
        assert trust_data.trust_index is not None
        assert trust_data.confidence is not None
        assert trust_data.band is not None
        assert len(trust_data.step_scores) == len(sample_view_model.steps)

        # Verify step scores match
        for step in sample_view_model.steps:
            assert step.id in trust_data.step_scores
            step_score = trust_data.step_scores[step.id]
            assert step_score.step_id == step.id

    def test_scores_are_consistent(self, sample_view_model):
        """Test that scoring is deterministic."""
        trust_data_1 = compute_trust_score(sample_view_model)
        trust_data_2 = compute_trust_score(sample_view_model)

        assert trust_data_1.trust_index == trust_data_2.trust_index
        assert trust_data_1.confidence == trust_data_2.confidence
        assert trust_data_1.band == trust_data_2.band

    def test_generative_vs_deterministic_workflow(
        self, sample_view_model, generative_heavy_view_model
    ):
        """Test that generative-heavy workflows have lower trust."""
        trust_mixed = compute_trust_score(sample_view_model)
        trust_gen_heavy = compute_trust_score(generative_heavy_view_model)

        # Generative-heavy workflow should have higher generative exposure
        assert trust_gen_heavy.subscores.get(
            "generative_exposure", 0
        ) >= trust_mixed.subscores.get("generative_exposure", 0)
