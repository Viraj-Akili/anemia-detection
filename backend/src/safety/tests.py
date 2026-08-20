"""Exhaustive tests for the safety layer (Hour 6).

Covers every red-flag rule, every escalation path, the action mapping, and
the escalation-only property (``final_risk >= fusion_risk`` always) across
200+ randomized cases.
"""

from __future__ import annotations

import random

import pytest

from models.schemas import OverallPriority, RecommendedAction, RiskBand
from safety import engine, rules
from safety.rules import RuleResult, SafetyInput

BANDS = [RiskBand.LOW, RiskBand.MODERATE, RiskBand.HIGH]
ORDER = {RiskBand.LOW: 0, RiskBand.MODERATE: 1, RiskBand.HIGH: 2}


def _result(**overrides) -> RuleResult:
    defaults = dict(
        safety_flags=(),
        anemia_risk_floor=None,
        nutrition_risk_floor=None,
        action=None,
    )
    defaults.update(overrides)
    return RuleResult(**defaults)


# ---------------------------------------------------------------------------
# Red-flag rules — one (at least) test per flag
# ---------------------------------------------------------------------------


def test_red_flag_1_severe_anemia_threshold() -> None:
    """Hb at/below the severe WHO cutoff for the group fires RED FLAG 1."""
    # Child 6-23 mo: severe cutoff 7.0 g/dL.
    result = rules.evaluate(SafetyInput(age_months=12, sex="male", hb_gdl=7.0))
    assert rules.RED_FLAG_1 in result.safety_flags
    assert result.anemia_risk_floor is RiskBand.HIGH
    assert result.action is RecommendedAction.IMMEDIATE_REFERRAL
    # Just above the cutoff: no flag.
    assert rules.evaluate(SafetyInput(age_months=12, sex="male", hb_gdl=7.1)).safety_flags == ()
    # Adult men: severe cutoff 8.0 g/dL.
    assert rules.RED_FLAG_1 in rules.evaluate(
        SafetyInput(age_months=300, sex="male", hb_gdl=8.0)
    ).safety_flags
    # Pregnancy 2nd tri: severe cutoff 7.0 g/dL.
    assert rules.RED_FLAG_1 in rules.evaluate(
        SafetyInput(pregnancy=True, trimester=2, hb_gdl=6.9)
    ).safety_flags


def test_red_flag_2_severe_malnutrition() -> None:
    """MUAC SAM category OR WHZ < -3 fires RED FLAG 2."""
    by_muac = rules.evaluate(SafetyInput(age_months=30, sex="female", muac_category="severe"))
    assert rules.RED_FLAG_2 in by_muac.safety_flags
    assert by_muac.nutrition_risk_floor is RiskBand.HIGH
    assert by_muac.action is RecommendedAction.IMMEDIATE_REFERRAL

    by_whz = rules.evaluate(SafetyInput(age_months=30, sex="female", whz=-3.1))
    assert rules.RED_FLAG_2 in by_whz.safety_flags

    # Boundary: WHZ exactly -3 is NOT severe wasting (z < -3).
    assert rules.evaluate(SafetyInput(age_months=30, sex="female", whz=-3.0)).safety_flags == ()
    # Moderate MUAC category alone does not fire.
    assert rules.evaluate(
        SafetyInput(age_months=30, sex="female", muac_category="moderate")
    ).safety_flags == ()


def test_red_flag_3_bilateral_oedema() -> None:
    result = rules.evaluate(SafetyInput(bilateral_oedema=True))
    assert rules.RED_FLAG_3 in result.safety_flags
    assert result.nutrition_risk_floor is RiskBand.HIGH
    assert result.action is RecommendedAction.IMMEDIATE_REFERRAL


def test_red_flag_4_pregnancy_red_flags() -> None:
    """Pregnancy + severe pallor + breathlessness fires RED FLAG 4."""
    result = rules.evaluate(
        SafetyInput(pregnancy=True, trimester=3, severe_pallor=True, breathlessness=True)
    )
    assert rules.RED_FLAG_4 in result.safety_flags
    assert result.anemia_risk_floor is RiskBand.HIGH
    assert result.action is RecommendedAction.IMMEDIATE_REFERRAL
    # Each component alone does not fire.
    assert rules.evaluate(
        SafetyInput(pregnancy=True, trimester=3, severe_pallor=True)
    ).safety_flags == ()
    assert rules.evaluate(
        SafetyInput(pregnancy=True, trimester=3, breathlessness=True)
    ).safety_flags == ()
    assert rules.evaluate(
        SafetyInput(severe_pallor=True, breathlessness=True)  # not pregnant
    ).safety_flags == ()


