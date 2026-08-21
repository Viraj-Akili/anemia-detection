"""Synthetic data generation + XGBoost training (Hours 4-5).

Re-runnable from the project root:

    .venv/bin/python -m src.fusion.model_train

Hour 4 (this module, implemented):

- ``generate_synthetic_dataset`` — simulates 20k-50k screening records from
  known clinical logic + noise:
  * demographics: children 6-179 months (~70%), pregnant women 180-540
    months (~15%), nonpregnant adults 180-780 months (~15%);
  * anthropometry: WHZ/HAZ/WAZ/MUAC-z sampled from a latent nutrition
    status z ~ N(-0.8, 1.2) (mild population-level undernutrition) + noise;
  * anemia: latent liability ~ N(0, 1) shifted by diet risk, IFA adherence,
    symptoms, pregnancy, and malnutrition; calibrated so ~35-45% of records
    cross the WHO 2024 Hb cutoff for their group;
  * CV pipeline output simulated as a noisy read of the latent liability;
  * labels from a hand-crafted "ground-truth rule" that mirrors the safety
    layer (Hour 6) — keeps the ML honest.
- ``split_dataset`` — deterministic 80/10/10 train/val/test split.
- ``__main__`` — generates, splits, and caches the dataset as CSV under
  ``assets/synthetic/``.

Hour 5 (pending): XGBoost training, Platt calibration, threshold selection,
SHAP integration, metrics report.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Allow `python -m src.fusion.model_train` from the project root: pytest gets
# `src` on sys.path from pytest.ini, plain Python does not.
_SRC_DIR = str(Path(__file__).resolve().parents[1])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

from context import engine as context_engine
from context import thresholds
from fusion.features import FUSION_FEATURES
from models.schemas import DietInput, IfaInput, SymptomsInput

logger = logging.getLogger(__name__)

#: Cache location for the generated dataset (project root / assets/synthetic).
DATA_DIR = Path(__file__).resolve().parents[2] / "assets" / "synthetic"

#: Artifact + report locations (project root).
MODELS_DIR = Path(__file__).resolve().parents[2] / "assets" / "models"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

#: The two late-fusion heads and their label columns.
HEADS = ("anemia", "nutrition")
LABEL_COLUMNS = {"anemia": "anemia_label", "nutrition": "nutrition_label"}

#: XGBoost hyperparameters (Implementation Plan Hour 5). Early stopping on the
#: validation split prevents overfitting the synthetic training set.
XGB_PARAMS = dict(
    max_depth=5,
    learning_rate=0.05,
    n_estimators=500,
    objective="binary:logistic",
    eval_metric="logloss",
    tree_method="hist",
    early_stopping_rounds=30,
)

#: Threshold selection constraint: screening must minimize missed cases, so
#: pick the most sensitive operating point with specificity >= this floor.
MIN_SPECIFICITY = 0.60

#: Split fractions — 80/10/10 train/val/test.
TRAIN_FRACTION = 0.8
VALIDATION_FRACTION = 0.1

#: Population mix (children / pregnant women / nonpregnant adults).
POPULATION_MIX = (0.70, 0.15, 0.15)

#: Latent nutrition status: z ~ N(mean, sd). Negative mean = mild population
#: undernutrition burden; sd spreads records across normal/moderate/severe.
NUTRITION_Z_MEAN = -0.8
NUTRITION_Z_SD = 1.2

#: Per-metric measurement noise (z units) on top of the latent status.
ANTHROPOMETRY_NOISE_SD = 0.35

#: Anemia base prevalence target (WHO: ~35-45% in the screened population).
#: The intercept calibrates the population mean liability so ~40% of records
#: cross the moderate-or-worse threshold; the shifts below are *relative*
#: risk contributions on top of this baseline.
ANEMIA_BASE_INTERCEPT = -1.45

#: Anemia liability shifts (positive = higher anemia risk).
ANEMIA_SHIFT_PREGNANCY = 0.35
ANEMIA_SHIFT_SYMPTOMS = 0.50
ANEMIA_SHIFT_MALNUTRITION = 0.40  # applied when nutrition label != normal
ANEMIA_SHIFT_MALNUTRITION_SEVERE = 0.80

#: CV pipeline simulation: score = clip(a*liability + noise, 0, 1).
CV_SCORE_SLOPE = 0.22
CV_SCORE_NOISE_SD = 0.12

#: Ground-truth rule cutoffs (mirror the safety layer, Hour 6).
GT_ANEMIA_HIGH_Z = 0.674    # top ~25% of the liability distribution
GT_ANEMIA_MODERATE_Z = -0.253  # ~40% moderate-or-worse
GT_NUTRITION_HIGH_Z = -2.0  # severe anthropometry
GT_NUTRITION_MODERATE_Z = -1.0

#: Symptom base probabilities (rare red flags).
SYMPTOM_PROBABILITIES = {
    "severe_pallor": 0.05,
    "breathlessness": 0.03,
    "bilateral_oedema": 0.02,
    "fatigue": 0.15,
}

#: Diet frequency mix (never / rare / sometimes / often).
DIET_FREQUENCY_MIX = (0.25, 0.35, 0.25, 0.15)
DIET_FREQUENCIES = ("never", "rare", "sometimes", "often")

#: IFA adherence mix (good / poor / unknown).
IFA_MIX = (0.35, 0.35, 0.30)
IFA_ADHERENCES = ("good", "poor", "unknown")


@dataclass(frozen=True)
class DatasetPaths:
    """On-disk locations of the cached synthetic dataset."""

    data: Path
    split: Path


def default_paths(n: int, seed: int) -> DatasetPaths:
    """Cache file paths for a given dataset size and seed."""
    stem = f"synthetic_n{n}_seed{seed}"
    return DatasetPaths(data=DATA_DIR / f"{stem}.csv", split=DATA_DIR / f"{stem}_split.csv")


# ---------------------------------------------------------------------------
# Demographics + context sampling
# ---------------------------------------------------------------------------


def _sample_demographics(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample (age_months, sex_codes, pregnancy_codes).

    sex: 0=female, 1=male. pregnancy: 1=pregnant (women 15-45 yr only).
    """
    group = rng.choice(3, size=n, p=POPULATION_MIX)
    age_months = np.empty(n)
    sex = np.zeros(n, dtype=int)
    pregnancy = np.zeros(n, dtype=int)

    children = group == 0
    age_months[children] = rng.integers(6, 180, size=children.sum())
    sex[children] = rng.integers(0, 2, size=children.sum())

    pregnant = group == 1
    age_months[pregnant] = rng.integers(180, 541, size=pregnant.sum())
    pregnancy[pregnant] = 1

    adults = group == 2
    age_months[adults] = rng.integers(180, 781, size=adults.sum())
    sex[adults] = rng.integers(0, 2, size=adults.sum())

    return age_months, sex, pregnancy


