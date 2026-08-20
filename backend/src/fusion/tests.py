"""Unit tests for fusion/features.py and fusion/model_train.py (Hour 4)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fusion import features, model_train


# ---------------------------------------------------------------------------
# build_features — vector shape, order, encodings
# ---------------------------------------------------------------------------


def _anthro(**overrides) -> dict:
    base = dict(
        whz=-1.2, haz=-0.8, waz=-1.0, muac_z=-0.5,
        whz_cat="moderate", haz_cat="normal", waz_cat="normal", muac_cat="normal",
    )
    base.update(overrides)
    return base


def _context(**overrides) -> dict:
    base = dict(
        diet_risk=0.6, ifa_protection=0.85, symptom_flags=["SEVERE_PALLOR"],
        age_months=36, sex="female", pregnancy=False, trimester=None,
    )
    base.update(overrides)
    return base


def _anemia(**overrides) -> dict:
    base = dict(risk="moderate", confidence=0.82)
    base.update(overrides)
    return base


def test_build_features_length_and_order() -> None:
    vector = features.build_features(
        anthropometry=_anthro(), context=_context(), anemia=_anemia(), history=None
    )
    assert len(vector) == len(features.FUSION_FEATURES) == 20
    assert all(isinstance(v, float) for v in vector)


def test_build_features_exact_values() -> None:
    vector = features.build_features(
        anthropometry=_anthro(),
        context=_context(),
        anemia=_anemia(),
        history=dict(prev_anemia_risk=0.4, prev_nutrition_risk=0.2, visits_count=3),
    )
    expected = dict(zip(features.FUSION_FEATURES, vector))
    assert expected["anemia_risk_score"] == 0.5          # moderate -> 0.5
    assert expected["anemia_confidence"] == 0.82
    assert expected["whz"] == -1.2 and expected["muac_z"] == -0.5
    assert expected["whz_cat"] == 1.0                    # moderate -> 1
    assert expected["haz_cat"] == 2.0                    # normal -> 2
    assert expected["diet_risk"] == 0.6
    assert expected["ifa_protection"] == 0.85
    assert expected["symptom_flags"] == 1.0              # count of flag list
    assert expected["age_months"] == 36.0
    assert expected["sex_enc"] == 0.0                    # female -> 0
    assert expected["pregnancy_enc"] == 0.0
    assert expected["trimester_enc"] == 0.0
    assert expected["prev_anemia_risk"] == 0.4
    assert expected["prev_nutrition_risk"] == 0.2
    assert expected["visits_count"] == 3.0


def test_build_features_pregnancy_trimester_encoding() -> None:
    vector = features.build_features(
        anthropometry=_anthro(),
        context=_context(age_months=300, pregnancy=True, trimester=2),
        anemia=_anemia(),
    )
    expected = dict(zip(features.FUSION_FEATURES, vector))
    assert expected["pregnancy_enc"] == 1.0
    assert expected["trimester_enc"] == 2.0


def test_build_features_risk_band_and_category_encodings() -> None:
    low = features.build_features(
        anthropometry=_anthro(whz_cat="severe", haz_cat="overweight"),
        context=_context(sex="male", symptom_flags=[]),
        anemia=_anemia(risk="low", confidence=0.1),
    )
    high = features.build_features(
        anthropometry=_anthro(), context=_context(), anemia=_anemia(risk="high")
    )
    low_map = dict(zip(features.FUSION_FEATURES, low))
    high_map = dict(zip(features.FUSION_FEATURES, high))
    assert low_map["anemia_risk_score"] == 0.0
    assert high_map["anemia_risk_score"] == 1.0
    assert low_map["whz_cat"] == 0.0        # severe -> 0
    assert low_map["haz_cat"] == 2.0        # overweight -> 2 (flag only)
    assert low_map["sex_enc"] == 1.0        # male -> 1
    assert low_map["symptom_flags"] == 0.0


def test_build_features_history_defaults_to_zero() -> None:
    vector = features.build_features(
        anthropometry=_anthro(), context=_context(), anemia=_anemia(), history=None
    )
    expected = dict(zip(features.FUSION_FEATURES, vector))
    assert expected["prev_anemia_risk"] == 0.0
    assert expected["prev_nutrition_risk"] == 0.0
    assert expected["visits_count"] == 0.0


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        (dict(anemia=dict(risk="extreme", confidence=0.5)), "risk"),
        (dict(anemia=dict(risk="low", confidence=1.5)), "confidence"),
        (dict(context=_context(sex="other")), "sex"),
        (dict(context=_context(pregnancy=True, trimester=None)), "trimester"),
        (dict(context=_context(pregnancy=True, trimester=4)), "trimester"),
        (dict(context=_context(age_months=-1)), "age_months"),
        (dict(anthropometry=_anthro(whz_cat="giant")), "whz_cat"),
        (dict(anthropometry=_anthro(whz=float("nan"))), "whz"),
        (dict(history=dict(visits_count=-2)), "visits_count"),
    ],
)
def test_build_features_rejects_bad_inputs(kwargs, match) -> None:
    defaults = dict(anthropometry=_anthro(), context=_context(), anemia=_anemia())
    defaults.update(kwargs)
    with pytest.raises(features.FeatureInputError, match=match):
        features.build_features(**defaults)


def test_build_features_missing_keys_rejected() -> None:
    bad_anthro = _anthro()
    del bad_anthro["muac_z"]
    with pytest.raises(features.FeatureInputError, match="muac_z"):
        features.build_features(anthropometry=bad_anthro, context=_context(), anemia=_anemia())


# ---------------------------------------------------------------------------
# generate_synthetic_dataset — schema, distributions, labels
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def dataset() -> pd.DataFrame:
    return model_train.generate_synthetic_dataset(n=5_000, seed=7)


def test_dataset_schema_and_feature_order(dataset) -> None:
    expected_columns = [
        *features.FUSION_FEATURES,
        "anemia_label", "nutrition_label", "red_flag", "split",
    ]
    assert list(dataset.columns) == expected_columns


def test_dataset_split_fractions(dataset) -> None:
    counts = dataset["split"].value_counts(normalize=True)
    assert counts["train"] == pytest.approx(0.8, abs=0.03)
    assert counts["val"] == pytest.approx(0.1, abs=0.03)
    assert counts["test"] == pytest.approx(0.1, abs=0.03)


def test_dataset_anemia_prevalence_in_target_band(dataset) -> None:
    """Plan: base rate ~35-45% moderate-or-worse anemia."""
    prevalence = float((dataset["anemia_label"] > 0).mean())
    assert 0.30 <= prevalence <= 0.55, prevalence


def test_dataset_demographics(dataset) -> None:
    children = dataset["age_months"] < 180
    pregnant = dataset["pregnancy_enc"] == 1.0
    assert children.mean() == pytest.approx(0.70, abs=0.05)
    assert pregnant.mean() == pytest.approx(0.15, abs=0.05)
    # Pregnant records are women 15-45 yr with a valid trimester.
    preg = dataset[pregnant]
    assert (preg["sex_enc"] == 0.0).all()
    assert preg["age_months"].between(180, 540).all()
    assert set(preg["trimester_enc"].unique()) <= {1.0, 2.0, 3.0}
    # Nonpregnant records carry trimester 0.
    assert (dataset.loc[~pregnant, "trimester_enc"] == 0.0).all()


def test_dataset_labels_valid_ranges(dataset) -> None:
    assert set(dataset["anemia_label"].unique()) <= {0, 1, 2}
    assert set(dataset["nutrition_label"].unique()) <= {0, 1, 2}
    assert set(dataset["red_flag"].unique()) <= {0, 1}
    assert dataset["anemia_confidence"].between(0.0, 1.0).all()
    assert dataset["anemia_risk_score"].between(0.0, 1.0).all()
    assert dataset["diet_risk"].between(0.0, 1.0).all()
    assert set(dataset["ifa_protection"].unique()) <= {0.85, 1.0}
    assert (dataset["visits_count"] >= 0).all()


def test_dataset_red_flags_force_high_labels(dataset) -> None:
    """Ground-truth rule mirrors the safety layer: escalation only."""
    flagged = dataset[dataset["red_flag"] == 1]
    assert (flagged["anemia_label"] == 2).all()
    assert (flagged["nutrition_label"] == 2).all()


def test_dataset_deterministic_for_same_seed() -> None:
    a = model_train.generate_synthetic_dataset(n=1_000, seed=11)
    b = model_train.generate_synthetic_dataset(n=1_000, seed=11)
    pd.testing.assert_frame_equal(a, b)


def test_dataset_rejects_tiny_n() -> None:
    with pytest.raises(ValueError, match="at least 100"):
        model_train.generate_synthetic_dataset(n=10)


def test_split_dataset_is_deterministic() -> None:
    frame = pd.DataFrame({"x": range(1000)})
    a = model_train.split_dataset(frame, seed=3)
    b = model_train.split_dataset(frame, seed=3)
    assert (a["split"] == b["split"]).all()
    assert set(a["split"].unique()) == {"train", "val", "test"}


# ---------------------------------------------------------------------------
# Hour 5 — threshold selection, training, artifacts, predict()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("y", "proba", "min_spec", "expected_sens", "expected_spec"),
    [
        # Perfect separation -> threshold at the lowest positive score.
        (np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9]), 0.5, 1.0, 1.0),
        # Overlapping scores: highest sensitivity subject to spec >= floor.
        (np.array([0, 1, 0, 1]), np.array([0.2, 0.4, 0.6, 0.8]), 0.5, 1.0, 0.5),
    ],
)
def test_select_threshold_maximizes_sensitivity(y, proba, min_spec, expected_sens, expected_spec) -> None:
    threshold, sensitivity, specificity = model_train.select_threshold(
        y, proba, min_specificity=min_spec
    )
    assert sensitivity == pytest.approx(expected_sens)
    assert specificity == pytest.approx(expected_spec)


def test_select_threshold_falls_back_to_youden() -> None:
    """Impossible specificity floor -> Youden's J fallback still returns."""
    y = np.array([0, 0, 1, 1])
    proba = np.array([0.4, 0.6, 0.5, 0.7])
    threshold, sensitivity, specificity = model_train.select_threshold(y, proba, min_specificity=1.0)
    assert 0.0 <= threshold <= 1.0
    assert 0.0 <= sensitivity <= 1.0 and 0.0 <= specificity <= 1.0