def test_red_flag_5_repeated_poor_quality() -> None:
    """2+ consecutive insufficient-quality results -> manual protocol."""
    result = rules.evaluate(SafetyInput(consecutive_poor_quality=2))
    assert rules.RED_FLAG_5 in result.safety_flags
    assert result.action is RecommendedAction.MANUAL_PROTOCOL_ESCALATION
    # Process flag only: no risk-axis opinion.
    assert result.anemia_risk_floor is None
    assert result.nutrition_risk_floor is None
    # One poor-quality result does not fire.
    assert rules.evaluate(SafetyInput(consecutive_poor_quality=1)).safety_flags == ()


def test_clean_input_raises_no_flags() -> None:
    result = rules.evaluate(
        SafetyInput(age_months=36, sex="female", hb_gdl=11.5, muac_category="normal", whz=-0.5)
    )
    assert result.safety_flags == ()
    assert result.action is None


def test_multiple_flags_fire_together() -> None:
    result = rules.evaluate(
        SafetyInput(
            age_months=12, sex="male", hb_gdl=6.0, whz=-3.5, bilateral_oedema=True
        )
    )
    assert set(result.safety_flags) == {rules.RED_FLAG_1, rules.RED_FLAG_2, rules.RED_FLAG_3}
    assert result.action is RecommendedAction.IMMEDIATE_REFERRAL


# ---------------------------------------------------------------------------
# apply() — escalation-only merge
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("band", BANDS)
def test_apply_no_flags_passes_fusion_through(band) -> None:
    result = engine.apply(anemia_risk=band, nutrition_risk=band, rule_output=_result())
    assert result["anemia_risk"] is band
    assert result["nutrition_risk"] is band
    assert result["safety_flags"] == []


def test_apply_floor_escalates_low_to_high() -> None:
    result = engine.apply(
        anemia_risk=RiskBand.LOW,
        nutrition_risk=RiskBand.LOW,
        rule_output=_result(anemia_risk_floor=RiskBand.HIGH),
    )
    assert result["anemia_risk"] is RiskBand.HIGH
    assert result["nutrition_risk"] is RiskBand.LOW  # untouched axis stays


def test_apply_never_downgrades_high_fusion() -> None:
    """A moderate floor must not pull a high fusion band down."""
    result = engine.apply(
        anemia_risk=RiskBand.HIGH,
        nutrition_risk=RiskBand.HIGH,
        rule_output=_result(anemia_risk_floor=RiskBand.MODERATE, nutrition_risk_floor=RiskBand.MODERATE),
    )
    assert result["anemia_risk"] is RiskBand.HIGH
    assert result["nutrition_risk"] is RiskBand.HIGH


def test_apply_accepts_string_bands() -> None:
    result = engine.apply(
        anemia_risk="moderate", nutrition_risk="low", rule_output=_result()
    )
    assert result["anemia_risk"] is RiskBand.MODERATE
    assert result["nutrition_risk"] is RiskBand.LOW


# ---------------------------------------------------------------------------
# overall_priority
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("anemia", "nutrition", "expected"),
    [
        (RiskBand.LOW, RiskBand.LOW, OverallPriority.LOW),
        (RiskBand.MODERATE, RiskBand.LOW, OverallPriority.MODERATE),
        (RiskBand.LOW, RiskBand.MODERATE, OverallPriority.MODERATE),
        (RiskBand.HIGH, RiskBand.LOW, OverallPriority.HIGH),
        (RiskBand.LOW, RiskBand.HIGH, OverallPriority.HIGH),
    ],
)
def test_overall_priority_without_flags(anemia, nutrition, expected) -> None:
    assert engine.overall_priority(anemia, nutrition, []) is expected


def test_overall_priority_any_flag_is_critical() -> None:
    for flag in (rules.RED_FLAG_1, rules.RED_FLAG_2, rules.RED_FLAG_3, rules.RED_FLAG_4, rules.RED_FLAG_5):
        assert engine.overall_priority(RiskBand.LOW, RiskBand.LOW, [flag]) is OverallPriority.CRITICAL