def _sample_context(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample (diet_frequency_codes, diet_diversity, ifa_codes).

    diet_frequency: 0=never, 1=rare, 2=sometimes, 3=often.
    ifa: 0=good, 1=poor, 2=unknown.
    """
    frequency = rng.choice(4, size=n, p=DIET_FREQUENCY_MIX)
    # Diversity correlates with frequency: better frequency -> more groups.
    diversity = np.clip(
        rng.normal(loc=2.0 + 1.6 * frequency, scale=1.8), 0, 9
    ).round().astype(int)
    ifa = rng.choice(3, size=n, p=IFA_MIX)
    return frequency, diversity, ifa


def _sample_symptoms(rng: np.random.Generator, n: int) -> np.ndarray:
    """Sample the four symptom booleans as a (n, 4) int array."""
    flags = np.zeros((n, 4), dtype=int)
    for col, probability in enumerate(SYMPTOM_PROBABILITIES.values()):
        flags[:, col] = rng.random(n) < probability
    return flags


def _sample_history(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample (prev_anemia_risk, prev_nutrition_risk, visits_count).

    ~30% of records are first visits (zero history); the rest carry noisy
    risks from earlier screenings.
    """
    visits = np.where(rng.random(n) < 0.30, 0, rng.integers(1, 6, size=n))
    has_history = visits > 0
    prev_anemia = np.clip(rng.beta(2.0, 3.0, size=n), 0.0, 1.0)
    prev_nutrition = np.clip(rng.beta(2.0, 3.5, size=n), 0.0, 1.0)
    prev_anemia[~has_history] = 0.0
    prev_nutrition[~has_history] = 0.0
    return prev_anemia, prev_nutrition, visits.astype(float)


# ---------------------------------------------------------------------------
# Latent clinical state -> observables
# ---------------------------------------------------------------------------


def _anemia_liability(
    rng: np.random.Generator,
    *,
    diet_risk: np.ndarray,
    ifa_protection: np.ndarray,
    symptom_count: np.ndarray,
    pregnancy: np.ndarray,
    nutrition_z: np.ndarray,
) -> np.ndarray:
    """Latent anemia liability ~ N(shift, 1); higher = more likely anaemic."""
    shift = (
        ANEMIA_BASE_INTERCEPT
        + 0.9 * diet_risk
        + 0.6 * (ifa_protection - 1.0)  # good adherence (0.85) -> negative shift
        + ANEMIA_SHIFT_SYMPTOMS * (symptom_count > 0)
        + ANEMIA_SHIFT_PREGNANCY * pregnancy
        + np.where(
            nutrition_z < GT_NUTRITION_HIGH_Z,
            ANEMIA_SHIFT_MALNUTRITION_SEVERE,
            np.where(nutrition_z < GT_NUTRITION_MODERATE_Z, ANEMIA_SHIFT_MALNUTRITION, 0.0),
        )
    )
    return rng.normal(loc=shift, scale=1.0)


def _cv_pipeline_output(rng: np.random.Generator, liability: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Simulate the CV classifier: noisy score in [0, 1] + confidence."""
    score = np.clip(CV_SCORE_SLOPE * liability + rng.normal(0.0, CV_SCORE_NOISE_SD, liability.size), 0.0, 1.0)
    # Confidence: high when the score is far from the 0.5 decision boundary.
    confidence = np.clip(0.55 + 0.9 * np.abs(score - 0.5) + rng.normal(0.0, 0.05, liability.size), 0.0, 1.0)
    return score, confidence


def _risk_band(score: np.ndarray) -> np.ndarray:
    """Continuous score -> low/moderate/high band (0/1/2)."""
    return np.where(score < 1 / 3, 0, np.where(score < 2 / 3, 1, 2))


def _ground_truth_labels(
    *,
    liability: np.ndarray,
    nutrition_z: np.ndarray,
    muac_cat: np.ndarray,
    symptom_oedema: np.ndarray,
    pregnancy: np.ndarray,
    symptom_pallor: np.ndarray,
    symptom_breathlessness: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hand-crafted ground-truth rule mirroring the safety layer (Hour 6).

    Returns (anemia_label, nutrition_label, red_flag) with labels 0=low,
    1=moderate, 2=high. Red flags only escalate (never downgrade), exactly
    like the safety layer contract.
    """
    anemia = np.where(
        liability >= GT_ANEMIA_HIGH_Z, 2, np.where(liability >= GT_ANEMIA_MODERATE_Z, 1, 0)
    )
    nutrition = np.where(
        nutrition_z <= GT_NUTRITION_HIGH_Z, 2, np.where(nutrition_z <= GT_NUTRITION_MODERATE_Z, 1, 0)
    )
    # RED FLAG 2: severe malnutrition (MUAC SAM category or severe wasting).
    red_flag = (muac_cat == 0) | (nutrition_z <= GT_NUTRITION_HIGH_Z)
    # RED FLAG 3: bilateral pitting oedema.
    red_flag |= symptom_oedema.astype(bool)
    # RED FLAG 4: pregnancy + severe pallor + breathlessness.
    red_flag |= pregnancy.astype(bool) & symptom_pallor.astype(bool) & symptom_breathlessness.astype(bool)
    # Escalation only: any red flag forces both axes to high.
    anemia = np.where(red_flag, 2, anemia)
    nutrition = np.where(red_flag, 2, nutrition)
    return anemia, nutrition, red_flag.astype(int)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_synthetic_dataset(n: int = 20_000, seed: int = 42) -> pd.DataFrame:
    """Simulate ``n`` screening records using known clinical logic + noise.

    Returns a DataFrame with the 20 :data:`fusion.features.FUSION_FEATURES`
    columns (in order) plus label columns: ``anemia_label``,
    ``nutrition_label`` (0=low, 1=moderate, 2=high), ``red_flag`` (0/1), and
    ``split`` (train/val/test).
    """
    if n < 100:
        raise ValueError(f"n must be at least 100 for a usable split, got {n}")
    rng = np.random.default_rng(seed)

    age_months, sex, pregnancy = _sample_demographics(rng, n)
    frequency, diversity, ifa = _sample_context(rng, n)
    symptoms = _sample_symptoms(rng, n)
    symptom_count = symptoms.sum(axis=1)

    # Context engine scores (reuse the production rule, not a re-implementation).
    diet_risk = np.array([
        context_engine.dietary_risk_score(DIET_FREQUENCIES[f], int(d))
        for f, d in zip(frequency, diversity)
    ])
    ifa_protection = np.array([
        context_engine.ifa_protection_multiplier(IfaInput(adherence=IFA_ADHERENCES[i]))
        for i in ifa
    ])

    # Anthropometry from a latent nutrition status + per-metric noise.
    nutrition_z = rng.normal(NUTRITION_Z_MEAN, NUTRITION_Z_SD, size=n)
    whz = nutrition_z + rng.normal(0.0, ANTHROPOMETRY_NOISE_SD, size=n)
    haz = nutrition_z + rng.normal(0.0, ANTHROPOMETRY_NOISE_SD, size=n)
    waz = nutrition_z + rng.normal(0.0, ANTHROPOMETRY_NOISE_SD, size=n)
    muac_z = nutrition_z + rng.normal(0.0, ANTHROPOMETRY_NOISE_SD, size=n)

    def _cat(z: np.ndarray) -> np.ndarray:
        return np.where(z < -3, 0, np.where(z < -2, 1, 2))

    whz_cat, haz_cat, waz_cat, muac_cat = _cat(whz), _cat(haz), _cat(waz), _cat(muac_z)

    # Anemia latent state -> CV pipeline simulation.
    liability = _anemia_liability(
        rng,
        diet_risk=diet_risk,
        ifa_protection=ifa_protection,
        symptom_count=symptom_count,
        pregnancy=pregnancy,
        nutrition_z=nutrition_z,
    )
    cv_score, cv_confidence = _cv_pipeline_output(rng, liability)

    prev_anemia, prev_nutrition, visits_count = _sample_history(rng, n)

    labels = _ground_truth_labels(
        liability=liability,
        nutrition_z=nutrition_z,
        muac_cat=muac_cat,
        symptom_oedema=symptoms[:, 2],
        pregnancy=pregnancy,
        symptom_pallor=symptoms[:, 0],
        symptom_breathlessness=symptoms[:, 1],
    )
    anemia_label, nutrition_label, red_flag = labels

    frame = pd.DataFrame(
        {
            "anemia_risk_score": cv_score,
            "anemia_confidence": cv_confidence,
            "whz": whz,
            "haz": haz,
            "waz": waz,
            "muac_z": muac_z,
            "whz_cat": whz_cat.astype(float),
            "haz_cat": haz_cat.astype(float),
            "waz_cat": waz_cat.astype(float),
            "muac_cat": muac_cat.astype(float),
            "diet_risk": diet_risk,
            "ifa_protection": ifa_protection,
            "symptom_flags": symptom_count.astype(float),
            "age_months": age_months,
            "sex_enc": sex.astype(float),
            "pregnancy_enc": pregnancy.astype(float),
            "trimester_enc": np.where(
                pregnancy.astype(bool), rng.integers(1, 4, size=n).astype(float), 0.0
            ),
            "prev_anemia_risk": prev_anemia,
            "prev_nutrition_risk": prev_nutrition,
            "visits_count": visits_count,
            "anemia_label": anemia_label,
            "nutrition_label": nutrition_label,
            "red_flag": red_flag,
        }
    )
    assert list(frame.columns[: len(FUSION_FEATURES)]) == FUSION_FEATURES, "feature order drifted"
    return split_dataset(frame, seed=seed)


def split_dataset(frame: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Add a deterministic ``split`` column: 80/10/10 train/val/test."""
    rng = np.random.default_rng(seed + 1)
    draw = rng.random(len(frame))
    split = np.where(
        draw < TRAIN_FRACTION,
        "train",
        np.where(draw < TRAIN_FRACTION + VALIDATION_FRACTION, "val", "test"),
    )
    out = frame.copy()
    out["split"] = split
    return out


def export_dataset(frame: pd.DataFrame, paths: DatasetPaths) -> DatasetPaths:
    """Cache the dataset (features + labels + split) as CSV."""
    paths.data.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(paths.data, index=False)
    logger.info("cached synthetic dataset: %s (%d rows)", paths.data, len(frame))
    return paths


def load_or_generate(n: int = 20_000, seed: int = 42, *, force: bool = False) -> tuple[pd.DataFrame, DatasetPaths]:
    """Load the cached dataset if present, else generate, split, and cache."""
    paths = default_paths(n, seed)
    if paths.data.exists() and not force:
        return pd.read_csv(paths.data), paths
    frame = generate_synthetic_dataset(n=n, seed=seed)
    export_dataset(frame, paths)
    return frame, paths


# ---------------------------------------------------------------------------
# Hour 5 — training, calibration, threshold selection, artifacts, metrics
# ---------------------------------------------------------------------------


def _binary_labels(labels: np.ndarray) -> np.ndarray:
    """Risk labels (0=low, 1=moderate, 2=high) -> binary (moderate-or-worse)."""
    return (labels > 0).astype(int)


def _fit_head(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
) -> xgb.XGBClassifier:
    """Train one XGBoost head with class weighting + early stopping on val."""
    n_pos = int(y_train.sum())
    n_neg = len(y_train) - n_pos
    model = xgb.XGBClassifier(
        **XGB_PARAMS,
        scale_pos_weight=(n_neg / n_pos) if n_pos else 1.0,
    )
    model.fit(
        x_train,
        y_train,
        eval_set=[(x_val, y_val)],
        verbose=False,
    )
    return model


def _platt_scaler(raw_proba: np.ndarray, y: np.ndarray) -> LogisticRegression:
    """Fit Platt scaling (logistic regression on raw probabilities) on val."""
    scaler = LogisticRegression(C=1e10, solver="lbfgs", max_iter=1000)
    scaler.fit(raw_proba.reshape(-1, 1), y)
    return scaler


def select_threshold(
    y_true: np.ndarray, proba: np.ndarray, *, min_specificity: float = MIN_SPECIFICITY
) -> tuple[float, float, float]:
    """Operating threshold maximizing sensitivity at specificity >= floor.

    Screening must minimize missed cases: among all candidate cutoffs whose
    specificity is at least ``min_specificity``, return the most sensitive
    one. Falls back to Youden's J if no candidate meets the floor.

    Returns (threshold, sensitivity, specificity).
    """
    candidates = np.unique(proba)
    positives = y_true.astype(bool)
    n_pos, n_neg = positives.sum(), (~positives).sum()
    best: tuple[float, float, float] | None = None
    fallback: tuple[float, float, float] | None = None
    for threshold in candidates:
        predicted = proba >= threshold
        tp = float((predicted & positives).sum())
        tn = float((~predicted & ~positives).sum())
        sensitivity = tp / n_pos if n_pos else 1.0
        specificity = tn / n_neg if n_neg else 1.0
        youden = sensitivity + specificity - 1.0
        if fallback is None or youden > fallback[1] + fallback[2] - 1.0:
            fallback = (float(threshold), sensitivity, specificity)
        if specificity >= min_specificity and (
            best is None
            or sensitivity > best[1]
            or (sensitivity == best[1] and specificity > best[2])  # tie: tighter cutoff
        ):
            best = (float(threshold), sensitivity, specificity)
    return best if best is not None else fallback  # type: ignore[return-value]


def _head_metrics(
    y_true: np.ndarray, proba: np.ndarray, threshold: float
) -> dict[str, float]:
    """ROC-AUC, PR-AUC, sensitivity/specificity/F1 at the operating point."""
    predicted = proba >= threshold
    positives = y_true.astype(bool)
    tp = float((predicted & positives).sum())
    fp = float((predicted & ~positives).sum())
    tn = float((~predicted & ~positives).sum())
    fn = float((~predicted & positives).sum())
    sensitivity = tp / (tp + fn) if tp + fn else 1.0
    specificity = tn / (tn + fp) if tn + fp else 1.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * precision * sensitivity / (precision + sensitivity) if precision + sensitivity else 0.0
    return {
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "pr_auc": float(average_precision_score(y_true, proba)),
        "threshold": float(threshold),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "precision": precision,
        "f1": f1,
    }


def train(
    n: int = 20_000,
    seed: int = 42,
    *,
    force_regenerate: bool = False,
) -> dict:
    """End-to-end training: fit both heads, calibrate, select thresholds,
    export artifacts (models, thresholds, feature list) and the metrics
    report. Returns the report dict.
    """
    started = time.perf_counter()
    frame, paths = load_or_generate(n=n, seed=seed, force=force_regenerate)

    x = frame[FUSION_FEATURES].to_numpy(dtype=float)
    splits = frame["split"].to_numpy()
    train_mask, val_mask, test_mask = splits == "train", splits == "val", splits == "test"

    models: dict[str, xgb.XGBClassifier] = {}
    scalers: dict[str, LogisticRegression] = {}
    thresholds: dict[str, float] = {}
    metrics: dict[str, dict] = {}

    for head in HEADS:
        y = _binary_labels(frame[LABEL_COLUMNS[head]].to_numpy())
        model = _fit_head(x[train_mask], y[train_mask], x[val_mask], y[val_mask])
        models[head] = model

        # Platt scaling on the held-out validation split (blueprint Part 22).
        val_raw = model.predict_proba(x[val_mask])[:, 1]
        scalers[head] = _platt_scaler(val_raw, y[val_mask])
        val_calibrated = scalers[head].predict_proba(val_raw.reshape(-1, 1))[:, 1]

        threshold, sensitivity, specificity = select_threshold(y[val_mask], val_calibrated)
        thresholds[head] = threshold
        metrics[head] = {
            "val": _head_metrics(y[val_mask], val_calibrated, threshold),
            "test": _head_metrics(
                y[test_mask],
                scalers[head].predict_proba(model.predict_proba(x[test_mask])[:, 1].reshape(-1, 1))[:, 1],
                threshold,
            ),
            "val_sensitivity_at_selection": sensitivity,
            "val_specificity_at_selection": specificity,
        }

    artifacts = export_artifacts(models, scalers, thresholds)
    report = {
        "dataset": {"rows": int(len(frame)), "path": str(paths.data), "seed": seed},
        "train_seconds": round(time.perf_counter() - started, 2),
        "heads": metrics,
        "artifacts": {name: str(path) for name, path in artifacts.items()},
    }
    write_report(report)
    logger.info("training finished in %.1fs", report["train_seconds"])
    return report


def export_artifacts(
    models: dict[str, xgb.XGBClassifier],
    scalers: dict[str, LogisticRegression],
    thresholds: dict[str, float],
) -> dict[str, Path]:
    """Persist model.json per head, thresholds.json, and features.json."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Path] = {}
    for head, model in models.items():
        model_path = MODELS_DIR / f"{head}_model.json"
        model.save_model(str(model_path))
        artifacts[f"{head}_model"] = model_path

    thresholds_path = MODELS_DIR / "thresholds.json"
    thresholds_path.write_text(
        json.dumps(
            {
                "operating_threshold": thresholds,
                "platt_scaling": {
                    head: {
                        "coef": float(scaler.coef_[0][0]),
                        "intercept": float(scaler.intercept_[0]),
                    }
                    for head, scaler in scalers.items()
                },
                "min_specificity_constraint": MIN_SPECIFICITY,
            },
            indent=2,
        )
    )
    artifacts["thresholds"] = thresholds_path

    features_path = MODELS_DIR / "features.json"
    features_path.write_text(json.dumps(FUSION_FEATURES, indent=2))
    artifacts["features"] = features_path
    return artifacts


def write_report(report: dict) -> Path:
    """Write the metrics report to ``reports/`` for the pitch."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "fusion_model_metrics.json"
    path.write_text(json.dumps(report, indent=2))
    return path


def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    report = train()
    for head, head_metrics in report["heads"].items():
        val = head_metrics["val"]
        print(
            f"{head}: ROC-AUC {val['roc_auc']:.3f}  PR-AUC {val['pr_auc']:.3f}  "
            f"sens {val['sensitivity']:.3f}  spec {val['specificity']:.3f}  "
            f"F1 {val['f1']:.3f}  @ threshold {val['threshold']:.3f}"
        )
    print(f"trained in {report['train_seconds']}s")
    print(f"report: {report['artifacts'] and REPORTS_DIR / 'fusion_model_metrics.json'}")


if __name__ == "__main__":
    _main()
