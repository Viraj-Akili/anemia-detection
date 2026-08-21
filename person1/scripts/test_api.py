"""End-to-end API test — hits the running FastAPI server with real samples.

Usage:
    # Terminal 1:
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

    # Terminal 2:
    python scripts/test_api.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests
import pandas as pd

BASE = "http://127.0.0.1:8000"


def _get_test_images() -> dict[str, str]:
    """Pull one anemic and one non-anemic image from the test split."""
    manifest = pd.read_csv("data/manifest.csv")
    test = manifest[manifest["split"] == "test"]
    anemic = test[test["label"] == "anemic"].iloc[0]["image_path"]
    non_anemic = test[test["label"] == "non_anemic"].iloc[0]["image_path"]
    return {"anemic": anemic, "non_anemic": non_anemic}


def _check(name: str, ok: bool, detail: str = "") -> bool:
    icon = "[PASS]" if ok else "[FAIL]"
    suffix = f" — {detail}" if detail else ""
    print(f"  {icon} {name}{suffix}")
    return ok


def main() -> int:
    passed = 0
    failed = 0
    samples = _get_test_images()

    # --- health ---
    print("\n=== GET /health ===")
    r = requests.get(f"{BASE}/health", timeout=5)
    ok = r.status_code == 200 and r.json().get("model_loaded") is True and r.json().get("status") == "ok"
    if _check("200 + status: ok + model_loaded", ok, json.dumps(r.json(), indent=2)[:200]):
        passed += 1
    else:
        failed += 1

    # --- models ---
    print("\n=== GET /models ===")
    r = requests.get(f"{BASE}/models", timeout=5)
    ok = r.status_code == 200 and "random_forest" in r.json().get("name", "")
    if _check("200 + model name", ok, json.dumps(r.json(), indent=2)[:200]):
        passed += 1
    else:
        failed += 1

    # --- valid anemic sample ---
    print("\n=== POST /api/v1/anemia/screen (anemic test sample) ===")
    path = samples["anemic"]
    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/api/v1/anemia/screen",
        files={"image": (Path(path).name, open(path, "rb"), "image/png")},
        timeout=30,
    )
    latency_ms = (time.perf_counter() - t0) * 1000
    body = r.json()
    ok = (
        r.status_code == 200
        and body.get("success") is True
        and "prediction" in body
        and body["prediction"]["label"] in ("anemic", "non_anemic")
        and 0.0 <= body["prediction"]["model_probability"] <= 1.0
        and 0.0 <= body["prediction"]["model_confidence"] <= 1.0
    )
    detail = json.dumps(body, indent=2)[:300]
    if _check("200 + success + valid prediction structure", ok, f"latency={latency_ms:.0f}ms\n{detail}"):
        passed += 1
    else:
        failed += 1

    # --- valid non-anemic sample ---
    print("\n=== POST /api/v1/anemia/screen (non-anemic test sample) ===")
    path = samples["non_anemic"]
    r = requests.post(
        f"{BASE}/api/v1/anemia/screen",
        files={"image": (Path(path).name, open(path, "rb"), "image/png")},
        timeout=30,
    )
    body = r.json()
    ok = (
        r.status_code == 200
        and body.get("success") is True
        and "prediction" in body
        and body["prediction"]["label"] in ("anemic", "non_anemic")
        and 0.0 <= body["prediction"]["model_probability"] <= 1.0
        and 0.0 <= body["prediction"]["model_confidence"] <= 1.0
    )
    if _check("200 + success + valid prediction structure", ok, json.dumps(body, indent=2)[:300]):
        passed += 1
    else:
        failed += 1

    # --- missing image ---
    print("\n=== POST /api/v1/anemia/screen (missing image) ===")
    r = requests.post(f"{BASE}/api/v1/anemia/screen", timeout=5)
    ok = r.status_code == 422
    if _check("422 for missing image", ok):
        passed += 1
    else:
        failed += 1

    # --- bad format ---
    print("\n=== POST /api/v1/anemia/screen (text/plain) ===")
    r = requests.post(
        f"{BASE}/api/v1/anemia/screen",
        files={"image": ("fake.txt", b"not an image", "text/plain")},
        timeout=5,
    )
    ok = r.status_code == 415
    if _check("415 for unsupported format", ok):
        passed += 1
    else:
        failed += 1

    # --- empty file ---
    print("\n=== POST /api/v1/anemia/screen (empty file) ===")
    r = requests.post(
        f"{BASE}/api/v1/anemia/screen",
        files={"image": ("empty.png", b"", "image/png")},
        timeout=5,
    )
    ok = r.status_code == 400
    if _check("400 for empty file", ok):
        passed += 1
    else:
        failed += 1

    # --- poor quality ---
    print("\n=== POST /api/v1/anemia/screen (synthetic dark/blurry) ===")
    from PIL import Image
    import numpy as np
    import tempfile, os
    arr = np.random.randint(0, 15, (50, 50, 3), dtype=np.uint8)
    tmp = os.path.join(tempfile.gettempdir(), "dark_blur.png")
    Image.fromarray(arr).save(tmp)
    r = requests.post(
        f"{BASE}/api/v1/anemia/screen",
        files={"image": ("dark_blur.png", open(tmp, "rb"), "image/png")},
        timeout=30,
    )
    body = r.json()
    ok = (
        r.status_code == 200
        and body.get("success") is False
        and body.get("error", {}).get("code") == "IMAGE_QUALITY_LOW"
    )
    if _check("quality rejected (success=false, code=IMAGE_QUALITY_LOW)", ok, json.dumps(body, indent=2)[:300]):
        passed += 1
    else:
        failed += 1

    # --- no stack trace leakage ---
    print("\n=== Stack trace check ===")
    r = requests.post(
        f"{BASE}/api/v1/anemia/screen",
        files={"image": ("fake.txt", b"not an image", "text/plain")},
        timeout=5,
    )
    text = r.text.lower()
    ok = "traceback" not in text and "exception" not in text
    if _check("No Python traceback in response", ok):
        passed += 1
    else:
        failed += 1

    print(f"\n{'='*40}")
    print(f"  {passed} passed, {failed} failed out of {passed + failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
