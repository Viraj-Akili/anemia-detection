"""Unit tests for context/thresholds.py.

Every expected value below is transcribed from the WHO 2024 guideline
(ISBN 978-92-4-008854-2, Tables 2-5) — the same primary source the module
documents. See assets/who_tables/WHO_2024_haemoglobin_cutoffs_guideline.pdf.
"""

from __future__ import annotations

import pytest

from context import thresholds


# ---------------------------------------------------------------------------
# Table 2 — cutoffs for any anaemia
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("age_months", "sex", "expected_gdl"),
    [
        (6, "male", 10.5),     # 6-23 mo, revised 2024 cutoff (105 g/L)
        (23, "female", 10.5),
        (24, "male", 11.0),    # 24-59 mo (110 g/L)
        (59, "female", 11.0),
        (60, "male", 11.5),    # 5-11 yr (115 g/L)
        (143, "female", 11.5),
        (144, "male", 12.0),   # 12-14 yr (120 g/L)
        (179, "female", 12.0),
        (180, "male", 13.0),   # adults 15-65 (men 130, women 120 g/L)
        (180, "female", 12.0),
    ],
)
def test_hb_threshold_age_groups(age_months, sex, expected_gdl) -> None:
    assert thresholds.hb_threshold(age_months=age_months, sex=sex) == expected_gdl


@pytest.mark.parametrize(
    ("trimester", "expected_gdl"),
    [(1, 11.0), (2, 10.5), (3, 11.0)],
)
def test_hb_threshold_pregnancy(trimester, expected_gdl) -> None:
    assert thresholds.hb_threshold(age_months=240, sex="female", pregnancy=True, trimester=trimester) == expected_gdl


def test_hb_threshold_pregnancy_requires_trimester() -> None:
    with pytest.raises(ValueError, match="trimester"):
        thresholds.hb_threshold(age_months=240, sex="female", pregnancy=True, trimester=None)


def test_hb_threshold_below_6_months_out_of_scope() -> None:
    with pytest.raises(ValueError, match="6 months"):
        thresholds.hb_threshold(age_months=5, sex="male")


def test_hb_threshold_requires_age_months() -> None:
    with pytest.raises(ValueError, match="age_months"):
        thresholds.hb_threshold(age_months=None, sex="female")


def test_hb_threshold_rejects_invalid_sex() -> None:
    with pytest.raises(ValueError, match="sex"):
        thresholds.hb_threshold(age_months=240, sex="other")


@pytest.mark.parametrize("trimester", [0, 4])
def test_hb_threshold_rejects_invalid_trimester(trimester) -> None:
    with pytest.raises(ValueError, match="trimester"):
        thresholds.hb_threshold(age_months=240, sex="female", pregnancy=True, trimester=trimester)


# ---------------------------------------------------------------------------
# Table 3 — severity bands
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("hb_gdl", "age_months", "sex", "expected"),
    [
        (10.5, 6, "male", "none"),        # 6-23 mo: >=105 g/L
        (10.0, 6, "male", "mild"),        # 95-104
        (9.4, 6, "male", "moderate"),     # 70-94
        (7.0, 6, "male", "moderate"),     # boundary: 70-94 inclusive
        (6.9, 6, "male", "severe"),       # <70
        (11.0, 24, "male", "none"),       # 24-59 mo
        (10.0, 24, "male", "mild"),       # 100-109
        (7.0, 24, "male", "moderate"),    # 70-99
        (6.9, 24, "male", "severe"),
        (11.5, 60, "male", "none"),       # 5-11 yr
        (11.0, 60, "male", "mild"),       # 110-114
        (8.0, 60, "male", "moderate"),    # 80-109
        (7.9, 60, "male", "severe"),      # <80
        (12.0, 144, "female", "none"),    # 12-14 yr: >=120 g/L
        (11.0, 144, "male", "mild"),      # 110-119
        (8.0, 144, "female", "moderate"), # 80-109
        (7.9, 144, "male", "severe"),     # <80
        (12.0, 180, "female", "none"),    # adult women: >=120 g/L
        (13.0, 180, "male", "none"),      # adult men: >=130 g/L
        (12.9, 180, "male", "mild"),      # men mild: 110-129
        (12.5, 180, "male", "mild"),
        (10.9, 180, "female", "moderate"),# women moderate: 80-109
        (11.5, 180, "female", "mild"),    # women mild: 110-119
    ],
)
def test_severity_bands(hb_gdl, age_months, sex, expected) -> None:
    assert (
        thresholds.classify_severity(hb_gdl, age_months=age_months, sex=sex) == expected
    )


