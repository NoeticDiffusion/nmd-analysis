from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import sys

import h5py
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

THIS_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = THIS_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from nmd_analysis.analysis_config import load_analysis_config
from nmd_analysis.reachability_cones import (
    ReachabilityConfig,
    _downsample,
    _resolve_time,
    _resolve_x_from_h5,
)
from nmd_analysis.reachability_core import compute_reachability_cones_from_mnps
from nmd_analysis.reachability_typst import latest_analysis_file


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANALYSIS_DIR = REPO_ROOT / "data" / "analysis"
SLEEP_STAGE_CODE_TO_LABEL = {
    0: "awake",
    2: "nrem2",
    3: "nrem3",
    4: "rem",
}


def _fmt(value: object, digits: int = 3) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not np.isfinite(numeric):
        return "nan"
    return f"{numeric:.{digits}f}"


def _rho(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    mask = np.isfinite(left) & np.isfinite(right)
    if int(mask.sum()) < 3:
        return float("nan")
    a = pd.Series(left[mask]).rank(method="average").to_numpy(dtype=float)
    b = pd.Series(right[mask]).rank(method="average").to_numpy(dtype=float)
    if np.std(a) == 0.0 or np.std(b) == 0.0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _dataset_label(dataset: str) -> str:
    return str(dataset).strip()


def _load_reachability_frame(analysis_dir: Path, dataset: str) -> pd.DataFrame:
    candidates = sorted(
        analysis_dir.glob(f"{dataset}_reachability_cones_*.parquet"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        path = latest_analysis_file(analysis_dir, dataset, "reachability_cones")
        candidates = [path]
    last_frame = pd.DataFrame()
    for path in candidates:
        frame = pd.read_parquet(path)
        if not frame.empty:
            frame["dataset"] = _dataset_label(dataset)
            return frame
        last_frame = frame
    last_frame["dataset"] = _dataset_label(dataset)
    return last_frame


def _stage_condition_indices(handle: h5py.File, condition: object, n_samples: int) -> Optional[np.ndarray]:
    if "/labels/stage" not in handle:
        return None
    stage = np.asarray(handle["/labels/stage"][:], dtype=int).reshape(-1)[:n_samples]
    label = str(condition or "").strip().lower()
    for code, stage_label in SLEEP_STAGE_CODE_TO_LABEL.items():
        if stage_label == label:
            idx = np.flatnonzero(stage == int(code))
            return idx if idx.size else None
    return None


def _load_state_series(h5_path: Path, row: pd.Series, cfg: ReachabilityConfig) -> Tuple[np.ndarray, np.ndarray]:
    with h5py.File(h5_path, "r") as handle:
        attrs = dict(handle.attrs.items())
        fs_out = attrs.get("fs_out")
        time_raw = handle["/time"][:] if "/time" in handle else None
        x, _ = _resolve_x_from_h5(handle, cfg.space)
        time = _resolve_time(time_raw, float(fs_out) if isinstance(fs_out, (int, float, np.number)) else None, x.shape[0])
        stage_idx = _stage_condition_indices(handle, row.get("condition"), x.shape[0])
        if stage_idx is not None:
            x = x[stage_idx]
            time = time[stage_idx]
    return _downsample(np.asarray(x, dtype=float), np.asarray(time, dtype=float), int(cfg.max_points))


def _standardize_x(x: np.ndarray, method: str, eps: float) -> np.ndarray:
    method_norm = str(method or "none").strip().lower()
    if method_norm == "none":
        return x
    if method_norm == "robust":
        center = np.nanmedian(x, axis=0)
        scale = np.nanmedian(np.abs(x - center), axis=0)
    else:
        center = np.nanmean(x, axis=0)
        scale = np.nanstd(x, axis=0)
    scale = np.where(np.isfinite(scale) & (scale > 0), scale, 1.0)
    return (x - center) / (scale + float(eps))


def _apply_dim_cap(x: np.ndarray, cap: Optional[int]) -> np.ndarray:
    if cap is None or int(cap) <= 0 or x.shape[1] <= int(cap):
        return x
    pca = PCA(n_components=int(cap), svd_solver="full")
    return pca.fit_transform(x)


def _occupancy_logdet(x: np.ndarray, eps: float = 1e-12) -> float:
    cov = np.cov(x, rowvar=False)
    if cov.ndim == 0:
        cov = np.eye(x.shape[1]) * float(cov)
    cov = cov + np.eye(cov.shape[0]) * float(eps)
    sign, logdet = np.linalg.slogdet(cov)
    if sign <= 0 or not np.isfinite(logdet):
        return float("nan")
    return float(logdet)


def _speed_median(x: np.ndarray, time: np.ndarray) -> float:
    if x.shape[0] < 2:
        return float("nan")
    dt = np.diff(time)
    dt[dt == 0] = np.nan
    dx = np.diff(x, axis=0)
    speed = np.linalg.norm(dx, axis=1) / dt
    return float(np.nanmedian(speed))


def _anisotropy_kappa(x: np.ndarray, eps: float = 1e-12) -> float:
    cov = np.cov(x, rowvar=False)
    if cov.ndim == 0:
        cov = np.eye(x.shape[1]) * float(cov)
    eigvals = np.linalg.eigvalsh(cov + np.eye(cov.shape[0]) * float(eps))
    if eigvals.size == 0:
        return float("nan")
    return float(np.nanmax(eigvals) / (np.nanmin(eigvals) + float(eps)))


def _auc_scores(features: np.ndarray, labels: np.ndarray) -> Tuple[float, float, int]:
    labels = np.asarray(labels)
    if len(np.unique(labels)) < 2:
        return float("nan"), float("nan"), 0
    n_pos = int((labels == 1).sum())
    n_neg = int((labels == 0).sum())
    min_class = min(n_pos, n_neg)
    if min_class < 3:
        return float("nan"), float("nan"), min_class
    n_splits = min(5, min_class)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=13)
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=500, solver="liblinear")),
        ]
    )
    scores = cross_val_score(model, features, labels, cv=cv, scoring="roc_auc")
    return float(np.mean(scores)), float(np.std(scores)), min_class


