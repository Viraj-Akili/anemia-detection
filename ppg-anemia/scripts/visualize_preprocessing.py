"""
scripts/visualize_preprocessing.py

STEP 2G — PREPROCESSING VISUALIZATION
PRAHARI PPG / Hardware ML Pipeline

Generates time-domain and frequency-domain comparison plots for representative
subjects (good-quality, typical, and borderline signals) and saves them under reports/figures/.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ppg.preprocessing import preprocess_ppg


def plot_single_subject_comparison(
    subject_id: int,
    raw_csv_path: Path,
    output_path: Path,
    fs: float = 25.0
) -> None:
    """
    Generate a detailed 4-panel comparison plot for a single subject:
    - Panel 1: Raw Red vs. Filtered & Normalized Red
    - Panel 2: Raw IR vs. Filtered & Normalized IR
    - Panel 3: Red Channel Frequency Spectrum (Raw vs Filtered)
    - Panel 4: IR Channel Frequency Spectrum (Raw vs Filtered)
    """
    df = pd.read_csv(raw_csv_path)
    raw_red = df["Red (a.u)"].to_numpy()
    raw_ir = df["Infra Red (a.u)"].to_numpy()
    gender = str(df["Gender"].iloc[0]) if "Gender" in df.columns else "N/A"
    age = int(df["Age"].iloc[0]) if "Age" in df.columns else -1
    hb = float(df["Hemoglobin (g/dL)"].iloc[0]) if "Hemoglobin (g/dL)" in df.columns else -1.0

    clean_red, clean_ir, quality = preprocess_ppg(raw_red, raw_ir, fs=fs)

    n_samples = len(clean_red)
    time_sec = np.arange(n_samples) / fs

    # Frequency analysis
    freqs = np.fft.rfftfreq(n_samples, d=1.0 / fs)
    raw_red_fft = np.abs(np.fft.rfft(raw_red - np.mean(raw_red)))
    filt_red_fft = np.abs(np.fft.rfft(clean_red))
    raw_ir_fft = np.abs(np.fft.rfft(raw_ir - np.mean(raw_ir)))
    filt_ir_fft = np.abs(np.fft.rfft(clean_ir))

    fig, axes = plt.subplots(2, 2, figsize=(14, 8), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")

    # Colors
    c_raw_red = "#C0392B"
    c_clean_red = "#E74C3C"
    c_raw_ir = "#8E44AD"
    c_clean_ir = "#9B59B6"

    # Panel 1: Red Time Domain
    ax1 = axes[0, 0]
    ax1.set_facecolor("#FFFFFF")
    ax1.plot(time_sec, clean_red, color=c_clean_red, lw=1.8, label="Clean Normalized Red")
    ax1.set_title(f"Red Channel — Filtered & Normalized (Subject {subject_id})", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Time (seconds)", fontsize=9)
    ax1.set_ylabel("Amplitude (Z-Score)", fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", fontsize=8)

    # Panel 2: IR Time Domain
    ax2 = axes[0, 1]
    ax2.set_facecolor("#FFFFFF")
    ax2.plot(time_sec, clean_ir, color=c_clean_ir, lw=1.8, label="Clean Normalized IR")
    ax2.set_title(f"Infrared Channel — Filtered & Normalized (Subject {subject_id})", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Time (seconds)", fontsize=9)
    ax2.set_ylabel("Amplitude (Z-Score)", fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=8)

    # Panel 3: Red Frequency Domain
    ax3 = axes[1, 0]
    ax3.set_facecolor("#FFFFFF")
    ax3.plot(freqs, raw_red_fft / (np.max(raw_red_fft) + 1e-6), color="#95A5A6", lw=1.2, label="Raw Red Spectrum", linestyle=":")
    ax3.plot(freqs, filt_red_fft / (np.max(filt_red_fft) + 1e-6), color=c_clean_red, lw=1.8, label="Filtered Red Spectrum")
    ax3.axvspan(0.5, 5.0, color="#2ECC71", alpha=0.15, label="Passband (0.5 - 5.0 Hz)")
    ax3.set_title(f"Red Spectrum (Cardiac SQI: {quality['metrics']['red_cardiac_sqi']:.2f})", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Frequency (Hz)", fontsize=9)
    ax3.set_ylabel("Normalized Magnitude", fontsize=9)
    ax3.set_xlim(0, fs / 2)
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(loc="upper right", fontsize=8)

    # Panel 4: IR Frequency Domain
    ax4 = axes[1, 1]
    ax4.set_facecolor("#FFFFFF")
    ax4.plot(freqs, raw_ir_fft / (np.max(raw_ir_fft) + 1e-6), color="#95A5A6", lw=1.2, label="Raw IR Spectrum", linestyle=":")
    ax4.plot(freqs, filt_ir_fft / (np.max(filt_ir_fft) + 1e-6), color=c_clean_ir, lw=1.8, label="Filtered IR Spectrum")
    ax4.axvspan(0.5, 5.0, color="#2ECC71", alpha=0.15, label="Passband (0.5 - 5.0 Hz)")
    ax4.set_title(f"IR Spectrum (Cardiac SQI: {quality['metrics']['ir_cardiac_sqi']:.2f})", fontsize=11, fontweight="bold")
    ax4.set_xlabel("Frequency (Hz)", fontsize=9)
    ax4.set_ylabel("Normalized Magnitude", fontsize=9)
    ax4.set_xlim(0, fs / 2)
    ax4.grid(True, linestyle="--", alpha=0.5)
    ax4.legend(loc="upper right", fontsize=8)

    status_color = "#27AE60" if quality["status"] == "GOOD" else ("#F39C12" if quality["status"] == "WARNING" else "#E74C3C")
    fig.suptitle(
        f"PRAHARI PPG Preprocessing — Subject {subject_id} ({gender}, Age {age}, Hb: {hb:.1f} g/dL)\n"
        f"Quality: [{quality['status']}] | Samples: {n_samples} | Red-IR Corr: {quality['metrics']['red_ir_cross_correlation']:.2f}",
        fontsize=13,
        fontweight="bold",
        color=status_color
    )
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_multi_subject_grid(
    subject_ids: List[int],
    raw_dir: Path,
    output_path: Path,
    fs: float = 25.0
) -> None:
    """
    Generate a consolidated multi-subject comparison grid highlighting signal morphologies.
    """
    n_subs = len(subject_ids)
    fig, axes = plt.subplots(n_subs, 2, figsize=(14, 3.0 * n_subs), dpi=150, sharex=True)
    fig.patch.set_facecolor("#FAFAFA")

    for i, s_id in enumerate(subject_ids):
        csv_path = raw_dir / f"{s_id}.csv"
        if not csv_path.exists():
            continue
        df = pd.read_csv(csv_path)
        clean_red, clean_ir, quality = preprocess_ppg(df["Red (a.u)"], df["Infra Red (a.u)"], fs=fs)
        time_sec = np.arange(len(clean_red)) / fs

        gender = df["Gender"].iloc[0] if "Gender" in df.columns else ""
        hb = df["Hemoglobin (g/dL)"].iloc[0] if "Hemoglobin (g/dL)" in df.columns else 0.0

        # Red axis
        ax_red = axes[i, 0]
        ax_red.set_facecolor("#FFFFFF")
        ax_red.plot(time_sec, clean_red, color="#E74C3C", lw=1.5)
        ax_red.set_ylabel(f"Sub {s_id}\nRed (Z)", fontsize=9, fontweight="bold")
        ax_red.grid(True, linestyle="--", alpha=0.4)
        if i == 0:
            ax_red.set_title("Clean Red Channel (0.5 - 5.0 Hz Bandpass)", fontsize=11, fontweight="bold")

        # IR axis
        ax_ir = axes[i, 1]
        ax_ir.set_facecolor("#FFFFFF")
        ax_ir.plot(time_sec, clean_ir, color="#8E44AD", lw=1.5)
        ax_ir.set_ylabel(f"Sub {s_id}\nIR (Z)", fontsize=9, fontweight="bold")
        ax_ir.grid(True, linestyle="--", alpha=0.4)
        if i == 0:
            ax_ir.set_title(f"Clean Infrared Channel [{quality['status']}]", fontsize=11, fontweight="bold")
        else:
            ax_ir.set_title(f"Subject {s_id} ({gender}, Hb: {hb:.1f} g/dL, Status: {quality['status']})", fontsize=9)

    axes[-1, 0].set_xlabel("Time (seconds)", fontsize=10)
    axes[-1, 1].set_xlabel("Time (seconds)", fontsize=10)

    fig.suptitle("PRAHARI PPG Preprocessing — Representative Subjects Comparison", fontsize=13, fontweight="bold")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate PPG preprocessing comparison plots.")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "data", "raw"),
        help="Path to raw data directory"
    )
    parser.add_argument(
        "--figures-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "reports", "figures"),
        help="Path to output figures directory"
    )
    parser.add_argument(
        "--fs",
        type=float,
        default=25.0,
        help="Verified sampling rate in Hz (default: 25.0)"
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    figures_dir = Path(args.figures_dir)

    if not raw_dir.exists():
        print(f"ERROR: Raw data directory not found: {raw_dir}", file=sys.stderr)
        return 1

    figures_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("PRAHARI PPG PIPELINE -- GENERATING PREPROCESSING VISUALIZATIONS (STEP 2G)")
    print("=" * 80)

    # 1. Generate individual plots for representative subjects
    representative_subs = [1, 2, 4, 8]
    for s_id in representative_subs:
        csv_file = raw_dir / f"{s_id}.csv"
        if csv_file.exists():
            out_img = figures_dir / f"subject_{s_id:02d}_preprocessing.png"
            plot_single_subject_comparison(s_id, csv_file, out_img, fs=args.fs)
            print(f"  [+] Saved Subject {s_id} plot: {out_img}")

    # 2. Generate multi-subject summary grid
    grid_img = figures_dir / "ppg_preprocessing_comparison.png"
    plot_multi_subject_grid(representative_subs, raw_dir, grid_img, fs=args.fs)
    print(f"  [+] Saved multi-subject comparison grid: {grid_img}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
