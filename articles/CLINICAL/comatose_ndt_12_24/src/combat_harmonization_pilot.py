from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import h5py
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from incremental_validity_analysis import compute_metrics, summarize_scores


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE_ROOT = (
    ARTICLE_DIR.parents[2] / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub"
)
DEFAULT_COMBAT_ROOT = (
    ARTICLE_DIR.parents[2]
    / "data"
    / "raw"
    / "neuralmanifolddynamics_physionet_icare_2_1_20260526_164042_part1_ComBat"
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "NeuroCombat_harmonization" / "results" / "combat_pilot_20260527"
DEFAULT_RANDOM_STATE = 20260527
DEFAULT_N_SPLITS = 5
DEFAULT_N_REPEATS = 20
OUTCOME_FEATURE_SETS = {
    "raw_features": "raw__",
    "dynamics_metrics": "dyn__",
    "raw_plus_dynamics": None,
}
SITE_FEATURE_SETS = OUTCOME_FEATURE_SETS
DYNAMICS_COLUMNS = ("dyn__mnps_rms", "dyn__mnps_speed", "dyn__mnj_fro", "dyn__mnjdot_fro")


@dataclass(frozen=True)
class Config:
    baseline_root: Path
    combat_root: Path
    output_dir: Path
    limit_runs: int | None
    n_splits: int
    n_repeats: int
    random_state: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Run a focused ComBat-vs-baseline pilot on paired I-CARE part1 H5 exports."
    )
    parser.add_argument("--baseline-root", type=Path, default=DEFAULT_BASELINE_ROOT)
    parser.add_argument("--combat-root", type=Path, default=DEFAULT_COMBAT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit-runs", type=int, default=None)
    parser.add_argument("--n-splits", type=int, default=DEFAULT_N_SPLITS)
    parser.add_argument("--n-repeats", type=int, default=DEFAULT_N_REPEATS)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    args = parser.parse_args()
    return Config(
        baseline_root=args.baseline_root,
        combat_root=args.combat_root,
        output_dir=args.output_dir,
        limit_runs=args.limit_runs,
        n_splits=args.n_splits,
        n_repeats=args.n_repeats,
        random_state=args.random_state,
    )


def decode_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.bytes_):
        return bytes(value).decode("utf-8")
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return decode_text(value.item())
        return json.dumps([decode_text(item) for item in value.tolist()], ensure_ascii=True)
    return str(value)


def read_json_dataset(group: h5py.Group, key: str) -> dict[str, Any]:
    if key not in group:
        return {}
    text = decode_text(group[key][()])
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def finite_median(values: np.ndarray, axis: int = 0) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return np.empty((0,), dtype=float)
    with np.errstate(all="ignore"):
        return np.nanmedian(arr, axis=axis)


