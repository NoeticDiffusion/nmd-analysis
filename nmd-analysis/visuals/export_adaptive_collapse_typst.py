from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from nmd_analysis.analysis_config import AnalysisConfig, ContrastConfig, load_analysis_config
from nmd_analysis.analysis_pipeline import _build_adaptive_collapse_rows
from nmd_analysis.propofol_depth import annotate_propofol_depth


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANALYSIS_DIR = REPO_ROOT / "data" / "analysis"

METRIC_SPECS: Dict[str, tuple[str, str]] = {
    "ati_reduced": ("C", "ATI"),
    "tube_log_det_median": ("C", "tube_log_det"),
    "tube_d_eff_median": ("C", "tube_d_eff"),
    "tube_rotation_median": ("C", "cone_rhoA"),
    "q_ratio_h4": ("TI", "Q-ratio_H4"),
    "capture_gate": ("TI", "CaptureGate"),
    "mdr_median": ("TI", "MDR"),
    "aci_median": ("P", "ACI"),
    "cfca": ("P", "CFCA"),
}

SPECTRAL_FEATURES = ["eeg_delta", "eeg_alpha", "eeg_beta_alpha"]
GEOMETRIC_FEATURES = ["ati_reduced", "q_ratio_h4", "capture_gate", "aci_median", "cfca", "mdr_median"]
ID_COLUMNS = ["dataset_id", "subject_id", "session", "run", "acq", "group", "condition", "task"]
SPECTRAL_ANALYSIS_PRIORITY = ["features_raw", "features_raw_sleep", "features_robust_z"]
PROPOFOL_CONDITIONS = {"awake", "sedated", "unresponsive", "recovery"}


def _fmt(value: object, digits: int = 3) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not np.isfinite(numeric):
        return "nan"
    return f"{numeric:.{digits}f}"


