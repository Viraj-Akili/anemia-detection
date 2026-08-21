"""Deterministic WHO red-flag rules (Hour 6) — escalation only.

Each rule sets a ``recommended_action`` and appends a ``safety_flags`` entry.
These are the exact flag identifiers the response contract exposes.

Rules never downgrade: each returns a risk *floor* (or none) that the safety
engine merges with the fusion output via ``final = max(fusion, rule)``.
"""

from __future__ import annotations

from dataclasses import dataclass

from context import thresholds
from models.schemas import RecommendedAction, RiskBand

RED_FLAG_1 = "SEVERE_ANEMIA_THRESHOLD"
RED_FLAG_2 = "SEVERE_MALNUTRITION"
RED_FLAG_3 = "BILATERAL_OEDEMA"
RED_FLAG_4 = "PREGNANCY_RED_FLAGS"
RED_FLAG_5 = "REPEATED_POOR_QUALITY"

#: Flags that demand immediate referral (all except repeated poor quality,
#: which routes to manual protocol / supervisor escalation instead).
REFERRAL_FLAGS = (RED_FLAG_1, RED_FLAG_2, RED_FLAG_3, RED_FLAG_4)

#: RED FLAG 5 fires at this many consecutive insufficient-quality results.
POOR_QUALITY_STREAK_LIMIT = 2

#: WHZ below this z-score is severe wasting (RED FLAG 2).
SEVERE_WASTING_WHZ = -3.0


@dataclass(frozen=True)
class SafetyInput:
    """Raw observations the red-flag rules evaluate.

    Demographics (age/sex or pregnancy+trimester) are required whenever
    ``hb_gdl`` is supplied, so RED FLAG 1 can resolve the WHO group.
    ``muac_category`` is the anthropometry engine's output (severe/moderate/
    normal/overweight); ``whz`` the weight-for-height z-score.
    """

    pregnancy: bool = False
    trimester: int | None = None
    age_months: float | None = None
    sex: str = "female"
    hb_gdl: float | None = None
    muac_category: str | None = None
    whz: float | None = None
    bilateral_oedema: bool = False
    severe_pallor: bool = False
    breathlessness: bool = False
    consecutive_poor_quality: int = 0


@dataclass(frozen=True)
class RuleResult:
    """Outcome of the red-flag scan: flags plus per-axis risk floors.

    A ``None`` floor means "no opinion" — the fusion output stands. Floors
    only ever raise risk; the safety engine takes the max per axis.
    """

    safety_flags: tuple[str, ...] = ()
    anemia_risk_floor: RiskBand | None = None
    nutrition_risk_floor: RiskBand | None = None
    action: RecommendedAction | None = None


def evaluate(inputs: SafetyInput) -> RuleResult:
    """Run all five red-flag rules; escalation only, never silently dropped."""
    flags: list[str] = []
    anemia_floor: RiskBand | None = None
    nutrition_floor: RiskBand | None = None

    # RED FLAG 1: Hb estimate at/below the severe WHO threshold for the group.
    if inputs.hb_gdl is not None:
        severe_cut = thresholds.severe_hb_threshold(
            age_months=inputs.age_months,
            sex=inputs.sex,
            pregnancy=inputs.pregnancy,
            trimester=inputs.trimester,
        )
        if inputs.hb_gdl <= severe_cut:
            flags.append(RED_FLAG_1)
            anemia_floor = RiskBand.HIGH

    # RED FLAG 2: MUAC in the SAM category OR severe wasting (WHZ < -3).
    if inputs.muac_category == "severe" or (
        inputs.whz is not None and inputs.whz < SEVERE_WASTING_WHZ
    ):
        flags.append(RED_FLAG_2)
        nutrition_floor = RiskBand.HIGH

    # RED FLAG 3: bilateral pitting oedema reported.
    if inputs.bilateral_oedema:
        flags.append(RED_FLAG_3)
        nutrition_floor = RiskBand.HIGH

    # RED FLAG 4: pregnancy + severe pallor + breathlessness.
    if inputs.pregnancy and inputs.severe_pallor and inputs.breathlessness:
        flags.append(RED_FLAG_4)
        anemia_floor = RiskBand.HIGH

    # RED FLAG 5: repeated insufficient-quality results — process flag, no
    # risk-axis opinion; routed to manual protocol, never silently dropped.
    if inputs.consecutive_poor_quality >= POOR_QUALITY_STREAK_LIMIT:
        flags.append(RED_FLAG_5)

    action: RecommendedAction | None = None
    if any(flag in REFERRAL_FLAGS for flag in flags):
        action = RecommendedAction.IMMEDIATE_REFERRAL
    elif RED_FLAG_5 in flags:
        action = RecommendedAction.MANUAL_PROTOCOL_ESCALATION

    return RuleResult(
        safety_flags=tuple(flags),
        anemia_risk_floor=anemia_floor,
        nutrition_risk_floor=nutrition_floor,
        action=action,
    )
