"""
scripts/train_evaluate_models.py

STEP 3G - 3M — LEAKAGE-FREE ML MODEL TRAINING, SELECTION, AND EVALUATION
PRAHARI PPG / Hardware ML Pipeline

PROTOCOL:
1. Load features from data/processed/ppg_features.csv.
2. Partition into Train (47), Validation (10), Test (11) by subject_id.
3. Assert zero subject overlap across splits (leakage prevention).
4. Fit StandardScaler ONLY on Training data.
5. Train candidate models on Train, evaluate on Validation.
6. Select best model based strictly on Validation MAE/RMSE.
7. Evaluate best model ONCE on Test set.
8. Extract feature importances and save models and reports.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
import joblib

from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.inspection import permutation_importance

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate MAE, RMSE, and R2 regression metrics."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(root_mean_squared_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4)
    }


def train_and_evaluate_all_models(
    features_csv: Path,
    metadata_dir: Path,
    models_dir: Path,
    reports_dir: Path,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Execute strict subject-level ML workflow and save models and comparison metrics.
    """
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    df_all = pd.read_csv(features_csv)

    # 1. Load Subject-Level Split Sets
    train_subs_df = pd.read_csv(metadata_dir / "train_subjects.csv")
    val_subs_df = pd.read_csv(metadata_dir / "validation_subjects.csv")
    test_subs_df = pd.read_csv(metadata_dir / "test_subjects.csv")

    train_ids = set(train_subs_df["subject_id"])
    val_ids = set(val_subs_df["subject_id"])
    test_ids = set(test_subs_df["subject_id"])

    # CRITICAL LEAKAGE ASSERTIONS
    assert len(train_ids & val_ids) == 0, f"DATA LEAKAGE: Train and Val overlap on {train_ids & val_ids}"
    assert len(train_ids & test_ids) == 0, f"DATA LEAKAGE: Train and Test overlap on {train_ids & test_ids}"
    assert len(val_ids & test_ids) == 0, f"DATA LEAKAGE: Val and Test overlap on {val_ids & test_ids}"

    # Subset datasets
    df_train = df_all[df_all["subject_id"].isin(train_ids)].copy()
    df_val = df_all[df_all["subject_id"].isin(val_ids)].copy()
    df_test = df_all[df_all["subject_id"].isin(test_ids)].copy()

    print(f"Dataset Partitions by Subject:")
    print(f"  * Train:      {len(df_train)} recordings ({len(train_ids)} unique subjects)")
    print(f"  * Validation: {len(df_val)} recordings ({len(val_ids)} unique subjects)")
    print(f"  * Test:       {len(df_test)} recordings ({len(test_ids)} unique subjects)")

    # 2. Separate Features and Target
    non_feature_cols = ["subject_id", "recording_id", "source_file", "gender", "hemoglobin_g_dl"]
    feature_cols = [c for c in df_all.columns if c not in non_feature_cols]

    X_train_raw = df_train[feature_cols].to_numpy(dtype=np.float64)
    y_train = df_train["hemoglobin_g_dl"].to_numpy(dtype=np.float64)

    X_val_raw = df_val[feature_cols].to_numpy(dtype=np.float64)
    y_val = df_val["hemoglobin_g_dl"].to_numpy(dtype=np.float64)

    X_test_raw = df_test[feature_cols].to_numpy(dtype=np.float64)
    y_test = df_test["hemoglobin_g_dl"].to_numpy(dtype=np.float64)

    # 3. Fit Scaler ONLY on Training Set
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_val = scaler.transform(X_val_raw)
    X_test = scaler.transform(X_test_raw)

    scaler_path = models_dir / "feature_scaler.joblib"
    joblib.dump(scaler, scaler_path)

    # Save feature names list
    feat_names_path = models_dir / "feature_names.json"
    with open(feat_names_path, "w", encoding="utf-8") as fp:
        json.dump(feature_cols, fp, indent=2)

    # 4. Candidate Models Definition
    candidate_models = {
        "Dummy (Mean Baseline)": DummyRegressor(strategy="mean"),
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=10.0, random_state=seed),
        "Lasso Regression": Lasso(alpha=0.1, random_state=seed),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, max_depth=4, min_samples_leaf=2, random_state=seed),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=seed),
        "Support Vector Regressor (SVR)": SVR(kernel="rbf", C=1.0, epsilon=0.2),
    }

    comparison_results = []
    fitted_models = {}
    val_predictions = {}
    test_predictions = {}

    print("-" * 80)
    print("TRAINING AND VALIDATING CANDIDATE MODELS:")
    print(f"{'Model':<30} | {'Val MAE':<9} | {'Val RMSE':<9} | {'Val R2':<9}")
    print("-" * 65)

    for name, model in candidate_models.items():
        # Fit on Training data only
        model.fit(X_train, y_train)
        fitted_models[name] = model

        # Evaluate on Validation set for model selection
        y_val_pred = model.predict(X_val)
        val_predictions[name] = y_val_pred
        val_metrics = evaluate_predictions(y_val, y_val_pred)

        # Evaluate on Training set for diagnostics
        y_train_pred = model.predict(X_train)
        train_metrics = evaluate_predictions(y_train, y_train_pred)

        comparison_results.append({
            "model_name": name,
            "train_mae": train_metrics["mae"],
            "train_rmse": train_metrics["rmse"],
            "train_r2": train_metrics["r2"],
            "val_mae": val_metrics["mae"],
            "val_rmse": val_metrics["rmse"],
            "val_r2": val_metrics["r2"],
        })

        print(f"{name:<30} | {val_metrics['mae']:<9.4f} | {val_metrics['rmse']:<9.4f} | {val_metrics['r2']:<9.4f}")

    df_comparison = pd.DataFrame(comparison_results)

    # 5. Model Selection based strictly on Validation MAE (excluding Dummy baseline)
    non_dummy_df = df_comparison[df_comparison["model_name"] != "Dummy (Mean Baseline)"]
    best_model_row = non_dummy_df.sort_values(by=["val_mae", "val_rmse"]).iloc[0]
    best_model_name = best_model_row["model_name"]
    best_model = fitted_models[best_model_name]

    print("-" * 80)
    print(f"Selected Best Model (via Validation Tuning): {best_model_name}")
    print(f"  * Validation MAE:  {best_model_row['val_mae']:.4f} g/dL")
    print(f"  * Validation RMSE: {best_model_row['val_rmse']:.4f} g/dL")
    print(f"  * Validation R2:   {best_model_row['val_r2']:.4f}")

    # 6. Final ONE-TIME Evaluation on Test Set
    final_test_metrics = {}
    for name, model in fitted_models.items():
        y_test_pred = model.predict(X_test)
        test_predictions[name] = y_test_pred
        test_metrics = evaluate_predictions(y_test, y_test_pred)
        final_test_metrics[name] = test_metrics

    # Attach test metrics to comparison table
    df_comparison["test_mae"] = [final_test_metrics[m]["mae"] for m in df_comparison["model_name"]]
    df_comparison["test_rmse"] = [final_test_metrics[m]["rmse"] for m in df_comparison["model_name"]]
    df_comparison["test_r2"] = [final_test_metrics[m]["r2"] for m in df_comparison["model_name"]]

    print("-" * 80)
    print("FINAL TEST EVALUATION (HELD-OUT SUBJECTS):")
    print(f"{'Model':<30} | {'Test MAE':<9} | {'Test RMSE':<9} | {'Test R2':<9}")
    print("-" * 65)
    for _, row in df_comparison.iterrows():
        print(f"{row['model_name']:<30} | {row['test_mae']:<9.4f} | {row['test_rmse']:<9.4f} | {row['test_r2']:<9.4f}")

    # 7. Save Best Model and Results
    best_model_path = models_dir / "best_ppg_hb_model.joblib"
    joblib.dump({
        "model_name": best_model_name,
        "model": best_model,
        "feature_cols": feature_cols,
        "scaler": scaler
    }, best_model_path)
    print(f"\nSaved Best Model Artifact to: {best_model_path}")

    # Save comparison table
    comp_csv_path = reports_dir / "model_comparison.csv"
    df_comparison.to_csv(comp_csv_path, index=False)

    comp_json_path = reports_dir / "model_comparison.json"
    with open(comp_json_path, "w", encoding="utf-8") as fp:
        json.dump(df_comparison.to_dict(orient="records"), fp, indent=2)

    # 8. Feature Importance Analysis for Best Model (or Tree Model)
    top_features_list = []
    tree_model = fitted_models.get("Random Forest Regressor", best_model)
    if hasattr(tree_model, "feature_importances_"):
        mdi_importances = tree_model.feature_importances_
        sorted_indices = np.argsort(mdi_importances)[::-1]
        for rank, idx in enumerate(sorted_indices[:15], 1):
            top_features_list.append({
                "rank": rank,
                "feature": feature_cols[idx],
                "importance": float(mdi_importances[idx]),
                "category": "Demographic" if feature_cols[idx] in ["age", "gender_encoded"] else (
                    "Cross-Channel" if any(k in feature_cols[idx] for k in ["red_ir_", "_ac_dc", "ratio_of_ratios"]) else (
                        "FFT" if "fft" in feature_cols[idx] else "Time/Morphology"
                    )
                )
            })

    # Save detailed evaluation report
    report_md_path = reports_dir / "model_evaluation_report.md"
    report_content = generate_evaluation_report(
        df_comparison,
        best_model_name,
        top_features_list,
        df_train,
        df_val,
        df_test
    )
    with open(report_md_path, "w", encoding="utf-8") as fp:
        fp.write(report_content)
    print(f"Saved Evaluation Report to: {report_md_path}")

    # Save test & validation prediction arrays for visualization script
    pred_data_path = reports_dir / "predictions_for_plotting.joblib"
    joblib.dump({
        "y_val": y_val,
        "y_val_pred": val_predictions[best_model_name],
        "y_test": y_test,
        "y_test_pred": test_predictions[best_model_name],
        "best_model_name": best_model_name,
        "df_comparison": df_comparison,
        "top_features": top_features_list
    }, pred_data_path)

    return {
        "best_model_name": best_model_name,
        "val_mae": float(best_model_row["val_mae"]),
        "val_rmse": float(best_model_row["val_rmse"]),
        "val_r2": float(best_model_row["val_r2"]),
        "test_mae": float(final_test_metrics[best_model_name]["mae"]),
        "test_rmse": float(final_test_metrics[best_model_name]["rmse"]),
        "test_r2": float(final_test_metrics[best_model_name]["r2"]),
        "dummy_test_mae": float(final_test_metrics["Dummy (Mean Baseline)"]["mae"]),
        "top_features": top_features_list[:10]
    }