def _q_ratio_by_h(A_hat: np.ndarray, sigmas: np.ndarray, horizon: int) -> Dict[int, float]:
    values: Dict[int, List[float]] = {h: [] for h in range(1, horizon + 1)}
    if sigmas.ndim != 4:
        return {h: float("nan") for h in range(1, horizon + 1)}
    for window_idx in range(A_hat.shape[0]):
        A = A_hat[window_idx]
        if not np.isfinite(A).all():
            continue
        for horizon_idx in range(1, horizon + 1):
            if horizon_idx >= sigmas.shape[1]:
                break
            sigma_prev = sigmas[window_idx, horizon_idx - 1]
            sigma_now = sigmas[window_idx, horizon_idx]
            if not np.isfinite(sigma_prev).all() or not np.isfinite(sigma_now).all():
                continue
            transport = A @ sigma_prev @ A.T
            delta = sigma_now - transport
            tr_transport = float(np.trace(transport))
            tr_delta = float(np.trace(delta))
            denom = tr_transport + tr_delta
            if np.isfinite(denom) and denom > 0:
                values[horizon_idx].append(float(tr_delta / denom))
    return {h: (float(np.nanmedian(values[h])) if values[h] else float("nan")) for h in range(1, horizon + 1)}


def _build_cfg(args: argparse.Namespace) -> ReachabilityConfig:
    return ReachabilityConfig(
        space=args.space,
        k=int(args.k),
        method=args.method,
        ridge_alpha=float(args.ridge_alpha),
        cv_folds=int(args.cv_folds),
        super_window_size=int(args.super_window_size),
        jitter=float(args.jitter),
        cov_estimator=args.cov_estimator,
        mnps_dim_cap=int(args.mnps_dim_cap) if args.mnps_dim_cap else None,
        eig_floor_scale=float(args.eig_floor_scale),
        standardize=args.standardize,
        standardize_eps=float(args.standardize_eps),
        sigma0_eps=float(args.sigma0_eps),
        horizon=int(args.horizon),
        max_points=int(args.max_points),
        persistence_window=int(args.persistence_window),
        persistence_mode=args.persistence_mode,
        persistence_baseline_quantile=float(args.persistence_baseline_quantile),
        persistence_low_alpha=float(args.persistence_low_alpha),
        persistence_recover_alpha=float(args.persistence_recover_alpha),
        persistence_hysteresis_window=int(args.persistence_hysteresis_window),
        agg=args.agg,
        eps=float(args.eps),
        knn_scope=args.knn_scope,
    )


