"""
ds004511_support.py — Shared constants, loaders, and statistics for the
Embodied Anchoring Principle (EAP) analysis of ds004511.

Dataset:  "Deception_data" — Makowski, Pham & Lau (CC0)
          44 healthy adults; EEG (128-ch) + BioPac physio (ECG, RSP, EDA, EMG)
Tasks:    GG  = Gambling Game (spontaneous deception, 144 rounds)
          CC  = Cognitive Control (response inhibition, conflict resolution)
          Rest = Eyes-closed resting state

Pipeline: NMD run 193708  (ds004511_20260701_193708, final N=44/45 corrected run)

Reproducibility note: this module resolves its two external-data dependencies
(`FEATURES_PARQUET`, raw BIDS `events.tsv`) through fallback chains so that the
article's `src/` scripts and `notebook/reproduce_results.ipynb` work from a
clean checkout of this repository alone, without access to the original
authors' external workstation drives. See `data/README.md` for details.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request
import warnings as _warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTICLE_DIR = REPO_ROOT / "articles" / "Neural flow geometry differentiates gambling and cognitive control"
RESULTS_DIR = ARTICLE_DIR / "results"
FIGURES_DIR = ARTICLE_DIR / "figures"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

NMD_RUN = "neuralmanifolddynamics_ds004511_20260701_193708"
NMD_ROOT = REPO_ROOT / "data" / "raw" / NMD_RUN


def _resolve_features_parquet() -> Optional[Path]:
    """Locate the epoch-level ``features.parquet`` table, if available.

    Checked in order:
      1. the repo-committed copy (`data/processed/ds004511/features.parquet`)
      2. the original authors' external workstation path (`J:\\processed\\...`),
         kept for convenience when running on that machine
    Returns None (resolved lazily, see `load_features`) if neither exists —
    this module is imported by scripts that never call `load_features()`
    (e.g. `01_cross_task_mnps.py`, `11_event_density_sensitivity.py`), so
    the absence of this file must not be a hard import-time error.
    """
    candidates = [
        REPO_ROOT / "data" / "processed" / "ds004511" / "features.parquet",
        Path(r"J:\processed\openneuro\ds004511\features.parquet"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


FEATURES_PARQUET = _resolve_features_parquet()

# ──────────────────────────────────────────────────────────────────────────────
# Raw-BIDS fallback (small text files only — events.tsv, ~20-50 KB/session)
# ──────────────────────────────────────────────────────────────────────────────

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/OpenNeuroDatasets/ds004511/main"
EVENTS_CACHE_DIR = REPO_ROOT / "data" / "external_cache" / "ds004511_events"


def _list_subjects_for_task_label(task_label: str) -> List[str]:
    """Subject IDs that have an NMD session folder for ``task_label``."""
    if not NMD_ROOT.exists():
        return []
    pattern = re.compile(rf"(sub-\w+)_ses-\w+_{re.escape(task_label)}_run-\w+")
    subs = set()
    for session_dir in NMD_ROOT.iterdir():
        m = pattern.match(session_dir.name)
        if m:
            subs.add(m.group(1))
    return sorted(subs)


def _fetch_events_tsv_from_github(subject_id: str, task_raw: str) -> Optional[pd.DataFrame]:
    """Fetch/cache one session's events.tsv from the public OpenNeuro mirror.

    Only used as a last-resort fallback when no local raw-BIDS copy of
    ds004511 is available (see `load_events`). Downloads are cached under
    `data/external_cache/` so repeated notebook runs don't re-fetch.
    """
    fname = f"{subject_id}_ses-01_task-{task_raw}_run-01_events.tsv"
    cache_path = EVENTS_CACHE_DIR / fname
    if not cache_path.exists():
        url = f"{GITHUB_RAW_BASE}/{subject_id}/ses-01/eeg/{fname}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                content = resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            _warnings.warn(f"Could not fetch {url}: {exc}")
            return None
        EVENTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(content)
    try:
        return pd.read_csv(cache_path, sep="\t")
    except Exception as exc:
        _warnings.warn(f"Could not parse cached {cache_path}: {exc}")
        return None

# ──────────────────────────────────────────────────────────────────────────────
# Task labels
# ──────────────────────────────────────────────────────────────────────────────

# task_raw (from file column) → task_label (NMD CSV convention)
TASK_RAW_TO_LABEL: Dict[str, str] = {
    "GG": "gambling",
    "CC": "cognitive_control",
    "Rest": "rest",
}
TASK_LABEL_TO_RAW: Dict[str, str] = {v: k for k, v in TASK_RAW_TO_LABEL.items()}
TASK_ORDER = ["gambling", "cognitive_control", "rest"]   # analysis order
TASK_DISPLAY = {
    "gambling": "Gambling (GG)",
    "cognitive_control": "Cognitive Control (CC)",
    "rest": "Rest",
}

NETWORKS = ["frontal", "central", "parietal_occipital", "temporal"]

# ──────────────────────────────────────────────────────────────────────────────
# Feature groups
# ──────────────────────────────────────────────────────────────────────────────

RESP_ANCHOR_COLS = [
    "resp_anchor_index",
    "resp_slowing_index",
    "resp_depth_index",
    "resp_regular_index",
    "resp_phase_consistency",
    "resp_rate_bpm",
    "resp_amplitude_median",
    "resp_amplitude_cv",
]
HRV_COLS = [
    "ecg_hrv_rmssd_ms",
    "ecg_hrv_sdnn_ms",
    "ecg_hrv_hr_mean_bpm",
    "ecg_hrv_dfa_alpha1",
    "ecg_hrv_pnn50",
]
CARDIORESP_COLS = [
    "cardioresp_rsa_amplitude",
    "cardioresp_coherence",
    "cardioresp_rpeak_resp_plv",
    "cardioresp_coupling_index",
]
SPECTRAL_COLS = [
    "eeg_alpha", "eeg_theta", "eeg_gamma", "eeg_beta", "eeg_delta",
    "eeg_alpha_theta", "eog_eye_stability_index", "eog_artifact_fraction",
    "eog_blink_rate",
]

MNPS_COLS = ["m_median", "d_median", "e_median"]
MNJ_KEYS = [
    "frobenius_norm_median",
    "rotation_norm_median",
    "trace_median",
    "spectral_radius_median",
    "rotational_power_median",
    "aci_median",
    "mdr_median",
]
REACH_KEYS = [
    "tube_log_det_median",
    "tube_d_eff_median",
    "tube_kappa_median",
    "tube_rotation_median",
    "tube_dir_entropy_median",
]

# ──────────────────────────────────────────────────────────────────────────────
# Data loaders
# ──────────────────────────────────────────────────────────────────────────────

def parse_file_column(feat: pd.DataFrame) -> pd.DataFrame:
    """Add subject_id and task_raw from the 'file' column."""
    feat = feat.copy()
    feat["subject_id"] = feat["file"].str.extract(r"(sub-\w+)_ses")
    feat["task_raw"] = feat["file"].str.extract(r"task-(\w+)_run")
    feat["task_label"] = feat["task_raw"].map(TASK_RAW_TO_LABEL)
    return feat


def load_features(*, add_task: bool = True) -> pd.DataFrame:
    """Load epoch-level features.parquet.

    Raises FileNotFoundError with reproduction instructions if the table
    isn't available at either of the paths checked by
    `_resolve_features_parquet()` (repo-committed copy, or the original
    authors' external `J:\\processed\\...` path).
    """
    if FEATURES_PARQUET is None:
        raise FileNotFoundError(
            "features.parquet not found. Expected it at "
            f"'{REPO_ROOT / 'data' / 'processed' / 'ds004511' / 'features.parquet'}' "
            "(repo-committed copy). This epoch-level EEG+physio feature table "
            "is required by scripts 00/02/03/09/10. See data/README.md for "
            "provenance and how to obtain/regenerate it."
        )
    feat = pd.read_parquet(FEATURES_PARQUET)
    if add_task:
        feat = parse_file_column(feat)
    return feat


def load_regional_mnps(*, exclude_falsified: bool = True) -> pd.DataFrame:
    """Load regional MNPS session-level summary CSV."""
    path = NMD_ROOT / f"regional_mnps_subjects_{NMD_RUN[-6:]}.csv"
    df = pd.read_csv(path)
    if exclude_falsified and "strat9_falsified" in df.columns:
        n_before = len(df)
        df = df[df["strat9_falsified"] != 1].copy()
        n_excl = n_before - len(df)
        if n_excl:
            import warnings
            warnings.warn(f"Excluded {n_excl} rows with strat9_falsified=1 from regional_mnps.")
    return df


def load_block_jacobians() -> pd.DataFrame:
    """Load regional block Jacobians CSV."""
    path = NMD_ROOT / f"regional_block_jacobians_subjects_{NMD_RUN[-6:]}.csv"
    return pd.read_csv(path)


def load_stratified_jacobians() -> pd.DataFrame:
    """Load stratified block Jacobians CSV."""
    path = NMD_ROOT / f"stratified_block_jacobians_subjects_{NMD_RUN[-6:]}.csv"
    return pd.read_csv(path)


def iter_h5_paths() -> List[Tuple[str, str, Path]]:
    """Yield (subject_id, task_label, h5_path) for all available H5 files.

    Folder pattern: sub-{ID}_ses-{SES}_{task_label}_run-{RUN}
    H5 file matches folder name.
    """
    task_labels = {"gambling", "cognitive_control", "rest"}
    results = []
    for session_dir in sorted(NMD_ROOT.iterdir()):
        if not session_dir.is_dir():
            continue
        # Parse folder: sub-S200116_ses-01_cognitive_control_run-01
        m = re.match(
            r"(sub-\w+)_ses-\w+_(gambling|cognitive_control|rest)_run-\w+",
            session_dir.name,
        )
        if not m:
            continue
        subject_id, task_label = m.group(1), m.group(2)
        h5_path = session_dir / f"{session_dir.name}.h5"
        if h5_path.exists():
            results.append((subject_id, task_label, h5_path))
    return results


def load_events(task_raw: str = "GG") -> pd.DataFrame:
    """Load pooled events.tsv for all subjects for a given task.

    NOTE: ds004511 events.tsv files only contain `Sync(1)` trigger pulses
    (button presses). Trial-type labels (deception/cooperation, win/loss)
    are NOT available in the BIDS format for this dataset. They would require
    the original behavioral data files (.mat/.csv) from the experimenters.
    Use this function only for timing / trigger alignment purposes.

    Resolution order:
      1. local raw-BIDS mirrors (`M:\\datasets\\received\\openneuro\\ds004511`,
         `J:\\datasets\\openneuro\\ds004511`) — fast path on the original
         authors' machines.
      2. public OpenNeuro GitHub mirror (`OpenNeuroDatasets/ds004511`) — small
         `events.tsv` files (~20-50 KB each) fetched per-subject and cached
         under `data/external_cache/ds004511_events/`, so this works from a
         clean checkout with just internet access (no raw physio needed).
    """
    bids_root = Path(r"M:\datasets\received\openneuro\ds004511")
    if not bids_root.exists():
        bids_root = Path(r"J:\datasets\openneuro\ds004511")

    rows = []
    if bids_root.exists():
        for evfile in sorted(bids_root.rglob(f"*task-{task_raw}_run-*_events.tsv")):
            m = re.search(r"(sub-\w+)_ses", evfile.name)
            if not m:
                continue
            sub = m.group(1)
            df = pd.read_csv(evfile, sep="\t")
            df["subject_id"] = sub
            df["task_raw"] = task_raw
            rows.append(df)
    else:
        task_label = TASK_RAW_TO_LABEL.get(task_raw, task_raw)
        subs = _list_subjects_for_task_label(task_label)
        if subs:
            print(
                f"  (no local raw-BIDS ds004511 mirror found; fetching "
                f"{len(subs)} {task_raw} events.tsv files from the public "
                f"OpenNeuro GitHub mirror, cached under "
                f"{EVENTS_CACHE_DIR.relative_to(REPO_ROOT)})"
            )
        for sub in subs:
            df = _fetch_events_tsv_from_github(sub, task_raw)
            if df is None:
                continue
            df["subject_id"] = sub
            df["task_raw"] = task_raw
            rows.append(df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def make_results_subdir(phase: str) -> Path:
    """Create and return a dated results subdirectory."""
    today = datetime.now().strftime("%Y%m%d")
    d = RESULTS_DIR / f"ds004511_{today}" / phase
    d.mkdir(parents=True, exist_ok=True)
    return d


# ──────────────────────────────────────────────────────────────────────────────
# Statistics helpers
# ──────────────────────────────────────────────────────────────────────────────

def wilcoxon_paired(
    a: np.ndarray, b: np.ndarray
) -> Tuple[float, float, int, float]:
    """Wilcoxon signed-rank test on paired (a, b), returning (stat, p, n, cohend)."""
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    n = len(a)
    if n < 5:
        return np.nan, np.nan, n, np.nan
    diff = a - b
    try:
        stat, p = stats.wilcoxon(diff, zero_method="wilcox")
    except ValueError:
        return np.nan, np.nan, n, np.nan
    d = float(np.mean(diff) / (np.std(diff) + 1e-12))
    return float(stat), float(p), n, d


def friedman_test(
    *groups: np.ndarray,
) -> Tuple[float, float]:
    """Friedman test across k repeated conditions."""
    arrays = [np.asarray(g, dtype=float) for g in groups]
    mask = np.ones(len(arrays[0]), dtype=bool)
    for a in arrays:
        mask &= np.isfinite(a)
    arrays = [a[mask] for a in arrays]
    if len(arrays[0]) < 5:
        return np.nan, np.nan
    stat, p = stats.friedmanchisquare(*arrays)
    return float(stat), float(p)


def bh_fdr(pvals: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg FDR correction."""
    pvals = np.asarray(pvals, dtype=float)
    n = len(pvals)
    if n == 0:
        return pvals
    rank = np.argsort(pvals).argsort() + 1
    adjusted = np.minimum(1.0, pvals * n / rank)
    # Enforce monotonicity
    sorted_idx = np.argsort(pvals)[::-1]
    min_so_far = 1.0
    result = adjusted.copy()
    for i in sorted_idx:
        min_so_far = min(min_so_far, adjusted[i])
        result[i] = min_so_far
    return result


def spearman_r(x, y) -> Tuple[float, float]:
    """Spearman r between two Series/arrays, dropping NaN pairs."""
    df = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(df) < 5:
        return np.nan, np.nan
    r, p = stats.spearmanr(df["x"], df["y"])
    return float(r), float(p)


def subject_task_medians(
    feat: pd.DataFrame,
    cols: List[str],
    *,
    task_col: str = "task_label",
) -> pd.DataFrame:
    """Median per subject × task for a list of feature columns."""
    avail = [c for c in cols if c in feat.columns]
    return (
        feat.groupby(["subject_id", task_col])[avail]
        .median()
        .reset_index()
    )
