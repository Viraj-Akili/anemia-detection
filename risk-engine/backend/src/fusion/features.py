"""Fusion feature engineering — the fixed 20-feature vector (Hour 4).

Column order is fixed and documented; both training (``model_train.py``) and
inference (``engine.py``) must build features in exactly this order.

Encodings (all features are floats):

- ``anemia_risk_score``: CV risk band → low=0.0 / moderate=0.5 / high=1.0.
- ``*_cat`` (whz/haz/waz/muac): severe=0, moderate=1, normal=2, overweight=2
  (overweight is a flag-only category with no undernutrition risk).
- ``symptom_flags``: count of present red-flag symptoms (0-4).
- ``sex_enc``: female=0, male=1.  ``pregnancy_enc``: no=0, yes=1.
- ``trimester_enc``: 0 when not pregnant, else the trimester number 1-3.
- History defaults (no previous visit): prev risks 0.0, visits_count 0.
"""

from __future__ import annotations

# Fixed feature order — do not reorder without retraining.
FUSION_FEATURES = [
    "anemia_risk_score",      # CV pipeline risk mapped low=0 / moderate=0.5 / high=1.0
    "anemia_confidence",      # CV pipeline confidence in [0, 1]
    "whz",                    # anthropometry z-scores
    "haz",
    "waz",
    "muac_z",
    "whz_cat",                # encoded categories (0-2)
    "haz_cat",
    "waz_cat",
    "muac_cat",
    "diet_risk",              # context modifiers
    "ifa_protection",
    "symptom_flags",
    "age_months",             # demographics
    "sex_enc",
    "pregnancy_enc",
    "trimester_enc",
    "prev_anemia_risk",       # history
    "prev_nutrition_risk",
    "visits_count",
]

#: CV risk band → numeric score.
RISK_SCORE: dict[str, float] = {"low": 0.0, "moderate": 0.5, "high": 1.0}

#: z-score / MUAC category → encoded value (0-2).
CATEGORY_ENC: dict[str, float] = {
    "severe": 0.0,
    "moderate": 1.0,
    "normal": 2.0,
    "overweight": 2.0,  # flag-only; no undernutrition risk signal
}

SEX_ENC: dict[str, float] = {"female": 0.0, "male": 1.0}

_ANEMIA_KEYS = ("risk", "confidence")
_ANTHRO_KEYS = ("whz", "haz", "waz", "muac_z", "whz_cat", "haz_cat", "waz_cat", "muac_cat")
_CONTEXT_KEYS = (
    "diet_risk", "ifa_protection", "symptom_flags",
    "age_months", "sex", "pregnancy", "trimester",
)
_HISTORY_KEYS = ("prev_anemia_risk", "prev_nutrition_risk", "visits_count")


class FeatureInputError(ValueError):
    """Raised for missing/invalid feature inputs; API layer maps to 422."""


def _require(mapping: dict, keys: tuple[str, ...], section: str) -> None:
    missing = [key for key in keys if key not in mapping]
    if missing:
        raise FeatureInputError(f"{section} input is missing required keys: {missing}")


def _finite_number(value: object, name: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise FeatureInputError(f"{name} must be a number, got {value!r}") from exc
    if number != number or number in (float("inf"), float("-inf")):
        raise FeatureInputError(f"{name} must be finite, got {value!r}")
    return number


def build_features(
    *,
    anthropometry: dict,
    context: dict,
    anemia: dict,
    history: dict | None = None,
) -> list[float]:
    """Build the 20-feature vector in :data:`FUSION_FEATURES` order.

    Inputs:

    - ``anemia``: ``{"risk": low|moderate|high, "confidence": [0, 1]}``
    - ``anthropometry``: z-scores ``whz/haz/waz/muac_z`` plus categories
      ``whz_cat/haz_cat/waz_cat/muac_cat`` (severe|moderate|normal|overweight)
    - ``context``: ``diet_risk``, ``ifa_protection``, ``symptom_flags`` (list
      of flag ids or a count), ``age_months``, ``sex`` (male|female),
      ``pregnancy`` (bool), ``trimester`` (1-3 when pregnant, else None)
    - ``history`` (optional): ``prev_anemia_risk``, ``prev_nutrition_risk``
      (both in [0, 1]), ``visits_count`` — defaults to a zero history.

    Returns a ``list[float]`` of length ``len(FUSION_FEATURES)``.
    """
    _require(anemia, _ANEMIA_KEYS, "anemia")
    _require(anthropometry, _ANTHRO_KEYS, "anthropometry")
    _require(context, _CONTEXT_KEYS, "context")
    history = dict(history or {})
    history.setdefault("prev_anemia_risk", 0.0)
    history.setdefault("prev_nutrition_risk", 0.0)
    history.setdefault("visits_count", 0)

    risk = str(anemia["risk"]).lower()
    if risk not in RISK_SCORE:
        raise FeatureInputError(f"anemia risk must be one of {sorted(RISK_SCORE)}, got {risk!r}")
    confidence = _finite_number(anemia["confidence"], "anemia_confidence")
    if not 0.0 <= confidence <= 1.0:
        raise FeatureInputError(f"anemia_confidence must be in [0, 1], got {confidence}")

    z_scores = [
        _finite_number(anthropometry[key], key) for key in ("whz", "haz", "waz", "muac_z")
    ]
    categories = []
    for key in ("whz_cat", "haz_cat", "waz_cat", "muac_cat"):
        category = str(anthropometry[key]).lower()
        if category not in CATEGORY_ENC:
            raise FeatureInputError(
                f"{key} must be one of {sorted(CATEGORY_ENC)}, got {anthropometry[key]!r}"
            )
        categories.append(CATEGORY_ENC[category])

    diet_risk = _finite_number(context["diet_risk"], "diet_risk")
    ifa_protection = _finite_number(context["ifa_protection"], "ifa_protection")
    flags = context["symptom_flags"]
    symptom_count = float(len(flags)) if isinstance(flags, (list, tuple)) else _finite_number(flags, "symptom_flags")

    age_months = _finite_number(context["age_months"], "age_months")
    if age_months < 0:
        raise FeatureInputError(f"age_months cannot be negative: {age_months}")
    sex = str(context["sex"]).lower()
    if sex not in SEX_ENC:
        raise FeatureInputError(f"sex must be one of {sorted(SEX_ENC)}, got {context['sex']!r}")
    pregnancy = bool(context["pregnancy"])
    trimester = context["trimester"]
    if pregnancy:
        if trimester not in (1, 2, 3):
            raise FeatureInputError("trimester must be 1, 2 or 3 when pregnancy is True")
        trimester_enc = float(trimester)
    else:
        trimester_enc = 0.0

    prev_anemia = _finite_number(history["prev_anemia_risk"], "prev_anemia_risk")
    prev_nutrition = _finite_number(history["prev_nutrition_risk"], "prev_nutrition_risk")
    visits_count = _finite_number(history["visits_count"], "visits_count")
    if visits_count < 0:
        raise FeatureInputError(f"visits_count cannot be negative: {visits_count}")

    return [
        RISK_SCORE[risk],
        confidence,
        *z_scores,
        *categories,
        diet_risk,
        ifa_protection,
        symptom_count,
        age_months,
        SEX_ENC[sex],
        1.0 if pregnancy else 0.0,
        trimester_enc,
        prev_anemia,
        prev_nutrition,
        visits_count,
    ]
