"""WHO 2024 haemoglobin thresholds and adjustments.

All values are transcribed from the primary source:

    WHO. Guideline on haemoglobin cutoffs to define anaemia in individuals
    and populations. Geneva: World Health Organization; 2024.
    ISBN 978-92-4-008854-2.  https://iris.who.int/handle/10665/378395
    (PDF archived at assets/who_tables/WHO_2024_haemoglobin_cutoffs_guideline.pdf)

The guideline publishes values in g/L; the module works in **g/dL** (= g/L / 10)
for consistency with the rest of the API (e.g. 1st/3rd trimester < 11.0 g/dL,
2nd trimester < 10.5 g/dL). The 105/110/... constants below are Table 2
values in g/L, verbatim.

Coverage:
- Table 2: cutoffs for any anaemia (6-23 mo revised table, 24-59 mo,
  5-11 yr, 12-14 yr, adults, pregnancy by trimester).
- Table 3: severity bands (none / mild / moderate / severe).
- Table 4: altitude adjustment (500 m increments + published equation).
- Table 5: smoking adjustment (by cigarettes/day + published equation).
- Infection/inflammation adjustment is intentionally NOT applied — the
  guideline explicitly recommends against it (Normative statement 2.b).
"""

from __future__ import annotations

from typing import Literal

# ---------------------------------------------------------------------------
# Table 2 — haemoglobin cutoffs to define any anaemia (g/L, WHO 2024)
# ---------------------------------------------------------------------------

#: Children 6-23 months (revised 2024 cutoff; previously 110 g/L).
CHILDREN_6_23MO_GPL = 105
#: Children 24-59 months (unchanged).
CHILDREN_24_59MO_GPL = 110
#: Children 5-11 years (unchanged).
CHILDREN_5_11YR_GPL = 115
#: Children 12-14 years, both sexes (unchanged).
CHILDREN_12_14YR_GPL = 120
#: Adults 15-65 years, nonpregnant women (unchanged).
ADULT_WOMEN_GPL = 120
#: Adults 15-65 years, men (unchanged).
ADULT_MEN_GPL = 130
#: Pregnancy 1st and 3rd trimester (unchanged).
PREGNANCY_T1_T3_GPL = 110
#: Pregnancy 2nd trimester (confirmed, not raised, in the 2024 revision).
PREGNANCY_T2_GPL = 105

# ---------------------------------------------------------------------------
# Table 3 — severity bands (g/L, WHO 2024, applying 1989 methodology)
# ---------------------------------------------------------------------------

#: (mild_low_gpl, moderate_low_gpl, severe_low_gpl) per population group.
#: Mild: [mild_low, cutoff); Moderate: [moderate_low, mild_low); Severe: < severe_low.
_SEVERITY_BANDS_GPL: dict[str, tuple[int, int, int]] = {
    "children_6_23mo": (95, 70, 70),
    "children_24_59mo": (100, 70, 70),
    "children_5_11yr": (110, 80, 80),
    "children_12_14yr": (110, 80, 80),
    "adult_women": (110, 80, 80),
    "adult_men": (110, 80, 80),
    "pregnancy_t1": (100, 70, 70),
    "pregnancy_t2": (95, 70, 70),
    "pregnancy_t3": (100, 70, 70),
}

# ---------------------------------------------------------------------------
# Table 4 — altitude adjustment (g/L, WHO 2024)
# ---------------------------------------------------------------------------

#: Elevation bins (metres above sea level) → adjustment (g/L), Table 4.
_ALTITUDE_BINS_GPL: list[tuple[int, int, int]] = [
    # (bin_low_m, bin_high_m, adjustment_gpl)
    (1, 499, 0),
    (500, 999, 4),
    (1000, 1499, 8),
    (1500, 1999, 11),
    (2000, 2499, 14),
    (2500, 2999, 18),
    (3000, 3499, 21),
    (3500, 3999, 25),
    (4000, 4499, 29),
    (4500, 4999, 33),
]

#: Continuous equation from the Table 4 footnote — reproduces the bins and is
#: preferred when exact elevation is known:
#:   adjustment (g/L) = 0.0056384 * elevation + 0.0000003 * elevation**2
ALTITUDE_EQUATION_COEFS = (0.0056384, 0.0000003)

