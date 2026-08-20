"""WHO z-score engine: WHZ, HAZ, WAZ, MUAC-for-age z, and MUAC category.

LMS method (WHO Child Growth Standards):

    Z = ((X / M)**L - 1) / (L * S)      L != 0
    Z = ln(X / M) / S                   L == 0  (log case)

``L``, ``M``, ``S`` are looked up in the primary-source tables (see
``who_tables.py``) with **linear interpolation** between rows, and the
published ``SD`` columns give exact reference checks (SD_alpha = M(1+LSa)^(1/L)).

Inputs are validated up front — physically impossible measurements raise
``AnthropometryInputError`` (the API layer maps these to HTTP 422).

MUAC category bands (6-59 mo) are the WHO SAM/MAM cutoffs (< 115 mm severe,
< 125 mm moderate). For 5-19 years there is **no WHO standard**; we use the
Mramba et al. 2017 (BMJ) MUAC-for-age SAM reference (explicitly labeled).
Adults use the MUAC < 230 mm undernutrition indicator.
"""

from __future__ import annotations

import math

import numpy as np

from anthropometry import who_tables

SEXES = ("male", "female")

#: WHO/UNICEF SAM/MAM cutoffs, children 6-59 months (WHO 2009/2013: SAM
#: cutoff raised 110 -> 115 mm; primary source: who.int/publications/i/item/9789241598163).
SAM_6_59MO_MM = 115.0
MAM_6_59MO_MM = 125.0

#: Mramba et al. 2017, BMJ 358:j3423 — proposed MUAC-for-age SAM cutoffs by
#: year of age for children 5-18 years. No WHO standard exists for this range
#: (see GNC Wasting GTWG briefing note, June 2025); values are research-based.
MRAMBA_SAM_MM_BY_YEAR: dict[int, float] = {
    5: 131.0, 6: 136.0, 7: 142.0, 8: 148.0, 9: 153.0, 10: 159.0,
    11: 165.0, 12: 170.0, 13: 176.0, 14: 182.0, 15: 187.0, 16: 193.0,
    17: 199.0, 18: 204.0,
}

#: Adult undernutrition indicator: MUAC < 230 mm (WHO/FANTA, correlates with
#: BMI < 18.5). Used for 19+ years, including pregnant women.
ADULT_LOW_MUAC_MM = 230.0


class AnthropometryInputError(ValueError):
    """Raised for physically impossible or out-of-scope anthropometry inputs.

    The API layer maps this to a 422 response with the message intact.
    """


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate_sex(sex: str) -> None:
    if sex not in SEXES:
        raise AnthropometryInputError(f"sex must be one of {SEXES}, got {sex!r}")


def _validate_age(age_months: float, *, max_months: float = 60.0) -> None:
    if age_months < 0:
        raise AnthropometryInputError(f"age_months cannot be negative: {age_months}")
    if age_months > max_months:
        raise AnthropometryInputError(
            f"age_months {age_months} exceeds the {max_months:g}-month WHO "
            "Child Growth Standards range (5-19 yr reference not yet loaded)"
        )


def _validate_measurement(value: float, name: str, *, upper: float) -> None:
    if not math.isfinite(value):
        raise AnthropometryInputError(f"{name} must be a finite number, got {value!r}")
    if value <= 0:
        raise AnthropometryInputError(f"{name} must be positive, got {value}")
    if value > upper:
        raise AnthropometryInputError(f"{name} exceeds the physically plausible maximum of {upper:g}, got {value}")


# ---------------------------------------------------------------------------
# LMS core
# ---------------------------------------------------------------------------

#: (sex, metric) -> (keys, L, M, S) numpy arrays, sorted by key.
_ARR_CACHE: dict[tuple[str, str], tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}


