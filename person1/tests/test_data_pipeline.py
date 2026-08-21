"""Tests for the data pipeline (Hour 2).

Run with:  pytest tests/test_data_pipeline.py
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from app.ai.preprocessing import normalize, preprocess_image
from app.data_pipeline import (
    build_group_table,
    check_no_leakage,
    label_to_id,
    normalize_label,
    split_groups,
    validate_dataset,
)


# ---------------------------------------------------------------------------
# Fixtures: tiny synthetic dataset
# ---------------------------------------------------------------------------
@pytest.fixture()
def tiny_raw(tmp_path: Path):
    """A miniature CP-AnemiC-like tree: two classes, one metadata sheet."""
    for cls in ("Anemic", "Non-anemic"):
        (tmp_path / cls).mkdir()

    def make_image(path: Path, color: tuple[int, int, int], size=(64, 24)):
        img = Image.new("RGBA", size, (*color, 255))
        img.save(path)

    make_image(tmp_path / "Anemic" / "Image_001.png", (200, 90, 90))
    make_image(tmp_path / "Anemic" / "Image_002.png", (210, 80, 80))
    make_image(tmp_path / "Non-anemic" / "Image_003.png", (240, 200, 200))

    sheet = pd.DataFrame(
        [
            {"IMAGE_ID": "Image_001", "HB_LEVEL": 9.8, "Severity": "Moderate", "Age(Months)": 6,
             "GENDER": "Female", "REMARK": "Anemic", "HOSPITAL": "A", "REGION": "R1"},
            {"IMAGE_ID": "Image_002", "HB_LEVEL": 10.5, "Severity": "Mild", "Age(Months)": 12,
             "GENDER": "Male", "REMARK": "Anemic", "HOSPITAL": "B", "REGION": "R2"},
            {"IMAGE_ID": "Image_003", "HB_LEVEL": 12.0, "Severity": "Non-Anemic", "Age(Months)": 24,
             "GENDER": "Female", "REMARK": "Non-anemic", "HOSPITAL": "A", "REGION": "R1"},
        ]
    )
    sheet.to_excel(tmp_path / "Anemia_Data_Collection_Sheet.xlsx", index=False)
    return tmp_path


@pytest.fixture()
def corrupt_raw(tmp_path: Path):
    (tmp_path / "Anemic").mkdir()
    bad = tmp_path / "Anemic" / "Image_999.png"
    bad.write_bytes(b"this is not an image")
    sheet = pd.DataFrame(
        [{"IMAGE_ID": "Image_999", "HB_LEVEL": 9.0, "Severity": "Moderate", "Age(Months)": 8,
          "GENDER": "Female", "REMARK": "Anemic", "HOSPITAL": "A", "REGION": "R1"}]
    )
    sheet.to_excel(tmp_path / "Anemia_Data_Collection_Sheet.xlsx", index=False)
    return tmp_path


# ---------------------------------------------------------------------------
# 1. Label mapping
# ---------------------------------------------------------------------------
def test_label_mapping_known_labels():
    assert normalize_label("Anemic") == "anemic"
    assert normalize_label("Non-anemic") == "non_anemic"
    assert label_to_id("anemic") == 1
    assert label_to_id("non_anemic") == 0


def test_label_mapping_unknown_label_raises():
    with pytest.raises(ValueError):
        normalize_label("Severe anemia")


def test_label_mapping_none_raises():
    with pytest.raises(ValueError):
        normalize_label(None)


# ---------------------------------------------------------------------------
# 2. Preprocessing: shape / dtype
# ---------------------------------------------------------------------------
def test_preprocess_shape_and_dtype(tiny_raw):
    arr = preprocess_image(tiny_raw / "Anemic" / "Image_001.png", size=224)
    assert arr.shape == (224, 224, 3)
    assert arr.dtype == np.uint8


def test_preprocess_is_rgb_and_white_padded(tiny_raw):
    # A narrow crop on a white canvas: corner pixels should be white (pad).
    arr = preprocess_image(tiny_raw / "Anemic" / "Image_001.png", size=64)
    assert arr.shape == (64, 64, 3)
    assert arr[0, 0].tolist() == [255, 255, 255]
    # Center should contain the reddish crop, not pure white.
    assert arr[32, 32, 0] > arr[32, 32, 2]


# ---------------------------------------------------------------------------
# 3. Normalization
# ---------------------------------------------------------------------------
def test_normalize_range_and_shape():
    img = np.full((8, 8, 3), 128, dtype=np.uint8)
    out = normalize(img)
    assert out.shape == (8, 8, 3)
    assert out.dtype == np.float32
    expected = (128 / 255.0 - 0.485) / 0.229
    assert np.allclose(out[0, 0, 0], expected, atol=1e-5)


def test_normalize_rejects_wrong_dtype():
    with pytest.raises(ValueError):
        normalize(np.zeros((4, 4, 3), dtype=np.float32))


# ---------------------------------------------------------------------------
# 4. Validation: corrupt image handling
# ---------------------------------------------------------------------------
def test_validation_flags_corrupt(corrupt_raw):
    records, _ = validate_dataset(corrupt_raw)
    rec = records[0]
    assert rec.status == "corrupt"
    assert any("unopenable" in r for r in rec.reasons)


def test_validation_marks_ok(tiny_raw):
    records, _ = validate_dataset(tiny_raw)
    assert all(r.status == "ok" for r in records)
    assert len(records) == 3


# ---------------------------------------------------------------------------
# 5. Split reproducibility + leakage
# ---------------------------------------------------------------------------
def _make_groups(n=60, n_hospitals=4):
    rng = np.random.default_rng(0)
    rows = []
    for i in range(n):
        label = "anemic" if i % 2 == 0 else "non_anemic"
        rows.append(
            {
                "content_group": f"g{i:03d}",
                "label": label,
                "hospital": f"H{i % n_hospitals}",
                "n_members": 1,
                "hospital_mixed": False,
                "image_ids": f"Image_{i:03d}",
            }
        )
    return pd.DataFrame(rows)


def test_split_reproducible_with_seed():
    groups = _make_groups()
    s1 = split_groups(groups, seed=42)
    s2 = split_groups(groups, seed=42)
    pd.testing.assert_frame_equal(s1[["content_group", "split"]], s2[["content_group", "split"]])


def test_split_differs_with_different_seed():
    groups = _make_groups()
    s1 = split_groups(groups, seed=42)
    s2 = split_groups(groups, seed=7)
    assert not s1["split"].equals(s2["split"])


def test_split_has_all_splits_and_no_leakage():
    groups = _make_groups()
    split = split_groups(groups, seed=42)
    check_no_leakage(split)
    assert set(split["split"].unique()) == {"train", "val", "test"}


def test_split_duplicates_stay_together():
    # Two images with identical content must never be in different splits.
    groups = _make_groups(n=20)
    dup = groups.iloc[[0]].copy()
    dup["content_group"] = "dup_group"
    dup["n_members"] = 2
    dup["image_ids"] = "Image_000,Image_100"
    groups = pd.concat([groups, dup], ignore_index=True)

    split = split_groups(groups, seed=42)
    rows = split[split.content_group == "dup_group"]
    assert len(rows) == 1  # one group -> one split
    assert rows.iloc[0]["n_members"] == 2


def test_build_group_table_groups_duplicates(tiny_raw):
    # Give two images identical bytes -> same content group.
    src = tiny_raw / "Anemic" / "Image_001.png"
    dup = tiny_raw / "Anemic" / "Image_002.png"
    dup.write_bytes(src.read_bytes())
    records, meta = validate_dataset(tiny_raw)
    groups = build_group_table(records, meta)
    dup_rows = groups[groups["n_members"] == 2]
    assert len(dup_rows) == 1
    assert set(dup_rows.iloc[0]["image_ids"].split(",")) == {"Image_001", "Image_002"}


# ---------------------------------------------------------------------------
# 6. Unknown-label handling
# ---------------------------------------------------------------------------
def test_unknown_label_rejected(tiny_raw):
    sheet = pd.read_excel(tiny_raw / "Anemia_Data_Collection_Sheet.xlsx")
    sheet.loc[0, "REMARK"] = "Anemic, severe"
    sheet.to_excel(tiny_raw / "Anemia_Data_Collection_Sheet.xlsx", index=False)
    records, _ = validate_dataset(tiny_raw)
    statuses = {r.image_id: r.status for r in records}
    assert statuses["Image_001"] == "unknown_label"


def test_label_conflict_detected(tiny_raw):
    # Same content, contradictory labels -> label_conflict for both.
    src = tiny_raw / "Anemic" / "Image_001.png"
    dst = tiny_raw / "Non-anemic" / "Image_003.png"
    dst.write_bytes(src.read_bytes())
    records, _ = validate_dataset(tiny_raw)
    conflicts = [r for r in records if r.status == "label_conflict"]
    assert {r.image_id for r in conflicts} == {"Image_001", "Image_003"}
