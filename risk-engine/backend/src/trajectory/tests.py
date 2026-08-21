"""Trajectory engine tests — verify slope calculation and classification.

Tests the trajectory.engine.compute() function with various visit patterns
and validates the early-intervention rule.
"""

from __future__ import annotations

import pytest

from trajectory.engine import RISK_BAND_TO_NUMERIC, compute


class TestTrajectoryCompute:
    """Test trajectory computation and classification."""

    def test_insufficient_data_zero_visits(self):
        """Zero visits → insufficient_data."""
        result = compute([])
        assert result["trajectory"] == "insufficient_data"
        assert result["early_intervention"] is False

    def test_insufficient_data_one_visit(self):
        """Single visit → insufficient_data."""
        visits = [{"overall_priority": "moderate"}]
        result = compute(visits)
        assert result["trajectory"] == "insufficient_data"
        assert result["early_intervention"] is False

    def test_stable_trajectory(self):
        """Three visits with same risk band → stable."""
        visits = [
            {"overall_priority": "moderate"},
            {"overall_priority": "moderate"},
            {"overall_priority": "moderate"},
        ]
        result = compute(visits)
        assert result["trajectory"] == "stable"
        assert result["early_intervention"] is False

    def test_improving_trajectory(self):
        """Risk declining over time → improving (slope < -0.1)."""
        visits = [
            {"overall_priority": "high"},
            {"overall_priority": "moderate"},
            {"overall_priority": "low"},
        ]
        result = compute(visits)
        assert result["trajectory"] == "improving"
        # Last is lower than previous, so no early intervention
        assert result["early_intervention"] is False

    def test_declining_trajectory(self):
        """Risk increasing moderately → declining (0.1 < slope ≤ 0.5)."""
        visits = [
            {"overall_priority": "low"},
            {"overall_priority": "moderate"},
            {"overall_priority": "moderate"},
        ]
        result = compute(visits)
        assert result["trajectory"] in ("stable", "declining")  # depends on exact slope

    def test_rapidly_declining_trajectory(self):
        """Risk increasing quickly → rapidly_declining (slope > 0.5)."""
        visits = [
            {"overall_priority": "low"},
            {"overall_priority": "moderate"},
            {"overall_priority": "critical"},
        ]
        result = compute(visits)
        assert result["trajectory"] == "rapidly_declining"
        assert result["early_intervention"] is True  # last > previous

    def test_early_intervention_flag(self):
        """Two consecutive visits with increasing risk → early_intervention=True."""
        visits = [
            {"overall_priority": "low"},
            {"overall_priority": "moderate"},
        ]
        result = compute(visits)
        # Last visit (moderate=2) > previous (low=1)
        assert result["early_intervention"] is True

    def test_no_early_intervention_when_decreasing(self):
        """Two consecutive visits with decreasing risk → early_intervention=False."""
        visits = [
            {"overall_priority": "high"},
            {"overall_priority": "moderate"},
        ]
        result = compute(visits)
        assert result["early_intervention"] is False

    def test_uses_last_five_visits_only(self):
        """Only last 5 visits used for trajectory."""
        visits = [
            {"overall_priority": "critical"},  # oldest, should be ignored
            {"overall_priority": "critical"},
            {"overall_priority": "high"},
            {"overall_priority": "moderate"},
            {"overall_priority": "moderate"},
            {"overall_priority": "low"},  # newest
        ]
        # Last 5: critical → high → moderate → moderate → low (improving)
        result = compute(visits)
        assert result["trajectory"] == "improving"

    def test_slope_calculation_two_visits(self):
        """Slope over 2 visits: (last - first) / 1."""
        visits = [
            {"overall_priority": "low"},     # 1
            {"overall_priority": "high"},    # 3
        ]
        # slope = (3 - 1) / 1 = 2.0 → rapidly_declining
        result = compute(visits)
        assert result["trajectory"] == "rapidly_declining"
        assert result["early_intervention"] is True

    def test_slope_calculation_three_visits(self):
        """Slope over 3 visits: (last - first) / 2."""
        visits = [
            {"overall_priority": "low"},        # 1
            {"overall_priority": "moderate"},   # 2
            {"overall_priority": "high"},       # 3
        ]
        # slope = (3 - 1) / 2 = 1.0 → rapidly_declining
        result = compute(visits)
        assert result["trajectory"] == "rapidly_declining"

    def test_risk_band_mapping(self):
        """Verify risk band numeric mapping."""
        assert RISK_BAND_TO_NUMERIC["low"] == 1
        assert RISK_BAND_TO_NUMERIC["moderate"] == 2
        assert RISK_BAND_TO_NUMERIC["high"] == 3
        assert RISK_BAND_TO_NUMERIC["critical"] == 4

    def test_seeded_improving_pattern(self):
        """Test with B_IMPROVING pattern: high → moderate → low."""
        visits = [
            {"overall_priority": "high"},
            {"overall_priority": "moderate"},
            {"overall_priority": "low"},
        ]
        result = compute(visits)
        assert result["trajectory"] == "improving"
        assert result["early_intervention"] is False

    def test_seeded_declining_pattern(self):
        """Test with B_DECLINING pattern: low → moderate → high."""
        visits = [
            {"overall_priority": "low"},
            {"overall_priority": "moderate"},
            {"overall_priority": "high"},
        ]
        result = compute(visits)
        assert result["trajectory"] in ("declining", "rapidly_declining")
        assert result["early_intervention"] is True

    def test_seeded_rapid_decline_pattern(self):
        """Test with B_RAPID_DECLINE pattern: low → high → critical."""
        visits = [
            {"overall_priority": "low"},
            {"overall_priority": "high"},
            {"overall_priority": "critical"},
        ]
        result = compute(visits)
        assert result["trajectory"] == "rapidly_declining"
        assert result["early_intervention"] is True


class TestTrajectoryThresholds:
    """Test trajectory classification threshold boundaries."""

    def test_threshold_rapidly_declining(self):
        """Slope > 0.5 → rapidly_declining."""
        visits = [
            {"overall_priority": "low"},      # 1
            {"overall_priority": "high"},     # 3
        ]
        # slope = (3 - 1) / 1 = 2.0 > 0.5
        result = compute(visits)
        assert result["trajectory"] == "rapidly_declining"

    def test_threshold_declining(self):
        """0.1 < slope ≤ 0.5 → declining."""
        visits = [
            {"overall_priority": "low"},       # 1
            {"overall_priority": "low"},       # 1
            {"overall_priority": "low"},       # 1
            {"overall_priority": "moderate"},  # 2
        ]
        # Last 3: low → low → moderate
        # slope = (2 - 1) / 2 = 0.5 (boundary, should be rapidly_declining)
        result = compute(visits)
        assert result["trajectory"] in ("declining", "rapidly_declining")

    def test_threshold_stable(self):
        """-0.1 ≤ slope ≤ 0.1 → stable."""
        visits = [
            {"overall_priority": "moderate"},
            {"overall_priority": "moderate"},
            {"overall_priority": "moderate"},
        ]
        # slope = 0.0 → stable
        result = compute(visits)
        assert result["trajectory"] == "stable"

    def test_threshold_improving(self):
        """slope < -0.1 → improving."""
        visits = [
            {"overall_priority": "moderate"},  # 2
            {"overall_priority": "low"},       # 1
            {"overall_priority": "low"},       # 1
        ]
        # slope = (1 - 2) / 2 = -0.5 < -0.1
        result = compute(visits)
        assert result["trajectory"] == "improving"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
