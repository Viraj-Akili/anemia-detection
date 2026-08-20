"""Safety layer: ``final = max(fusion_output, rule_output)`` per risk axis
(Hour 6). The safety layer can only ESCALATE, never downgrade.

Also computes ``overall_priority`` (max of anemia/nutrition risk + any red
flag -> critical) and maps risk to ``recommended_action``.

The output dict is shaped for ``ScreeningResponse`` (enum values); the API
layer (Hour 8) copies it straight into the response model.
"""

from __future__ import annotations

from models.schemas import OverallPriority, RecommendedAction, RiskBand
from safety import rules

#: Risk-band ordering for the escalation-only max.
_BAND_ORDER: dict[RiskBand, int] = {
    RiskBand.LOW: 0,
    RiskBand.MODERATE: 1,
    RiskBand.HIGH: 2,
}

#: Priority ordering (superset of risk bands + critical).
_PRIORITY_ORDER: dict[OverallPriority, int] = {
    OverallPriority.LOW: 0,
    OverallPriority.MODERATE: 1,
    OverallPriority.HIGH: 2,
    OverallPriority.CRITICAL: 3,
}


def _as_band(value: RiskBand | str) -> RiskBand:
    return value if isinstance(value, RiskBand) else RiskBand(value)


def _max_band(a: RiskBand, b: RiskBand | None) -> RiskBand:
    if b is None:
        return a
    return a if _BAND_ORDER[a] >= _BAND_ORDER[b] else b


def overall_priority(anemia_risk: RiskBand, nutrition_risk: RiskBand, safety_flags: list[str]) -> OverallPriority:
    """Max of both risk axes; any red flag escalates to critical."""
    base = OverallPriority(_max_band(anemia_risk, nutrition_risk).value)
    if safety_flags:
        return OverallPriority.CRITICAL
    return base


def recommended_action(
    anemia_risk: RiskBand,
    nutrition_risk: RiskBand,
    safety_flags: list[str],
) -> RecommendedAction:
    """Map final risk + flags to the frontline-worker action.

    Precedence: referral red flags > repeated poor quality > anemia risk
    (confirmatory testing) > nutrition risk moderate-or-high (counselling)
    > routine.
    """
    if any(flag in rules.REFERRAL_FLAGS for flag in safety_flags):
        return RecommendedAction.IMMEDIATE_REFERRAL
    if rules.RED_FLAG_5 in safety_flags:
        return RecommendedAction.MANUAL_PROTOCOL_ESCALATION
    if anemia_risk in (RiskBand.MODERATE, RiskBand.HIGH):
        return RecommendedAction.CONFIRMATORY_TESTING
    if nutrition_risk in (RiskBand.MODERATE, RiskBand.HIGH):
        return RecommendedAction.NUTRITION_COUNSELLING
    return RecommendedAction.ROUTINE_MONITORING


def apply(
    *,
    anemia_risk: RiskBand | str,
    nutrition_risk: RiskBand | str,
    rule_output: rules.RuleResult,
) -> dict:
    """Merge fusion risk bands with the red-flag rule output, escalation-only.

    ``final = max(fusion_output, rule_output)`` per risk axis: rule floors
    can only raise a band, never lower it. Returns a dict shaped for
    ``ScreeningResponse``: ``anemia_risk``, ``nutrition_risk``,
    ``overall_priority``, ``recommended_action``, ``safety_flags``.
    """
    fusion_anemia = _as_band(anemia_risk)
    fusion_nutrition = _as_band(nutrition_risk)

    final_anemia = _max_band(fusion_anemia, rule_output.anemia_risk_floor)
    final_nutrition = _max_band(fusion_nutrition, rule_output.nutrition_risk_floor)
    flags = list(rule_output.safety_flags)

    return {
        "anemia_risk": final_anemia,
        "nutrition_risk": final_nutrition,
        "overall_priority": overall_priority(final_anemia, final_nutrition, flags),
        "recommended_action": recommended_action(final_anemia, final_nutrition, flags),
        "safety_flags": flags,
    }