def finite_mean(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return float("nan")
    with np.errstate(all="ignore"):
        return float(np.nanmean(arr))


def sanitize_feature_name(name: str) -> str:
    keep = []
    for char in name:
        keep.append(char if char.isalnum() or char == "_" else "_")
    sanitized = "".join(keep).strip("_")
    return sanitized or "unnamed_feature"


def parse_bool_like(value: Any) -> float:
    text = str(value).strip().lower()
    mapping = {"true": 1.0, "false": 0.0, "1": 1.0, "0": 0.0, "yes": 1.0, "no": 0.0}
    return float(mapping[text]) if text in mapping else float("nan")


def choose_h5_path(run_dir: Path) -> Path:
    preferred = run_dir / f"{run_dir.name}.h5"
    if preferred.exists():
        return preferred
    candidates = sorted(run_dir.glob("*.h5"))
    if not candidates:
        raise FileNotFoundError(f"No H5 found under {run_dir}")
    return candidates[0]


def iter_common_run_dirs(baseline_root: Path, combat_root: Path) -> Iterable[tuple[str, Path, Path]]:
    baseline_dirs = {path.name: path for path in baseline_root.iterdir() if path.is_dir()}
    combat_dirs = {path.name: path for path in combat_root.iterdir() if path.is_dir()}
    for run_key in sorted(set(baseline_dirs) & set(combat_dirs)):
        yield run_key, baseline_dirs[run_key], combat_dirs[run_key]


def summarize_run(h5_path: Path) -> dict[str, Any]:
    with h5py.File(h5_path, "r") as h5:
        participant = read_json_dataset(h5["participant"], "row_json") if "participant" in h5 else {}
        raw_names = (
            [decode_text(item) or f"feature_{idx}" for idx, item in enumerate(np.asarray(h5["features_raw"]["names"]))]
            if "features_raw" in h5 and "names" in h5["features_raw"]
            else []
        )
        raw_values = (
            np.asarray(h5["features_raw"]["values"], dtype=float)
            if "features_raw" in h5 and "values" in h5["features_raw"]
            else np.empty((0, 0), dtype=float)
        )
        mnps = np.asarray(h5["mnps_3d"], dtype=float) if "mnps_3d" in h5 else np.empty((0, 0), dtype=float)
        mnps_dot = np.asarray(h5["mnps_3d_dot"], dtype=float) if "mnps_3d_dot" in h5 else np.empty((0, 0), dtype=float)
        jacobian = (
            np.asarray(h5["jacobian"]["J_hat"], dtype=float)
            if "jacobian" in h5 and "J_hat" in h5["jacobian"]
            else np.empty((0, 0, 0), dtype=float)
        )
        jacobian_dot = (
            np.asarray(h5["jacobian"]["J_dot"], dtype=float)
            if "jacobian" in h5 and "J_dot" in h5["jacobian"]
            else np.empty((0, 0, 0), dtype=float)
        )

    row: Dict[str, Any] = {
        "subject": str(participant.get("participant_id") or ""),
        "hospital": str(participant.get("hospital") or "missing"),
        "outcome": str(participant.get("outcome") or ""),
        "cpc": pd.to_numeric(pd.Series([participant.get("cpc")]), errors="coerce").iloc[0],
        "age": pd.to_numeric(pd.Series([participant.get("age")]), errors="coerce").iloc[0],
        "sex": str(participant.get("sex") or ""),
        "ohca": parse_bool_like(participant.get("ohca")),
        "shockable_rhythm": parse_bool_like(participant.get("shockable_rhythm")),
        "ttm_celsius": pd.to_numeric(pd.Series([participant.get("ttm")]), errors="coerce").iloc[0],
        "rosc_minutes": pd.to_numeric(pd.Series([participant.get("rosc")]), errors="coerce").iloc[0],
        "n_feature_windows": int(raw_values.shape[0]),
        "n_feature_columns": int(raw_values.shape[1]) if raw_values.ndim == 2 else 0,
        "dyn__mnps_rms": float(np.sqrt(np.nanmean(np.square(mnps)))) if mnps.size else float("nan"),
        "dyn__mnps_speed": finite_mean(np.linalg.norm(mnps_dot, axis=1)) if mnps_dot.size else float("nan"),
        "dyn__mnj_fro": finite_mean(np.linalg.norm(jacobian, axis=(1, 2))) if jacobian.size else float("nan"),
        "dyn__mnjdot_fro": finite_mean(np.linalg.norm(jacobian_dot, axis=(1, 2))) if jacobian_dot.size else float("nan"),
    }
    if raw_names and raw_values.ndim == 2 and raw_values.shape[1] == len(raw_names):
        raw_medians = finite_median(raw_values, axis=0)
        for name, value in zip(raw_names, raw_medians):
            row[f"raw__{sanitize_feature_name(name)}"] = float(value) if np.isfinite(value) else float("nan")
    return row


def build_condition_frames(config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    condition_rows: List[Dict[str, Any]] = []
    pair_rows: List[Dict[str, Any]] = []
    skipped_missing_h5 = 0
    skipped_read_errors = 0

    common_dirs = list(iter_common_run_dirs(config.baseline_root, config.combat_root))
    if config.limit_runs is not None:
        limit = max(int(config.limit_runs), 0)
        if limit and len(common_dirs) > limit:
            rng = np.random.default_rng(config.random_state)
            selected = np.sort(rng.choice(len(common_dirs), size=limit, replace=False))
            common_dirs = [common_dirs[int(idx)] for idx in selected]
        elif limit == 0:
            common_dirs = []
    print(f"Found {len(common_dirs)} common run directories.")
    for idx, (run_key, baseline_dir, combat_dir) in enumerate(common_dirs, start=1):
        try:
            baseline_h5 = choose_h5_path(baseline_dir)
            combat_h5 = choose_h5_path(combat_dir)
        except FileNotFoundError:
            skipped_missing_h5 += 1
            continue
        try:
            baseline_row = summarize_run(baseline_h5)
            combat_row = summarize_run(combat_h5)
        except Exception:
            skipped_read_errors += 1
            continue

        baseline_row.update({"condition": "baseline", "run_key": run_key})
        combat_row.update({"condition": "combat", "run_key": run_key})
        condition_rows.extend([baseline_row, combat_row])

        pair_row: Dict[str, Any] = {
            "run_key": run_key,
            "subject": combat_row["subject"] or baseline_row["subject"],
            "hospital": combat_row["hospital"] or baseline_row["hospital"],
            "outcome": combat_row["outcome"] or baseline_row["outcome"],
            "cpc": combat_row["cpc"] if pd.notna(combat_row["cpc"]) else baseline_row["cpc"],
        }
        for metric in DYNAMICS_COLUMNS:
            before = pd.to_numeric(pd.Series([baseline_row.get(metric)]), errors="coerce").iloc[0]
            after = pd.to_numeric(pd.Series([combat_row.get(metric)]), errors="coerce").iloc[0]
            pair_row[f"baseline__{metric}"] = before
            pair_row[f"combat__{metric}"] = after
            if np.isfinite(before) and abs(before) > 1e-12 and np.isfinite(after):
                pair_row[f"delta_pct__{metric}"] = float(100.0 * (after - before) / abs(before))
            else:
                pair_row[f"delta_pct__{metric}"] = float("nan")
        pair_rows.append(pair_row)

        if idx % 250 == 0 or idx == len(common_dirs):
            print(f"Read {idx}/{len(common_dirs)} paired runs.")
    print(f"Skipped {skipped_missing_h5} runs with missing H5 and {skipped_read_errors} runs with read errors.")

    condition_frame = pd.DataFrame(condition_rows).sort_values(["condition", "subject", "run_key"]).reset_index(drop=True)
    pair_frame = pd.DataFrame(pair_rows).sort_values(["subject", "run_key"]).reset_index(drop=True)
    return condition_frame, pair_frame


def build_subject_frame(condition_frame: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        column
        for column in condition_frame.columns
        if column
        not in {
            "condition",
            "run_key",
            "subject",
            "hospital",
            "outcome",
            "sex",
        }
    ]
    rows: List[Dict[str, Any]] = []
    for (condition, subject), group in condition_frame.groupby(["condition", "subject"], sort=True):
        row: Dict[str, Any] = {
            "condition": condition,
            "subject": subject,
            "hospital": group["hospital"].dropna().astype(str).iloc[0] if group["hospital"].notna().any() else "missing",
            "outcome": group["outcome"].dropna().astype(str).iloc[0] if group["outcome"].notna().any() else "",
            "sex": group["sex"].dropna().astype(str).iloc[0] if group["sex"].notna().any() else "",
            "n_runs": int(len(group)),
        }
        row["cpc"] = pd.to_numeric(group["cpc"], errors="coerce").dropna().iloc[0] if pd.to_numeric(group["cpc"], errors="coerce").notna().any() else np.nan
        for column in numeric_columns:
            values = pd.to_numeric(group[column], errors="coerce").dropna().to_numpy(dtype=float)
            row[column] = float(np.median(values)) if values.size else np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["condition", "subject"]).reset_index(drop=True)


def get_feature_columns(frame: pd.DataFrame, prefix: str | None) -> List[str]:
    if prefix is None:
        columns = [column for column in frame.columns if column.startswith("raw__") or column.startswith("dyn__")]
    else:
        columns = [column for column in frame.columns if column.startswith(prefix)]
    active = []
    for column in columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        finite = values[np.isfinite(values)]
        if finite.empty:
            continue
        if finite.nunique(dropna=True) < 2:
            continue
        active.append(column)
    return sorted(active)


def make_binary_classifier(random_state: int) -> Pipeline:
    return Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    solver="liblinear",
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=random_state,
                ),
            ),
        ]
    )


