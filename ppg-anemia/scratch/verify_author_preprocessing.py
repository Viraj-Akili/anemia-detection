"""
scratch/verify_author_preprocessing.py
Analyze exact chunking / moving average used by the original dataset authors
to create the 12 rows per subject in Preprocessing dataset per subject / Final Dataset Hb PPG.csv
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np

ORIG_DIR = Path(r"C:\Users\Viraj Akili\OneDrive\Desktop\Hemoglobin Photoplethysmography Dataset\Hemoglobin Photoplethysmography Dataset")
RAW_DIR = Path("data/raw")
final_csv = ORIG_DIR / "Final Dataset Hb PPG.csv"
df_final = pd.read_csv(final_csv)

# Let's check across 5 subjects:
for sub_id in [1, 2, 3, 4, 5, 10, 20]:
    df_raw = pd.read_csv(RAW_DIR / f"{sub_id}.csv")
    r_red = df_raw["Red (a.u)"].to_numpy()
    r_ir = df_raw["Infra Red (a.u)"].to_numpy()
    
    block = df_final.iloc[(sub_id-1)*12 : sub_id*12]
    f_red = block["Red (a.u)"].to_numpy()
    f_ir = block["Infra Red (a.u)"].to_numpy()
    
    # Check 12 chunks of length 20:
    # 12 * 20 = 240 samples. The remaining 10 samples (or 9 samples) might be in the last chunk or truncated
    chunk_20_red = [np.mean(r_red[i*20:(i+1)*20]) for i in range(12)]
    # Or chunks of size len(r_red)/12
    chunk_div_red = [np.mean(c) for c in np.array_split(r_red, 12)]
    
    print(f"\n--- Subject {sub_id} (Raw length: {len(r_red)}) ---")
    print(f"Final Red (12 rows) : {[round(x, 1) for x in f_red]}")
    print(f"Chunk 20-sample mean: {[round(x, 1) for x in chunk_20_red]}")
    print(f"Split 12 equal-mean : {[round(x, 1) for x in chunk_div_red]}")
    
    diff_20 = np.abs(np.array(f_red[:11]) - np.array(chunk_20_red[:11]))
    print(f"Max absolute diff for first 11 chunks (size 20): {np.max(diff_20):.4f}")
    
    # For IR:
    chunk_20_ir = [np.mean(r_ir[i*20:(i+1)*20]) for i in range(12)]
    diff_20_ir = np.abs(np.array(f_ir[:11]) - np.array(chunk_20_ir[:11]))
    print(f"Max absolute diff for IR first 11 chunks (size 20): {np.max(diff_20_ir):.4f}")