def _latest_frame_path(analysis_dir: Path, dataset: str, analysis_type: str) -> Path:
    pattern = f"{dataset}_{analysis_type}_*.parquet"
    direct = sorted(analysis_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if direct:
        return direct[0]

    recursive = sorted(analysis_dir.glob(f"**/{pattern}"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not recursive:
        raise FileNotFoundError(f"No analysis file matching {pattern} under {analysis_dir}")

    def _priority(path: Path) -> tuple[int, float]:
        path_text = str(path).lower()
        if "stage_port_full" in path_text:
            return (0, -path.stat().st_mtime)
        if "stage_port_contract" in path_text:
            return (1, -path.stat().st_mtime)
        return (2, -path.stat().st_mtime)

    recursive.sort(key=_priority)
    return recursive[0]


def _latest_frame(analysis_dir: Path, dataset: str, analysis_type: str) -> pd.DataFrame:
    return pd.read_parquet(_latest_frame_path(analysis_dir, dataset, analysis_type))


def _match_selector(frame: pd.DataFrame, selector: Dict[str, object]) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype=bool)
    mask = pd.Series(True, index=frame.index, dtype=bool)
    for key, value in selector.items():
        if key not in frame.columns:
            mask &= False
            continue
        if isinstance(value, list):
            mask &= frame[key].isin(value)
        else:
            mask &= frame[key] == value
    return mask


def _first_metadata_value(series: pd.Series) -> object:
    values = [value for value in series.tolist() if pd.notna(value) and str(value).strip()]
    if not values:
        return None
    if series.name == "condition":
        for value in values:
            if str(value) in PROPOFOL_CONDITIONS:
                return value
    return values[0]


def _load_subject_metrics(analysis_dir: Path, dataset: str, cfg: AnalysisConfig) -> pd.DataFrame:
    frame = _latest_frame(analysis_dir, dataset, "subject_metrics")
    frame = annotate_propofol_depth(frame, dataset=dataset)
    if "adaptive_collapse" not in frame.get("analysis_type", pd.Series(dtype=object)).astype(str).unique():
        derived = _build_adaptive_collapse_rows(frame, cfg)
        if not derived.empty:
            frame = pd.concat([frame, derived], ignore_index=True, sort=False)
            frame = annotate_propofol_depth(frame, dataset=dataset)
    return frame


def _load_contrast_results(analysis_dir: Path, dataset: str) -> pd.DataFrame:
    frame = _latest_frame(analysis_dir, dataset, "contrast_results")
    return annotate_propofol_depth(frame, dataset=dataset)


def _deduplicate_panel_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep one representative row per (contrast_name, metric) pair.

    Reachability metrics such as tube_log_det_median can appear many times
    in contrast_results because the reachability pipeline runs at multiple
    horizon/k configurations.  For paper-facing output we select the row with
    the lowest q_value (most significant); ties are broken by lowest p_value,
    then largest absolute effect_size.
    """
    dedup_key = ["contrast_name", "metric"]
    if not all(col in frame.columns for col in dedup_key):
        return frame
    sort_cols: List[str] = []
    ascending: List[bool] = []
    for col, asc in (("q_value", True), ("p_value", True)):
        if col in frame.columns:
            sort_cols.append(col)
            ascending.append(asc)
    if "effect_size" in frame.columns:
        frame = frame.copy()
        frame["_abs_effect"] = pd.to_numeric(frame["effect_size"], errors="coerce").abs()
        sort_cols.append("_abs_effect")
        ascending.append(False)
    if sort_cols:
        frame = frame.sort_values(sort_cols, ascending=ascending, na_position="last")
    return frame.drop_duplicates(subset=dedup_key, keep="first").drop(columns=["_abs_effect"], errors="ignore")


def _panel_rows(results: pd.DataFrame, config: Sequence[ContrastConfig]) -> List[str]:
    if results.empty:
        return []
    allowed_metrics = set(METRIC_SPECS)
    frame = results[results["metric"].isin(allowed_metrics)].copy()
    if frame.empty:
        return []
    frame = _deduplicate_panel_frame(frame)
    order = {contrast.name: idx for idx, contrast in enumerate(config)}
    frame["contrast_order"] = frame["contrast_name"].map(order).fillna(999).astype(int)
    frame["metric_order"] = frame["metric"].map({name: idx for idx, name in enumerate(METRIC_SPECS)}).fillna(999).astype(int)
    lines: List[str] = []
    for _, row in frame.sort_values(["contrast_order", "metric_order"]).iterrows():
        axis, label = METRIC_SPECS[str(row["metric"])]
        lines.append(
            "    [{0}], [{1}], [{2}], [{3}], [{4}], [{5}], [{6}], [{7}],".format(
                row["contrast_name"],
                axis,
                label,
                int(row.get("n_pairs", 0) or 0),
                _fmt(row.get("effect_estimate")),
                _fmt(row.get("effect_size")),
                _fmt(row.get("p_value")),
                _fmt(row.get("q_value")),
            )
        )
    return lines


def _build_feature_table(
    subject_metrics: pd.DataFrame,
    *,
    cfg: AnalysisConfig,
) -> pd.DataFrame:
    metrics = subject_metrics[subject_metrics["metric_role"] == "signal"].copy()
    metrics = metrics[~metrics["value"].isna()].copy()
    if metrics.empty:
        return pd.DataFrame()
    if "base_feature_name" not in metrics.columns:
        metrics["base_feature_name"] = None

    spectral = pd.DataFrame()
    for analysis_type in SPECTRAL_ANALYSIS_PRIORITY:
        candidate = metrics[
            (metrics["analysis_type"] == analysis_type)
            & (metrics["metric"] == "feature_median")
            & (metrics["base_feature_name"].isin(SPECTRAL_FEATURES))
        ].copy()
        if not candidate.empty:
            spectral = candidate
            break
    geom = metrics[
        (
            ((metrics["analysis_type"] == "adaptive_collapse") & metrics["metric"].isin(["ati_reduced", "q_ratio_h4", "capture_gate", "cfca"]))
            | ((metrics["analysis_type"] == "global_mnps_jacobian_3d") & metrics["metric"].isin(["aci_median", "mdr_median"]))
        )
    ].copy()
    if spectral.empty and geom.empty:
        return pd.DataFrame()

    key_column = "dataset_id" if "dataset_id" in metrics.columns else None
    if key_column is None:
        return pd.DataFrame()

    meta_columns = [column for column in ID_COLUMNS if column in metrics.columns and column != key_column]
    metadata = (
        metrics[[key_column] + meta_columns]
        .groupby(key_column, dropna=False)
        .agg({column: _first_metadata_value for column in meta_columns})
        .reset_index()
    )

    merged = metadata.copy()
    if not spectral.empty:
        spec_wide = spectral.pivot_table(
            index=key_column,
            columns="base_feature_name",
            values="value",
            aggfunc="first",
        ).reset_index()
        merged = merged.merge(spec_wide, on=key_column, how="left")
    if not geom.empty:
        geom_wide = geom.pivot_table(
            index=key_column,
            columns="metric",
            values="value",
            aggfunc="first",
        ).reset_index()
        merged = merged.merge(geom_wide, on=key_column, how="left")
    return merged


def _auc_scores(features: np.ndarray, labels: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=int)
    if len(np.unique(labels)) < 2:
        return float("nan")
    counts = np.bincount(labels)
    if counts.size < 2 or np.min(counts) < 3:
        return float("nan")
    cv = StratifiedKFold(n_splits=min(5, int(np.min(counts))), shuffle=True, random_state=13)
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=500, solver="liblinear")),
        ]
    )
    scores = cross_val_score(model, features, labels, cv=cv, scoring="roc_auc")
    return float(np.mean(scores))


def _mask_with_columns(frame: pd.DataFrame, columns: Sequence[str]) -> np.ndarray:
    if not columns:
        return np.zeros((len(frame),), dtype=bool)
    values = frame[list(columns)].to_numpy(dtype=float)
    return np.isfinite(values).all(axis=1)


def _class_counts(labels: np.ndarray, mask: np.ndarray) -> np.ndarray:
    if labels.size == 0 or not np.any(mask):
        return np.zeros((0,), dtype=int)
    masked = np.asarray(labels, dtype=int)[mask]
    if masked.size == 0:
        return np.zeros((0,), dtype=int)
    return np.bincount(masked)


def _select_geom_cols(contrast_frame: pd.DataFrame, y: np.ndarray, spectral_cols: Sequence[str], geom_cols: Sequence[str]) -> List[str]:
    selected = list(geom_cols)
    if not selected:
        return []
    min_class_n = 3
    while selected:
        mask = _mask_with_columns(contrast_frame, list(spectral_cols) + selected)
        counts = _class_counts(y, mask)
        if counts.size >= 2 and int(np.min(counts)) >= min_class_n:
            return selected
        worst_col = min(
            selected,
            key=lambda column: int(np.isfinite(pd.to_numeric(contrast_frame[column], errors="coerce")).sum()),
        )
        selected.remove(worst_col)
    return []


def _resolve_label_column(feature_table: pd.DataFrame, contrast: ContrastConfig, cfg: AnalysisConfig) -> str | None:
    candidates: List[str] = []
    if cfg.design.condition_column:
        candidates.append(cfg.design.condition_column)
    for key in contrast.left:
        if contrast.left.get(key) != contrast.right.get(key):
            candidates.append(key)
    for fallback in ("condition", "task", "group"):
        candidates.append(fallback)
    seen = set()
    for column in candidates:
        if column in seen:
            continue
        seen.add(column)
        if column not in feature_table.columns:
            continue
        left_value = contrast.left.get(column)
        right_value = contrast.right.get(column)
        if left_value is None or right_value is None or left_value == right_value:
            continue
        if feature_table[column].notna().any():
            return column
    return None


def _incremental_rows(subject_metrics: pd.DataFrame, cfg: AnalysisConfig) -> List[str]:
    feature_table = _build_feature_table(subject_metrics, cfg=cfg)
    if feature_table.empty:
        return []
    rows: List[str] = []
    for contrast in cfg.contrasts:
        subset = feature_table[_match_selector(feature_table, contrast.subset)].copy() if contrast.subset else feature_table.copy()
        if subset.empty:
            continue
        left = subset[_match_selector(subset, contrast.left)].copy()
        right = subset[_match_selector(subset, contrast.right)].copy()
        if left.empty or right.empty:
            continue
        label_col = _resolve_label_column(subset, contrast, cfg)
        if label_col is None:
            continue
        contrast_frame = pd.concat([left, right], ignore_index=True)
        contrast_frame = contrast_frame[contrast_frame[label_col].isin([contrast.left.get(label_col), contrast.right.get(label_col)])].copy()
        if contrast_frame.empty:
            continue
        y = (contrast_frame[label_col] == contrast.right.get(label_col)).astype(int).to_numpy()
        spectral_cols = [column for column in SPECTRAL_FEATURES if column in contrast_frame.columns]
        geom_cols = [column for column in GEOMETRIC_FEATURES if column in contrast_frame.columns]
        if not spectral_cols or not geom_cols:
            continue
        geom_cols = _select_geom_cols(contrast_frame, y, spectral_cols, geom_cols)
        if not geom_cols:
            continue
        base = contrast_frame[spectral_cols].to_numpy(dtype=float)
        full = contrast_frame[spectral_cols + geom_cols].to_numpy(dtype=float)
        # Both AUCs must be evaluated on the same rows so the delta is a fair
        # comparison.  Use the joint mask (intersection of both finitude masks).
        mask_base = np.isfinite(base).all(axis=1)
        mask_full = np.isfinite(full).all(axis=1)
        mask_joint = mask_base & mask_full
        auc_base = _auc_scores(base[mask_joint], y[mask_joint]) if np.any(mask_joint) else float("nan")
        auc_full = _auc_scores(full[mask_joint], y[mask_joint]) if np.any(mask_joint) else float("nan")
        delta = float(auc_full - auc_base) if np.isfinite(auc_base) and np.isfinite(auc_full) else float("nan")
        rows.append(
            "    [{0}], [{1}], [{2}], [{3}], [{4}], [{5}],".format(
                contrast.name,
                int(mask_joint.sum()),
                _fmt(auc_base),
                _fmt(auc_full),
                _fmt(delta),
                ", ".join([column for column in geom_cols]),
            )
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Export adaptive collapse Typst rows from nmd-analysis outputs.")
    parser.add_argument("--table", choices=["panel", "incremental"], required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--analysis-dir", default=str(DEFAULT_ANALYSIS_DIR))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = load_analysis_config(Path(args.config).resolve())
    analysis_dir = Path(args.analysis_dir).resolve()
    out_path = Path(args.out).resolve()

    if args.table == "panel":
        contrast_results = _load_contrast_results(analysis_dir, config.dataset)
        lines = _panel_rows(contrast_results, config.contrasts)
    else:
        subject_metrics = _load_subject_metrics(analysis_dir, config.dataset, config)
        lines = _incremental_rows(subject_metrics, config)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
