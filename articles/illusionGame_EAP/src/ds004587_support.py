"""Shared, evidence-bounded utilities for the ds004587 illusion-game EAP pipeline.

Set ``NMD_DS004587_ROOT`` to a completed NMD export when it is not located in
one of the documented repository locations.  No loader fabricates missing
columns, conditions, or trial labels.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from scipy import stats
import h5py

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTICLE_DIR = REPO_ROOT / "articles" / "illusionGame_EAP"
RESULTS_DIR = ARTICLE_DIR / "results"
FIGURES_DIR = ARTICLE_DIR / "figures"
DATASET_ID = "ds004587"

REST_LABELS = {"rest", "eyes_closed", "eyes-closed", "ec_rest", "baseline"}
ILLUSION_PATTERNS = ("illusion", "ig", "game", "visual")
MNPS_COLUMNS = ("m", "d", "e", "m_median", "d_median", "e_median")
MNJ_COLUMNS = (
    "frobenius_norm", "rotation_norm", "trace", "spectral_radius",
    "rotational_power", "aci", "mdr", "tube_log_det", "tube_d_eff",
)
ANCHOR_COLUMNS = (
    "anchor_state", "anchor_index", "resp_anchor_index", "resp_regular_index",
    "resp_phase_consistency", "ecg_hrv_rmssd_ms", "ecg_hrv_hr_mean_bpm",
    "resp_rate_bpm", "cardioresp_rsa_amplitude",
)
QC_COLUMNS = (
    "qc_ok_eeg", "qc_ok_ecg", "qc_ok_ecg_hrv", "qc_ok_resp",
    "qc_ok_cardioresp", "qc_ok_ppg", "artifact_fraction", "ppg_quality_score",
)

# ``ppg_quality_score`` is a PPG signal-quality metric, not a physiological
# anchor. It was previously listed in ``ANCHOR_COLUMNS`` and therefore entered
# the EAP inference family; its unadjusted association with geometry
# (e.g. r = -0.34, p = .022 against m in an earlier IG-only screen) reflected
# recording quality, not an anchor-geometry coupling, and must not be reported
# as EAP evidence. It remains available under ``QC_COLUMNS`` for diagnostics.

# Documented, source-level physiology recording gaps confirmed by the phase-0
# BIDS audit (`articles/illusionGame_EAP/handover/20260712_ds004587_phase0_audit.md`,
# "Inclusion / exclusion policy" item 2). These are release-level absences of
# ``*_physio.tsv.gz`` (both IG and rest), not incidental missing values, so
# they are excluded explicitly here rather than relying on a later
# ``dropna()`` to remove them alongside unrelated NaNs.
PHYSIO_EXCLUDED_SUBJECTS: dict[str, str] = {
    "FFE111": "missing IG and rest *_physio.tsv.gz in the canonical BIDS release (phase0 audit 2026-07-12)",
    "FFE116": "missing IG and rest *_physio.tsv.gz in the canonical BIDS release (phase0 audit 2026-07-12)",
}


def candidate_run_roots() -> list[Path]:
    """Return ordered, de-duplicated potential completed-export locations."""
    supplied = os.environ.get("NMD_DS004587_ROOT")
    roots = [
        Path(supplied) if supplied else None,
        REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds004587",
        REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds004587_20260711_235903",
        Path(r"J:\data\raw\neuralmanifolddynamics_ds004587_20260711_235903"),
        Path(r"J:\datasets\processed\openneuro\ds004587"),
        Path(r"M:\datasets\processed\openneuro\ds004587"),
        REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds004587_20260712_111138",
        Path(r"K:\ExternalReceivedDatasets\openneuro\processed_ds004587_full\ds004587"
             r"\neuralmanifolddynamics_ds004587_20260712_111138"),
        Path(r"K:\ExternalReceivedDatasets\openneuro\processed_ds004587_full\ds004587"
             r"\neuralmanifolddynamics_ds004587_20260712_081757"),
    ]
    return list(dict.fromkeys(path for path in roots if path is not None))


def discover_run_root() -> Path:
    """Find an existing export root or raise an actionable error."""
    attempted = candidate_run_roots()
    for root in attempted:
        if root.is_dir() and (any(root.rglob("*.parquet")) or any(root.rglob("*.h5"))):
            return root
    locations = "\n  - ".join(str(path) for path in attempted)
    raise FileNotFoundError(
        "No usable ds004587 NMD export was found (an export must contain at "
        "least one Parquet or HDF5 file). Set NMD_DS004587_ROOT to the completed run "
        "directory, then rerun.\n  - " + locations
    )


def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() == ".tsv":
        return pd.read_csv(path, sep="\t")
    raise ValueError(f"Unsupported table type: {path}")


def discover_tables(root: Path | None = None) -> list[Path]:
    """Discover tabular artifacts, preferring block/window-level exports."""
    root = root or discover_run_root()
    paths = [*root.rglob("*.parquet"), *root.rglob("*.csv"), *root.rglob("*.tsv")]
    if not paths:
        raise FileNotFoundError(f"No tabular artifacts found under {root}")
    priority = ("block_native", "window", "feature", "subject", "summary", "event")
    return sorted(paths, key=lambda p: (min((p.name.lower().find(x) if x in p.name.lower() else 99 for x in priority)), str(p)))


def load_analysis_table(required: Sequence[str] = (), root: Path | None = None) -> tuple[pd.DataFrame, Path]:
    """Load the first artifact containing every required canonical field.

    Canonical fields are resolved conservatively; this function never fills
    missing values or invents condition labels.
    """
    root = root or discover_run_root()
    h5_paths = sorted(root.rglob("*.h5"))
    if h5_paths:
        return load_h5_analysis_table(h5_paths), root

    aliases = {
        "subject_id": ("subject_id", "subject", "participant_id", "sub_id"),
        "condition": ("condition", "task_label", "task_state_label", "state", "task"),
        "m": ("m", "m_median"), "d": ("d", "d_median"), "e": ("e", "e_median"),
        "trial_id": ("trial_id", "trial", "trial_index", "event_id"),
    }
    errors: list[str] = []
    for path in discover_tables(root):
        try:
            frame = _read_table(path)
        except Exception as exc:  # report unreadable candidates, continue discovery
            errors.append(f"{path.name}: {exc}")
            continue
        renamed = {}
        lower = {str(c).lower(): c for c in frame.columns}
        for canonical, options in aliases.items():
            match = next((lower[x] for x in options if x in lower), None)
            if match is not None and match != canonical:
                renamed[match] = canonical
        frame = frame.rename(columns=renamed)
        if all(field in frame.columns for field in required):
            return frame, path
    detail = "; ".join(errors[:3]) or "all readable artifacts lacked the required fields"
    raise ValueError(
        f"No ds004587 artifact provided required fields {list(required)}. "
        f"Discovery detail: {detail}"
    )


def _decode_names(values: np.ndarray) -> list[str]:
    """Decode HDF5 string arrays without changing column identity."""
    return [item.decode() if isinstance(item, bytes) else str(item) for item in values]


def _jacobian_metrics(jacobian: np.ndarray) -> dict[str, np.ndarray]:
    """Return documented scalar MNJ summaries for a [window, 3, 3] tensor."""
    symmetric = (jacobian + np.swapaxes(jacobian, 1, 2)) / 2.0
    antisymmetric = (jacobian - np.swapaxes(jacobian, 1, 2)) / 2.0
    frobenius = np.linalg.norm(jacobian, axis=(1, 2))
    rotation = np.linalg.norm(antisymmetric, axis=(1, 2))
    eigenvalues = np.linalg.eigvals(jacobian)
    return {
        "frobenius_norm": frobenius,
        "rotation_norm": rotation,
        "trace": np.trace(jacobian, axis1=1, axis2=2),
        "spectral_radius": np.max(np.abs(eigenvalues), axis=1),
        "rotational_power": rotation / (frobenius + 1e-12),
        "aci": rotation / (np.linalg.norm(symmetric, axis=(1, 2)) + 1e-12),
        "mdr": np.sum(np.abs(np.diagonal(jacobian, axis1=1, axis2=2)), axis=1) / (frobenius + 1e-12),
    }


def load_h5_analysis_table(h5_paths: Sequence[Path]) -> pd.DataFrame:
    """Build an epoch-level table from native H5 exports.

    This path is intentionally conservative: all rows retain their original
    run identity, while Jacobian metrics are attached only at the exported
    Jacobian centres.  It supports session-level EAP associations but cannot
    create absent rest labels, trial labels, or clock provenance.
    """
    frames: list[pd.DataFrame] = []
    for path in h5_paths:
        match = re.match(r"(sub-[^_]+)_ses-[^_]+_([^_]+(?:_[^_]+)*)_run-([^_]+)$", path.stem)
        if match is None:
            continue
        subject_id, condition, run_id = match.groups()
        with h5py.File(path, "r") as handle:
            if "mnps_3d" not in handle:
                continue
            mnps = np.asarray(handle["mnps_3d"], dtype=float)
            payload: dict[str, np.ndarray | str] = {
                "m": mnps[:, 0], "d": mnps[:, 1], "e": mnps[:, 2],
                "subject_id": subject_id, "condition": condition, "run_id": run_id, "source_h5": str(path),
            }
            if "anchor_state/values" in handle and "anchor_state/names" in handle:
                values = np.asarray(handle["anchor_state/values"], dtype=float)
                for name, value in zip(_decode_names(handle["anchor_state/names"][()]), values.T):
                    payload[name] = value
            if "features_raw/values" in handle and "features_raw/names" in handle:
                values = np.asarray(handle["features_raw/values"], dtype=float)
                for name, value in zip(_decode_names(handle["features_raw/names"][()]), values.T):
                    if name in ANCHOR_COLUMNS or name in QC_COLUMNS:
                        payload.setdefault(name, value)
            frame = pd.DataFrame(payload)
            if "jacobian/J_hat" in handle and "jacobian/centers" in handle:
                jacobian = np.asarray(handle["jacobian/J_hat"], dtype=float)
                centres = np.asarray(handle["jacobian/centers"], dtype=int)
                valid = (centres >= 0) & (centres < len(frame))
                for name, values in _jacobian_metrics(jacobian).items():
                    frame[name] = np.nan
                    frame.loc[centres[valid], name] = values[valid]
            frames.append(frame)
    if not frames:
        raise ValueError("No usable ds004587 HDF5 exports contained /mnps_3d.")
    table = pd.concat(frames, ignore_index=True)
    # ds004587's two pilot participants have split IG recordings.  Retain
    # run-01 only rather than silently pooling unequal run counts into their
    # participant median; a fuller run-level model is a future analysis.
    if (table.run_id == "01").any():
        table = table.loc[table.run_id.eq("01")].copy()
    return table


def classify_condition(value: object) -> str | None:
    """Map an observed label to rest/illusion only when unambiguous."""
    text = str(value).strip().lower()
    if text in REST_LABELS:
        return "rest"
    if any(token in text for token in ILLUSION_PATTERNS):
        return "illusion"
    return None


def require_columns(frame: pd.DataFrame, columns: Iterable[str], context: str) -> list[str]:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{context} requires columns absent from the export: {missing}")
    return list(columns)


def valid_anchor_columns(frame: pd.DataFrame) -> list[str]:
    """Return anchor columns passing minimum coverage and gross-scale checks.

    The scale check is a data-integrity screen, not a physiological threshold:
    a single value more than 1,000 IQRs from zero makes a session summary
    numerically unstable and is excluded pending source-level diagnosis.
    """
    valid: list[str] = []
    for column in ANCHOR_COLUMNS:
        if column not in frame:
            continue
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        if len(values) < 5 or values.nunique() <= 1:
            continue
        iqr = values.quantile(.75) - values.quantile(.25)
        if not np.isfinite(iqr) or iqr <= 0:
            continue
        if values.abs().max() / iqr > 1000:
            continue
        valid.append(column)
    return valid


def apply_documented_physio_exclusions(frame: pd.DataFrame, *, context: str) -> pd.DataFrame:
    """Drop subjects with a documented, source-level physiology recording gap.

    This makes ``PHYSIO_EXCLUDED_SUBJECTS`` an explicit, logged filter for
    physiology-required analyses (anchor validation, EAP coupling), rather
    than an implicit side effect of a later ``dropna()`` call. Geometry-only
    analyses (MNPS/MNJ without anchors) should not call this: those subjects'
    EEG-derived geometry is not affected by the physiology gap.
    """
    if "subject_id" not in frame.columns:
        return frame
    # ``subject_id`` may or may not carry the BIDS "sub-" prefix depending on
    # loader (H5 exports keep it; generic table aliasing may strip it), so
    # match against both forms rather than assuming one convention.
    bare_ids = frame["subject_id"].astype(str).str.removeprefix("sub-")
    excluded_mask = bare_ids.isin(PHYSIO_EXCLUDED_SUBJECTS)
    present = sorted(set(bare_ids[excluded_mask]))
    for subject_id in present:
        print(f"ds004587_support[{context}]: excluding {subject_id} "
              f"({PHYSIO_EXCLUDED_SUBJECTS[subject_id]})")
    if not present:
        return frame
    return frame.loc[~excluded_mask].copy()


def concurrent_subject_condition_medians(
    frame: pd.DataFrame, anchor: str, metric: str, *, extra_columns: Sequence[str] = (),
) -> pd.DataFrame:
    """Per-subject/condition medians of ``anchor`` and ``metric``, time-matched.

    Restricts all columns to the rows where ``metric`` is finite before
    aggregating. For MNPS columns (``m``/``d``/``e``), which are defined at
    every window, this is equivalent to a whole-session median. For MNJ
    (Jacobian-derived) columns, which are only populated at sparse Jacobian
    centres, this ensures the anchor (and any ``extra_columns``, e.g. an HRV
    control) value used is the concurrent value at those same centres rather
    than a whole-session summary that mixes in windows the Jacobian metric
    never described.
    """
    columns = ["subject_id", "condition", anchor, metric, *extra_columns]
    require_columns(frame, columns, "Concurrent median aggregation")
    mask = pd.to_numeric(frame[metric], errors="coerce").notna()
    concurrent = frame.loc[mask, columns]
    return concurrent.groupby(["subject_id", "condition"], dropna=False)[[anchor, metric, *extra_columns]].median().reset_index()


def make_results_subdir(phase: str) -> Path:
    out = RESULTS_DIR / f"{DATASET_ID}_{datetime.now():%Y%m%d}" / phase
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_metadata(out: Path, *, script: str, source: Path, extra: dict | None = None) -> None:
    payload = {
        "dataset": DATASET_ID, "script": script, "generated_at": datetime.now().isoformat(),
        "source_artifact": str(source), "source_exists_at_run": source.exists(),
        "notes": "Outputs are computed from the discovered source artifact; no values are imputed.",
    }
    if extra:
        payload.update(extra)
    (out / "run_metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def bh_fdr(p_values: Sequence[float]) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    valid = np.isfinite(p)
    out = np.full(len(p), np.nan)
    if not valid.any():
        return out
    pv, n = p[valid], valid.sum()
    order = np.argsort(pv)
    adjusted = np.empty(n)
    adjusted[order] = np.minimum.accumulate((pv[order] * n / np.arange(1, n + 1))[::-1])[::-1]
    out[valid] = np.minimum(adjusted, 1.0)
    return out


def paired_wilcoxon(a: pd.Series, b: pd.Series) -> dict:
    paired = pd.DataFrame({"a": a, "b": b}).dropna()
    diff = paired.a - paired.b
    n = len(diff)
    result = {"n_pairs": n, "median_a": paired.a.median(), "median_b": paired.b.median(),
              "median_difference": diff.median(), "wilcoxon_stat": np.nan, "p": np.nan, "cohen_dz": np.nan}
    if n < 5 or np.isclose(diff.std(ddof=1), 0):
        return result
    result["cohen_dz"] = diff.mean() / diff.std(ddof=1)
    try:
        statistic, p_value = stats.wilcoxon(diff, zero_method="wilcox")
        result.update(wilcoxon_stat=float(statistic), p=float(p_value))
    except ValueError:
        pass
    return result


def spearman(x: pd.Series, y: pd.Series) -> dict:
    paired = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(paired) < 5:
        return {"n": len(paired), "spearman_r": np.nan, "p": np.nan}
    r, p = stats.spearmanr(paired.x, paired.y)
    return {"n": len(paired), "spearman_r": float(r), "p": float(p)}


def subject_condition_medians(frame: pd.DataFrame, metrics: Sequence[str]) -> pd.DataFrame:
    require_columns(frame, ("subject_id", "condition"), "Subject-condition aggregation")
    available = [metric for metric in metrics if metric in frame.columns]
    if not available:
        raise ValueError(f"None of the requested metrics are available: {list(metrics)}")
    return frame.groupby(["subject_id", "condition"], dropna=False)[available].median().reset_index()


# Per-trial fields recovered by the LUX photosensor sync
# (`mndm.pipeline.ds004587_lux_sync`, `project/scripts/28_ds004587_lux_trial_sync.py`)
# and folded into the generic ``event_metadata_json`` column by NMD's
# event-locked export (fields outside the standard EventTable schema are
# never dropped, just serialized -- see `event_locked_export.py`).
IG_TRIAL_METADATA_FIELDS = (
    "illusion_strength", "illusion_difference", "type", "correct", "rt",
    "block_number", "trial_number", "qc_ok_event_sync", "within_sync_bracket",
    "stimulus", "subject_id", "run_id",
)
# ``illusion_strength`` carries a small number of extreme sentinel-scale
# outliers (observed up to ~3.3e11 against a typical |value| < 20 range),
# almost certainly a division-by-near-zero artifact in the source
# behavioral log rather than a real illusion magnitude. ``illusion_difference``
# (bounded, [-1.4, 1.4] observed) does not show this pathology and is the
# safer primary continuous illusion-strength proxy; ``illusion_strength`` is
# kept but screened to a generous plausible bound before use.
ILLUSION_STRENGTH_PLAUSIBLE_ABS_MAX = 1000.0


def _parse_event_metadata_json(frame: pd.DataFrame) -> pd.DataFrame:
    """Expand ``event_metadata_json`` into real, typed columns.

    Never invents a value: fields absent from a given row's JSON blob become
    NaN/None, not zero or a default.
    """
    if "event_metadata_json" not in frame.columns:
        return frame
    parsed = frame["event_metadata_json"].apply(
        lambda blob: json.loads(blob) if isinstance(blob, str) and blob.strip() else {}
    )
    expanded = pd.json_normalize(parsed)
    for column in IG_TRIAL_METADATA_FIELDS:
        if column not in expanded.columns:
            continue
        if column in ("qc_ok_event_sync", "within_sync_bracket"):
            expanded[column] = expanded[column].map(
                {"True": True, "True ": True, True: True, "False": False, False: False}
            ).astype("boolean")
        elif column in ("illusion_strength", "illusion_difference", "rt", "block_number"):
            expanded[column] = pd.to_numeric(expanded[column], errors="coerce")
        elif column == "correct":
            expanded[column] = expanded[column].map(
                {"True": True, True: True, "False": False, False: False}
            ).astype("boolean")
    out = frame.reset_index(drop=True).join(expanded.reset_index(drop=True), rsuffix="_meta")
    return out


def discover_event_locked_tables(root: Path | None = None) -> list[Path]:
    """Return every per-run event-locked Parquet export under ``root``."""
    root = root or discover_run_root()
    return sorted(root.rglob("event_locked.parquet"))


def load_event_locked_trial_table(
    root: Path | None = None,
    *,
    event_type: str = "ig_trial",
) -> tuple[pd.DataFrame, list[Path]]:
    """Load and flatten ds004587's per-trial event-locked export.

    Concatenates every discovered ``event_locked.parquet`` (one per
    subject/run), expands ``event_metadata_json`` into real columns
    (``illusion_strength``/``type``/``correct``/``rt``/``block_number``/
    ``trial_number``), and collapses each trial (``event_id``) down to the
    single MNPS window nearest its recovered onset (minimum
    ``abs(rel_time_sec)``).

    Collapsing to one row per trial is necessary, not cosmetic: MNPS windows
    are 8s wide with a 4s step (`config_ingest_common_eeg.yaml`) while IG
    trials occur roughly every 1-3s, so the alignment step (`bins:
    at_trial: [-2, 2]` in `config_ingest_ds004587.yaml`) legitimately
    produces more than one candidate window per trial; without this
    collapse, downstream correlations would double-count some trials against
    the same underlying geometry sample.

    Returns the flattened per-trial frame and the list of source Parquet
    paths actually used (both are required for provenance metadata).
    """
    paths = discover_event_locked_tables(root)
    if not paths:
        raise FileNotFoundError(
            f"No event_locked.parquet files found under {root or discover_run_root()}. "
            "Run `project/scripts/28_ds004587_lux_trial_sync.py` then "
            "`python -m mndm.cli resummarize --dataset ds004587` first."
        )
    frames = []
    for path in paths:
        part = pd.read_parquet(path)
        if "event_type" in part.columns:
            part = part.loc[part["event_type"].astype(str) == event_type]
        if not len(part):
            continue
        part["source_parquet"] = str(path)
        frames.append(part)
    if not frames:
        raise ValueError(
            f"All discovered event_locked.parquet files were empty for event_type='{event_type}' "
            f"(checked {len(paths)} files)."
        )
    frame = pd.concat(frames, ignore_index=True)
    frame = _parse_event_metadata_json(frame)

    required = ["subject_id", "run_id", "event_id", "rel_time_sec", "m", "d", "e"]
    require_columns(frame, required, "Event-locked trial table")

    frame["abs_rel_time_sec"] = frame["rel_time_sec"].abs()
    frame = frame.sort_values("abs_rel_time_sec")
    nearest = frame.groupby(["subject_id", "run_id", "event_id"], as_index=False).first()

    if "illusion_strength" in nearest.columns:
        implausible = nearest["illusion_strength"].abs() > ILLUSION_STRENGTH_PLAUSIBLE_ABS_MAX
        n_implausible = int(implausible.sum())
        if n_implausible:
            print(f"ds004587_support[load_event_locked_trial_table]: masking {n_implausible} "
                  f"implausible illusion_strength values (|value| > {ILLUSION_STRENGTH_PLAUSIBLE_ABS_MAX}) to NaN")
        nearest.loc[implausible, "illusion_strength"] = np.nan

    return nearest, paths