# ---------------------------------------------------------------------------
# recommended_action mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("anemia", "nutrition", "expected"),
    [
        (RiskBand.LOW, RiskBand.LOW, RecommendedAction.ROUTINE_MONITORING),
        (RiskBand.LOW, RiskBand.MODERATE, RecommendedAction.NUTRITION_COUNSELLING),
        (RiskBand.LOW, RiskBand.HIGH, RecommendedAction.NUTRITION_COUNSELLING),
        (RiskBand.MODERATE, RiskBand.LOW, RecommendedAction.CONFIRMATORY_TESTING),
        (RiskBand.MODERATE, RiskBand.MODERATE, RecommendedAction.CONFIRMATORY_TESTING),
        (RiskBand.HIGH, RiskBand.LOW, RecommendedAction.CONFIRMATORY_TESTING),
        (RiskBand.HIGH, RiskBand.HIGH, RecommendedAction.CONFIRMATORY_TESTING),
    ],
)
def test_recommended_action_without_flags(anemia, nutrition, expected) -> None:
    assert engine.recommended_action(anemia, nutrition, []) is expected


def test_recommended_action_referral_flag_wins() -> None:
    assert (
        engine.recommended_action(RiskBand.LOW, RiskBand.LOW, [rules.RED_FLAG_2])
        is RecommendedAction.IMMEDIATE_REFERRAL
    )


def test_recommended_action_poor_quality_overrides_risk_mapping() -> None:
    assert (
        engine.recommended_action(RiskBand.MODERATE, RiskBand.MODERATE, [rules.RED_FLAG_5])
        is RecommendedAction.MANUAL_PROTOCOL_ESCALATION
    )


def test_recommended_action_referral_beats_poor_quality() -> None:
    flags = [rules.RED_FLAG_5, rules.RED_FLAG_3]
    assert engine.recommended_action(RiskBand.LOW, RiskBand.LOW, flags) is RecommendedAction.IMMEDIATE_REFERRAL


# ---------------------------------------------------------------------------
# Escalation-only property test — 200+ randomized cases
# ---------------------------------------------------------------------------


def test_property_final_risk_never_below_fusion_risk() -> None:
    """final_risk >= fusion_risk on BOTH axes, for any rule output."""
    rng = random.Random(20260818)
    floors = [None, *BANDS]
    flag_pool = [
        rules.RED_FLAG_1, rules.RED_FLAG_2, rules.RED_FLAG_3, rules.RED_FLAG_4, rules.RED_FLAG_5,
    ]
    for _ in range(250):
        fusion_anemia = rng.choice(BANDS)
        fusion_nutrition = rng.choice(BANDS)
        rule_output = _result(
            safety_flags=tuple(rng.sample(flag_pool, rng.randint(0, 3))),
            anemia_risk_floor=rng.choice(floors),
            nutrition_risk_floor=rng.choice(floors),
            action=None,
        )
        result = engine.apply(
            anemia_risk=fusion_anemia, nutrition_risk=fusion_nutrition, rule_output=rule_output
        )
        assert ORDER[result["anemia_risk"]] >= ORDER[fusion_anemia]
        assert ORDER[result["nutrition_risk"]] >= ORDER[fusion_nutrition]
        # Flags always escalate priority to critical.
        if rule_output.safety_flags:
            assert result["overall_priority"] is OverallPriority.CRITICAL
            assert result["recommended_action"] in (
                RecommendedAction.IMMEDIATE_REFERRAL,
                RecommendedAction.MANUAL_PROTOCOL_ESCALATION,
            )


def test_property_end_to_end_rules_never_downgrade() -> None:
    """Randomized raw observations through rules.evaluate + apply: the
    final bands never fall below the fusion bands."""
    rng = random.Random(7)
    for _ in range(200):
        inputs = SafetyInput(
            pregnancy=rng.random() < 0.2,
            trimester=rng.choice([1, 2, 3]),
            age_months=rng.randint(6, 780),
            sex=rng.choice(["male", "female"]),
            hb_gdl=round(rng.uniform(4.0, 15.0), 1),
            muac_category=rng.choice(["severe", "moderate", "normal", None]),
            whz=round(rng.uniform(-4.5, 2.0), 1),
            bilateral_oedema=rng.random() < 0.1,
            severe_pallor=rng.random() < 0.15,
            breathlessness=rng.random() < 0.1,
            consecutive_poor_quality=rng.randint(0, 3),
        )
        fusion_anemia = rng.choice(BANDS)
        fusion_nutrition = rng.choice(BANDS)
        result = engine.apply(
            anemia_risk=fusion_anemia,
            nutrition_risk=fusion_nutrition,
            rule_output=rules.evaluate(inputs),
        )
        assert ORDER[result["anemia_risk"]] >= ORDER[fusion_anemia]
        assert ORDER[result["nutrition_risk"]] >= ORDER[fusion_nutrition]