def make_multiclass_classifier(random_state: int) -> Pipeline:
    return Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    solver="lbfgs",
                    class_weight="balanced",
                    max_iter=3000,
                    random_state=random_state,
                ),
            ),
        ]
    )


def resolve_multiclass_split_count(labels: Sequence[str], requested_splits: int) -> int:
    counts = pd.Series(labels).value_counts()
    if counts.empty or counts.min() < 2:
        raise ValueError("Need at least two samples in each site class for repeated CV.")
    return int(min(requested_splits, counts.min()))


def resolve_binary_split_count(labels: Sequence[int], requested_splits: int) -> int:
    counts = pd.Series(labels).value_counts()
    if counts.empty or counts.min() < 2:
        raise ValueError("Need at least two samples in each outcome class for repeated CV.")
    return int(min(requested_splits, counts.min()))


def evaluate_outcome_models(subject_frame: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: List[Dict[str, Any]] = []
    keep = subject_frame[subject_frame["cpc"].isin([1, 5])].copy()
    keep["label"] = np.where(keep["cpc"] == 1, 1, 0)

    for condition, group in keep.groupby("condition", sort=False):
        y = group["label"].astype(int).to_numpy()
        groups = group["hospital"].fillna("missing").astype(str).to_numpy()
        for model_name, prefix in OUTCOME_FEATURE_SETS.items():
            columns = get_feature_columns(group, prefix)
            if not columns:
                continue
            try:
                n_splits = resolve_binary_split_count(y, config.n_splits)
            except ValueError:
                continue
            folds = RepeatedStratifiedKFold(
                n_splits=n_splits,
                n_repeats=config.n_repeats,
                random_state=config.random_state,
            )
            x = group[columns]
            for fold_idx, (train_idx, test_idx) in enumerate(folds.split(x, y)):
                model = make_binary_classifier(config.random_state)
                model.fit(x.iloc[train_idx], y[train_idx])
                y_prob = model.predict_proba(x.iloc[test_idx])[:, 1]
                rows.append(
                    {
                        "condition": condition,
                        "evaluation": "repeated_stratified_cv",
                        "model": model_name,
                        "fold": fold_idx,
                        "n_train": int(len(train_idx)),
                        "n_test": int(len(test_idx)),
                        "n_features": int(len(columns)),
                        **compute_metrics(y[test_idx], y_prob),
                    }
                )

            splitter = LeaveOneGroupOut()
            for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(x, y, groups)):
                if len(np.unique(y[train_idx])) < 2 or len(np.unique(y[test_idx])) < 2:
                    continue
                model = make_binary_classifier(config.random_state)
                model.fit(x.iloc[train_idx], y[train_idx])
                y_prob = model.predict_proba(x.iloc[test_idx])[:, 1]
                rows.append(
                    {
                        "condition": condition,
                        "evaluation": "leave_one_site_out",
                        "model": model_name,
                        "fold": fold_idx,
                        "held_out_site": pd.Series(groups[test_idx]).mode().iloc[0],
                        "n_train": int(len(train_idx)),
                        "n_test": int(len(test_idx)),
                        "n_features": int(len(columns)),
                        **compute_metrics(y[test_idx], y_prob),
                    }
                )
    scores = pd.DataFrame(rows)
    summary_frames = []
    for condition, group in scores.groupby("condition", sort=False):
        summary = summarize_scores(group.drop(columns=["condition"]).copy())
        summary.insert(0, "condition", condition)
        summary_frames.append(summary)
    summary_frame = pd.concat(summary_frames, ignore_index=True) if summary_frames else pd.DataFrame()
    return scores, summary_frame


