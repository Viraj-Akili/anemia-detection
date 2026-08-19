#!/usr/bin/env python
"""Download + extract the CP-AnemiC dataset (official Mendeley source).

Reproducible: re-running is a no-op once the verified archive and extracted
tree exist. The raw archive is stored under data/raw/ and treated as
immutable input (never modified by later pipeline stages).

Usage:
    python scripts/download_dataset.py [--force]

The dataset is served as a single RAR archive. RAR extraction needs a tool:
- a system `7z`, `7za`, `7zr`, `unrar` or `unar` on PATH, or
- the bundled project tools (scripts/tools/7zip-full/7z.exe on Windows),
  which this script bootstraps from official sources when missing.

Verification: the archive's SHA-256 is checked against the value reported
by Mendeley's API (78d7c2eca49d250f3208b7cf384238d0793f5e772d33153e6ee7d73294cd319c).
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MENDELEY_DATASET_ID = "m53vz6b7fx"
MENDELEY_FILES_API = f"https://data.mendeley.com/api/datasets/{MENDELEY_DATASET_ID}/files"
ARCHIVE_SHA256 = "78d7c2eca49d250f3208b7cf384238d0793f5e772d33153e6ee7d73294cd319c"
ARCHIVE_FILENAME = "CP-AnemiC_dataset.rar"

RAW_DIR = PROJECT_ROOT / "data" / "raw"
ARCHIVE_PATH = RAW_DIR / ARCHIVE_FILENAME
EXTRACT_DIR = RAW_DIR / "cp-anemic"
EXTRACT_MARKER = EXTRACT_DIR / ".extracted_ok"
TOOLS_DIR = PROJECT_ROOT / "scripts" / "tools"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_extractor() -> list[str]:
    """Return a working extractor command (7z / unrar / unar)."""
    for tool in ("7z", "7za", "7zr", "unrar", "unar"):
        exe = shutil.which(tool)
        if exe:
            return [exe]
    bundled = TOOLS_DIR / "7zip-full" / "7z.exe"
    if bundled.is_file():
        return [str(bundled)]
    return []


def bootstrap_7zip() -> None:
    """Download 7-Zip tooling into scripts/tools/ (project-local, official source)."""
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    sevenzr = TOOLS_DIR / "7zr.exe"
    installer = TOOLS_DIR / "7z2301-x64.exe"
    full_dir = TOOLS_DIR / "7zip-full"
    if (full_dir / "7z.exe").is_file():
        return

    print("[download_dataset] bootstrapping 7-Zip into scripts/tools/ ...")
    if not sevenzr.is_file():
        urllib.request.urlretrieve("https://www.7-zip.org/a/7zr.exe", sevenzr)  # noqa: S310 - pinned https URL
    if not installer.is_file():
        urllib.request.urlretrieve("https://www.7-zip.org/a/7z2301-x64.exe", installer)  # noqa: S310

    # The 7-Zip installer is a 7z SFX; 7zr.exe can extract it directly.
    subprocess.run([str(sevenzr), "x", str(installer), f"-o{full_dir}", "-y"], check=True)


def download_archive() -> Path:
    """Fetch the file list from Mendeley's API and download the archive."""
    import json

    print(f"[download_dataset] fetching file list from {MENDELEY_FILES_API}")
    with urllib.request.urlopen(MENDELEY_FILES_API) as resp:  # noqa: S310 - pinned https URL
        files = json.load(resp)
    if not files:
        raise RuntimeError("Mendeley API returned an empty file list")
    entry = files[0]
    download_url = entry["content_details"]["download_url"]
    expected_sha = entry["content_details"]["sha256_hash"]

    print(f"[download_dataset] downloading {entry['filename']} ({entry['size']} bytes)")
    urllib.request.urlretrieve(download_url, ARCHIVE_PATH)  # noqa: S310

    actual = sha256_of(ARCHIVE_PATH)
    if actual != expected_sha:
        raise RuntimeError(
            f"SHA-256 mismatch: expected {expected_sha}, got {actual}. "
            "Delete data/raw/CP-AnemiC_dataset.rar and re-run."
        )
    print(f"[download_dataset] sha256 verified: {actual}")
    return ARCHIVE_PATH


def extract_archive() -> None:
    extractor = find_extractor()
    if not extractor:
        bootstrap_7zip()
        extractor = find_extractor()
    if not extractor:
        raise RuntimeError(
            "No RAR extractor available. Install 7-Zip and re-run, or extract "
            f"{ARCHIVE_PATH} manually to {EXTRACT_DIR}."
        )
    print(f"[download_dataset] extracting with {extractor[0]}")
    subprocess.run([*extractor, "x", str(ARCHIVE_PATH), f"-o{EXTRACT_DIR}", "-y"], check=True)
    EXTRACT_MARKER.write_text("ok\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and extract CP-AnemiC.")
    parser.add_argument("--force", action="store_true", help="re-download and re-extract even if present")
    args = parser.parse_args()

    if EXTRACT_MARKER.exists() and (EXTRACT_DIR / "Anemia_Data_Collection_Sheet.xlsx").exists() and not args.force:
        print(f"[download_dataset] already extracted at {EXTRACT_DIR} — nothing to do.")
        return

    if ARCHIVE_PATH.exists() and sha256_of(ARCHIVE_PATH) == ARCHIVE_SHA256 and not args.force:
        print("[download_dataset] verified archive already present — skipping download.")
    else:
        if args.force or not ARCHIVE_PATH.exists():
            download_archive()
        else:
            print("[download_dataset] archive present but SHA-256 mismatch — re-downloading.")
            download_archive()

    if (EXTRACT_DIR / "Anemia_Data_Collection_Sheet.xlsx").exists() and not args.force:
        print(f"[download_dataset] extraction already present at {EXTRACT_DIR}.")
        return
    extract_archive()
    print(f"[download_dataset] done. Raw dataset: {EXTRACT_DIR}")


if __name__ == "__main__":
    sys.exit(main())
