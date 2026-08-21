"""
scratch/verify_last_chunk.py
Find exact formula for chunk 12 (the last row)
"""

import pandas as pd
import numpy as np
from pathlib import Path

ORIG_DIR = Path(r"C:\Users\Viraj Akili\OneDrive\Desktop\Hemoglobin Photoplethysmography Dataset\Hemoglobin Photoplethysmography Dataset")
RAW_DIR = Path("data/raw")
final_csv = ORIG_DIR / "Final Dataset Hb PPG.csv"
df_final = pd.read_csv(final_csv)

for sub_id in [1, 2, 3, 4, 5, 10, 20]:
    df_raw = pd.read_csv(RAW_DIR / f"{sub_id}.csv")
    r_red = df_raw["Red (a.u)"].to_numpy()
    block = df_final.iloc[(sub_id-1)*12 : sub_id*12]
    f12_red = block["Red (a.u)"].iloc[11]
    
    # Try different slice ranges for the 12th row:
    # Option 1: samples 220:250 or 220:249
    m1 = np.mean(r_red[220:])
    # Option 2: last 20 samples [-20:]
    m2 = np.mean(r_red[-20:])
    # Option 3: samples from index 230:
    m3 = np.mean(r_red[230:])
    # Option 4: samples 220:240
    m4 = np.mean(r_red[220:240])
    
    print(f"Sub {sub_id} (len {len(r_red)}): Final Row 12 = {f12_red:.1f} | Mean(220:) = {m1:.1f} | Mean(-20:) = {m2:.1f} | Mean(230:) = {m3:.1f}")
    
    # Check if there is an exact slice [start:end]
    for s in range(200, len(r_red)):
        for e in range(s+1, len(r_red)+1):
            if abs(np.mean(r_red[s:e]) - f12_red) < 0.06:
                print(f"   -> Match slice [{s}:{e}] (length {e-s}): mean={np.mean(r_red[s:e]):.1f}")
                break