def _validity_rows(frame: pd.DataFrame) -> List[str]:
    rows: List[str] = []
    for (_, condition), group in frame.groupby(["dataset", "condition"], dropna=False):
        split_log_a = pd.to_numeric(
            group["tube_log_det_split_half_a_median"] if "tube_log_det_split_half_a_median" in group.columns else pd.Series(dtype=float),
            errors="coerce",
        ).to_numpy(dtype=float)
        split_log_b = pd.to_numeric(
            group["tube_log_det_split_half_b_median"] if "tube_log_det_split_half_b_median" in group.columns else pd.Series(dtype=float),
            errors="coerce",
        ).to_numpy(dtype=float)
        split_deff_a = pd.to_numeric(
            group["tube_d_eff_split_half_a_median"] if "tube_d_eff_split_half_a_median" in group.columns else pd.Series(dtype=float),
            errors="coerce",
        ).to_numpy(dtype=float)
        split_deff_b = pd.to_numeric(
            group["tube_d_eff_split_half_b_median"] if "tube_d_eff_split_half_b_median" in group.columns else pd.Series(dtype=float),
            errors="coerce",
        ).to_numpy(dtype=float)
        rho_log_det = _rho(
            split_log_a,
            split_log_b,
        )
        rho_d_eff = _rho(
            split_deff_a,
            split_deff_b,
        )
        rows.append(
            "    [{0}], [{1}], [{2}], [{3}], [{4}], [{5}], [{6}], [{7}], [{8}],".format(
                group["dataset"].iloc[0],
                condition,
                _fmt(pd.to_numeric(group.get("pred_err_h1"), errors="coerce").median()),
                _fmt(pd.to_numeric(group.get("pred_err_h2"), errors="coerce").median()),
                _fmt(pd.to_numeric(group.get("pred_err_h3"), errors="coerce").median()),
                _fmt(pd.to_numeric(group.get("pred_err_h4"), errors="coerce").median()),
                _fmt(rho_log_det),
                _fmt(rho_d_eff),
                _fmt(pd.to_numeric(group.get("near_singular_rate"), errors="coerce").median()),
            )
        )
    return rows