@pytest.mark.parametrize(
    ("hb_gdl", "trimester", "expected"),
    [
        (11.0, 1, "none"),        # pregnancy 1st tri: >=110 g/L
        (10.9, 1, "mild"),        # 100-109
        (7.0, 1, "moderate"),     # 70-99
        (6.9, 1, "severe"),       # <70
        (10.5, 2, "none"),        # pregnancy 2nd tri: >=105 g/L
        (10.0, 2, "mild"),        # 95-104
        (9.4, 2, "moderate"),     # 70-94
        (6.9, 2, "severe"),
        (11.0, 3, "none"),        # 3rd tri same bands as 1st
        (10.9, 3, "mild"),
        (7.0, 3, "moderate"),
        (6.9, 3, "severe"),
    ],
)
def test_severity_bands_pregnancy(hb_gdl, trimester, expected) -> None:
    assert (
        thresholds.classify_severity(
            hb_gdl, age_months=240, sex="female", pregnancy=True, trimester=trimester
        )
        == expected
    )


# ---------------------------------------------------------------------------
# Table 4 — altitude adjustment
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("elevation_m", "expected_gdl"),
    [
        (0, 0.0),
        (499, 0.0),    # 1-499: 0
        (500, 0.4),    # 500-999: 4 g/L
        (999, 0.4),
        (1000, 0.8),   # 1000-1499: 8 g/L
        (1500, 1.1),   # 1500-1999: 11 g/L
        (2000, 1.4),   # 2000-2499: 14 g/L
        (2500, 1.8),   # 2500-2999: 18 g/L
        (3000, 2.1),   # 3000-3499: 21 g/L
        (3500, 2.5),   # 3500-3999: 25 g/L
        (4000, 2.9),   # 4000-4499: 29 g/L
        (4500, 3.3),   # 4500-4999: 33 g/L
    ],
)
def test_altitude_correction_bins(elevation_m, expected_gdl) -> None:
    assert thresholds.altitude_correction(elevation_m) == pytest.approx(expected_gdl)


def test_altitude_equation_reproduces_published_bins() -> None:
    """Table 4 footnote equation: 0.0056384*elev + 0.0000003*elev^2 (g/L).

    The equation is a statistical fit; the guideline deliberately rounds the
    1-499 m bin to 0 and publishes integer values per 500 m bin, so compare
    with a loose tolerance and skip the rounded-to-zero low bin.
    """
    for low, high, adj_gpl in thresholds._ALTITUDE_BINS_GPL:
        if low < 500:
            continue
        mid = (low + high) / 2
        formula = thresholds.altitude_correction_formula_gpl(mid)
        assert abs(formula - adj_gpl) <= 1.0, (mid, formula, adj_gpl)


def test_altitude_correction_rejects_negative() -> None:
    with pytest.raises(ValueError):
        thresholds.altitude_correction(-1)


def test_altitude_correction_extrapolates_beyond_table() -> None:
    """Above 4999 m the published table ends; the footnote equation applies."""
    assert thresholds.altitude_correction(5000) == pytest.approx(
        thresholds.altitude_correction_formula_gpl(5000) / 10.0
    )


# ---------------------------------------------------------------------------
# Table 5 — smoking adjustment
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("cigs", "expected_gdl"),
    [
        (None, 0.0),   # non-smoker / unknown status -> no adjustment
        (0, 0.0),
        (1, 0.3),      # 1-9: 3 g/L (lower boundary)
        (5, 0.3),      # <10: 3 g/L
        (9, 0.3),
        (10, 0.5),     # 10-19: 5 g/L (lower boundary)
        (15, 0.5),
        (19, 0.5),     # upper boundary
        (20, 0.6),     # >=20: 6 g/L (lower boundary)
        (25, 0.6),
        (-1, 0.3),     # smoker, quantity unknown: 3 g/L
    ],
)
def test_smoking_correction(cigs, expected_gdl) -> None:
    assert thresholds.smoking_correction(cigs) == pytest.approx(expected_gdl)


def test_smoking_equation_reproduces_published_values() -> None:
    """Table 5 footnote equation solved at n=9, 19, 30 is consistent with the
    published 3/5/6 g/L categorical values (fit, so loose tolerance)."""
    assert thresholds.smoking_correction_formula_gpl(9) == pytest.approx(3.0, abs=1.0)
    assert thresholds.smoking_correction_formula_gpl(19) == pytest.approx(5.0, abs=1.0)
    assert thresholds.smoking_correction_formula_gpl(30) == pytest.approx(6.0, abs=1.0)


# ---------------------------------------------------------------------------
# Infection / inflammation — explicitly NOT adjusted (WHO 2024, stmt 2.b)
# ---------------------------------------------------------------------------

def test_infection_inflammation_adjustment_is_zero() -> None:
    assert thresholds.INFECTION_INFLAMMATION_ADJUSTMENT_GDL == 0.0


