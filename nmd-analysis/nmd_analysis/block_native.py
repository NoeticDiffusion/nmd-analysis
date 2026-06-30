"""
Block-native sidecar loader for MNDM 2.3+ outputs.

This module is **dataset-agnostic**: it works with any MNDM run that produces
block_native_windows.csv/parquet sidecars, regardless of stage codes, anchor
availability, or dataset-specific label conventions.

Each subject/task directory produced by MNDM contains:

  block_native_windows.csv  /  .parquet
    - one row per analysis window
    - columns: MNPS (m, d, e, dots), HRV (ecg_hrv_*), anchor state
      (sympathetic_index, vagal_index, vascular_index, pupil_arousal_index,
      anchor_index), quality flags, task state labels

  event_locked.csv  /  .parquet
    - one row per event-aligned window
    - same MNPS + anchor columns plus event metadata

Stage codes depend on the dataset and ingest config.  Pass ``stage_labels``
explicitly to any function that needs human-readable labels.  Named constants
for common datasets are provided for convenience but are not used as defaults.

  DS003838_STAGE_LABELS  — digit-span / rest dataset
  DS006036_STAGE_LABELS  — alzheimer_ftd photic stress dataset

To load stage labels from an analysis YAML config, use
``stage_labels_from_config()``.  To infer them from the run manifest, use
``stage_labels_from_manifest()``.

Design rules:
  - honor geometry_contract before using Jacobian surfaces
  - do not conflate feature_anchors (coordinate contract) with anchor_state
  - treat anchor_coupling as optional
  - first claims should be interaction, not replacement of MNPS
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Dataset-specific stage code constants (not used as defaults)
# ---------------------------------------------------------------------------

DS003838_STAGE_LABELS: Dict[int, str] = {
    0: "rest",
    1: "listen",
    5: "mem5",
    9: "mem9",
    13: "mem13",
}
DS003838_STAGE_CODES: Dict[str, int] = {v: k for k, v in DS003838_STAGE_LABELS.items()}

DS006036_STAGE_LABELS: Dict[int, str] = {
    50: "photic_5hz",
    51: "photic_10hz",
    52: "photic_15hz",
    53: "photic_20hz",
    60: "open_eyes",
    61: "closed_eyes",
    62: "eye_movement",
}
DS006036_STAGE_CODES: Dict[str, int] = {v: k for k, v in DS006036_STAGE_LABELS.items()}

# Standard sleep-stage map — matches SLEEP_STAGE_CODE_TO_LABEL in legacy_adapters.py.
# Used by ANPHY, ds005555, and other PSG datasets.
# NOTE: sleep datasets do not use block_native sidecars in the current pipeline;
# these codes appear in /labels/stage within H5 files and are converted to the
# `condition` string column by the main analysis pipeline.
# Exposed here for completeness and forward-compatibility.
SLEEP_STAGE_CODE_TO_LABEL: Dict[int, str] = {
    0: "awake",
    2: "nrem2",
    3: "nrem3",
    4: "rem",
}

KNOWN_STAGE_LABELS: Dict[str, Dict[int, str]] = {
    "ds003838": DS003838_STAGE_LABELS,
    "ds006036": DS006036_STAGE_LABELS,
    # sleep stage default — used when dataset_id matches a known PSG dataset
    # or when cfg.flags.sleep_data_contrast is True.
    "_sleep_default": SLEEP_STAGE_CODE_TO_LABEL,
}

# ---------------------------------------------------------------------------
# Config bridging
# ---------------------------------------------------------------------------

def stage_labels_from_config(cfg: Any) -> Dict[int, str]:
    """Extract stage code map from an ``AnalysisConfig`` or ``DatasetConfig``.

    Accepts any config object that exposes a ``stage_code_map`` attribute
    (on ``cfg.block_native`` or ``cfg.flags``), or a plain dict.

    Falls back to ``SLEEP_STAGE_CODE_TO_LABEL`` when ``cfg.flags.sleep_data_contrast``
    is True and no explicit stage map is defined.  This matches the behaviour in
    ``legacy_adapters._build_adapters_impl``.

    Returns an empty dict if no stage map can be determined.
    """
    # 1. AnalysisConfig.block_native.stage_code_map
    block_native_cfg = getattr(cfg, "block_native", None)
    if block_native_cfg is not None:
        scm = getattr(block_native_cfg, "stage_code_map", None)
        if isinstance(scm, dict) and scm:
            return dict(scm)

    # 2. DatasetConfig.flags.stage_code_map
    flags = getattr(cfg, "flags", None)
    if flags is not None:
        scm = getattr(flags, "stage_code_map", None)
        if isinstance(scm, dict) and scm:
            return dict(scm)
        # 3. sleep_data_contrast fallback (matches legacy_adapters behaviour)
        if getattr(flags, "sleep_data_contrast", False):
            return dict(SLEEP_STAGE_CODE_TO_LABEL)

    # 4. plain dict
    if isinstance(cfg, dict):
        scm = cfg.get("stage_code_map") or cfg.get("block_native", {}).get("stage_code_map") or {}
        if scm:
            return {int(k): str(v) for k, v in scm.items() if str(v).strip()}
        if cfg.get("sleep_data_contrast"):
            return dict(SLEEP_STAGE_CODE_TO_LABEL)

    return {}


def stage_labels_from_manifest(manifest: Dict[str, Any]) -> Dict[int, str]:
    """Infer stage labels from a ``run_manifest.json`` dict.

    Tries the following sources in order:
      1. ``capabilities.stage_code_map`` (if present)
      2. ``block_native_qc.aggregate.block_counts_by_stage`` keys + KNOWN_STAGE_LABELS

    Returns an empty dict if no labels can be reliably inferred — use
    ``KNOWN_STAGE_LABELS[dataset_id]`` directly if you know the dataset.
    """
    caps = manifest.get("capabilities", {})
    # explicit map in manifest
    explicit = caps.get("stage_code_map")
    if isinstance(explicit, dict) and explicit:
        return {int(k): str(v) for k, v in explicit.items() if str(v).strip()}

    # try matching dataset_id against KNOWN_STAGE_LABELS
    dataset_id = str(manifest.get("dataset_id") or "").strip().lower()
    if dataset_id in KNOWN_STAGE_LABELS:
        return dict(KNOWN_STAGE_LABELS[dataset_id])

    return {}


def stage_labels_from_dataset_id(dataset_id: str) -> Dict[int, str]:
    """Return stage labels for a known dataset ID, or empty dict."""
    return dict(KNOWN_STAGE_LABELS.get(dataset_id.strip().lower(), {}))


def qc_mask_from_config(df: pd.DataFrame, cfg: Any) -> pd.Series:
    """Apply QC thresholds from an ``AnalysisConfig.block_native.qc`` object.

    Falls back to ``combined_qc_mask`` defaults when no config is supplied.
    """
    block_native_cfg = getattr(cfg, "block_native", None)
    if block_native_cfg is None:
        return combined_qc_mask(df)
    qc = getattr(block_native_cfg, "qc", None)
    if qc is None:
        return combined_qc_mask(df)
    return combined_qc_mask(
        df,
        require_mnps_finite=bool(getattr(qc, "require_mnps_finite", True)),
        min_anchor_support=float(getattr(qc, "min_anchor_support", 0.3)),
        min_anchor_state_finite=int(getattr(qc, "min_anchor_state_finite", 1)),
    )


ANCHOR_STATE_COLS = [
    "sympathetic_index",
    "vagal_index",
    "vascular_index",
    "pupil_arousal_index",
    "anchor_index",
]

ANCHOR_DOT_COLS = [
    "sympathetic_index_dot",
    "vagal_index_dot",
    "vascular_index_dot",
    "pupil_arousal_index_dot",
    "anchor_index_dot",
]

ANCHOR_QUALITY_COLS = [
    "ecg_quality_quality",
    "ppg_quality_quality",
    "pupil_quality_quality",
    "anchor_support_fraction_quality",
]

HRV_COLS = [
    "ecg_hrv_hr_mean_bpm",
    "ecg_hrv_ibi_mean_ms",
    "ecg_hrv_sdnn_ms",
    "ecg_hrv_rmssd_ms",
    "ecg_hrv_pnn50",
    "ecg_hrv_nn_count",
    "ecg_hrv_artifact_fraction",
    "ecg_hrv_coverage_fraction",
    "ecg_hrv_quality_score",
]

MNPS_COLS = ["m", "d", "e"]
MNPS_DOT_COLS = ["m_dot", "d_dot", "e_dot"]
COORDS_9D_COLS = ["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"]


# ---------------------------------------------------------------------------
# QC / filtering utilities
# ---------------------------------------------------------------------------

def anchor_support_mask(
    df: pd.DataFrame,
    min_support: float = 0.3,
    col: str = "anchor_support_fraction_quality",
) -> pd.Series:
    """Boolean mask: rows where anchor_support_fraction >= min_support.

    Rows where the column is NaN are **included** by default (conservative
    pass-through for subjects where quality was not computed).
    """
    if col not in df.columns:
        return pd.Series(True, index=df.index)
    v = df[col]
    return v.isna() | (v >= min_support)


def anchor_state_finite_mask(df: pd.DataFrame, min_finite: int = 1) -> pd.Series:
    """Boolean mask: rows with at least ``min_finite`` finite anchor state values."""
    available = [c for c in ANCHOR_STATE_COLS if c in df.columns]
    if not available:
        return pd.Series(True, index=df.index)
    finite_count = df[available].notna().sum(axis=1)
    return finite_count >= min_finite


def mnps_finite_mask(df: pd.DataFrame) -> pd.Series:
    """Boolean mask: rows where mnps_finite == 1 (or column absent)."""
    if "mnps_finite" not in df.columns:
        return pd.Series(True, index=df.index)
    return df["mnps_finite"] == 1


def combined_qc_mask(
    df: pd.DataFrame,
    *,
    require_mnps_finite: bool = True,
    min_anchor_support: float = 0.3,
    min_anchor_state_finite: int = 1,
) -> pd.Series:
    """Combine geometry and anchor quality masks into one boolean Series."""
    mask = pd.Series(True, index=df.index)
    if require_mnps_finite:
        mask &= mnps_finite_mask(df)
    mask &= anchor_support_mask(df, min_support=min_anchor_support)
    mask &= anchor_state_finite_mask(df, min_finite=min_anchor_state_finite)
    return mask


# ---------------------------------------------------------------------------
# Subject-centering (within-subject normalization)
# ---------------------------------------------------------------------------

def subject_center(
    df: pd.DataFrame,
    cols: Sequence[str],
    group_col: str = "subject_id",
    suffix: str = "_sc",
) -> pd.DataFrame:
    """Add subject-centered columns (subtract within-subject median).

    Parameters
    ----------
    df:
        Input DataFrame.
    cols:
        Column names to center.
    group_col:
        Column identifying subjects.
    suffix:
        Suffix appended to centered column names.

    Returns
    -------
    DataFrame with new ``{col}{suffix}`` columns added in-place.
    """
    out = df.copy()
    existing = [c for c in cols if c in df.columns]
    if not existing or group_col not in df.columns:
        return out
    medians = out.groupby(group_col)[existing].transform("median")
    for c in existing:
        out[f"{c}{suffix}"] = out[c] - medians[c]
    return out


# ---------------------------------------------------------------------------
# Stage summaries
# ---------------------------------------------------------------------------

@dataclass
class BlockStageSummary:
    """Aggregate statistics for one stage across subjects.

    All statistics are computed over non-NaN values only.
    """

    stage_code: Optional[int]
    stage_label: Optional[str]
    n_subjects: int
    n_blocks: int
    n_windows: int
    mnps_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    anchor_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    hrv_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_flat_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "stage_code": self.stage_code,
            "stage_label": self.stage_label,
            "n_subjects": self.n_subjects,
            "n_blocks": self.n_blocks,
            "n_windows": self.n_windows,
        }
        for group_name, group_stats in [
            ("mnps", self.mnps_stats),
            ("anchor", self.anchor_stats),
            ("hrv", self.hrv_stats),
        ]:
            for col, stats in group_stats.items():
                for stat_name, val in stats.items():
                    out[f"{group_name}_{col}_{stat_name}"] = val
        return out


def _resolve_stage_identity(
    stage_value: Any,
    stage_labels: Dict[int, str],
) -> Tuple[Optional[int], Optional[str]]:
    """Return ``(stage_code, stage_label)`` from a raw stage column value.

    Handles both integer stage codes and string stage labels:

    - Integer (or integer-like float): tries ``stage_labels.get(code, str(code))``
    - String value (e.g. "nrem3", "awake"): passes through as label; ``stage_code=None``
    - NaN / None: returns ``(None, None)``

    This makes ``compute_stage_summaries`` and ``build_run_inventory`` safe to
    call on both block_native sidecars (``stage_code`` int column) and cleaned
    analysis outputs (``condition`` string column).
    """
    try:
        if pd.isna(stage_value):
            return None, None
    except (TypeError, ValueError):
        pass  # pd.isna raises on some non-scalar types

    # try integer code path
    try:
        code = int(float(str(stage_value)))
        label = stage_labels.get(code, str(code))
        return code, label
    except (ValueError, TypeError):
        pass

    # string label path
    label = str(stage_value).strip()
    return None, label if label else None


def _col_stats(series: pd.Series) -> Dict[str, float]:
    finite = series.dropna()
    if len(finite) == 0:
        return {
            "mean": float("nan"),
            "median": float("nan"),
            "std": float("nan"),
            "mad": float("nan"),
            "iqr": float("nan"),
            "n": 0,
        }
    med = float(np.median(finite))
    mad = float(np.median(np.abs(finite - med)))
    q25, q75 = float(np.percentile(finite, 25)), float(np.percentile(finite, 75))
    return {
        "mean": float(np.mean(finite)),
        "median": med,
        "std": float(np.std(finite)),
        "mad": mad,
        "iqr": q75 - q25,
        "n": int(len(finite)),
    }


def compute_stage_summaries(
    df: pd.DataFrame,
    *,
    stage_col: str = "stage_code",
    subject_col: str = "subject_id",
    block_col: str = "block_id",
    stage_labels: Optional[Dict[int, str]] = None,
    mnps_cols: Optional[List[str]] = None,
    anchor_cols: Optional[List[str]] = None,
    hrv_cols: Optional[List[str]] = None,
) -> List[BlockStageSummary]:
    """Compute per-stage summary statistics over block_native windows.

    Parameters
    ----------
    df:
        Block-native DataFrame (all subjects concatenated or single subject).
    stage_col:
        Column identifying stage/condition.
    subject_col:
        Column identifying subjects.
    block_col:
        Column identifying blocks within subjects.
    stage_labels:
        Optional mapping from stage code (int) to label (str).
        When None, the numeric code is used as the label string.
        Use ``stage_labels_from_config()`` or ``DS003838_STAGE_LABELS``
        to supply dataset-specific labels.

    Returns
    -------
    List of :class:`BlockStageSummary`, one per unique stage code.
    """
    if stage_labels is None:
        stage_labels = {}

    mnps_cols = mnps_cols or [c for c in MNPS_COLS if c in df.columns]
    anchor_cols = anchor_cols or [c for c in ANCHOR_STATE_COLS if c in df.columns]
    hrv_cols = hrv_cols or [c for c in HRV_COLS if c in df.columns]

    summaries: List[BlockStageSummary] = []
    stages = sorted(df[stage_col].dropna().unique()) if stage_col in df.columns else []

    for stage in stages:
        subset = df[df[stage_col] == stage]
        n_subjects = subset[subject_col].nunique() if subject_col in df.columns else 0
        n_blocks = (
            subset[[subject_col, block_col]].drop_duplicates().shape[0]
            if block_col in df.columns and subject_col in df.columns
            else len(subset)
        )
        n_windows = len(subset)

        stage_code, stage_label = _resolve_stage_identity(stage, stage_labels)

        mnps_stats = {c: _col_stats(subset[c]) for c in mnps_cols}
        anchor_stats = {c: _col_stats(subset[c]) for c in anchor_cols}
        hrv_stats = {c: _col_stats(subset[c]) for c in hrv_cols}

        summaries.append(
            BlockStageSummary(
                stage_code=stage_code,
                stage_label=stage_label,
                n_subjects=n_subjects,
                n_blocks=n_blocks,
                n_windows=n_windows,
                mnps_stats=mnps_stats,
                anchor_stats=anchor_stats,
                hrv_stats=hrv_stats,
            )
        )

    return summaries


# ---------------------------------------------------------------------------
# Per-subject loaders
# ---------------------------------------------------------------------------

def load_block_native_table(
    subject_dir: str | Path,
    *,
    prefer_parquet: bool = True,
) -> Optional[pd.DataFrame]:
    """Load the block_native_windows table for one subject/task directory.

    Parameters
    ----------
    subject_dir:
        Path to a subject/task directory (e.g. ``sub-032_digit_span/``).
    prefer_parquet:
        Try ``.parquet`` first (faster), fall back to ``.csv``.

    Returns
    -------
    DataFrame or None if no file is found.
    """
    subject_dir = Path(subject_dir)
    candidates: List[Path] = []
    if prefer_parquet:
        candidates = [
            subject_dir / "block_native_windows.parquet",
            subject_dir / "block_native_windows.csv",
        ]
    else:
        candidates = [
            subject_dir / "block_native_windows.csv",
            subject_dir / "block_native_windows.parquet",
        ]

    for path in candidates:
        if path.exists():
            if path.suffix == ".parquet":
                return pd.read_parquet(path)
            else:
                return pd.read_csv(path)
    return None


def load_event_locked_table(
    subject_dir: str | Path,
    *,
    prefer_parquet: bool = True,
) -> Optional[pd.DataFrame]:
    """Load the event_locked table for one subject/task directory.

    Parameters
    ----------
    subject_dir:
        Path to a subject/task directory.
    prefer_parquet:
        Try ``.parquet`` first, fall back to ``.csv``.

    Returns
    -------
    DataFrame or None if no file is found.
    """
    subject_dir = Path(subject_dir)
    candidates: List[Path] = []
    if prefer_parquet:
        candidates = [
            subject_dir / "event_locked.parquet",
            subject_dir / "event_locked.csv",
        ]
    else:
        candidates = [
            subject_dir / "event_locked.csv",
            subject_dir / "event_locked.parquet",
        ]

    for path in candidates:
        if path.exists():
            if path.suffix == ".parquet":
                return pd.read_parquet(path)
            else:
                return pd.read_csv(path)
    return None


def load_subject_summary(subject_dir: str | Path) -> Optional[Dict[str, Any]]:
    """Load ``summary.json`` for one subject/task directory."""
    path = Path(subject_dir) / "summary.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def load_subject_qc_summary(subject_dir: str | Path) -> Optional[Dict[str, Any]]:
    """Load ``qc_summary.json`` for one subject/task directory."""
    path = Path(subject_dir) / "qc_summary.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Run-level loader
# ---------------------------------------------------------------------------

def _is_subject_dir(path: Path) -> bool:
    """Return True if the directory looks like a subject/task output dir."""
    return (
        path.is_dir()
        and (
            (path / "block_native_windows.csv").exists()
            or (path / "block_native_windows.parquet").exists()
            or (path / "summary.json").exists()
        )
    )


def iter_subject_dirs(run_dir: str | Path) -> Iterator[Path]:
    """Yield all subject/task directories under a run directory."""
    run_dir = Path(run_dir)
    for child in sorted(run_dir.iterdir()):
        if _is_subject_dir(child):
            yield child


def load_run_manifest(run_dir: str | Path) -> Optional[Dict[str, Any]]:
    """Load ``run_manifest.json`` from a run directory."""
    path = Path(run_dir) / "run_manifest.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def load_run_block_native_table(
    run_dir: str | Path,
    *,
    prefer_parquet: bool = True,
    apply_qc: bool = False,
    qc_kwargs: Optional[Dict[str, Any]] = None,
    cfg: Any = None,
    max_subjects: Optional[int] = None,
) -> pd.DataFrame:
    """Load and concatenate block_native tables for all subjects in a run.

    Parameters
    ----------
    run_dir:
        Root directory of the MNDM run output.
    prefer_parquet:
        Load parquet sidecars when available (faster than CSV).
    apply_qc:
        If True, apply QC masking to each table before concat.
    qc_kwargs:
        Keyword arguments forwarded to :func:`combined_qc_mask`.
        Ignored when ``cfg`` is provided.
    cfg:
        Optional ``AnalysisConfig`` (or object with ``block_native`` attr).
        When supplied, QC thresholds and ``prefer_parquet`` are read from
        the config; ``qc_kwargs`` is ignored.
    max_subjects:
        Load at most this many subject dirs (useful for quick exploration).

    Returns
    -------
    Concatenated DataFrame with rows from all subjects, or an empty DataFrame
    if no tables were found.
    """
    run_dir = Path(run_dir)

    # resolve prefer_parquet from config
    if cfg is not None:
        block_native_cfg = getattr(cfg, "block_native", None)
        if block_native_cfg is not None:
            prefer_parquet = bool(getattr(block_native_cfg, "prefer_parquet", prefer_parquet))

    qc_kwargs = qc_kwargs or {}
    frames: List[pd.DataFrame] = []

    for i, subject_dir in enumerate(iter_subject_dirs(run_dir)):
        if max_subjects is not None and i >= max_subjects:
            break
        df = load_block_native_table(subject_dir, prefer_parquet=prefer_parquet)
        if df is None or df.empty:
            continue
        if apply_qc:
            mask = qc_mask_from_config(df, cfg) if cfg is not None else combined_qc_mask(df, **qc_kwargs)
            df = df[mask].copy()
        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def load_run_event_locked_table(
    run_dir: str | Path,
    *,
    prefer_parquet: bool = True,
    max_subjects: Optional[int] = None,
) -> pd.DataFrame:
    """Load and concatenate event_locked tables for all subjects in a run.

    Parameters
    ----------
    run_dir:
        Root directory of the MNDM run output.
    prefer_parquet:
        Load parquet sidecars when available.
    max_subjects:
        Load at most this many subject dirs.

    Returns
    -------
    Concatenated DataFrame, or empty DataFrame if none found.
    """
    run_dir = Path(run_dir)
    frames: List[pd.DataFrame] = []

    for i, subject_dir in enumerate(iter_subject_dirs(run_dir)):
        if max_subjects is not None and i >= max_subjects:
            break
        df = load_event_locked_table(subject_dir, prefer_parquet=prefer_parquet)
        if df is None or df.empty:
            continue
        frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Inventory / QC summary
# ---------------------------------------------------------------------------

@dataclass
class RunInventory:
    """QC inventory of anchor and MNPS availability across a run."""

    run_dir: Path
    n_subject_dirs: int
    n_with_block_native: int
    n_with_event_locked: int
    n_with_anchor_state: int
    n_with_hrv: int
    n_windows_total: int
    n_windows_anchor_ok: int
    n_windows_mnps_ok: int
    stage_window_counts: Dict[str, int] = field(default_factory=dict)
    subject_ids: List[str] = field(default_factory=list)

    @property
    def anchor_availability_fraction(self) -> float:
        if self.n_subject_dirs == 0:
            return 0.0
        return self.n_with_anchor_state / self.n_subject_dirs

    @property
    def anchor_window_fraction(self) -> float:
        if self.n_windows_total == 0:
            return 0.0
        return self.n_windows_anchor_ok / self.n_windows_total

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "run_dir": str(self.run_dir),
            "n_subject_dirs": self.n_subject_dirs,
            "n_with_block_native": self.n_with_block_native,
            "n_with_event_locked": self.n_with_event_locked,
            "n_with_anchor_state": self.n_with_anchor_state,
            "n_with_hrv": self.n_with_hrv,
            "n_windows_total": self.n_windows_total,
            "n_windows_anchor_ok": self.n_windows_anchor_ok,
            "n_windows_mnps_ok": self.n_windows_mnps_ok,
            "anchor_availability_fraction": self.anchor_availability_fraction,
            "anchor_window_fraction": self.anchor_window_fraction,
            "stage_window_counts": self.stage_window_counts,
        }


def build_run_inventory(
    run_dir: str | Path,
    *,
    min_anchor_support: float = 0.3,
    stage_col: str = "stage_code",
    stage_labels: Optional[Dict[int, str]] = None,
    cfg: Any = None,
) -> RunInventory:
    """Scan a run directory and report availability of anchor and MNPS surfaces.

    This is the recommended first step before any analysis — use it to confirm
    that the anchor surface is present and passes basic QC thresholds.

    Parameters
    ----------
    run_dir:
        Root directory of the MNDM run output.
    min_anchor_support:
        Minimum ``anchor_support_fraction_quality`` for a window to count
        as "anchor ok". Ignored when ``cfg`` is supplied.
    stage_col:
        Column identifying stage/condition in the block_native table.
    stage_labels:
        Mapping from stage code to label string.  When None, the run manifest
        is probed first; if nothing is found the numeric code is used as-is.
        Pass ``DS003838_STAGE_LABELS`` explicitly for that dataset, or use
        ``stage_labels_from_manifest()`` / ``stage_labels_from_config()``.
    cfg:
        Optional ``AnalysisConfig`` (or any object with a ``block_native``
        attribute). When supplied, QC thresholds and stage labels are read
        from the config.

    Returns
    -------
    :class:`RunInventory`
    """
    run_dir = Path(run_dir)

    # resolve stage labels
    if stage_labels is None and cfg is not None:
        stage_labels = stage_labels_from_config(cfg)
    if stage_labels is None:
        manifest = load_run_manifest(run_dir)
        stage_labels = stage_labels_from_manifest(manifest) if manifest else {}

    # resolve QC threshold
    if cfg is not None:
        block_native_cfg = getattr(cfg, "block_native", None)
        qc_cfg = getattr(block_native_cfg, "qc", None)
        if qc_cfg is not None:
            min_anchor_support = float(getattr(qc_cfg, "min_anchor_support", min_anchor_support))

    n_subject_dirs = 0
    n_with_block_native = 0
    n_with_event_locked = 0
    n_with_anchor_state = 0
    n_with_hrv = 0
    n_windows_total = 0
    n_windows_anchor_ok = 0
    n_windows_mnps_ok = 0
    stage_window_counts: Dict[str, int] = {}
    subject_ids: List[str] = []

    for subject_dir in iter_subject_dirs(run_dir):
        n_subject_dirs += 1

        bn_path_csv = subject_dir / "block_native_windows.csv"
        bn_path_parquet = subject_dir / "block_native_windows.parquet"
        el_path_csv = subject_dir / "event_locked.csv"
        el_path_parquet = subject_dir / "event_locked.parquet"

        has_bn = bn_path_parquet.exists() or bn_path_csv.exists()
        has_el = el_path_parquet.exists() or el_path_csv.exists()

        if has_bn:
            n_with_block_native += 1
        if has_el:
            n_with_event_locked += 1

        df = load_block_native_table(subject_dir)
        if df is None or df.empty:
            continue

        sid = str(df["subject_id"].iloc[0]) if "subject_id" in df.columns else subject_dir.name
        subject_ids.append(sid)

        n_windows_total += len(df)

        anchor_col_present = any(c in df.columns for c in ANCHOR_STATE_COLS)
        if anchor_col_present:
            n_with_anchor_state += 1

        hrv_col_present = any(c in df.columns for c in HRV_COLS)
        if hrv_col_present:
            n_with_hrv += 1

        anchor_mask = anchor_support_mask(df, min_support=min_anchor_support)
        n_windows_anchor_ok += int(anchor_mask.sum())

        mnps_mask = mnps_finite_mask(df)
        n_windows_mnps_ok += int(mnps_mask.sum())

        if stage_col in df.columns:
            for code, count in df[stage_col].value_counts().items():
                _, label = _resolve_stage_identity(code, stage_labels)
                key = label if label is not None else "unknown"
                stage_window_counts[key] = stage_window_counts.get(key, 0) + int(count)

    return RunInventory(
        run_dir=run_dir,
        n_subject_dirs=n_subject_dirs,
        n_with_block_native=n_with_block_native,
        n_with_event_locked=n_with_event_locked,
        n_with_anchor_state=n_with_anchor_state,
        n_with_hrv=n_with_hrv,
        n_windows_total=n_windows_total,
        n_windows_anchor_ok=n_windows_anchor_ok,
        n_windows_mnps_ok=n_windows_mnps_ok,
        stage_window_counts=stage_window_counts,
        subject_ids=sorted(set(subject_ids)),
    )


__all__ = [
    "DS003838_STAGE_LABELS",
    "DS003838_STAGE_CODES",
    "DS006036_STAGE_LABELS",
    "DS006036_STAGE_CODES",
    "SLEEP_STAGE_CODE_TO_LABEL",
    "KNOWN_STAGE_LABELS",
    "stage_labels_from_config",
    "stage_labels_from_manifest",
    "stage_labels_from_dataset_id",
    "qc_mask_from_config",
    "ANCHOR_STATE_COLS",
    "ANCHOR_DOT_COLS",
    "ANCHOR_QUALITY_COLS",
    "HRV_COLS",
    "MNPS_COLS",
    "MNPS_DOT_COLS",
    "COORDS_9D_COLS",
    "anchor_support_mask",
    "anchor_state_finite_mask",
    "mnps_finite_mask",
    "combined_qc_mask",
    "subject_center",
    "BlockStageSummary",
    "compute_stage_summaries",
    "load_block_native_table",
    "load_event_locked_table",
    "load_subject_summary",
    "load_subject_qc_summary",
    "iter_subject_dirs",
    "load_run_manifest",
    "load_run_block_native_table",
    "load_run_event_locked_table",
    "RunInventory",
    "build_run_inventory",
]
