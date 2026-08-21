#!/usr/bin/env python3
"""PRAHARI AI/CV — Single-image Anemia Screening Demo Script.

Usage:
    python scripts/demo.py <image_path>
    python scripts/demo.py data/processed/test/anemic/Image_013.png

Prints:
    - image path
    - quality status
    - quality score
    - prediction
    - model probability
    - model confidence
    - model name
    - model version
    - latency
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.ai.inference import AnemiaInferenceEngine
from app.ai.errors import InferenceError


def run_demo(image_path: str) -> int:
    path = Path(image_path)
    if not path.exists():
        print(f"[ERROR] Image path does not exist: {image_path}")
        return 1

    print("=" * 60)
    print("PRAHARI — Anemia Screening AI Demo")
    print("=" * 60)
    print(f"Input image     : {image_path}")

    # Load inference engine
    t_start = time.perf_counter()
    engine = AnemiaInferenceEngine()
    try:
        engine.load()
    except Exception as exc:
        print(f"[ERROR] Failed to load model: {exc}")
        return 1

    # Run analysis
    try:
        result = engine.analyze(str(path))
    except InferenceError as exc:
        print(f"[ERROR] Inference error ({exc.code}): {exc}")
        return 1
    except Exception as exc:
        print(f"[ERROR] Unexpected error: {exc}")
        return 1

    total_latency_ms = (time.perf_counter() - t_start) * 1000.0

    # Extract quality fields
    quality = result.get("image_quality") or {}
    q_status = quality.get("status", "unknown")
    q_score = quality.get("score", 0.0)

    print("-" * 60)
    print("1. Image Quality Assessment")
    print(f"   - Quality Status   : {q_status.upper()}")
    print(f"   - Quality Score    : {q_score:.4f}")
    if q_status == "poor":
        reasons = quality.get("reasons", [])
        print(f"   - Rejection Reasons: {', '.join(reasons) if reasons else 'Low overall quality'}")
        if result.get("error"):
            print(f"   - Error Code       : {result['error'].get('code')}")
            print(f"   - Message          : {result['error'].get('message')}")
        print("-" * 60)
        print("Screening aborted: Image quality insufficient for AI prediction.")
        print("=" * 60)
        return 0

    # Extract prediction fields
    pred = result.get("prediction") or {}
    label = pred.get("label", "n/a")
    probability = pred.get("model_probability", 0.0)
    confidence = pred.get("model_confidence", 0.0)

    # Extract inference metadata
    infer = result.get("inference") or {}
    model_name = infer.get("model", engine.metadata.get("name", "n/a"))
    model_version = infer.get("version", engine.metadata.get("version", "n/a"))
    latency_ms = infer.get("latency_ms", total_latency_ms)

    print("-" * 60)
    print("2. Model Prediction")
    print(f"   - Prediction       : {label.upper()}")
    print(f"   - Model Probability: {probability:.4f} (anemic class probability)")
    print(f"   - Model Confidence : {confidence:.4f}")
    print("-" * 60)
    print("3. Model Metadata & Performance")
    print(f"   - Model Name       : {model_name}")
    print(f"   - Model Version    : {model_version}")
    print(f"   - Latency          : {latency_ms:.2f} ms")
    print("=" * 60)
    print("NOTE: Screening prototype only. Signal to be ingested by Swayam's multimodal risk engine.")
    print("=" * 60)
    return 0


def main():
    parser = argparse.ArgumentParser(description="PRAHARI AI Anemia Screening Demo")
    parser.add_argument("image", type=str, help="Path to input conjunctiva image")
    args = parser.parse_args()
    sys.exit(run_demo(args.image))


if __name__ == "__main__":
    main()
