#!/usr/bin/env python
"""End-to-end inference CLI for the PRAHARI screening engine.

Usage:
    python scripts/test_inference.py <image_path>        # analyze one image
    python scripts/test_inference.py --samples           # self-test: good/poor/invalid

Examples:
    python scripts/test_inference.py data/raw/cp-anemic/Anemic/Image_001.png
    python scripts/test_inference.py --samples
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_result(result: dict) -> None:
    print(json.dumps(result, indent=2, default=str))


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--") or a == "--samples"]
    if "--samples" in sys.argv[1:]:
        return self_test()
    if len(args) != 1:
        print(__doc__)
        return 2
    return analyze_one(args[0])


def analyze_one(image: str) -> int:
    from app.ai.inference import AnemiaInferenceEngine

    engine = AnemiaInferenceEngine()
    engine.load()
    try:
        result = engine.analyze(image)
    except Exception as exc:  # noqa: BLE001 - CLI should always print something
        print(json.dumps({"success": False, "error": {"code": getattr(exc, "code", "INFERENCE_FAILED"), "message": str(exc)}}, indent=2))
        return 1
    print_result(result)
    return 0 if result.get("success") else 1


def self_test() -> int:
    """Run the three required cases: good / poor-quality / invalid image."""
    import cv2

    from app.ai.inference import AnemiaInferenceEngine

    print("=" * 60)
    print("PRAHARI inference self-test (Random Forest)")
    print("=" * 60)
    engine = AnemiaInferenceEngine()
    engine.load()
    failures = 0

    # 1. known good sample (real conjunctiva crop from the dataset)
    good = next((PROJECT_ROOT / "data/raw/cp-anemic/Anemic").glob("Image_*.png"))
    r = engine.analyze(good)
    ok = r["success"] and r["prediction"]["label"] in ("anemic", "non_anemic")
    print(f"\n[1] GOOD sample  {good.name}")
    print(f"    success={r['success']} prediction={r['prediction']} quality={r['image_quality']['status']}")
    failures += 0 if ok else 1

    # 2. poor-quality image (real crop, heavily blurred — test artifact only)
    import tempfile

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    img = cv2.imread(str(good), cv2.IMREAD_UNCHANGED)
    cv2.imwrite(tmp.name, cv2.GaussianBlur(img, (41, 41), 0))
    r = engine.analyze(tmp.name)
    ok = (not r["success"]) and r["error"]["code"] == "IMAGE_QUALITY_LOW"
    print(f"\n[2] POOR sample (blurred {good.name})")
    print(f"    success={r['success']} quality={r['image_quality']['status']} reasons={r['image_quality']['reasons']}")
    failures += 0 if ok else 1
    Path(tmp.name).unlink(missing_ok=True)

    # 3. invalid image (not an image at all)
    bad = PROJECT_ROOT / "data/samples/invalid_test.txt"
    bad.write_text("this is not an image")
    try:
        engine.analyze(bad)
        print("\n[3] INVALID sample  -> NOT rejected (BUG)")
        failures += 1
    except Exception as exc:  # noqa: BLE001
        print(f"\n[3] INVALID sample  -> rejected cleanly ({getattr(exc, 'code', type(exc).__name__)})")
    bad.unlink(missing_ok=True)

    print("\n" + ("ALL SELF-TESTS PASSED" if failures == 0 else f"{failures} SELF-TEST FAILURE(S)"))
    return failures


if __name__ == "__main__":
    sys.exit(main())