@pytest.mark.parametrize(
    ("kwargs", "expected_gdl"),
    [
        (dict(age_months=12, sex="male"), 7.0),                    # 6-23 mo
        (dict(age_months=36, sex="female"), 7.0),                  # 24-59 mo
        (dict(age_months=72, sex="male"), 8.0),                    # 5-11 yr
        (dict(age_months=150, sex="female"), 8.0),                 # 12-14 yr
        (dict(age_months=300, sex="female"), 8.0),                 # adult women
        (dict(age_months=300, sex="male"), 8.0),                   # adult men
        (dict(age_months=None, sex="female", pregnancy=True, trimester=1), 7.0),
        (dict(age_months=None, sex="female", pregnancy=True, trimester=2), 7.0),
        (dict(age_months=None, sex="female", pregnancy=True, trimester=3), 7.0),
    ],
)
def test_severe_hb_threshold(kwargs, expected_gdl) -> None:
    assert thresholds.severe_hb_threshold(**kwargs) == expected_gdl


# ---------------------------------------------------------------------------
# Context engine — compute_modifiers()
# ---------------------------------------------------------------------------

from context import engine  # noqa: E402
from models.schemas import DietInput, IfaInput, SymptomsInput  # noqa: E402


def _mods(**kwargs) -> engine.ContextModifiers:
    defaults = dict(
        age_months=36,
        sex="female",
        pregnancy=False,
        trimester=None,
        diet=DietInput(),
        ifa=IfaInput(),
        symptoms=SymptomsInput(),
    )
    defaults.update(kwargs)
    return engine.compute_modifiers(**defaults)


def test_pregnancy_selects_trimester_threshold() -> None:
    assert _mods(pregnancy=True, trimester=1).hb_threshold_gdl == 11.0
    assert _mods(pregnancy=True, trimester=3).hb_threshold_gdl == 11.0
    assert _mods(pregnancy=True, trimester=2).hb_threshold_gdl == 10.5


def test_non_pregnant_thresholds_flow_through() -> None:
    assert _mods(age_months=36, sex="female").hb_threshold_gdl == 11.0  # 24-59 mo
    assert _mods(age_months=240, sex="male").hb_threshold_gdl == 13.0  # adult man


def test_trimester_mandatory_when_pregnant() -> None:
    with pytest.raises(engine.ContextInputError, match="trimester"):
        _mods(pregnancy=True, trimester=None)
    with pytest.raises(engine.ContextInputError, match="trimester"):
        _mods(pregnancy=True, trimester=0)


@pytest.mark.parametrize(
    ("frequency", "diversity", "expected"),
    [
        ("never", 0, 1.0),                      # worst case
        ("never", 9, 0.0),                      # full diversity cancels frequency
        ("often", 9, 0.0),                      # best case
        ("often", 0, 0.4),
        ("rare", 4, 0.8 * 5 / 9),               # 0.8 x (9-4)/9
        ("sometimes", 6, 0.6 * 3 / 9),          # 0.2
        ("rare", 3, 0.8 * 6 / 9),
    ],
)
def test_dietary_risk_score(frequency, diversity, expected) -> None:
    assert engine.dietary_risk_score(frequency, diversity) == pytest.approx(expected)


def test_dietary_risk_score_rejects_bad_inputs() -> None:
    with pytest.raises(engine.ContextInputError, match="frequency"):
        engine.dietary_risk_score("daily", 5)
    with pytest.raises(engine.ContextInputError, match="diversity"):
        engine.dietary_risk_score("never", 10)
    with pytest.raises(engine.ContextInputError, match="diversity"):
        engine.dietary_risk_score("never", -1)


@pytest.mark.parametrize(
    ("adherence", "expected"),
    [("good", 0.85), ("poor", 1.0), ("unknown", 1.0)],
)
def test_ifa_protection_multiplier(adherence, expected) -> None:
    assert engine.ifa_protection_multiplier(IfaInput(adherence=adherence)) == expected


def test_symptom_flag_scan() -> None:
    assert engine.symptom_flag_scan(SymptomsInput()) == []
    assert engine.symptom_flag_scan(
        SymptomsInput(severe_pallor=True, breathlessness=True, bilateral_oedema=True, fatigue=True)
    ) == ["SEVERE_PALLOR", "BREATHLESSNESS", "BILATERAL_OEDEMA", "FATIGUE"]
    assert engine.symptom_flag_scan(SymptomsInput(bilateral_oedema=True)) == ["BILATERAL_OEDEMA"]


def test_compute_modifiers_end_to_end() -> None:
    mods = engine.compute_modifiers(
        age_months=30,
        sex="female",
        diet=DietInput(frequency="never", diversity=1),
        ifa=IfaInput(adherence="good"),
        symptoms=SymptomsInput(severe_pallor=True),
    )
    assert mods.hb_threshold_gdl == 11.0           # 24-59 mo
    assert mods.dietary_risk == pytest.approx(1.0 * 8 / 9)
    assert mods.ifa_protection == 0.85
    assert mods.symptom_flags == ["SEVERE_PALLOR"]
    assert mods.pregnancy is False


def test_compute_modifiers_defaults_to_safe_unknowns() -> None:
    """No diet/IFA/symptoms supplied -> worst-case diet risk, no protection."""
    mods = _mods(age_months=24, sex="male")
    assert mods.dietary_risk == 1.0
    assert mods.ifa_protection == 1.0
    assert mods.symptom_flags == []