def summarize_site_scores(scores: pd.DataFrame) -> pd.DataFrame:
    if scores.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for (condition, model), group in scores.groupby(["condition", "model"], sort=False):
        row: Dict[str, Any] = {
            "condition": condition,
            "model": model,
            "n_folds": int(len(group)),
            "n_features_median": int(group["n_features"].median()),
            "chance_accuracy_mean": float(group["chance_accuracy"].mean()),
        }
        for metric in ("accuracy", "balanced_accuracy", "macro_f1"):
            values = pd.to_numeric(group[metric], errors="coerce").to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_sd"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def evaluate_site_models(subject_frame: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: List[Dict[str, Any]] = []
    for condition, group in subject_frame.groupby("condition", sort=False):
        y = group["hospital"].fillna("missing").astype(str).to_numpy()
        chance_accuracy = float(pd.Series(y).value_counts(normalize=True).max())
        for model_name, prefix in SITE_FEATURE_SETS.items():
            columns = get_feature_columns(group, prefix)
            if not columns:
                continue
            try:
                n_splits = resolve_multiclass_split_count(y, config.n_splits)
            except ValueError:
                continue
            folds = RepeatedStratifiedKFold(
                n_splits=n_splits,
                n_repeats=config.n_repeats,
                random_state=config.random_state,
            )
            x = group[columns]
            for fold_idx, (train_idx, test_idx) in enumerate(folds.split(x, y)):
                model = make_multiclass_classifier(config.random_state)
                model.fit(x.iloc[train_idx], y[train_idx])
                y_hat = model.predict(x.iloc[test_idx])
                rows.append(
                    {
                        "condition": condition,
                        "evaluation": "repeated_stratified_cv",
                        "model": model_name,
                        "fold": fold_idx,
                        "n_train": int(len(train_idx)),
                        "n_test": int(len(test_idx)),
                        "n_features": int(len(columns)),
                        "chance_accuracy": chance_accuracy,
                        "accuracy": float(accuracy_score(y[test_idx], y_hat)),
                        "balanced_accuracy": float(balanced_accuracy_score(y[test_idx], y_hat)),
                        "macro_f1": float(f1_score(y[test_idx], y_hat, average="macro", zero_division=0)),
                    }
                )
    scores = pd.DataFrame(rows)
    return scores, summarize_site_scores(scores)


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    if p.size == 0:
        return np.empty((0,), dtype=float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.empty_like(ranked)
    n = len(ranked)
    running = 1.0
    for idx in range(n - 1, -1, -1):
        rank = idx + 1
        running = min(running, ranked[idx] * n / rank)
        adjusted[idx] = running
    q = np.empty_like(adjusted)
    q[order] = adjusted
    return q


def eta_squared_by_group(values: np.ndarray, groups: Sequence[str]) -> float:
    frame = pd.DataFrame({"value": values, "group": groups}).dropna()
    if frame.empty or frame["group"].nunique() < 2 or frame["value"].nunique() < 2:
        return float("nan")
    grand_mean = float(frame["value"].mean())
    ss_total = float(np.sum(np.square(frame["value"] - grand_mean)))
    if ss_total <= 0:
        return float("nan")
    ss_between = 0.0
    for _, group in frame.groupby("group"):
        ss_between += float(len(group) * np.square(group["value"].mean() - grand_mean))
    return float(ss_between / ss_total)


def summarize_site_dependence(subject_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_rows: List[Dict[str, Any]] = []
    summary_rows: List[Dict[str, Any]] = []
    for condition, group in subject_frame.groupby("condition", sort=False):
        hospitals = group["hospital"].fillna("missing").astype(str)
        for set_name, prefix in SITE_FEATURE_SETS.items():
            columns = get_feature_columns(group, prefix)
            local_rows: List[Dict[str, Any]] = []
            p_values = []
            for column in columns:
                values = pd.to_numeric(group[column], errors="coerce")
                frame = pd.DataFrame({"value": values, "hospital": hospitals}).dropna()
                if frame["hospital"].nunique() < 2 or frame["value"].nunique() < 2:
                    continue
                grouped = [sub["value"].to_numpy(dtype=float) for _, sub in frame.groupby("hospital", sort=True)]
                kw = stats.kruskal(*grouped)
                eta2 = eta_squared_by_group(frame["value"].to_numpy(dtype=float), frame["hospital"].to_numpy())
                local_rows.append(
                    {
                        "condition": condition,
                        "feature_set": set_name,
                        "feature": column,
                        "eta_squared": eta2,
                        "kruskal_h": float(kw.statistic),
                        "kruskal_p": float(kw.pvalue),
                    }
                )
                p_values.append(float(kw.pvalue))
            if not local_rows:
                continue
            q_values = benjamini_hochberg(np.asarray(p_values, dtype=float))
            for row, q_value in zip(local_rows, q_values):
                row["kruskal_q"] = float(q_value)
            feature_rows.extend(local_rows)
            eta_values = np.asarray([row["eta_squared"] for row in local_rows], dtype=float)
            summary_rows.append(
                {
                    "condition": condition,
                    "feature_set": set_name,
                    "n_features_tested": int(len(local_rows)),
                    "eta_squared_median": float(np.nanmedian(eta_values)),
                    "eta_squared_p95": float(np.nanquantile(eta_values, 0.95)),
                    "eta_squared_max": float(np.nanmax(eta_values)),
                    "kruskal_q_lt_0_05": int(sum(row["kruskal_q"] < 0.05 for row in local_rows)),
                }
            )
    return pd.DataFrame(feature_rows), pd.DataFrame(summary_rows)


def summarize_paired_dynamics(pair_frame: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for metric in DYNAMICS_COLUMNS:
        delta = pd.to_numeric(pair_frame[f"delta_pct__{metric}"], errors="coerce").dropna().to_numpy(dtype=float)
        rows.append(
            {
                "metric": metric,
                "n_pairs": int(delta.size),
                "median_pct_change": float(np.median(delta)) if delta.size else float("nan"),
                "p95_abs_pct_change": float(np.quantile(np.abs(delta), 0.95)) if delta.size else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def extract_key_rows(frame: pd.DataFrame, *, condition: str, evaluation: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    return frame[(frame["condition"] == condition) & (frame["evaluation"] == evaluation)].copy()


def format_outcome_line(summary: pd.DataFrame, condition: str, model: str, evaluation: str) -> str:
    row = summary[
        (summary["condition"] == condition) & (summary["model"] == model) & (summary["evaluation"] == evaluation)
    ]
    if row.empty:
        return f"- `{condition}` / `{model}` / `{evaluation}`: no valid folds."
    item = row.iloc[0]
    return (
        f"- `{condition}` / `{model}` / `{evaluation}`: "
        f"roc_auc={item['roc_auc_mean']:.3f}, auprc={item['average_precision_mean']:.3f}, "
        f"brier={item['brier_score_mean']:.3f}, n_features={int(item['n_features_median'])}"
    )


def format_site_line(summary: pd.DataFrame, condition: str, model: str) -> str:
    row = summary[(summary["condition"] == condition) & (summary["model"] == model)]
    if row.empty:
        return f"- `{condition}` / `{model}`: no valid folds."
    item = row.iloc[0]
    return (
        f"- `{condition}` / `{model}`: "
        f"balanced_accuracy={item['balanced_accuracy_mean']:.3f}, macro_f1={item['macro_f1_mean']:.3f}, "
        f"accuracy={item['accuracy_mean']:.3f}, chance={item['chance_accuracy_mean']:.3f}"
    )


def format_site_dependence_line(summary: pd.DataFrame, condition: str, feature_set: str) -> str:
    row = summary[(summary["condition"] == condition) & (summary["feature_set"] == feature_set)]
    if row.empty:
        return f"- `{condition}` / `{feature_set}`: no valid univariate site tests."
    item = row.iloc[0]
    return (
        f"- `{condition}` / `{feature_set}`: "
        f"median_eta2={item['eta_squared_median']:.3f}, p95_eta2={item['eta_squared_p95']:.3f}, "
        f"q<0.05 features={int(item['kruskal_q_lt_0_05'])}/{int(item['n_features_tested'])}"
    )


def write_summary_markdown(
    config: Config,
    condition_frame: pd.DataFrame,
    subject_frame: pd.DataFrame,
    paired_dynamics: pd.DataFrame,
    site_dependence_summary: pd.DataFrame,
    site_prediction_summary: pd.DataFrame,
    outcome_summary: pd.DataFrame,
) -> str:
    common_runs = int(condition_frame["run_key"].nunique()) if not condition_frame.empty else 0
    common_subjects = (
        int(subject_frame.groupby("condition")["subject"].nunique().median()) if not subject_frame.empty else 0
    )
    outcome_subjects = (
        int(subject_frame[subject_frame["cpc"].isin([1, 5])].groupby("condition")["subject"].nunique().median())
        if not subject_frame.empty
        else 0
    )
    lines = [
        "# ComBat Harmonization Pilot",
        "",
        "## Scope",
        "",
        f"- Baseline root: `{config.baseline_root}`",
        f"- ComBat root: `{config.combat_root}`",
        f"- Common paired run directories: `{common_runs}`",
        f"- Common subjects after aggregation: `{common_subjects}`",
        f"- CPC1/CPC5 subjects after aggregation: `{outcome_subjects}`",
        "- Evidence class: internal pilot using paired H5 exports and internal CV summaries only.",
        "",
        "## Main readout",
        "",
        "### Site dependence (lower is better if hospital effects are being removed)",
        "",
        format_site_dependence_line(site_dependence_summary, "baseline", "raw_features"),
        format_site_dependence_line(site_dependence_summary, "combat", "raw_features"),
        format_site_dependence_line(site_dependence_summary, "baseline", "dynamics_metrics"),
        format_site_dependence_line(site_dependence_summary, "combat", "dynamics_metrics"),
        "",
        "### Site prediction from subject-level summaries (lower is better for de-batching)",
        "",
        format_site_line(site_prediction_summary, "baseline", "raw_features"),
        format_site_line(site_prediction_summary, "combat", "raw_features"),
        format_site_line(site_prediction_summary, "baseline", "dynamics_metrics"),
        format_site_line(site_prediction_summary, "combat", "dynamics_metrics"),
        "",
        "### CPC1 vs CPC5 prediction (higher ROC AUC/AUPRC and lower Brier are better)",
        "",
        format_outcome_line(outcome_summary, "baseline", "raw_features", "repeated_stratified_cv"),
        format_outcome_line(outcome_summary, "combat", "raw_features", "repeated_stratified_cv"),
        format_outcome_line(outcome_summary, "baseline", "raw_features", "leave_one_site_out"),
        format_outcome_line(outcome_summary, "combat", "raw_features", "leave_one_site_out"),
        format_outcome_line(outcome_summary, "baseline", "dynamics_metrics", "repeated_stratified_cv"),
        format_outcome_line(outcome_summary, "combat", "dynamics_metrics", "repeated_stratified_cv"),
        format_outcome_line(outcome_summary, "baseline", "dynamics_metrics", "leave_one_site_out"),
        format_outcome_line(outcome_summary, "combat", "dynamics_metrics", "leave_one_site_out"),
        "",
        "## Paired dynamics shifts",
        "",
    ]
    for _, row in paired_dynamics.iterrows():
        lines.append(
            f"- `{row['metric']}`: median pct change `{row['median_pct_change']:+.3f}%`, "
            f"p95 abs pct `{row['p95_abs_pct_change']:.3f}%` over `{int(row['n_pairs'])}` paired runs"
        )
    lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            "- Reduced site dependence is direct evidence that ComBat is removing hospital-linked structure, but it does not by itself prove improved clinical utility.",
            "- Improved CPC discrimination under leave-one-site-out is the strongest pilot signal that harmonization is helping generalization across hospitals rather than just reshaping feature marginals.",
            "- These are internal retrospective checks on one paired export set and should be read as pilot evidence, not as a final theorem about harmonization.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    condition_frame, pair_frame = build_condition_frames(config)
    subject_frame = build_subject_frame(condition_frame)
    paired_dynamics = summarize_paired_dynamics(pair_frame)
    site_dependence_detail, site_dependence_summary = summarize_site_dependence(subject_frame)
    site_scores, site_prediction_summary = evaluate_site_models(subject_frame, config)
    outcome_scores, outcome_summary = evaluate_outcome_models(subject_frame, config)

    condition_frame.to_csv(config.output_dir / "combat_pilot_run_level.csv", index=False)
    subject_frame.to_csv(config.output_dir / "combat_pilot_subject_level.csv", index=False)
    pair_frame.to_csv(config.output_dir / "combat_pilot_paired_dynamics.csv", index=False)
    paired_dynamics.to_csv(config.output_dir / "combat_pilot_paired_dynamics_summary.csv", index=False)
    site_dependence_detail.to_csv(config.output_dir / "combat_pilot_site_dependence_detail.csv", index=False)
    site_dependence_summary.to_csv(config.output_dir / "combat_pilot_site_dependence_summary.csv", index=False)
    site_scores.to_csv(config.output_dir / "combat_pilot_site_prediction_scores.csv", index=False)
    site_prediction_summary.to_csv(config.output_dir / "combat_pilot_site_prediction_summary.csv", index=False)
    outcome_scores.to_csv(config.output_dir / "combat_pilot_outcome_scores.csv", index=False)
    outcome_summary.to_csv(config.output_dir / "combat_pilot_outcome_summary.csv", index=False)
    (config.output_dir / "combat_pilot_manifest.json").write_text(
        json.dumps(
            {
                "baseline_root": str(config.baseline_root),
                "combat_root": str(config.combat_root),
                "n_splits": config.n_splits,
                "n_repeats": config.n_repeats,
                "random_state": config.random_state,
                "paired_runs": int(condition_frame["run_key"].nunique()) if not condition_frame.empty else 0,
                "subjects_per_condition": (
                    subject_frame.groupby("condition")["subject"].nunique().astype(int).to_dict()
                    if not subject_frame.empty
                    else {}
                ),
                "outcome_subjects_per_condition": (
                    subject_frame[subject_frame["cpc"].isin([1, 5])]
                    .groupby("condition")["subject"]
                    .nunique()
                    .astype(int)
                    .to_dict()
                    if not subject_frame.empty
                    else {}
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (config.output_dir / "combat_pilot_summary.md").write_text(
        write_summary_markdown(
            config,
            condition_frame,
            subject_frame,
            paired_dynamics,
            site_dependence_summary,
            site_prediction_summary,
            outcome_summary,
        ),
        encoding="utf-8",
    )

    print(f"Wrote run-level pilot table to {config.output_dir / 'combat_pilot_run_level.csv'}")
    print(f"Wrote subject-level pilot table to {config.output_dir / 'combat_pilot_subject_level.csv'}")
    print(f"Wrote summary markdown to {config.output_dir / 'combat_pilot_summary.md'}")


if __name__ == "__main__":
    main()
