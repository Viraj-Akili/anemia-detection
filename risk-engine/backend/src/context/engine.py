"""Context engine: rule-based risk modifiers (Implementation Plan Hour 3).

Produces the :class:`ContextModifiers` object consumed by the fusion feature
builder (dietary risk, IFA protection, symptom flags) and the safety layer
(hemoglobin threshold for the group, symptom escalation inputs).

- **Pregnancy + trimester** → the correct WHO 2024 Hb cutoff via
  ``context/thresholds.hb_threshold`` (1st/3rd < 11.0, 2nd < 10.5 g/dL).
  Trimester is mandatory and validated whenever pregnancy is True.
- **Dietary risk score** — iron-rich food frequency factor
  (never=1.0, rare=0.8, sometimes=0.6, often=0.4) × dietary diversity
  (0-9 food groups mapped linearly to risk: 9 groups → 0.0, 0 groups → 1.0).
- **IFA adherence** — good → protective multiplier 0.85; poor/unknown → 1.0.
- **Symptom red-flag scan** — severe pallor, breathlessness, bilateral
  oedema, fatigue → escalation inputs for the safety layer (Hour 6).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from context import thresholds
from models.schemas import DietInput, IfaInput, SymptomsInput

#: Iron-rich food intake frequency → risk factor (Higher = riskier).
FREQUENCY_RISK: dict[str, float] = {
    "never": 1.0,
    "rare": 0.8,
    "sometimes": 0.6,
    "often": 0.4,
}

#: Dietary diversity is scored over 0-9 food groups (linear risk scale).
MAX_DIETARY_DIVERSITY = 9

#: IFA supplement adherence → protective multiplier.
IFA_PROTECTION: dict[str, float] = {
    "good": 0.85,   # adherent → protection
    "poor": 1.0,    # no protection
    "unknown": 1.0, # no protection assumed
}

#: Symptom → escalation flag identifier (consumed by safety/rules.py).
SYMPTOM_FLAG_MAP: dict[str, str] = {
    "severe_pallor": "SEVERE_PALLOR",
    "breathlessness": "BREATHLESSNESS",
    "bilateral_oedema": "BILATERAL_OEDEMA",
    "fatigue": "FATIGUE",
}


class ContextInputError(ValueError):
    """Raised for invalid context inputs; the API layer maps to HTTP 422."""


@dataclass(frozen=True)
class ContextModifiers:
    """Complete modifier object for one screening context."""

    hb_threshold_gdl: float = field(
        metadata={"description": "WHO 2024 anemia cutoff (g/dL) for the group."}
    )
    dietary_risk: float = field(
        metadata={"description": "Dietary risk score in [0, 1] (1 = worst)."}
    )
    ifa_protection: float = field(
        metadata={"description": "IFA adherence multiplier (0.85 or 1.0)."}
    )
    symptom_flags: list[str] = field(
        default_factory=list,
        metadata={"description": "Present red-flag symptoms (escalation inputs)."},
    )
    pregnancy: bool = field(default=False)
    trimester: int | None = field(default=None)


def dietary_risk_score(frequency: str, diversity: int) -> float:
    """Dietary risk = frequency factor x diversity factor, both in [0, 1].

    ``frequency``: never=1.0, rare=0.8, sometimes=0.6, often=0.4.
    ``diversity``: 0-9 food groups → linear risk (9 → 0.0, 0 → 1.0).
    """
    try:
        freq_factor = FREQUENCY_RISK[frequency]
    except KeyError as exc:
        raise ContextInputError(
            f"frequency must be one of {sorted(FREQUENCY_RISK)}, got {frequency!r}"
        ) from exc
    if not 0 <= diversity <= MAX_DIETARY_DIVERSITY:
        raise ContextInputError(
            f"diversity must be 0-{MAX_DIETARY_DIVERSITY}, got {diversity}"
        )
    diversity_factor = (MAX_DIETARY_DIVERSITY - diversity) / MAX_DIETARY_DIVERSITY
    return freq_factor * diversity_factor


def ifa_protection_multiplier(ifa: IfaInput) -> float:
    """IFA adherence multiplier: good → 0.85; poor/unknown → 1.0."""
    return IFA_PROTECTION[ifa.adherence]


def symptom_flag_scan(symptoms: SymptomsInput) -> list[str]:
    """Return the escalation flag identifiers for present symptoms."""
    return [flag for field_name, flag in SYMPTOM_FLAG_MAP.items() if getattr(symptoms, field_name)]


def compute_modifiers(
    *,
    age_months: float | None,
    sex: str,
    pregnancy: bool = False,
    trimester: int | None = None,
    diet: DietInput | None = None,
    ifa: IfaInput | None = None,
    symptoms: SymptomsInput | None = None,
) -> ContextModifiers:
    """Compute the full modifier object for a screening context.

    ``trimester`` must be provided (and valid) when ``pregnancy`` is True —
    otherwise a ``ValueError`` (from this module or ``thresholds``) is raised
    and the API layer responds 422.
    """
    if pregnancy and trimester not in (1, 2, 3):
        raise ContextInputError("trimester is mandatory (1, 2 or 3) when pregnancy is True")

    hb = thresholds.hb_threshold(
        age_months=age_months, sex=sex, pregnancy=pregnancy, trimester=trimester
    )

    diet = diet or DietInput()
    ifa = ifa or IfaInput()
    symptoms = symptoms or SymptomsInput()

    return ContextModifiers(
        hb_threshold_gdl=hb,
        dietary_risk=dietary_risk_score(diet.frequency, diet.diversity),
        ifa_protection=ifa_protection_multiplier(ifa),
        symptom_flags=symptom_flag_scan(symptoms),
        pregnancy=pregnancy,
        trimester=trimester,
    )