# ---------------------------------------------------------------------------
# Table 5 — smoking adjustment (g/L, WHO 2024)
# ---------------------------------------------------------------------------

#: cigarettes/day → adjustment (g/L), Table 5.
_SMOKING_BINS_GPL: list[tuple[int | None, int | None, int]] = [
    # (min_cigs, max_cigs, adjustment_gpl); None = unbounded.
    (None, 0, 0),        # non-smoker
    (1, 9, 3),           # <10 cigarettes/day
    (10, 19, 5),
    (20, None, 6),       # >=20 cigarettes/day
]
#: "Smoker, quantity unknown" — Table 5 row.
SMOKER_UNKNOWN_QUANTITY_GPL = 3

#: Continuous equation from the Table 5 footnote:
#:   adjustment (g/L) = 0.4565 * n - 0.0078 * n**2   (n = cigarettes/day)
SMOKING_EQUATION_COEFS = (0.4565, -0.0078)

# ---------------------------------------------------------------------------
# Infection / inflammation — explicitly NOT adjusted (WHO 2024, stmt 2.b)
# ---------------------------------------------------------------------------

#: Always zero. WHO rejected the infection/inflammation adjustment for
#: haemoglobin due to insufficient evidence.
INFECTION_INFLAMMATION_ADJUSTMENT_GDL = 0.0


def _gdl(gpl: float) -> float:
    """Convert g/L (primary-source units) to g/dL (API units)."""
    return gpl / 10.0


def _resolve_group(*, age_months: float | None, sex: str, pregnancy: bool, trimester: int | None) -> str:
    """Return the population-group key for the given demographics.

    Raises ValueError for inputs outside the guideline's scope or invalid
    combinations (the API layer turns these into 422 responses).
    """
    if pregnancy:
        if trimester not in (1, 2, 3):
            raise ValueError("trimester is mandatory (1, 2 or 3) when pregnancy is True")
        return f"pregnancy_t{trimester}"
    if age_months is None:
        raise ValueError("age_months is required for non-pregnant screening")
    if age_months < 6:
        raise ValueError("WHO 2024 haemoglobin cutoffs apply from 6 months of age")
    if age_months < 24:
        return "children_6_23mo"
    if age_months < 60:
        return "children_24_59mo"
    if age_months < 144:
        return "children_5_11yr"
    if age_months < 180:
        return "children_12_14yr"
    # 15 years and older.
    if sex.lower() not in ("male", "female"):
        raise ValueError(f"invalid sex: {sex!r}")
    return "adult_men" if sex.lower() == "male" else "adult_women"


_CUTOFF_GPL: dict[str, int] = {
    "children_6_23mo": CHILDREN_6_23MO_GPL,
    "children_24_59mo": CHILDREN_24_59MO_GPL,
    "children_5_11yr": CHILDREN_5_11YR_GPL,
    "children_12_14yr": CHILDREN_12_14YR_GPL,
    "adult_women": ADULT_WOMEN_GPL,
    "adult_men": ADULT_MEN_GPL,
    "pregnancy_t1": PREGNANCY_T1_T3_GPL,
    "pregnancy_t2": PREGNANCY_T2_GPL,
    "pregnancy_t3": PREGNANCY_T1_T3_GPL,
}


def hb_threshold(
    *,
    age_months: float | None,
    sex: str,
    pregnancy: bool = False,
    trimester: int | None = None,
) -> float:
    """WHO 2024 anaemia cutoff (g/dL) for the population group (Table 2).

    Examples: children 6-23 mo → 10.5 g/dL; 24-59 mo → 11.0 g/dL;
    5-11 yr → 11.5 g/dL; 12-14 yr → 12.0 g/dL; nonpregnant women → 12.0;
    men → 13.0; pregnancy 1st/3rd → 11.0, 2nd → 10.5 g/dL.
    """
    group = _resolve_group(age_months=age_months, sex=sex, pregnancy=pregnancy, trimester=trimester)
    return _gdl(_CUTOFF_GPL[group])