def generate_evaluation_report(
    df_comparison: pd.DataFrame,
    best_model_name: str,
    top_features: List[Dict[str, Any]],
    df_train: pd.DataFrame,
    df_val: pd.DataFrame,
    df_test: pd.DataFrame
) -> str:
    """Generate Markdown Model Evaluation Report."""
    best_row = df_comparison[df_comparison["model_name"] == best_model_name].iloc[0]
    dummy_row = df_comparison[df_comparison["model_name"] == "Dummy (Mean Baseline)"].iloc[0]

    lines = [
        "# Model Evaluation & Benchmark Report — PRAHARI PPG Pipeline (Step 3)",
        "",
        "## 1. Dataset & Subject-Level Partition Overview",
        f"- **Total Subjects**: 68",
        f"- **Train Subjects (47)**: Hb Mean = {df_train['hemoglobin_g_dl'].mean():.2f} ± {df_train['hemoglobin_g_dl'].std():.2f} g/dL (Range: {df_train['hemoglobin_g_dl'].min():.1f} - {df_train['hemoglobin_g_dl'].max():.1f})",
        f"- **Validation Subjects (10)**: Hb Mean = {df_val['hemoglobin_g_dl'].mean():.2f} ± {df_val['hemoglobin_g_dl'].std():.2f} g/dL (Range: {df_val['hemoglobin_g_dl'].min():.1f} - {df_val['hemoglobin_g_dl'].max():.1f})",
        f"- **Test Subjects (11)**: Hb Mean = {df_test['hemoglobin_g_dl'].mean():.2f} ± {df_test['hemoglobin_g_dl'].std():.2f} g/dL (Range: {df_test['hemoglobin_g_dl'].min():.1f} - {df_test['hemoglobin_g_dl'].max():.1f})",
        "- **Subject Leakage Check**: Zero subject overlap verified across partitions.",
        "",
        "---",
        "",
        "## 2. Model Comparison Table",
        "| Model | Val MAE (g/dL) | Val RMSE (g/dL) | Val R² | Test MAE (g/dL) | Test RMSE (g/dL) | Test R² |",
        "|---|---|---|---|---|---|---|"
    ]

    for _, r in df_comparison.iterrows():
        prefix = "**" if r["model_name"] == best_model_name else ""
        suffix = "** (Selected)" if r["model_name"] == best_model_name else ""
        lines.append(
            f"| {prefix}{r['model_name']}{suffix} | {r['val_mae']:.4f} | {r['val_rmse']:.4f} | {r['val_r2']:.4f} | {r['test_mae']:.4f} | {r['test_rmse']:.4f} | {r['test_r2']:.4f} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Best Model Performance & Baseline Comparison",
        f"- **Selected Model**: `{best_model_name}`",
        f"- **Validation MAE**: `{best_row['val_mae']:.4f} g/dL` (vs Dummy: `{dummy_row['val_mae']:.4f} g/dL`)",
        f"- **Final Test MAE**: `{best_row['test_mae']:.4f} g/dL` (vs Dummy: `{dummy_row['test_mae']:.4f} g/dL`)",
        f"- **Final Test RMSE**: `{best_row['test_rmse']:.4f} g/dL` (vs Dummy: `{dummy_row['test_rmse']:.4f} g/dL`)",
        f"- **Final Test R²**: `{best_row['test_r2']:.4f}` (vs Dummy: `{dummy_row['test_r2']:.4f}`)",
        "",
        "---",
        "",
        "## 4. Top 10 Influential Features",
        "| Rank | Feature Name | Category | Gini / MDI Importance |",
        "|---|---|---|---|"
    ])

    for f in top_features[:10]:
        lines.append(f"| {f['rank']} | `{f['feature']}` | {f['category']} | {f['importance']:.4f} |")

    lines.extend([
        "",
        "> [!IMPORTANT]",
        "> **Interpretability Notice**: Feature importances reflect tree split frequency and variance reduction within this dataset. They do not denote clinical causality.",
        "",
        "---",
        "",
        "## 5. Prototype Limitations & Context",
        "1. **Cohort Size**: The current dataset contains 68 unique subjects. While valid for prototyping and establishing an end-to-end pipeline, clinical generalization requires expanded multi-center data collection.",
        "2. **Sensor Hardware**: Calibration against gold-standard laboratory spectrophotometry (e.g. Sysmex / HemoCue) across diverse skin tones and perfusion indices will be required during clinical hardware trials.",
        "3. **Multi-Modal Role**: In the full PRAHARI system, this PPG model output acts as an optical hemodynamic feature vector for multimodal fusion with conjunctival imaging."
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate regression models on PPG features.")
    parser.add_argument(
        "--features-path",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "processed", "ppg_features.csv"),
        help="Path to ppg_features.csv"
    )
    parser.add_argument(
        "--metadata-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "metadata"),
        help="Path to metadata directory with train/val/test split CSVs"
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "models"),
        help="Path to output models directory"
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "reports"),
        help="Path to output reports directory"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    feat_path = Path(args.features_path)
    meta_dir = Path(args.metadata_dir)
    models_dir = Path(args.models_dir)
    reports_dir = Path(args.reports_dir)

    if not feat_path.exists():
        print(f"ERROR: Features file not found: {feat_path}. Run extract_features.py first.", file=sys.stderr)
        return 1

    print("=" * 80)
    print("PRAHARI PPG PIPELINE -- MODEL TRAINING & EVALUATION (STEP 3G - 3M)")
    print("=" * 80)

    summary = train_and_evaluate_all_models(
        feat_path,
        meta_dir,
        models_dir,
        reports_dir,
        seed=args.seed
    )

    print("=" * 80)
    print("SUMMARY RESULTS:")
    print(f"  * Best Model:        {summary['best_model_name']}")
    print(f"  * Validation MAE:    {summary['val_mae']:.4f} g/dL")
    print(f"  * Final Test MAE:    {summary['test_mae']:.4f} g/dL (Baseline: {summary['dummy_test_mae']:.4f} g/dL)")
    print(f"  * Final Test RMSE:   {summary['test_rmse']:.4f} g/dL")
    print(f"  * Final Test R2:     {summary['test_r2']:.4f}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