def _lms_arrays(sex: str, metric: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    key = (sex, metric)
    cached = _ARR_CACHE.get(key)
    if cached is not None:
        return cached
    table = who_tables.load_table(sex, metric)
    kcol = who_tables.KEY_COLUMN[metric]
    keys = table[kcol].to_numpy(dtype=float)
    order = np.argsort(keys)
    arrs = (
        keys[order],
        table["L"].to_numpy(dtype=float)[order],
        table["M"].to_numpy(dtype=float)[order],
        table["S"].to_numpy(dtype=float)[order],
    )
    _ARR_CACHE[key] = arrs
    return arrs


def _interp_lms(sex: str, metric: str, key_value: float) -> tuple[float, float, float]:
    """Linearly interpolate (L, M, S) at ``key_value`` (age in months or
    height in cm, depending on the metric's key column)."""
    keys, L, M, S = _lms_arrays(sex, metric)
    if key_value < keys[0] or key_value > keys[-1]:
        kcol = who_tables.KEY_COLUMN[metric]
        raise AnthropometryInputError(
            f"{kcol} {key_value:g} is outside the WHO {metric} table range "
            f"[{keys[0]:g}, {keys[-1]:g}]"
        )
    idx = int(np.searchsorted(keys, key_value, side="right")) - 1
    if idx == len(keys) - 1:  # exact hit on the last row
        return float(L[idx]), float(M[idx]), float(S[idx])
    t = (key_value - keys[idx]) / (keys[idx + 1] - keys[idx])
    return (
        float(L[idx] + t * (L[idx + 1] - L[idx])),
        float(M[idx] + t * (M[idx + 1] - M[idx])),
        float(S[idx] + t * (S[idx + 1] - S[idx])),
    )


def _lms_z(x: float, l: float, m: float, s: float) -> float:
    """Apply the LMS formula; guards the L == 0 log case."""
    if l == 0.0:
        return math.log(x / m) / s
    return ((x / m) ** l - 1.0) / (l * s)


def _zscore(sex: str, metric: str, key_value: float, x: float) -> float:
    """Interpolated LMS z-score for measurement ``x`` at ``key_value``."""
    l, m, s = _interp_lms(sex, metric, key_value)
    return _lms_z(x, l, m, s)


# ---------------------------------------------------------------------------
# Public metrics
# ---------------------------------------------------------------------------


def waz(age_months: float, sex: str, weight_kg: float) -> float:
    """Weight-for-age z-score (0-60 months)."""
    _validate_sex(sex)
    _validate_age(age_months)
    _validate_measurement(weight_kg, "weight_kg", upper=250.0)
    return _zscore(sex, "wfa", age_months, weight_kg)


def haz(age_months: float, sex: str, height_cm: float) -> float:
    """Height/length-for-age z-score (0-60 months).

    Uses the WHO length-based segment (< 24 mo) and height-based segment
    (>= 24 mo), merged in who_tables.load_table("hfa").
    """
    _validate_sex(sex)
    _validate_age(age_months)
    _validate_measurement(height_cm, "height_cm", upper=250.0)
    return _zscore(sex, "hfa", age_months, height_cm)


def whz(age_months: float, sex: str, weight_kg: float, height_cm: float) -> float:
    """Weight-for-height z-score (0-60 months).

    Weight-for-recumbent-length (45-110 cm) for age < 24 months, and
    weight-for-standing-height (65-120 cm) for age >= 24 months, matching
    WHO Anthro conventions. The child's height must fall inside the chosen
    table's range.
    """
    _validate_sex(sex)
    _validate_age(age_months)
    _validate_measurement(weight_kg, "weight_kg", upper=250.0)
    _validate_measurement(height_cm, "height_cm", upper=250.0)
    metric = "wfl" if age_months < 24 else "wfh"
    return _zscore(sex, metric, height_cm, weight_kg)


def muac_z(age_months: float, sex: str, muac_mm: float) -> float:
    """MUAC-for-age z-score (3-60 months; WHO ACA standard, values in cm).

    The WHO arm-circumference-for-age standard is published for 3-60 months
    only; outside that range this raises rather than extrapolating.
    """
    _validate_sex(sex)
    _validate_age(age_months)
    if age_months < 3:
        raise AnthropometryInputError(
            "WHO arm-circumference-for-age standard starts at 3 months"
        )
    _validate_measurement(muac_mm, "muac_mm", upper=500.0)
    return _zscore(sex, "muac", age_months, muac_mm / 10.0)


def muac_category(age_months: float, sex: str, muac_mm: float) -> str:
    """WHO SAM/MAM MUAC category.

    - 6-59 months: severe < 115 mm, moderate < 125 mm (WHO).
    - 5-18 years: severe below the Mramba et al. 2017 (BMJ) MUAC-for-age SAM
      cutoff; no standardized MAM band exists for this range, so the result
      is ``severe`` or ``normal`` (research-based, not WHO).
    - 19+ years (incl. pregnant women): ``moderate`` below 230 mm (adult
      undernutrition indicator, WHO/FANTA), else ``normal``.

    MUAC classification below 6 months of age is out of scope (WHO does not
    apply these cutoffs to infants).
    """
    _validate_sex(sex)
    _validate_measurement(muac_mm, "muac_mm", upper=500.0)
    if age_months < 0:
        raise AnthropometryInputError(f"age_months cannot be negative: {age_months}")
    if age_months < 6:
        raise AnthropometryInputError(
            "MUAC-based SAM/MAM classification applies from 6 months of age"
        )
    if age_months < 60:
        if muac_mm < SAM_6_59MO_MM:
            return "severe"
        if muac_mm < MAM_6_59MO_MM:
            return "moderate"
        return "normal"
    if age_months < 228:  # 5 to <19 years
        return "severe" if muac_mm < _mramba_cutoff_mm(age_months) else "normal"
    # 19+ years / adults.
    return "moderate" if muac_mm < ADULT_LOW_MUAC_MM else "normal"


def _mramba_cutoff_mm(age_months: float) -> float:
    """Interpolated Mramba et al. 2017 SAM cutoff (mm) for 5-18 years."""
    years = age_months / 12.0
    lo_year = math.floor(years)
    if lo_year >= 18:  # 18-18.99 years -> 18 y cutoff (table stops there)
        return MRAMBA_SAM_MM_BY_YEAR[18]
    hi_year = lo_year + 1
    lo_cut = MRAMBA_SAM_MM_BY_YEAR[lo_year]
    hi_cut = MRAMBA_SAM_MM_BY_YEAR[hi_year]
    t = years - lo_year
    return lo_cut + t * (hi_cut - lo_cut)


def zscore_to_category(z: float) -> str:
    """Map a z-score to ``severe | moderate | normal | overweight``.

    ``z < -3`` → severe; ``-3 <= z < -2`` → moderate; ``-2 <= z <= 2`` →
    normal; ``z > 2`` → overweight (flag only, per Implementation Plan).
    """
    if z < -3:
        return "severe"
    if z < -2:
        return "moderate"
    if z <= 2:
        return "normal"
    return "overweight"