def classify_severity(
    hb_gdl: float,
    *,
    age_months: float | None,
    sex: str,
    pregnancy: bool = False,
    trimester: int | None = None,
) -> Literal["none", "mild", "moderate", "severe"]:
    """Classify a haemoglobin value against Table 3 severity bands (WHO 2024).

    ``hb_gdl`` is the (already altitude/smoking-adjusted) measured value.
    """
    group = _resolve_group(age_months=age_months, sex=sex, pregnancy=pregnancy, trimester=trimester)
    cutoff = _CUTOFF_GPL[group]
    mild_low, moderate_low, severe_low = _SEVERITY_BANDS_GPL[group]
    hb_gpl = hb_gdl * 10.0
    if hb_gpl >= cutoff:
        return "none"
    if hb_gpl >= mild_low:
        return "mild"
    if hb_gpl >= moderate_low:
        return "moderate"
    if hb_gpl < severe_low:
        return "severe"
    raise AssertionError("unreachable")


def severe_hb_threshold(
    *,
    age_months: float | None,
    sex: str,
    pregnancy: bool = False,
    trimester: int | None = None,
) -> float:
    """Hb level (g/dL) at/below which anaemia is SEVERE for the group
    (Table 3 lower band, WHO 2024) — the safety layer's red-flag cutoff.

    Examples: children 6-23 mo and pregnancy 1st-3rd tri -> 7.0 g/dL;
    children 5-11 yr / 12-14 yr / adults -> 8.0 g/dL.
    """
    group = _resolve_group(age_months=age_months, sex=sex, pregnancy=pregnancy, trimester=trimester)
    return _gdl(_SEVERITY_BANDS_GPL[group][2])


def altitude_correction(elevation_m: float) -> float:
    """Altitude adjustment (g/dL) for elevation, per Table 4 (WHO 2024).

    Returns the amount to SUBTRACT from the observed Hb (equivalently, the
    amount to ADD to the anaemia cutoff) — the guideline's application rule.
    Bins below 500 m adjust by 0.
    """
    if elevation_m < 0:
        raise ValueError(f"elevation cannot be negative: {elevation_m}")
    if elevation_m < 500:
        return 0.0
    for low, high, adjustment_gpl in _ALTITUDE_BINS_GPL:
        if low <= elevation_m <= high:
            return _gdl(adjustment_gpl)
    # Beyond the published table (>4999 m): extrapolate with the equation.
    return _gdl(altitude_correction_formula_gpl(elevation_m))


def altitude_correction_formula_gpl(elevation_m: float) -> float:
    """Continuous Table 4 equation (g/L): 0.0056384*elev + 0.0000003*elev^2."""
    a, b = ALTITUDE_EQUATION_COEFS
    return a * elevation_m + b * elevation_m**2


def smoking_correction(cigarettes_per_day: int | None) -> float:
    """Smoking adjustment (g/dL), per Table 5 (WHO 2024).

    Returns the amount to SUBTRACT from the observed Hb (equivalently, the
    amount to ADD to the anaemia cutoff) — the guideline's application rule.

    ``cigarettes_per_day``: 0/None → non-smoker (0); 1-9 → 0.3; 10-19 → 0.5;
    >=20 → 0.6 g/dL. Pass a negative sentinel (e.g. -1) for "smoker, quantity
    unknown" → 0.3 g/dL.
    """
    if cigarettes_per_day is None:
        return 0.0
    if cigarettes_per_day < 0:
        return _gdl(SMOKER_UNKNOWN_QUANTITY_GPL)
    for low, high, adjustment_gpl in _SMOKING_BINS_GPL:
        if (low is None or cigarettes_per_day >= low) and (high is None or cigarettes_per_day <= high):
            return _gdl(adjustment_gpl)
    raise AssertionError("unreachable")


def smoking_correction_formula_gpl(cigarettes_per_day: float) -> float:
    """Continuous Table 5 equation (g/L): 0.4565*n - 0.0078*n^2."""
    a, b = SMOKING_EQUATION_COEFS
    return a * cigarettes_per_day + b * cigarettes_per_day**2
