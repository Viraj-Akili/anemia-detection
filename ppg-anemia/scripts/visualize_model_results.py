"""
scripts/visualize_model_results.py

STEP 3N — MODEL & FEATURE VISUALIZATIONS
PRAHARI PPG / Hardware ML Pipeline

Generates publication-quality diagnostic plots for model performance, residuals,
feature importances, and correlation matrices under reports/figures/.
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def plot_actual_vs_predicted(
    y_val: np.ndarray,
    y_val_pred: np.ndarray,
    y_test: np.ndarray,
    y_test_pred: np.ndarray,
    model_name: str,
    output_path: Path
) -> None:
    """Scatter plot of Actual vs Predicted Hb for Validation and Test sets."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")

    # Min/Max bounds for reference line
    all_vals = np.concatenate([y_val, y_val_pred, y_test, y_test_pred])
    val_min, val_max = float(np.min(all_vals)) - 0.5, float(np.max(all_vals)) + 0.5

    # Panel 1: Validation Set
    ax1 = axes[0]
    ax1.set_facecolor("#FFFFFF")
    ax1.scatter(y_val, y_val_pred, color="#2980B9", s=65, alpha=0.85, edgecolors="#1A5276", label="Validation Subjects")
    ax1.plot([val_min, val_max], [val_min, val_max], color="#E74C3C", linestyle="--", lw=1.5, label="Perfect Fit (y=x)")
    val_mae = float(np.mean(np.abs(y_val - y_val_pred)))
    ax1.set_title(f"Validation Set (N={len(y_val)})\nMAE = {val_mae:.2f} g/dL", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Actual Hemoglobin (g/dL)", fontsize=10)
    ax1.set_ylabel("Predicted Hemoglobin (g/dL)", fontsize=10)
    ax1.set_xlim(val_min, val_max)
    ax1.set_ylim(val_min, val_max)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="upper left", fontsize=9)

    # Panel 2: Test Set
    ax2 = axes[1]
    ax2.set_facecolor("#FFFFFF")
    ax2.scatter(y_test, y_test_pred, color="#27AE60", s=65, alpha=0.85, edgecolors="#196F3D", label="Held-Out Test Subjects")
    ax2.plot([val_min, val_max], [val_min, val_max], color="#E74C3C", linestyle="--", lw=1.5, label="Perfect Fit (y=x)")
    test_mae = float(np.mean(np.abs(y_test - y_test_pred)))
    ax2.set_title(f"Held-Out Test Set (N={len(y_test)})\nMAE = {test_mae:.2f} g/dL", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Actual Hemoglobin (g/dL)", fontsize=10)
    ax2.set_ylabel("Predicted Hemoglobin (g/dL)", fontsize=10)
    ax2.set_xlim(val_min, val_max)
    ax2.set_ylim(val_min, val_max)
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc="upper left", fontsize=9)

    fig.suptitle(f"PRAHARI PPG Model — Actual vs. Predicted Hemoglobin ({model_name})", fontsize=13, fontweight="bold")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_residuals(
    y_test: np.ndarray,
    y_test_pred: np.ndarray,
    model_name: str,
    output_path: Path
) -> None:
    """Plot prediction residuals vs predicted values and error histogram."""
    residuals = y_test - y_test_pred

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.0), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")

    # Residuals vs Predicted
    ax1 = axes[0]
    ax1.set_facecolor("#FFFFFF")
    ax1.scatter(y_test_pred, residuals, color="#8E44AD", s=65, alpha=0.85, edgecolors="#512E5F")
    ax1.axhline(0, color="#E74C3C", linestyle="--", lw=1.5)
    ax1.set_title(f"Residuals vs. Predicted ({model_name})", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Predicted Hemoglobin (g/dL)", fontsize=10)
    ax1.set_ylabel("Residual (Actual - Predicted) [g/dL]", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Residual Distribution Histogram
    ax2 = axes[1]
    ax2.set_facecolor("#FFFFFF")
    ax2.hist(residuals, bins=8, color="#3498DB", edgecolor="#1B4F72", alpha=0.75)
    ax2.axvline(0, color="#E74C3C", linestyle="--", lw=1.5)
    ax2.set_title("Test Error Distribution", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Prediction Error (g/dL)", fontsize=10)
    ax2.set_ylabel("Count", fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.4)

    fig.suptitle("PRAHARI PPG Model — Residual Diagnostics", fontsize=13, fontweight="bold")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_model_comparison(df_comparison: pd.DataFrame, output_path: Path) -> None:
    """Bar chart comparing validation and test MAE across models."""
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FFFFFF")

    models = df_comparison["model_name"].tolist()
    x = np.arange(len(models))
    width = 0.35

    val_maes = df_comparison["val_mae"].tolist()
    test_maes = df_comparison["test_mae"].tolist()

    rects1 = ax.bar(x - width/2, val_maes, width, label="Validation MAE", color="#3498DB", edgecolor="#1B4F72")
    rects2 = ax.bar(x + width/2, test_maes, width, label="Test MAE", color="#2ECC71", edgecolor="#196F3D")

    ax.set_ylabel("Mean Absolute Error (g/dL)", fontsize=10)
    ax.set_title("PRAHARI Model Comparison — Validation vs. Test MAE", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=25, ha="right", fontsize=9)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")

    # Value labels
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.2f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8)
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h:.2f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_feature_importance(top_features: list, output_path: Path) -> None:
    """Horizontal bar plot of top feature importances."""
    if not top_features:
        return

    features = [f["feature"] for f in top_features[:12]][::-1]
    importances = [f["importance"] for f in top_features[:12]][::-1]
    categories = [f["category"] for f in top_features[:12]][::-1]

    category_colors = {
        "Demographic": "#E67E22",
        "Cross-Channel": "#8E44AD",
        "FFT": "#3498DB",
        "Time/Morphology": "#2ECC71"
    }
    colors = [category_colors.get(c, "#95A5A6") for c in categories]

    fig, ax = plt.subplots(figsize=(10, 6.0), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FFFFFF")

    bars = ax.barh(features, importances, color=colors, edgecolor="#2C3E50", height=0.65)
    ax.set_xlabel("Relative Feature Importance (MDI)", fontsize=10)
    ax.set_title("PRAHARI PPG Model — Top 12 Feature Importances", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.4, axis="x")

    # Legend for categories
    handles = [plt.Rectangle((0,0),1,1, color=col, ec="#2C3E50") for cat, col in category_colors.items()]
    ax.legend(handles, category_colors.keys(), loc="lower right", title="Feature Category", fontsize=8)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_feature_correlation_heatmap(features_csv: Path, output_path: Path) -> None:
    """Correlation heatmap of selected key PPG optical & demographic features."""
    df = pd.read_csv(features_csv)

    selected_cols = [
        "hemoglobin_g_dl",
        "age",
        "gender_encoded",
        "ratio_of_ratios",
        "red_ir_pearson_corr",
        "red_ac_dc_ratio",
        "ir_ac_dc_ratio",
        "red_fft_dominant_freq_hz",
        "ir_fft_dominant_freq_hz",
        "red_pulse_rate_bpm",
        "red_raw_dc",
        "ir_raw_dc"
    ]
    present_cols = [c for c in selected_cols if c in df.columns]
    corr = df[present_cols].corr()

    fig, ax = plt.subplots(figsize=(10, 8.5), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")

    cax = ax.matshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(present_cols)))
    ax.set_yticks(range(len(present_cols)))
    ax.set_xticklabels(present_cols, rotation=45, ha="left", fontsize=8)
    ax.set_yticklabels(present_cols, fontsize=8)

    # Annotate numbers
    for i in range(len(present_cols)):
        for j in range(len(present_cols)):
            val = corr.iloc[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="black" if abs(val) < 0.6 else "white", fontsize=7)

    ax.set_title("PRAHARI Key Features Correlation Heatmap", fontsize=12, fontweight="bold", pad=20)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate model diagnostic and feature plots.")
    parser.add_argument(
        "--features-path",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "processed", "ppg_features.csv"),
        help="Path to ppg_features.csv"
    )
    parser.add_argument(
        "--pred-data-path",
        type=str,
        default=os.path.join(PROJECT_ROOT, "reports", "predictions_for_plotting.joblib"),
        help="Path to predictions_for_plotting.joblib"
    )
    parser.add_argument(
        "--figures-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "reports", "figures"),
        help="Path to figures output directory"
    )
    args = parser.parse_args()

    feat_path = Path(args.features_path)
    pred_path = Path(args.pred_data_path)
    figures_dir = Path(args.figures_dir)

    if not pred_path.exists():
        print(f"ERROR: Prediction data file not found: {pred_path}. Run train_evaluate_models.py first.", file=sys.stderr)
        return 1

    figures_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("PRAHARI PPG PIPELINE -- GENERATING MODEL & FEATURE PLOTS (STEP 3N)")
    print("=" * 80)

    pred_data = joblib.load(pred_path)
    y_val = pred_data["y_val"]
    y_val_pred = pred_data["y_val_pred"]
    y_test = pred_data["y_test"]
    y_test_pred = pred_data["y_test_pred"]
    best_model_name = pred_data["best_model_name"]
    df_comparison = pred_data["df_comparison"]
    top_features = pred_data["top_features"]

    # 1. Actual vs Predicted Plot
    out_avp = figures_dir / "hb_actual_vs_predicted.png"
    plot_actual_vs_predicted(y_val, y_val_pred, y_test, y_test_pred, best_model_name, out_avp)
    print(f"  [+] Saved Actual vs Predicted plot: {out_avp}")

    # 2. Residuals Plot
    out_res = figures_dir / "hb_residuals.png"
    plot_residuals(y_test, y_test_pred, best_model_name, out_res)
    print(f"  [+] Saved Residuals plot: {out_res}")

    # 3. Model Comparison Bar Chart
    out_comp = figures_dir / "model_comparison.png"
    plot_model_comparison(df_comparison, out_comp)
    print(f"  [+] Saved Model Comparison plot: {out_comp}")

    # 4. Feature Importance Bar Chart
    out_imp = figures_dir / "feature_importance.png"
    plot_feature_importance(top_features, out_imp)
    print(f"  [+] Saved Feature Importance plot: {out_imp}")

    # 5. Correlation Heatmap
    if feat_path.exists():
        out_hm = figures_dir / "feature_correlation_heatmap.png"
        plot_feature_correlation_heatmap(feat_path, out_hm)
        print(f"  [+] Saved Correlation Heatmap: {out_hm}")

    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
