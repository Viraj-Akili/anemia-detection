"""Unit tests for the anthropometry engine (WHO LMS z-scores + MUAC).

Verification strategy — no values invented from memory:
1. **SD-column self-consistency**: every primary-source table row carries
   published SD values (SD_alpha = M(1+LSa)^(1/L)); computing the z-score of
   SD3neg must return -3, SD0 -> 0, SD3 -> +3, etc. This validates the LMS
   formula, table loading, and metric plumbing against the exact WHO numbers.
2. Category mapping, input validation, and MUAC bands (WHO + Mramba 2017).
"""

from __future__ import annotations

import math

import pytest

from anthropometry import engine, who_tables
from models.schemas import RiskBand, Trajectory

TOL = 0.05  # published SD values are rounded to 0.1, so allow +/-0.05


def test_contract_enums_match_appendix_a() -> None:
    """Smoke check that the Appendix A contract enums compile to exact values."""
    assert {r.value for r in RiskBand} == {"low", "moderate", "high"}
    assert {t.value for t in Trajectory} == {
        "improving",
        "stable",
        "declining",
        "rapidly_declining",
        "insufficient_data",
    }


# ---------------------------------------------------------------------------
# WHO table loader
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sex", ["male", "female"])
@pytest.mark.parametrize("metric", ["wfa", "hfa", "wfl", "wfh", "muac"])
def test_who_table_loads_with_lms_columns(sex, metric) -> None:
    table = who_tables.load_table(sex, metric)
    assert {"L", "M", "S"}.issubset(table.columns)
    assert table["L"].notna().all()
    assert table["M"].gt(0).all()
    assert table["S"].gt(0).all()
    key = who_tables.KEY_COLUMN[metric]
    assert key in table.columns


def test_who_table_ranges() -> None:
    """Sanity-check the primary-source spans for each table."""
    assert who_tables.load_table("male", "wfa")["Month"].min() == 0
    assert who_tables.load_table("male", "wfa")["Month"].max() == 60
    hfa = who_tables.load_table("female", "hfa")  # merged 0-2 + 2-5 yr
    assert hfa["Month"].min() == 0 and hfa["Month"].max() == 60
    assert len(hfa) == 25 + 37 - 1  # month 24 overlaps; height segment wins
    assert who_tables.load_table("male", "wfl")["Length"].min() == 45.0
    assert who_tables.load_table("male", "wfl")["Length"].max() == 110.0
    assert who_tables.load_table("male", "wfh")["Height"].min() == 65.0
    assert who_tables.load_table("male", "wfh")["Height"].max() == 120.0
    # The ACA (MUAC) standard is published for 3-60 months, values in cm.
    muac = who_tables.load_table("male", "muac")
    assert muac["Month"].min() == 3 and muac["Month"].max() == 60
    assert muac["M"].max() < 30  # centimetres, not millimetres


def test_who_table_loader_caches() -> None:
    who_tables._cache.clear()
    first = who_tables.load_table("female", "wfa")
    second = who_tables.load_table("female", "wfa")
    assert first is second


def test_who_table_preload_all() -> None:
    who_tables._cache.clear()
    who_tables.preload()
    assert len(who_tables._cache) == 10  # 5 metrics x 2 sexes


# ---------------------------------------------------------------------------
# LMS math — verified against the primary-source SD reference values
# ---------------------------------------------------------------------------

#: SD_alpha as defined by the WHO (published formula, full precision).
def sd_alpha(l: float, m: float, s: float, alpha: float) -> float:
    if l == 0:
        return m * math.exp(s * alpha)
    return m * (1 + l * s * alpha) ** (1 / l)


@pytest.mark.parametrize("sex", ["male", "female"])
@pytest.mark.parametrize("metric", ["wfa", "hfa", "muac", "wfl", "wfh"])
@pytest.mark.parametrize("alpha", [-3, -2, -1, 0, 1, 2, 3])
def test_lms_reproduces_who_sd_formula(sex, metric, alpha) -> None:
    """z(SD_alpha) == alpha to machine precision for every table row.

    Uses the WHO's own SD definition (SD_alpha = M(1+LSa)^(1/L)) so this
    validates the LMS implementation itself, independent of the 0.1-decimal
    rounding of the published SD columns.
    """
    table = who_tables.load_table(sex, metric)
    kcol = who_tables.KEY_COLUMN[metric]
    for _, row in table.iterrows():
        x = sd_alpha(float(row["L"]), float(row["M"]), float(row["S"]), alpha)
        z = engine._zscore(sex, metric, float(row[kcol]), x)
        assert z == pytest.approx(alpha, abs=1e-9), (sex, metric, row[kcol], alpha)


