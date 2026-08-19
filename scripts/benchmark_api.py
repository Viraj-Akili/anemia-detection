#!/usr/bin/env python3
"""HTTP API benchmark for PRAHARI AI/CV backend.

Hits the live FastAPI /api/v1/anemia/screen endpoint over HTTP and measures
client-observed round-trip latency, success rate, and quality rejection rate.

Usage:
    python scripts/benchmark_api.py [--n 50] [--url http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_benchmark(base_url: str, n_samples: int) -> dict:
    manifest_path = PROJECT_ROOT / "data/manifest.csv"
    if not manifest_path.exists():
        print(f"[ERROR] Manifest not found at {manifest_path}")
        return {}

    manifest = pd.read_csv(manifest_path)
    test_split = manifest[manifest["split"] == "test"]
    if len(test_split) == 0:
        test_split = manifest

    samples = test_split.head(n_samples)
    screen_url = f"{base_url.rstrip('/')}/api/v1/anemia/screen"

    print(f"Benchmarking {len(samples)} HTTP requests to {screen_url} ...")

    latencies = []
    success_count = 0
    rejected_count = 0
    error_count = 0

    for idx, (_, row) in enumerate(samples.iterrows(), 1):
        img_path = PROJECT_ROOT / row["image_path"]
        if not img_path.exists():
            continue

        with open(img_path, "rb") as f:
            files = {"image": (img_path.name, f, "image/png")}
            t0 = time.perf_counter()
            try:
                resp = requests.post(screen_url, files=files, timeout=30)
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                latencies.append(elapsed_ms)

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") is True:
                        success_count += 1
                    else:
                        rejected_count += 1
                else:
                    error_count += 1
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                latencies.append(elapsed_ms)
                error_count += 1

        if idx % 10 == 0 or idx == len(samples):
            print(f"  Processed {idx}/{len(samples)} requests...")

    lat_arr = np.array(latencies)
    mean_lat = float(np.mean(lat_arr)) if len(lat_arr) else 0.0
    median_lat = float(np.median(lat_arr)) if len(lat_arr) else 0.0
    p95_lat = float(np.percentile(lat_arr, 95)) if len(lat_arr) else 0.0
    min_lat = float(np.min(lat_arr)) if len(lat_arr) else 0.0
    max_lat = float(np.max(lat_arr)) if len(lat_arr) else 0.0

    summary = {
        "endpoint": screen_url,
        "request_count": len(latencies),
        "successful_requests": success_count,
        "rejected_requests": rejected_count,
        "error_requests": error_count,
        "latency_stats_ms": {
            "mean": round(mean_lat, 2),
            "median": round(median_lat, 2),
            "p95": round(p95_lat, 2),
            "min": round(min_lat, 2),
            "max": round(max_lat, 2),
        },
    }

    out_path = PROJECT_ROOT / "data/results/api_benchmark.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "=" * 50)
    print("API BENCHMARK RESULTS")
    print("=" * 50)
    print(f"Total Requests       : {summary['request_count']}")
    print(f"Successful Requests  : {summary['successful_requests']}")
    print(f"Quality-Rejected     : {summary['rejected_requests']}")
    print(f"HTTP Errors          : {summary['error_requests']}")
    print(f"Mean Latency         : {summary['latency_stats_ms']['mean']} ms")
    print(f"Median Latency       : {summary['latency_stats_ms']['median']} ms")
    print(f"p95 Latency          : {summary['latency_stats_ms']['p95']} ms")
    print(f"Min / Max Latency    : {summary['latency_stats_ms']['min']} ms / {summary['latency_stats_ms']['max']} ms")
    print("=" * 50)
    print(f"Saved benchmark summary to {out_path}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="PRAHARI API Benchmark")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base API URL")
    parser.add_argument("--n", type=int, default=50, help="Number of requests")
    args = parser.parse_args()

    run_benchmark(args.url, args.n)


if __name__ == "__main__":
    main()
