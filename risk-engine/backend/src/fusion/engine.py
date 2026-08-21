"""Late-fusion prediction: calibrated XGBoost probabilities + SHAP top-3
contributors (Hour 5).

``predict()`` returns calibrated ``anemia_risk_proba`` and
``nutrition_risk_proba`` (Platt-scaled on the validation split, blueprint
Part 22), plus the top-3 contributing features mapped to human-readable
labels for the response ``contributors`` list.

Artifacts are produced by ``fusion.model_train.train()`` and live under
``assets/models/``: ``{head}_model.json``, ``thresholds.json`` (operating
thresholds + Platt coefficients), ``features.json`` (fixed feature order).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import shap
import xgboost as xgb

from fusion.features import FUSION_FEATURES

MODELS_DIR = Path(__file__).resolve().parents[2] / "assets" / "models"

HEADS = ("anemia", "nutrition")

#: Machine feature name -> plain-language label for the response
#: ``contributors`` list (Appendix A).
FEATURE_LABELS: dict[str, str] = {
    "anemia_risk_score": "AI camera-based anemia estimate",
    "anemia_confidence": "Confidence of the camera-based estimate",
    "whz": "Low weight for height (wasting)",
    "haz": "Low height for age (stunting)",
    "waz": "Low weight for age (underweight)",
    "muac_z": "Low mid-upper arm circumference",
    "whz_cat": "Wasting severity category",
    "haz_cat": "Stunting severity category",
    "waz_cat": "Underweight severity category",
    "muac_cat": "MUAC severity category",
    "diet_risk": "Low reported dietary iron intake",
    "ifa_protection": "Iron-folic acid supplement adherence",
    "symptom_flags": "Reported red-flag symptoms",
    "age_months": "Age of the beneficiary",
    "sex_enc": "Sex of the beneficiary",
    "pregnancy_enc": "Pregnancy status",
    "trimester_enc": "Pregnancy trimester",
    "prev_anemia_risk": "Anemia risk at the previous visit",
    "prev_nutrition_risk": "Nutrition risk at the previous visit",
    "visits_count": "Number of previous screening visits",
}


class FusionModelError(RuntimeError):
    """Raised when artifacts are missing or inputs are malformed."""


@dataclass(frozen=True)
class _Head:
    model: xgb.XGBClassifier
    platt_coef: float
    platt_intercept: float
    threshold: float


@dataclass(frozen=True)
class FusionBundle:
    """Loaded artifacts: both heads, their SHAP explainers, feature order."""

    heads: dict[str, _Head]
    explainer: shap.TreeExplainer
    features: list[str]


_BUNDLE_CACHE: FusionBundle | None = None


def load_bundle(models_dir: Path | None = None) -> FusionBundle:
    """Load models + thresholds + feature list from disk (cached)."""
    global _BUNDLE_CACHE
    if _BUNDLE_CACHE is not None and models_dir is None:
        return _BUNDLE_CACHE

    base = models_dir or MODELS_DIR
    thresholds_path = base / "thresholds.json"
    features_path = base / "features.json"
    if not thresholds_path.exists() or not features_path.exists():
        raise FusionModelError(
            f"fusion artifacts not found in {base} — run "
            "`python -m src.fusion.model_train` first"
        )
    thresholds = json.loads(thresholds_path.read_text())
    features = json.loads(features_path.read_text())

    heads: dict[str, _Head] = {}
    for name in HEADS:
        model_path = base / f"{name}_model.json"
        if not model_path.exists():
            raise FusionModelError(f"missing model artifact: {model_path}")
        model = xgb.XGBClassifier()
        model.load_model(str(model_path))
        platt = thresholds["platt_scaling"][name]
        heads[name] = _Head(
            model=model,
            platt_coef=platt["coef"],
            platt_intercept=platt["intercept"],
            threshold=thresholds["operating_threshold"][name],
        )

    # One TreeExplainer over the anemia head suffices: both heads consume the
    # identical 20-feature vector, and contributors explain the input, not the
    # head. The anemia head is the primary clinical axis.
    explainer = shap.TreeExplainer(heads["anemia"].model)
    bundle = FusionBundle(heads=heads, explainer=explainer, features=features)
    if models_dir is None:
        _BUNDLE_CACHE = bundle
    return bundle


def _calibrate(raw_proba: np.ndarray, head: _Head) -> np.ndarray:
    """Platt scaling: logistic transform of the raw XGBoost probability."""
    logit = head.platt_coef * raw_proba + head.platt_intercept
    return 1.0 / (1.0 + np.exp(-logit))


def _top_contributors(shap_values: np.ndarray, features: list[str], k: int = 3) -> list[dict]:
    """Top-k features by |SHAP|, most important first, human-readable."""
    order = np.argsort(-np.abs(shap_values))[:k]
    return [
        {
            "feature": features[int(idx)],
            "label": FEATURE_LABELS.get(features[int(idx)], features[int(idx)]),
            "importance": float(np.clip(shap_values[int(idx)], -1.0, 1.0)),
        }
        for idx in order
    ]


def predict(features: list[float], *, models_dir: Path | None = None) -> dict:
    """Predict calibrated risk probabilities + top-3 contributors.

    ``features`` must be the 20-feature vector in
    :data:`fusion.features.FUSION_FEATURES` order (see ``build_features``).

    Returns ``{"anemia_risk_proba", "nutrition_risk_proba", "confidence",
    "contributors", "flags"}`` where ``flags`` lists heads whose calibrated
    probability crosses its operating threshold (the safety layer makes the
    final escalation decision — this is advisory only).
    """
    bundle = load_bundle(models_dir)
    vector = np.asarray(features, dtype=float)
    if vector.shape != (len(bundle.features),):
        raise FusionModelError(
            f"expected {len(bundle.features)} features, got {vector.shape}"
        )
    matrix = vector.reshape(1, -1)

    probabilities: dict[str, float] = {}
    flags: list[str] = []
    for name, head in bundle.heads.items():
        raw = head.model.predict_proba(matrix)[:, 1]
        calibrated = float(_calibrate(raw, head)[0])
        probabilities[f"{name}_risk_proba"] = calibrated
        if calibrated >= head.threshold:
            flags.append(name)

    shap_values = np.asarray(bundle.explainer.shap_values(matrix)).reshape(-1)
    return {
        **probabilities,
        "confidence": float(max(probabilities.values())),
        "contributors": _top_contributors(shap_values, bundle.features),
        "flags": flags,
    }


def load_time_seconds(models_dir: Path | None = None) -> float:
    """Wall-clock time to load the artifact bundle (DoD: < 1 s)."""
    global _BUNDLE_CACHE
    _BUNDLE_CACHE = None  # force a cold load for measurement
    started = time.perf_counter()
    load_bundle(models_dir)
    return time.perf_counter() - started
