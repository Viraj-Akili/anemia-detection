"""WHO Child Growth Standards LMS tables (weight-for-age, length/height-for-age,
weight-for-length/height, by sex).

Source: WHO Child Growth Standards z-score tables downloaded from
``who.int/tools/child-growth-standards/standards`` (scripts/fetch_who_tables.py
re-downloads and converts them). The CSVs under ``assets/who_tables/`` are the
primary-source tables with the published ``L``, ``M``, ``S`` columns verbatim.

Coverage (0-5 years):
- ``wfa``  — weight-for-age, monthly 0-60 mo (key column ``Month``)
- ``hfa``  — length/height-for-age; WHO publishes two segments which this
  loader merges: recumbent length 0-24 mo + standing height 24-60 mo
- ``wfl``  — weight-for-recumbent-length, 45-110 cm (key column ``Length``)
- ``wfh``  — weight-for-standing-height, 65-120 cm (key column ``Height``)

WHZ uses ``wfl`` for children < 24 months (length-based) and ``wfh`` for
>= 24 months (height-based), matching WHO Anthro convention.
"""

from __future__ import annotations

import os

import pandas as pd

TABLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "who_tables")

#: metric -> per-sex files. "hfa" spans two segments (0-2 yr, 2-5 yr).
_FILE_PLAN: dict[str, dict[str, list[str]]] = {
    "wfa": {
        "male": ["wfa_boys_0-to-5-years_zscores.csv"],
        "female": ["wfa_girls_0-to-5-years_zscores.csv"],
    },
    "hfa": {
        "male": ["lhfa_boys_0-to-2-years_zscores.csv", "lhfa_boys_2-to-5-years_zscores.csv"],
        "female": ["lhfa_girls_0-to-2-years_zscores.csv", "lhfa_girls_2-to-5-years_zscores.csv"],
    },
    "wfl": {
        "male": ["wfl_boys_0-to-2-years_zscores.csv"],
        "female": ["wfl_girls_0-to-2-years_zscores.csv"],
    },
    "wfh": {
        "male": ["wfh_boys_2-to-5-years_zscores.csv"],
        "female": ["wfh_girls_2-to-5-years_zscores.csv"],
    },
    # Arm circumference-for-age (MUAC) — WHO publishes this standard for
    # 3-60 months only; values are in cm.
    "muac": {
        "male": ["acfa_boys_3-to-5-zscores.csv"],
        "female": ["acfa_girls_3-to-5-zscores.csv"],
    },
}

#: The key column each table is indexed by.
KEY_COLUMN = {"wfa": "Month", "hfa": "Month", "wfl": "Length", "wfh": "Height", "muac": "Month"}

_cache: dict[tuple[str, str], pd.DataFrame] = {}


def load_table(sex: str, metric: str) -> pd.DataFrame:
    """Load (and cache) the LMS table for a sex and metric.

    Returns a DataFrame with the table's key column (``Month``/``Length``/
    ``Height``), ``L``, ``M``, ``S`` and the published SD columns.
    """
    key = (sex.lower(), metric.lower())
    if key in _cache:
        return _cache[key]

    try:
        filenames = _FILE_PLAN[metric][sex]
    except KeyError as exc:  # pragma: no cover - defensive
        raise ValueError(f"unknown table: sex={sex!r}, metric={metric!r}") from exc

    frames = []
    for filename in filenames:
        path = os.path.join(TABLES_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"WHO table not found: {path}. Run scripts/fetch_who_tables.py "
                "to download the primary sources."
            )
        frame = pd.read_csv(path)
        frame.columns = [c.strip() for c in frame.columns]
        frames.append(frame)

    table = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    # Segmented tables (e.g. hfa: 0-2 yr length + 2-5 yr height) overlap at the
    # boundary month (24). WHO uses the height-based segment from 24 months, so
    # keep the LAST occurrence of each key when merging.
    kcol = KEY_COLUMN[metric]
    table = table.drop_duplicates(subset=kcol, keep="last").reset_index(drop=True)
    _cache[key] = table
    return table


def preload() -> None:
    """Load all six (sex, metric) tables at startup so screening never hits
    the filesystem lazily (Implementation Plan: tables loaded at startup)."""
    for metric in _FILE_PLAN:
        for sex in _FILE_PLAN[metric]:
            load_table(sex, metric)
