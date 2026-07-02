"""
06_eda_extraction.py — Standalone EDA feature extraction for ds004511.

Strategy:
  - Stream-read only column 5 (EDA) from each physio.tsv.gz using Python's
    gzip module — no pandas overhead, no parsing of unused columns.
  - Downsample from 4000 Hz to 50 Hz with scipy.decimate (anti-aliased).
  - Run neurokit2.eda_process ONCE per session on the full downsampled signal.
  - Extract per-epoch features from the continuous tonic/phasic/SCR arrays.

Features per epoch (8 s windows):
  eda_tonic_scl          — mean tonic skin conductance level (µS)
  eda_tonic_slope        — linear slope of tonic component (µS/s)
  eda_phasic_scr_rate    — SCR events per minute
  eda_phasic_scr_amp     — mean SCR peak amplitude in window (µS)
  eda_phasic_scr_count   — SCR count in window
  eda_phasic_auc         — mean absolute phasic signal
  eda_arousal_index      — SCR_rate + |slope|
  qc_ok_eda              — 1 = QC pass

Output:
  results/06_eda_extraction/
    eda_features.parquet
    eda_qc_summary.csv
"""
import sys
import re
import gzip
import json
import time
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from itertools import combinations

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from scipy.signal import decimate
import neurokit2 as nk

from ds004511_support import (
    TASK_ORDER,
    load_features,
    make_results_subdir,
    wilcoxon_paired,
)

OUT = make_results_subdir("06_eda_extraction")

BIDS_ROOT = Path(r"M:\datasets\received\openneuro\ds004511")
PHYSIO_SR  = 4000
EDA_SR     = 50              # target after downsampling
DEC_FACTOR = PHYSIO_SR // EDA_SR   # 80 = 8 × 10
EDA_COL    = 5               # 0-indexed column in physio TSV

# ─────────────────────────────────────────────────────────────────────────────
# Fast streaming EDA reader — Python gzip line iterator, no pandas
# ─────────────────────────────────────────────────────────────────────────────

