"""Dataset pipeline for the PRAHARI anemia model.

Implements the reproducible raw -> validate -> clean -> split flow used by
scripts/validate_dataset.py and scripts/prepare_dataset.py. Kept importable
so tests can exercise it without running the CLI scripts.

Dataset facts verified in Hour 2 (CP-AnemiC):
- 710 RGBA PNG ROI crops (palpebral conjunctiva), heterogeneous sizes.
- Metadata sheet: IMAGE_ID (matches filename minus ".png"), HB_LEVEL,
  Severity, Age(Months), GENDER, REMARK (binary label), hospital/region.
- 303 files are byte-identical duplicates (91 content groups); 1 group is
  a cross-class label conflict (Image_310 "anemic" vs Image_188 "non-anemic").
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from PIL import Image

# ---------------------------------------------------------------------------
# Labels (canonical, dataset-defined - no invented classes)
# ---------------------------------------------------------------------------
# Canonical class names are lowercase-underscore versions of the dataset's
# own REMARK values ("Anemic" / "Non-anemic"). "non_anemic" is NOT a
# medically stronger claim; it is the dataset's label, normalized.
LABEL_MAP = {"anemic": 1, "non_anemic": 0}
CLASS_NAMES = ["non_anemic", "anemic"]  # index = label id

# Sheet REMARK -> canonical label name
_REMARK_TO_LABEL = {"anemic": "anemic", "non-anemic": "non_anemic"}


def normalize_label(raw: str) -> str:
    """Normalize a raw label string to a canonical class name.

    Raises ValueError for unknown labels (never silently renames).
    """
    if raw is None:
        raise ValueError("label is None")
    norm = str(raw).strip().lower().replace("_", "-")
    if norm in _REMARK_TO_LABEL:
        return _REMARK_TO_LABEL[norm]
    raise ValueError(f"unknown label: {raw!r}")


def label_to_id(label: str) -> int:
    if label not in LABEL_MAP:
        raise ValueError(f"unknown label: {label!r}")
    return LABEL_MAP[label]


# ---------------------------------------------------------------------------
# Raw dataset layout
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RawLayout:
    root: Path
    sheet_name: str = "Anemia_Data_Collection_Sheet.xlsx"
    class_folders: tuple[str, ...] = ("Anemic", "Non-anemic")

    @property
    def sheet_path(self) -> Path:
        return self.root / self.sheet_name

    def image_paths(self) -> list[Path]:
        out = []
        for folder in self.class_folders:
            d = self.root / folder
            if d.is_dir():
                out.extend(sorted(p for p in d.glob("*.png") if p.is_file()))
        return sorted(out)


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
@dataclass
class ValidationRecord:
    image_path: str
    image_id: str
    label: str | None
    status: str  # ok | corrupt | missing_label | label_conflict | unknown_label
    reasons: list[str]
    width: int | None = None
    height: int | None = None
    channels: int | None = None
    size_bytes: int | None = None
    md5: str | None = None
    content_group: str | None = None
    brightness: float | None = None
    contrast: float | None = None
    sharpness: float | None = None
    tissue_fraction: float | None = None


def load_metadata(sheet_path: Path) -> pd.DataFrame:
    """Load the CP-AnemiC metadata sheet keyed by IMAGE_ID (no extension)."""
    df = pd.read_excel(sheet_path)
    df["IMAGE_ID"] = df["IMAGE_ID"].astype(str).str.strip()
    df["_file"] = df["IMAGE_ID"] + ".png"
    return df


def validate_dataset(raw_root: Path, min_tissue_fraction: float = 0.10) -> tuple[list[ValidationRecord], pd.DataFrame]:
    """Validate every image and the sheet mapping.

    Returns (records, metadata_df). No data is deleted; rejected samples are
    marked with a status + reasons.
    """
    from app.ai.quality_gate import compute_metrics, tissue_coverage
    from app.ai.preprocessing import load_rgb

    layout = RawLayout(raw_root)
    meta = load_metadata(layout.sheet_path)
    meta_by_file = {r["_file"]: r for _, r in meta.iterrows()}

    records: list[ValidationRecord] = []
    by_group: dict[str, list[ValidationRecord]] = {}

    for path in layout.image_paths():
        name = path.name
        rec = ValidationRecord(
            image_path=str(path),
            image_id=name.removesuffix(".png"),
            label=None,
            status="ok",
            reasons=[],
            size_bytes=path.stat().st_size,
        )

        # 1) label from sheet
        row = meta_by_file.get(name)
        if row is None:
            rec.status = "missing_label"
            rec.reasons.append("no metadata row")
            records.append(rec)
            continue
        try:
            rec.label = normalize_label(row["REMARK"])
        except ValueError:
            rec.status = "unknown_label"
            rec.reasons.append(f"unrecognized REMARK value {row['REMARK']!r}")
            records.append(rec)
            continue

        # 2) image openable / dimensions / channels
        try:
            with Image.open(path) as im:
                im.load()
                rec.width, rec.height = im.size
                rec.channels = len(im.getbands())
        except Exception as exc:  # noqa: BLE001 - any PIL error => corrupt
            rec.status = "corrupt"
            rec.reasons.append(f"unopenable: {exc}")
            records.append(rec)
            continue

        # 3) content hash (leakage grouping)
        rec.md5 = file_md5(path)
        rec.content_group = rec.md5[:16]
        by_group.setdefault(rec.content_group, []).append(rec)

        # 4) quality metrics (best-effort; failures never reject the image)
        try:
            metrics = compute_metrics(load_rgb(path))
            rec.brightness = metrics["brightness"]
            rec.contrast = metrics["contrast"]
            rec.sharpness = metrics["sharpness"]
        except Exception:  # noqa: BLE001
            pass
        try:
            rec.tissue_fraction = tissue_coverage(Image.open(path))
            if rec.tissue_fraction < min_tissue_fraction:
                rec.reasons.append(f"low_tissue_coverage({rec.tissue_fraction:.2f})")
        except Exception:  # noqa: BLE001
            pass

        records.append(rec)

    # 5) label conflicts: identical content with different labels
    for group, members in by_group.items():
        labels = {m.label for m in members if m.label}
        if len(labels) > 1:
            for m in members:
                m.status = "label_conflict"
                m.reasons.append(f"identical content labeled {sorted(labels)}")

    return records, meta


def validation_summary(records: list[ValidationRecord]) -> dict:
    """Aggregate validation results into a summary dict."""
    from collections import Counter

    statuses = Counter(r.status for r in records)
    usable = [r for r in records if r.status == "ok"]
    duplicated_files = sum(
        1
        for i, r in enumerate(records)
        if r.content_group
        and any(o.content_group == r.content_group for o in records[i + 1 :])
    )
    return {
        "total_files": len(records),
        "usable": len(usable),
        "by_status": dict(statuses),
        "rejected": [
            {"image": r.image_id, "reason": r.status, "details": r.reasons}
            for r in records
            if r.status != "ok"
        ],
        "duplicate_files": duplicated_files,
    }


# ---------------------------------------------------------------------------
# Leakage-safe split
# ---------------------------------------------------------------------------
SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
SPLIT_ORDER = ["train", "val", "test"]


def build_group_table(records: list[ValidationRecord], meta: pd.DataFrame) -> pd.DataFrame:
    """One row per content group: group id, unanimous label, hospital mode."""
    meta_by_file = {r["_file"]: r for _, r in meta.iterrows()}
    rows = []
    for rec in records:
        if rec.status != "ok" or not rec.content_group:
            continue
        row = meta_by_file.get(rec.image_id + ".png")
        hospital = str(row["HOSPITAL"]) if row is not None else "UNKNOWN"
        rows.append(
            {
                "content_group": rec.content_group,
                "label": rec.label,
                "hospital": hospital,
                "image_id": rec.image_id,
            }
        )
    groups = (
        pd.DataFrame(rows)
        .groupby("content_group")
        .agg(
            label=("label", "first"),
            hospital=("hospital", lambda s: s.mode().iloc[0] if len(s) else "UNKNOWN"),
            n_members=("image_id", "count"),
            hospital_mixed=("hospital", lambda s: s.nunique() > 1),
            image_ids=("image_id", lambda s: ",".join(sorted(s))),
        )
        .reset_index()
    )
    return groups


def split_groups(groups: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Deterministically assign each content group to train/val/test.

    Leakage-safe: the unit of assignment is the content group, so
    byte-identical images never span splits. Stratification is by
    (label, hospital) so class and site distributions stay proportional.
    """
    rng = random.Random(seed)
    groups = groups.copy()
    groups["split"] = ""
    for (_label, _hospital), stratum in groups.groupby(["label", "hospital"]):
        idx = list(stratum.index)
        rng.shuffle(idx)
        n = len(idx)
        n_train = round(n * SPLIT_RATIOS["train"])
        n_val = round(n * SPLIT_RATIOS["val"])
        for pos, i in enumerate(idx):
            if pos < n_train:
                groups.loc[i, "split"] = "train"
            elif pos < n_train + n_val:
                groups.loc[i, "split"] = "val"
            else:
                groups.loc[i, "split"] = "test"
    return groups


def check_no_leakage(groups: pd.DataFrame) -> None:
    """Assert no content group is assigned to more than one split."""
    dup = groups[groups.duplicated("content_group", keep=False)]
    if not dup.empty:
        raise AssertionError("content group appears in multiple splits")
    counts = groups["split"].value_counts()
    missing = set(SPLIT_ORDER) - set(counts.index)
    if missing:
        raise AssertionError(f"missing splits: {sorted(missing)}")


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