@pytest.fixture(scope="module")
def trained(tmp_path_factory) -> dict:
    """Train a small model end-to-end into a temp dir (module-scoped)."""
    tmp = tmp_path_factory.mktemp("fusion_artifacts")
    # Point artifact/report dirs at the temp location for this run.
    original_models, original_reports = model_train.MODELS_DIR, model_train.REPORTS_DIR
    model_train.MODELS_DIR = tmp / "models"
    model_train.REPORTS_DIR = tmp / "reports"
    try:
        report = model_train.train(n=4_000, seed=3)
    finally:
        model_train.MODELS_DIR, model_train.REPORTS_DIR = original_models, original_reports
    report["_dir"] = tmp
    return report


def test_train_writes_artifacts_and_report(trained) -> None:
    tmp = trained["_dir"]
    assert (tmp / "models" / "anemia_model.json").exists()
    assert (tmp / "models" / "nutrition_model.json").exists()
    assert (tmp / "models" / "thresholds.json").exists()
    assert (tmp / "models" / "features.json").exists()
    assert (tmp / "reports" / "fusion_model_metrics.json").exists()
    assert set(trained["heads"]) == {"anemia", "nutrition"}


def test_train_metrics_sane(trained) -> None:
    for head in ("anemia", "nutrition"):
        val = trained["heads"][head]["val"]
        assert val["roc_auc"] > 0.7, (head, val)   # synthetic signal is learnable
        assert val["pr_auc"] > 0.5
        assert 0.0 < val["threshold"] < 1.0
        # Screening contract: sensitivity prioritized at the operating point.
        assert val["sensitivity"] >= 0.7, (head, val)