def _incremental_rows(frame: pd.DataFrame, cfg: ReachabilityConfig) -> List[str]:
    baseline_rows: List[Dict[str, object]] = []
    keep_cols = ["dataset", "dataset_id", "subject_id", "group", "condition", "task", "source_h5_path"]
    unique_rows = frame[keep_cols].drop_duplicates().copy()
    for _, row in unique_rows.iterrows():
        h5_path = Path(str(row.get("source_h5_path") or ""))
        if not h5_path.exists():
            continue
        try:
            x, time = _load_state_series(h5_path, row, cfg)
        except Exception:
            continue
        baseline_rows.append(
            {
                "dataset": row.get("dataset"),
                "dataset_id": row.get("dataset_id"),
                "subject_id": row.get("subject_id"),
                "group": row.get("group"),
                "condition": row.get("condition"),
                "task": row.get("task"),
                "occupancy_logdet": _occupancy_logdet(x, eps=cfg.eps),
                "speed_median": _speed_median(x, time),
                "anisotropy_kappa": _anisotropy_kappa(x, eps=cfg.eps),
            }
        )
    baseline = pd.DataFrame(baseline_rows)
    if baseline.empty:
        return []

    merge_keys = [col for col in ["dataset", "dataset_id", "subject_id", "group", "condition", "task"] if col in frame.columns]
    merged = frame.merge(baseline, on=merge_keys, how="inner")
    if merged.empty:
        return []

    if "group" in merged.columns and merged["group"].nunique(dropna=True) > 1:
        label_col = "group"
    elif "condition" in merged.columns and merged["condition"].nunique(dropna=True) > 1:
        label_col = "condition"
    else:
        label_col = "task"

    labels = sorted([value for value in merged[label_col].dropna().unique()])
    rows: List[str] = []
    for idx, left in enumerate(labels):
        for right in labels[idx + 1 :]:
            subset = merged[merged[label_col].isin([left, right])].copy()
            if subset.empty:
                continue
            y = (subset[label_col] == right).astype(int).to_numpy()
            base_feats = subset[["occupancy_logdet", "speed_median", "anisotropy_kappa"]].to_numpy(dtype=float)
            reach_feats = subset[["tube_log_det_median", "tube_d_eff_median"]].to_numpy(dtype=float)
            mask = np.isfinite(base_feats).all(axis=1) & np.isfinite(reach_feats).all(axis=1)
            if not np.any(mask):
                continue
            base_feats = base_feats[mask]
            reach_feats = reach_feats[mask]
            y_masked = y[mask]
            auc_base, _, _ = _auc_scores(base_feats, y_masked)
            auc_full, _, _ = _auc_scores(np.hstack([base_feats, reach_feats]), y_masked)
            delta = float(auc_full - auc_base) if np.isfinite(auc_full) and np.isfinite(auc_base) else float("nan")
            rows.append(
                "    [{0}], [{1}], [{2}], [{3}], [{4}], [{5}],".format(
                    subset["dataset"].iloc[0],
                    f"{left} vs {right}",
                    int(len(y_masked)),
                    _fmt(auc_base),
                    _fmt(auc_full),
                    _fmt(delta),
                )
            )
    return rows


