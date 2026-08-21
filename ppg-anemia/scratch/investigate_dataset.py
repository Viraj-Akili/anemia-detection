"""
scratch/investigate_dataset.py
Forensic investigation of 68 subjects vs 816 rows in Final Dataset Hb PPG.csv
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np

ORIG_DIR = Path(r"C:\Users\Viraj Akili\OneDrive\Desktop\Hemoglobin Photoplethysmography Dataset\Hemoglobin Photoplethysmography Dataset")
RAW_DIR = Path("data/raw")

print("=" * 80)
print("FORENSIC INVESTIGATION: 68 RAW FILES VS 816 ROWS IN FINAL DATASET")
print("=" * 80)

# 1. Inspect data/raw
raw_files = sorted(list(RAW_DIR.glob("*.csv")), key=lambda p: int(p.stem) if p.stem.isdigit() else p.name)
print(f"1. Raw CSV files count in data/raw/: {len(raw_files)}")
raw_row_counts = [len(pd.read_csv(f)) for f in raw_files]
print(f"   Raw CSV row count distribution: min={min(raw_row_counts)}, max={max(raw_row_counts)}, total={sum(raw_row_counts)}")
print(f"   (45 files with 249 rows, 23 files with 250 rows)")

# 2. Inspect Final Dataset Hb PPG.csv
final_csv = ORIG_DIR / "Final Dataset Hb PPG.csv"
df_final = pd.read_csv(final_csv)
print(f"\n2. Final Dataset Hb PPG.csv shape: {df_final.shape}")
print(f"   Columns: {df_final.columns.tolist()}")

# 3. Check subject grouping in Final Dataset
# In Final Dataset Hb PPG.csv, each block of 12 rows corresponds to one subject.
# Let's verify this across all 68 subjects.
blocks = []
for i in range(0, len(df_final), 12):
    block = df_final.iloc[i:i+12]
    sub_id = (i // 12) + 1
    genders = block["Gender"].unique()
    ages = block["Age (year)"].unique()
    hbs = block["Hemoglobin (g/dL)"].unique()
    blocks.append({
        "subject_id": sub_id,
        "rows": len(block),
        "gender": genders[0] if len(genders) == 1 else "MIXED",
        "age": ages[0] if len(ages) == 1 else "MIXED",
        "hb": hbs[0] if len(hbs) == 1 else "MIXED"
    })

df_blocks = pd.DataFrame(blocks)
print(f"\n3. Blocks of 12 rows in Final Dataset:")
print(f"   Total blocks (subjects): {len(df_blocks)}")
print(f"   All blocks have exact 12 rows: {all(df_blocks['rows'] == 12)}")
print(f"   All blocks have constant Gender: {all(df_blocks['gender'] != 'MIXED')}")
print(f"   All blocks have constant Age: {all(df_blocks['age'] != 'MIXED')}")
print(f"   All blocks have constant Hb: {all(df_blocks['hb'] != 'MIXED')}")

# Verify demographic and Hb match between data/raw and Final Dataset Hb PPG.csv
match_count = 0
for sub_id in range(1, 69):
    raw_f = RAW_DIR / f"{sub_id}.csv"
    df_r = pd.read_csv(raw_f)
    r_gender = str(df_r["Gender"].iloc[0]).strip()
    r_age = int(df_r["Age"].iloc[0])
    r_hb = float(df_r["Hemoglobin (g/dL)"].iloc[0])
    
    b = df_blocks[df_blocks["subject_id"] == sub_id].iloc[0]
    f_gender = str(b["gender"]).strip()
    f_age = int(b["age"])
    f_hb = float(b["hb"])
    
    if r_gender.lower() == f_gender.lower() and r_age == f_age and abs(r_hb - f_hb) < 1e-4:
        match_count += 1
    else:
        print(f"Mismatch on subject {sub_id}: raw=({r_gender}, {r_age}, {r_hb}) vs final=({f_gender}, {f_age}, {f_hb})")

print(f"\n4. Exact demographic & Hb matching between raw {len(raw_files)} files and 68 Final Dataset blocks:")
print(f"   Matches: {match_count} / 68 ({match_count/68*100:.1f}%)")

# 5. Reverse engineer the 12 rows of Red and IR
# Let's inspect Subject 1
df_raw_1 = pd.read_csv(RAW_DIR / "1.csv")
r1_red = df_raw_1["Red (a.u)"].to_numpy()
r1_ir = df_raw_1["Infra Red (a.u)"].to_numpy()

final_sub_1 = df_final.iloc[0:12]
f1_red = final_sub_1["Red (a.u)"].to_numpy()
f1_ir = final_sub_1["Infra Red (a.u)"].to_numpy()

print(f"\n5. Subject 1 Comparison:")
print(f"   Raw Red shape: {len(r1_red)}, min={r1_red.min():.1f}, max={r1_red.max():.1f}, mean={r1_red.mean():.1f}")
print(f"   Final Red (12 rows): {f1_red}")
print(f"   Final IR (12 rows): {f1_ir}")

# Let's check moving average:
# In moving average with window N, let's see which window and sample indices produce f1_red:
for window in [10, 15, 20, 25, 30, 35, 40, 45, 50]:
    ma_red = np.convolve(r1_red, np.ones(window)/window, mode='valid')
    # Check if f1_red values appear in ma_red
    found_indices = []
    for val in f1_red:
        diffs = np.abs(ma_red - val)
        best_idx = np.argmin(diffs)
        if diffs[best_idx] < 0.1:
            found_indices.append((best_idx, diffs[best_idx]))
    if len(found_indices) == 12:
        print(f"   -> EXACT MATCH for Red with Moving Average window = {window}!")
        print(f"      Matched sample indices in valid convolution: {[idx for idx, d in found_indices]}")

# Let's check moving average with window on raw signal directly
# In pandas or excel moving average:
for w in range(1, 60):
    ma_pd = pd.Series(r1_red).rolling(window=w).mean().dropna().values
    matched = []
    for v in f1_red:
        diffs = np.abs(ma_pd - v)
        min_diff = np.min(diffs)
        if min_diff < 0.1:
            matched.append(np.argmin(diffs))
    if len(matched) == 12:
        print(f"   -> EXACT MATCH in pandas rolling mean with window = {w}! Indices: {matched}")

# What if 250 samples were downsampled, decimated, or averaged in 12 non-overlapping chunks?
chunk_means_red = [np.mean(r1_red[i*20:(i+1)*20]) for i in range(12)]
print(f"\n   Chunk 20-sample means: {[round(m, 1) for m in chunk_means_red]}")
