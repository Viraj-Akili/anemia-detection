#!/usr/bin/env python
"""Benchmark the production inference engine over the held-out test split.

Reports decode/quality/features/predict/total latency, plus how many
images were successfully screened vs rejected by the quality gate.

Usage:
    python scripts/benchmark_inference.py [--n 113] [--out data/results/inference_benchmark.json]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ai.inference import AnemiaInferenceEngine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the inference engine on the test split.")
    parser.add_argument("--n", type=int, default=113, help="number of test images to run")
    parser.add_argument("--out", default=str(PROJECT_ROOT / "data/results/inference_benchmark.json"))
    parser.add_argument("--ai-model", default=None, help="random_forest (default) or cnn")
    args = parser.parse_args()

    manifest = pd.read_csv(PROJECT_ROOT / "data/manifest.csv")
    test = manifest[manifest.split == "test"].head(args.n)
    paths = [Path(p) for p in test["raw_path"].tolist()]

    engine = AnemiaInferenceEngine(ai_model=args.ai_model)
    t_load = time.perf_counter()
    engine.load()
    load_ms = (time.perf_counter() - t_load) * 1000.0

    totals, decodes, quality_ms, features, predicts = [], [], [], [], []
    rejected = {"count": 0, "reasons": []}
    n_ok = 0
    for p in paths:
        t0 = time.perf_counter()
        try:
            result = engine.analyze(p)
        except Exception as exc:  # noqa: BLE001 - count hard failures
            rejected["count"] += 1
            rejected["reasons"].append({"image": p.name, "error": getattr(exc, "code", type(exc).__name__)})
            continue
        totals.append((time.perf_counter() - t0) * 1000.0)
        decodes.append(result["timings_ms"]["decode_ms"])
        quality_ms.append(result["timings_ms"]["quality_ms"])
        features.append(result["timings_ms"]["features_ms"])
        predicts.append(result["timings_ms"]["predict_ms"])
        if result["success"]:
            n_ok += 1
        else:
            rejected["count"] += 1
            rejected["reasons"].append({"image": p.name, "error": result["error"]["code"]})

    def stats(x):
        x = np.array(x)
        return {"mean_ms": float(x.mean()), "median_ms": float(np.median(x)), "p95_ms": float(np.percentile(x, 95))}

    report = {
        "ai_model": engine.metadata["name"],
        "n_images": len(paths),
        "successful": n_ok,
        "rejected": rejected,
        "model_load_ms": round(load_ms, 2),
        "latency": {
            "total": stats(totals) if totals else None,
            "decode": stats(decodes) if decodes else None,
            "quality_gate": stats(quality_ms) if quality_ms else None,
            "features_predict": stats(features) if features else None,
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"model: {engine.metadata['name']}")
    print(f"images: {len(paths)} | successful: {n_ok} | rejected: {rejected['count']}")
    if totals:
        t = report["latency"]["total"]
        print(f"total latency  mean={t['mean_ms']:.1f}ms median={t['median_ms']:.1f}ms p95={t['p95_ms']:.1f}ms")
    print(f"model load: {load_ms:.0f}ms (one-time, excluded from per-image latency)")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