def _q_vs_a_rows(frame: pd.DataFrame, cfg: ReachabilityConfig) -> List[str]:
    rows: List[Dict[str, object]] = []
    keep_cols = ["dataset", "dataset_id", "subject_id", "group", "condition", "task", "source_h5_path"]
    unique_rows = frame[keep_cols].drop_duplicates().copy()
    for _, row in unique_rows.iterrows():
        h5_path = Path(str(row.get("source_h5_path") or ""))
        if not h5_path.exists():
            continue
        try:
            x, time = _load_state_series(h5_path, row, cfg)
        except Exception:
            continue
        x = _apply_dim_cap(_standardize_x(x, cfg.standardize, cfg.standardize_eps), cfg.mnps_dim_cap)
        if x.shape[0] < 2:
            continue
        try:
            results = compute_reachability_cones_from_mnps(
                x=x,
                time=time,
                k=cfg.k,
                super_window_size=cfg.super_window_size,
                method=cfg.method,
                alpha_grid=[cfg.ridge_alpha],
                cv_folds=cfg.cv_folds,
                horizon=cfg.horizon,
                sigma0=max(float(cfg.sigma0_eps), float(cfg.jitter)),
                jitter=cfg.jitter,
                agg=cfg.agg,
                cov_estimator=cfg.cov_estimator,
                eig_floor_scale=cfg.eig_floor_scale,
                persistence_window=cfg.persistence_window,
                persistence_mode=cfg.persistence_mode,
                persistence_baseline_quantile=cfg.persistence_baseline_quantile,
                persistence_low_alpha=cfg.persistence_low_alpha,
                persistence_recover_alpha=cfg.persistence_recover_alpha,
                persistence_hysteresis_window=cfg.persistence_hysteresis_window,
                eps=cfg.eps,
                knn_scope=cfg.knn_scope,
            )
        except Exception:
            continue
        ratios = _q_ratio_by_h(results["A_hat"], results["sigmas"], int(cfg.horizon))
        row_out: Dict[str, object] = {
            "dataset": row.get("dataset"),
            "condition": row.get("condition"),
        }
        for horizon_idx in range(1, int(cfg.horizon) + 1):
            row_out[f"q_ratio_h{horizon_idx}_median"] = ratios.get(horizon_idx, float("nan"))
        rows.append(row_out)

    if not rows:
        return []
    summary = pd.DataFrame(rows).groupby(["dataset", "condition"], dropna=False).median(numeric_only=True).reset_index()
    output: List[str] = []
    for _, row in summary.sort_values(["dataset", "condition"]).iterrows():
        output.append(
            "    [{0}], [{1}], [{2}], [{3}], [{4}], [{5}],".format(
                row["dataset"],
                row["condition"],
                _fmt(row.get("q_ratio_h1_median")),
                _fmt(row.get("q_ratio_h2_median")),
                _fmt(row.get("q_ratio_h3_median")),
                _fmt(row.get("q_ratio_h4_median")),
            )
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Export reachability control tables from nmd-analysis data.")
    parser.add_argument("--table", choices=["validity", "incremental", "q_vs_a"], required=True)
    parser.add_argument("--config", required=True, help="Path to analysis YAML for the dataset.")
    parser.add_argument("--analysis-dir", default=str(DEFAULT_ANALYSIS_DIR), help="Directory containing analysis parquet outputs.")
    parser.add_argument("--out", required=True, help="Output text file with Typst rows.")
    parser.add_argument("--space", default="v2")
    parser.add_argument("--k", type=int, default=25)
    parser.add_argument("--method", default="ridge")
    parser.add_argument("--ridge-alpha", type=float, default=1e-3)
    parser.add_argument("--cv-folds", type=int, default=5)
    parser.add_argument("--super-window-size", type=int, default=3)
    parser.add_argument("--jitter", type=float, default=1e-6)
    parser.add_argument("--cov-estimator", default="empirical")
    parser.add_argument("--mnps-dim-cap", type=int, default=0)
    parser.add_argument("--eig-floor-scale", type=float, default=0.0)
    parser.add_argument("--standardize", default="none")
    parser.add_argument("--standardize-eps", type=float, default=1e-6)
    parser.add_argument("--sigma0-eps", type=float, default=0.0)
    parser.add_argument("--horizon", type=int, default=4)
    parser.add_argument("--max-points", type=int, default=500)
    parser.add_argument("--persistence-window", type=int, default=11)
    parser.add_argument("--persistence-mode", default="all")
    parser.add_argument("--persistence-baseline-quantile", type=float, default=0.5)
    parser.add_argument("--persistence-low-alpha", type=float, default=0.8)
    parser.add_argument("--persistence-recover-alpha", type=float, default=0.9)
    parser.add_argument("--persistence-hysteresis-window", type=int, default=11)
    parser.add_argument("--agg", default="median")
    parser.add_argument("--eps", type=float, default=1e-12)
    parser.add_argument("--knn-scope", default="all")
    args = parser.parse_args()

    config = load_analysis_config(Path(args.config).resolve())
    analysis_dir = Path(args.analysis_dir).resolve()
    output_path = Path(args.out).resolve()
    frame = _load_reachability_frame(analysis_dir, config.dataset)
    cfg = _build_cfg(args)

    if args.table == "validity":
        lines = _validity_rows(frame)
    elif args.table == "incremental":
        lines = _incremental_rows(frame, cfg)
    else:
        lines = _q_vs_a_rows(frame, cfg)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
