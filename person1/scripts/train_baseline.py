#!/usr/bin/env python
"""Train the classical computer-vision baseline (Hour 3).

Flow: manifest -> features (RGB+LAB over tissue pixels) -> StandardScaler
(fit on TRAIN only) -> Logistic Regression + Random Forest (class-balanced)
-> validation comparison -> select best (validation anemic-class F1) ->
ONE test evaluation -> save pipeline, metrics, confusion matrix, feature
importance, latency.

Run from the repository root:
    python scripts/train_baseline.py

All reported numbers are measured; nothing is fabricated.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from app.ai.features import FEATURE_NAMES, ColorFeatureExtractor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.csv"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
MODEL_PATH = PROJECT_ROOT / "models" / "baseline_classifier.joblib"
SEED = 42
ANEMIC = "anemic"  # positive class for screening metrics


def load_manifest() -> pd.DataFrame:
    df = pd.read_csv(MANIFEST_PATH)
    # raw_path is absolute on this machine; resolve to a Path for feature extraction
    df["raw_path"] = df["raw_path"].apply(lambda p: Path(p))
    return df


def build_pipeline(clf) -> Pipeline:
    return Pipeline(
        [
            ("features", ColorFeatureExtractor()),
            ("scaler", StandardScaler()),
            ("clf", clf),
        ]
    )


def evaluate(pipeline: Pipeline, paths, y_true: np.ndarray) -> dict:
    y_pred = pipeline.predict(paths)
    proba = pipeline.predict_proba(paths)
    classes = pipeline.classes_
    pos_idx = list(classes).index(ANEMIC)
    y_prob = proba[:, pos_idx]
    # roc_auc_score needs numeric binary labels; string labels would be
    # encoded alphabetically ('anemic' -> 0), silently flipping the AUC.
    y_true_bin = (y_true == ANEMIC).astype(int)
    y_pred_bin = (y_pred == ANEMIC).astype(int)

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_anemic": float(precision_score(y_true, y_pred, pos_label=ANEMIC, zero_division=0)),
        "recall_anemic": float(recall_score(y_true, y_pred, pos_label=ANEMIC, zero_division=0)),
        "f1_anemic": float(f1_score(y_true, y_pred, pos_label=ANEMIC, zero_division=0)),
        "precision_non_anemic": float(
            precision_score(y_true, y_pred, pos_label="non_anemic", zero_division=0)
        ),
        "recall_non_anemic": float(recall_score(y_true, y_pred, pos_label="non_anemic", zero_division=0)),
        "f1_non_anemic": float(f1_score(y_true, y_pred, pos_label="non_anemic", zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true_bin, y_prob)),
        "confusion_matrix": confusion_matrix(y_true_bin, y_pred_bin, labels=[0, 1]).tolist(),
        "n_samples": int(len(y_true)),
    }


def measure_latency(pipeline: Pipeline, paths, repeats: int = 3) -> dict:
    """Per-image pipeline latency (feature extraction + prediction), ms."""
    times = []
    for _ in range(repeats):
        for p in paths:
            t0 = time.perf_counter()
            pipeline.predict_proba([p])
            times.append((time.perf_counter() - t0) * 1000.0)
    times = np.array(times)
    return {
        "mean_ms": float(times.mean()),
        "median_ms": float(np.median(times)),
        "p95_ms": float(np.percentile(times, 95)),
        "samples": int(len(times)),
    }


def save_confusion_matrix(cm: np.ndarray, title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1], ["non_anemic", "anemic"])
    ax.set_yticks([0, 1], ["non_anemic", "anemic"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def save_feature_importance(clf, path: Path) -> None:
    if isinstance(clf, RandomForestClassifier):
        values = clf.feature_importances_
        ylabel = "RF feature importance"
    elif isinstance(clf, LogisticRegression):
        values = np.abs(clf.coef_[0])
        ylabel = "|logistic regression coefficient|"
    else:
        raise TypeError(f"unsupported classifier: {type(clf)}")

    order = np.argsort(values)[::-1]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh([FEATURE_NAMES[i] for i in order][::-1], values[order][::-1], color="#4C72B0")
    ax.set_xlabel(ylabel)
    ax.set_title("Features associated with model prediction")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main() -> int:
    manifest = load_manifest()
    train = manifest[manifest.split == "train"]
    val = manifest[manifest.split == "val"]
    test = manifest[manifest.split == "test"]
    print(f"train={len(train)} val={len(val)} test={len(test)}")

    train_paths = train["raw_path"].tolist()
    val_paths = val["raw_path"].tolist()
    test_paths = test["raw_path"].tolist()
    y_train = train["label"].to_numpy()
    y_val = val["label"].to_numpy()
    y_test = test["label"].to_numpy()

    models = {
        "logistic_regression": LogisticRegression(
            class_weight="balanced", max_iter=3000, random_state=SEED
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=500, class_weight="balanced", random_state=SEED, n_jobs=-1
        ),
    }

    print("\n[1/5] extracting features + fitting scaler on TRAIN only ...")
    feature_extractor = ColorFeatureExtractor()
    scaler = StandardScaler()
    X_train = scaler.fit_transform(feature_extractor.fit_transform(train_paths))
    print(f"      train feature matrix: {X_train.shape} (NaN: {int(np.isnan(X_train).sum())})")

    val_metrics = {}
    fitted = {}
    for name, clf in models.items():
        print(f"[2/5] training {name} ...")
        pipe = Pipeline(
            [
                ("features", feature_extractor),
                ("scaler", scaler),
                ("clf", clf),
            ]
        )
        pipe.fit(train_paths, y_train)
        fitted[name] = pipe
        val_metrics[name] = evaluate(pipe, val_paths, y_val)
        m = val_metrics[name]
        print(
            f"      val acc={m['accuracy']:.3f} rec_anemic={m['recall_anemic']:.3f} "
            f"prec_anemic={m['precision_anemic']:.3f} f1_anemic={m['f1_anemic']:.3f} "
            f"auc={m['roc_auc']:.3f}"
        )

    # [3/5] model selection on VALIDATION only (anemic-class F1)
    best_name = max(val_metrics, key=lambda n: val_metrics[n]["f1_anemic"])
    print(f"\n[3/5] selected baseline on validation: {best_name} (anemic F1 = {val_metrics[best_name]['f1_anemic']:.3f})")
    best_pipe = fitted[best_name]

    # [4/5] ONE test evaluation
    print("[4/5] evaluating TEST once (no tuning after this) ...")
    test_metrics = evaluate(best_pipe, test_paths, y_test)

    latency = measure_latency(best_pipe, test_paths)
    test_metrics["latency_ms"] = latency

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    save_confusion_matrix(
        np.array(test_metrics["confusion_matrix"]),
        f"Baseline {best_name} — test set",
        RESULTS_DIR / "baseline_confusion_matrix.png",
    )
    save_feature_importance(best_pipe.named_steps["clf"], RESULTS_DIR / "feature_importance.png")

    # [5/5] save artifacts
    joblib.dump(best_pipe, MODEL_PATH)
    metrics_payload = {
        "model": best_name,
        "model_path": str(MODEL_PATH),
        "n_features": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "validation": val_metrics,
        "test": test_metrics,
        "latency": latency,
        "selection_criterion": "validation anemic-class F1",
        "seed": SEED,
        "note": (
            "Screening research prototype. Metrics are model predictions on the "
            "held-out test split; no clinical validity is claimed."
        ),
    }
    (RESULTS_DIR / "baseline_metrics.json").write_text(
        json.dumps(metrics_payload, indent=2), encoding="utf-8"
    )
    (RESULTS_DIR / "baseline_latency.json").write_text(
        json.dumps({"model": best_name, **latency}), encoding="utf-8"
    )

    print(f"\n[5/5] saved model -> {MODEL_PATH}")
    print(f"      saved metrics -> {RESULTS_DIR / 'baseline_metrics.json'}")
    print(f"      saved latency -> {RESULTS_DIR / 'baseline_latency.json'}")
    print(f"      saved confusion matrix -> {RESULTS_DIR / 'baseline_confusion_matrix.png'}")
    print(f"      saved feature importance -> {RESULTS_DIR / 'feature_importance.png'}")

    print("\n===== TEST RESULTS (final, once) =====")
    for k, v in test_metrics.items():
        if k != "confusion_matrix":
            print(f"  {k}: {v}")
    print(f"  confusion_matrix (rows=true, cols=pred; [non_anemic, anemic]):")
    print(f"    {test_metrics['confusion_matrix']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