@pytest.mark.parametrize("sex", ["male", "female"])
@pytest.mark.parametrize("metric", ["wfa", "hfa", "muac", "wfl", "wfh"])
@pytest.mark.parametrize("alpha", [-3, -2, -1, 0, 1, 2, 3])
def test_lms_reproduces_published_sd_columns(sex, metric, alpha) -> None:
    """z(published SD_alpha column) == alpha within the source rounding.

    The published SD columns are rounded to 0.1, and L/M/S to 4 decimals, so
    the round-trip carries up to ~0.3 z of noise (steepest on the
    weight-for-length table). Tolerance is set from the measured maximum.
    """
    table = who_tables.load_table(sex, metric)
    kcol = who_tables.KEY_COLUMN[metric]
    col = {0: "SD0", 1: "SD1", 2: "SD2", 3: "SD3", -1: "SD1neg", -2: "SD2neg", -3: "SD3neg"}[alpha]
    if col not in table.columns:
        pytest.skip(f"{metric} table has no {col} column")
    for _, row in table.iterrows():
        z = engine._zscore(sex, metric, float(row[kcol]), float(row[col]))
        assert z == pytest.approx(alpha, abs=0.3), (sex, metric, row[kcol], alpha)


def test_lms_log_case_guard() -> None:
    """L == 0 must use ln(X/M)/S, not divide by zero."""
    assert engine._lms_z(12.0, 0.0, 10.0, 0.1) == pytest.approx(math.log(1.2) / 0.1)
    assert engine._lms_z(10.0, 0.0, 10.0, 0.1) == 0.0


def test_public_metrics_known_references() -> None:
    """Spot checks via the public API against the published WHO reference
    values (median M gives exactly 0; published SD columns give alpha within
    the source's 0.1-decimal rounding)."""
    # WFA boy, month 0: median M=3.3464 -> z exactly 0.
    assert engine.waz(0, "male", 3.3464) == pytest.approx(0.0, abs=1e-9)
    # Published SD3neg=2.1 -> z=-3 within rounding noise.
    assert engine.waz(0, "male", 2.1) == pytest.approx(-3.0, abs=0.15)
    # HFA girl, month 36: median M -> exactly 0.
    hfa = who_tables.load_table("female", "hfa")
    row36 = hfa[hfa["Month"] == 36].iloc[0]
    assert engine.haz(36, "female", float(row36["M"])) == pytest.approx(0.0, abs=1e-9)
    # WHZ girl, month 30 (uses wfh): at height 100 cm, SD1 -> +1.
    wfh = who_tables.load_table("female", "wfh")
    row100 = wfh[wfh["Height"] == 100.0].iloc[0]
    assert engine.whz(30, "female", float(row100["SD1"]), 100.0) == pytest.approx(1.0, abs=0.15)
    # MUAC z boy, month 12: median M (cm) -> exactly 0.
    muac = who_tables.load_table("male", "muac")
    row12 = muac[muac["Month"] == 12].iloc[0]
    assert engine.muac_z(12, "male", float(row12["M"]) * 10.0) == pytest.approx(0.0, abs=1e-9)


def test_whz_interpolation_between_rows() -> None:
    """Mid-row height uses interpolated M, so the median weight gives z ~ 0."""
    # 100.4 cm sits between the 100.0 and 100.5 cm rows of the wfh table.
    assert engine.whz(30, "male", 13.0, 100.4) != engine.whz(30, "male", 13.0, 100.0)
    # Interpolated M at 100.4 must yield z ~ 0.
    l, m, s = engine._interp_lms("male", "wfh", 100.4)
    assert engine.whz(30, "male", m, 100.4) == pytest.approx(0.0, abs=0.01)