def read_eda_column(phys_path: Path, col_idx: int = EDA_COL) -> np.ndarray | None:
    """
    Read a single column from a large physio.tsv.gz by streaming line by line.
    Splitting is limited to col_idx+1 fields so later columns are never parsed.
    Roughly 5–10× faster than pd.read_csv for large multi-column gzip files.
    """
    buf: list[float] = []
    try:
        with gzip.open(phys_path, "rt", encoding="ascii", errors="replace") as fh:
            for line in fh:
                # split('\t', col_idx+1) stops after extracting the column we need
                parts = line.split("\t", col_idx + 1)
                if len(parts) > col_idx:
                    try:
                        buf.append(float(parts[col_idx]))
                    except ValueError:
                        buf.append(np.nan)
    except Exception as exc:
        print(f"    read_eda_column error: {exc}")
        return None
    if not buf:
        return None
    return np.array(buf, dtype=np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# Session-level EDA processing (one neurokit2 call per session at 50 Hz)
# ─────────────────────────────────────────────────────────────────────────────

def process_session_eda(eda_4k: np.ndarray) -> dict | None:
    """Downsample 4 kHz → 50 Hz, decompose with neurokit2 (tonic + phasic)."""
    # Cascaded decimation: 80 = 8 × 10
    try:
        eda_ds = decimate(eda_4k.astype(np.float64), q=8, zero_phase=True)
        eda_ds = decimate(eda_ds, q=10, zero_phase=True)
    except Exception:
        return None

    eda_range = float(np.ptp(eda_ds))
    eda_mean  = float(np.nanmean(eda_ds))
    if eda_range < 0.01 or not (0 < eda_mean < 100):
        return None

    try:
        signals, info = nk.eda_process(eda_ds, sampling_rate=EDA_SR,
                                        method="neurokit")
    except Exception:
        return None

    return {
        "tonic":          signals["EDA_Tonic"].values,
        "phasic":         signals["EDA_Phasic"].values,
        "scr_peaks":      np.asarray(info.get("SCR_Peaks",     []), dtype=int),
        "scr_amplitudes": np.asarray(info.get("SCR_Amplitude", []), dtype=float),
        "n_ds":           len(eda_ds),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Per-epoch feature extraction from pre-processed session
# ─────────────────────────────────────────────────────────────────────────────

def _nan_row() -> dict:
    return {k: np.nan for k in [
        "eda_tonic_scl", "eda_tonic_slope", "eda_phasic_scr_rate",
        "eda_phasic_scr_amp", "eda_phasic_scr_count", "eda_phasic_auc",
        "eda_arousal_index",
    ]} | {"qc_ok_eda": 0}


def epoch_features(sess: dict, t_start: float, t_end: float,
                   physio_start_s: float) -> dict:
    """Extract scalar EDA features for one epoch window."""
    sr = EDA_SR
    duration_s = t_end - t_start

    i0 = int(round((t_start - physio_start_s) * sr))
    i1 = int(round((t_end   - physio_start_s) * sr))
    i0 = max(0, i0)
    i1 = min(sess["n_ds"], i1)

    if i1 - i0 < int(sr * 2):
        return _nan_row()

    tonic_seg  = sess["tonic"][i0:i1]
    phasic_seg = sess["phasic"][i0:i1]

    if not np.any(np.isfinite(tonic_seg)):
        return _nan_row()

    tonic_scl = float(np.nanmean(tonic_seg))
    t_arr = np.arange(len(tonic_seg)) / sr
    valid = np.isfinite(tonic_seg)
    slope = np.nan
    if valid.sum() >= 4:
        slope, *_ = scipy_stats.linregress(t_arr[valid], tonic_seg[valid])

    phasic_auc = float(np.nanmean(np.abs(phasic_seg)))

    mask  = (sess["scr_peaks"] >= i0) & (sess["scr_peaks"] < i1)
    peaks_in = sess["scr_peaks"][mask]
    scr_count = int(len(peaks_in))
    scr_rate  = float(scr_count / duration_s * 60)

    scr_amp = 0.0
    if scr_count > 0 and len(sess["scr_amplitudes"]) > 0:
        amp_idx = np.where(np.isin(sess["scr_peaks"], peaks_in))[0]
        amps = sess["scr_amplitudes"][amp_idx]
        amps = amps[np.isfinite(amps) & (amps > 0)]
        if len(amps):
            scr_amp = float(amps.mean())

    return {
        "eda_tonic_scl":       tonic_scl,
        "eda_tonic_slope":     float(slope) if np.isfinite(slope) else np.nan,
        "eda_phasic_scr_rate": scr_rate,
        "eda_phasic_scr_amp":  scr_amp,
        "eda_phasic_scr_count": float(scr_count),
        "eda_phasic_auc":      phasic_auc,
        "eda_arousal_index":   float(scr_rate + abs(slope or 0)),
        "qc_ok_eda": 1,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

print("Loading features.parquet ...")
feat = load_features()
print(f"  {len(feat):,} epochs  {feat['subject_id'].nunique()} subjects")

task_raw_map = {"GG": "gambling", "CC": "cognitive_control", "Rest": "rest"}

physio_files = sorted(
    BIDS_ROOT.rglob("*_physio.tsv.gz"),
    key=lambda p: p.stat().st_size,   # smallest files first → faster early feedback
)
print(f"Found {len(physio_files)} physio.tsv.gz files (sorted smallest to largest)\n")

all_rows: list[dict] = []
qc_rows:  list[dict] = []
t_global = time.time()

for i, phys_path in enumerate(physio_files):
    stem = phys_path.name.replace(".tsv.gz", "")
    m = re.search(r"(sub-\w+)_ses-\w+_task-(\w+)_run", stem)
    if not m:
        continue
    subject_id, task_raw = m.group(1), m.group(2)
    task_label = task_raw_map.get(task_raw)
    if not task_label:
        continue

    file_stem = f"{subject_id}_ses-01_task-{task_raw}_run-01_eeg.edf"
    sess_epochs = feat[feat["file"] == file_stem][["t_start", "t_end"]]
    if len(sess_epochs) == 0:
        continue

    # Physio StartTime offset
    physio_start_s = 0.0
    json_path = phys_path.with_suffix("").with_suffix(".json")
    if json_path.exists():
        try:
            physio_start_s = float(
                json.loads(json_path.read_text()).get("StartTime", 0.0)
            )
        except Exception:
            pass

    t0 = time.time()
    mb = phys_path.stat().st_size / 1e6

    # ── Read EDA column (streaming, no pandas) ──────────────────────────────
    eda_4k = read_eda_column(phys_path)
    if eda_4k is None or len(eda_4k) < PHYSIO_SR * 10:
        print(f"  [{i+1:3d}/{len(physio_files)}] SKIP {stem}  (read failed)")
        continue

    # ── Session-level decomposition ─────────────────────────────────────────
    sess = process_session_eda(eda_4k)
    if sess is None:
        print(f"  [{i+1:3d}/{len(physio_files)}] SKIP {stem}  (EDA QC failed)")
        continue

    # ── Per-epoch feature extraction ────────────────────────────────────────
    n_ok = n_fail = 0
    for _, row in sess_epochs.iterrows():
        fd = epoch_features(sess, row["t_start"], row["t_end"], physio_start_s)
        fd.update({"subject_id": subject_id, "task_label": task_label,
                   "t_start": row["t_start"], "file": file_stem})
        all_rows.append(fd)
        if fd["qc_ok_eda"] == 1:
            n_ok += 1
        else:
            n_fail += 1

    elapsed = time.time() - t0
    qc_frac = n_ok / (n_ok + n_fail) if (n_ok + n_fail) else 0.0
    qc_rows.append({
        "subject_id": subject_id, "task_label": task_label,
        "n_epochs": n_ok + n_fail, "n_ok": n_ok,
        "qc_ok_frac": round(qc_frac, 3),
    })

    total_elapsed = time.time() - t_global
    avg_s = total_elapsed / (i + 1)
    eta_s  = avg_s * (len(physio_files) - i - 1)
    print(
        f"  [{i+1:3d}/{len(physio_files)}] {subject_id} {task_label:18s}"
        f"  {mb:5.0f} MB  {elapsed:4.0f}s  QC={qc_frac:.0%}"
        f"  ETA {eta_s/60:.0f} min"
    )


print(f"\nTotal epochs: {len(all_rows):,}  "
      f"elapsed: {(time.time()-t_global)/60:.1f} min")

# ─────────────────────────────────────────────────────────────────────────────
# Save outputs
# ─────────────────────────────────────────────────────────────────────────────

eda_df = pd.DataFrame(all_rows)
eda_df.to_parquet(OUT / "eda_features.parquet", index=False)

qc_df = pd.DataFrame(qc_rows)
qc_df.to_csv(OUT / "eda_qc_summary.csv", index=False)

print("\nEDA QC by task:")
print(qc_df.groupby("task_label")[["n_epochs", "qc_ok_frac"]].mean().round(3))

print("\nEDA tonic SCL by task (QC-OK epochs):")
print(
    eda_df[eda_df["qc_ok_eda"] == 1]
    .groupby("task_label")["eda_tonic_scl"]
    .describe().round(3)
)

print("\nCross-task Wilcoxon (eda_tonic_scl, subject medians):")
sub_eda = (
    eda_df[eda_df["qc_ok_eda"] == 1]
    .groupby(["subject_id", "task_label"])["eda_tonic_scl"]
    .median().unstack()
)
for t1, t2 in combinations(TASK_ORDER, 2):
    if t1 in sub_eda.columns and t2 in sub_eda.columns:
        common = sub_eda[[t1, t2]].dropna().index
        _, p, n, d = wilcoxon_paired(
            sub_eda.loc[common, t1].values,
            sub_eda.loc[common, t2].values,
        )
        print(f"  {t1} vs {t2}: d={d:.3f}  p={p:.4f}  n={n}")

print(f"\n=== EDA extraction complete ===")
print(f"Outputs: {OUT}")
