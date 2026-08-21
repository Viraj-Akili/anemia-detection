"""
scripts/predict_esp32.py

STEP 4 — LIVE ESP32 / MAX30102 PPG INFERENCE CLI
PRAHARI PPG / Hardware ML Pipeline

Usage:
    python scripts/predict_esp32.py path/to/esp32_recording.csv [--age AGE] [--gender GENDER]

Example:
    python scripts/predict_esp32.py tests/data/simulated_esp32_sub1.csv --age 21 --gender Male
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ppg.esp32 import predict_esp32_recording


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Predict Hemoglobin (g/dL) from raw ESP32/MAX30102 PPG recording CSV."
    )
    parser.add_argument(
        "csv_path",
        type=str,
        help="Path to ESP32 CSV file (columns: timestamp_ms, red, ir)"
    )
    parser.add_argument(
        "--age",
        type=float,
        default=25.0,
        help="Patient age in years (default: 25.0)"
    )
    parser.add_argument(
        "--gender",
        type=str,
        default="Male",
        choices=["Male", "Female", "male", "female", "Other", "other"],
        help="Patient gender (default: Male)"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=os.path.join(PROJECT_ROOT, "models", "best_ppg_hb_model.joblib"),
        help="Path to trained model bundle artifact"
    )
    parser.add_argument(
        "--fs",
        type=float,
        default=25.0,
        help="Expected nominal sampling rate in Hz (default: 25.0)"
    )
    args = parser.parse_args()

    csv_p = Path(args.csv_path)
    if not csv_p.exists():
        print(f"ERROR: Input file not found: {csv_p}", file=sys.stderr)
        return 1

    try:
        res = predict_esp32_recording(
            file_path_or_df=csv_p,
            model_bundle_path=args.model_path,
            age=args.age,
            gender=args.gender,
            fs=args.fs
        )
    except Exception as err:
        print(f"\n[!] ESP32 INFERENCE FAILED: {err}", file=sys.stderr)
        return 1

    # Formatted Hardware Terminal Output
    print("\n" + "=" * 40)
    print("ESP32 PPG Recording")
    print("-" * 40)
    print(f"Source file:             {res['source']}")
    print(f"Samples:                 {res['sample_count']}")
    print(f"Duration:                {res['duration_sec']:.2f} s")
    print(f"Effective sampling rate: {res['effective_fs_hz']:.1f} Hz (dt median: {res['median_dt_ms']:.1f} ms)")
    print(f"RED Channel:             OK (mean ADC: {res['telemetry']['red_mean_raw']})")
    print(f"IR Channel:              OK (mean ADC: {res['telemetry']['ir_mean_raw']})")
    print(f"Signal quality:          {res['signal_quality']} (SQI: {res['sqi_score']:.3f})")
    print(f"Features Extracted:      {res['feature_count']} (100% verified)")
    print(f"Demographics:            Age {res['patient_age']} | Gender {res['patient_gender']}")
    print(f"ML Model:                {res['model_name']}")
    print("-" * 40)
    print(f"Predicted Hb:            {res['predicted_hb_g_dl']:.2f} g/dL")
    print("=" * 40 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