def test_whz_uses_length_table_below_24_months() -> None:
    """Age < 24 mo -> weight-for-length; >= 24 mo -> weight-for-height."""
    # 60 cm is only valid in the length table (45-110), not height (65-120).
    assert engine.whz(20, "male", 6.0, 60.0) != 0.0  # computes fine via wfl
    with pytest.raises(engine.AnthropometryInputError):
        engine.whz(24, "male", 6.0, 60.0)  # wfh range starts at 65 cm


# ---------------------------------------------------------------------------
# z-score -> category mapping (Implementation Plan boundaries)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("z", "expected"),
    [
        (-3.01, "severe"),
        (-3.0, "moderate"),   # -3 <= z < -2
        (-2.01, "moderate"),
        (-2.0, "normal"),     # -2 <= z <= 2
        (-1.5, "normal"),
        (0.0, "normal"),
        (2.0, "normal"),
        (2.01, "overweight"),  # z > 2 flag only
        (4.5, "overweight"),
    ],
)
def test_zscore_to_category_boundaries(z, expected) -> None:
    assert engine.zscore_to_category(z) == expected


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_waz_rejects_invalid_measurements() -> None:
    for bad in (0, -1, 251):
        with pytest.raises(engine.AnthropometryInputError):
            engine.waz(12, "male", bad)


def test_haz_rejects_tall_height() -> None:
    with pytest.raises(engine.AnthropometryInputError, match="height_cm"):
        engine.haz(12, "male", 250.1)


def test_rejects_bad_sex() -> None:
    with pytest.raises(engine.AnthropometryInputError, match="sex"):
        engine.waz(12, "other", 10.0)


def test_rejects_negative_age() -> None:
    with pytest.raises(engine.AnthropometryInputError, match="age"):
        engine.waz(-1, "male", 10.0)


def test_rejects_age_beyond_5_year_standard() -> None:
    with pytest.raises(engine.AnthropometryInputError, match="60"):
        engine.waz(61, "male", 15.0)
    with pytest.raises(engine.AnthropometryInputError, match="60"):
        engine.whz(61, "male", 15.0, 110.0)


def test_muac_z_out_of_aca_range() -> None:
    with pytest.raises(engine.AnthropometryInputError, match="3 months"):
        engine.muac_z(2, "male", 130.0)
    with pytest.raises(engine.AnthropometryInputError, match="60"):
        engine.muac_z(61, "male", 150.0)


# ---------------------------------------------------------------------------
# MUAC category bands
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("muac_mm", "expected"),
    [
        (114.9, "severe"),   # < 115
        (115.0, "moderate"), # >= 115, < 125
        (124.9, "moderate"),
        (125.0, "normal"),   # >= 125
        (150.0, "normal"),
    ],
)
def test_muac_category_6_59_months(muac_mm, expected) -> None:
    for age in (6, 30, 59):  # age-independent within 6-59 months
        assert engine.muac_category(age, "male", muac_mm) == expected


def test_muac_category_below_6_months_out_of_scope() -> None:
    with pytest.raises(engine.AnthropometryInputError, match="6 months"):
        engine.muac_category(5, "male", 120.0)


def test_muac_category_5_to_18_years_mramba_reference() -> None:
    """Research-based SAM cutoffs (Mramba et al. 2017); no WHO standard."""
    # 8 years: cutoff 148 mm.
    assert engine.muac_category(96, "male", 147.9) == "severe"
    assert engine.muac_category(96, "male", 148.0) == "normal"
    # 15 years: cutoff 187 mm (interpolated between 14 y=182 and 15 y=187).
    assert engine.muac_category(180, "female", 186.0) == "severe"
    assert engine.muac_category(180, "female", 187.0) == "normal"
    # 6.5 years interpolates between 6 y (136) and 7 y (142): 139 mm.
    assert engine.muac_category(78, "male", 138.0) == "severe"
    assert engine.muac_category(78, "male", 140.0) == "normal"


def test_muac_category_adults_230mm_indicator() -> None:
    """19+ years: MUAC < 230 mm -> moderate (adult undernutrition indicator)."""
    assert engine.muac_category(228, "female", 229.0) == "moderate"
    assert engine.muac_category(228, "female", 230.0) == "normal"
    assert engine.muac_category(300, "male", 215.0) == "moderate"  # pregnant-woman example
    assert engine.muac_category(300, "male", 260.0) == "normal"