def test_train_under_five_minutes(trained) -> None:
    assert trained["train_seconds"] < 300


def test_predict_returns_calibrated_probabilities_and_contributors(trained) -> None:
    from fusion import engine

    vector = features.build_features(
        anthropometry=_anthro(),
        context=_context(),
        anemia=_anemia(risk="high", confidence=0.9),
        history=dict(prev_anemia_risk=0.7, prev_nutrition_risk=0.5, visits_count=2),
    )
    result = engine.predict(vector, models_dir=trained["_dir"] / "models")
    assert 0.0 <= result["anemia_risk_proba"] <= 1.0
    assert 0.0 <= result["nutrition_risk_proba"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["contributors"]) == 3
    for contributor in result["contributors"]:
        assert contributor["feature"] in features.FUSION_FEATURES
        assert contributor["label"]
        assert -1.0 <= contributor["importance"] <= 1.0


def test_predict_high_risk_input_scores_higher_than_low(trained) -> None:
    from fusion import engine

    high = engine.predict(
        features.build_features(
            anthropometry=_anthro(whz=-3.5, whz_cat="severe", muac_cat="severe", muac_z=-3.2),
            context=_context(diet_risk=1.0, ifa_protection=1.0, symptom_flags=["SEVERE_PALLOR"]),
            anemia=_anemia(risk="high", confidence=0.95),
        ),
        models_dir=trained["_dir"] / "models",
    )
    low = engine.predict(
        features.build_features(
            anthropometry=_anthro(whz=0.5, whz_cat="normal", muac_z=0.4),
            context=_context(diet_risk=0.0, ifa_protection=0.85, symptom_flags=[]),
            anemia=_anemia(risk="low", confidence=0.9),
        ),
        models_dir=trained["_dir"] / "models",
    )
    assert high["anemia_risk_proba"] > low["anemia_risk_proba"]
    assert high["nutrition_risk_proba"] > low["nutrition_risk_proba"]


def test_predict_rejects_wrong_feature_count(trained) -> None:
    from fusion import engine

    with pytest.raises(engine.FusionModelError, match="features"):
        engine.predict([0.0] * 5, models_dir=trained["_dir"] / "models")


def test_load_time_under_one_second(trained) -> None:
    from fusion import engine

    elapsed = engine.load_time_seconds(models_dir=trained["_dir"] / "models")
    assert elapsed < 1.0, elapsed
