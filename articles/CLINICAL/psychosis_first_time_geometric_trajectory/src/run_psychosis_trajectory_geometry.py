"""
run_psychosis_trajectory_geometry.py

Compute exploratory trajectory / repertoire geometry metrics for the two
first-episode-psychosis resting-state EEG cohorts (ds003944, ds003947)
using subject-anchored 3D and 9D MNPS coordinates from NeuralManifoldDynamics 2.1.

Metrics (mirrors comatose_geometric_trajectory pipeline):
  Article-facing : irreversibility, entropy_rate, noetic_action
  Supportive     : entropy_production, self_loop_rate, transition_sparsity,
                   noetic_action_kinetic, noetic_action_jerk, noetic_action_potential

Groups:
  Healthy           – participant type == "Control"
  FEP_unmedicated   – type == "Psychosis" AND CPZ_at_scan == 0 or NaN
  FEP_medicated     – type == "Psychosis" AND CPZ_at_scan > 0

Contrasts (per dataset):
  FEP_unmedicated vs Healthy
  FEP_medicated   vs Healthy
  FEP_medicated   vs FEP_unmedicated

Usage:
  cd articles/CLINICAL/psychosis_first_time_geometric_trajectory/src
  python run_psychosis_trajectory_geometry.py --smoke   # 10 subjects per dataset
  python run_psychosis_trajectory_geometry.py --full    # all subjects
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.cluster import MiniBatchKMeans


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]

RAW_ROOTS: dict[str, list[Path]] = {
    "ds003944": [
        REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003944_20260520_121126",
    ],
    "ds003947": [
        REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003947_20260520_114135",
    ],
}

RESULT_STAMP = "20260607"
RESULTS_DIR = ARTICLE_DIR / "results"

# ---------------------------------------------------------------------------
# Algorithm constants (identical to comatose_geometric_trajectory pipeline)
# ---------------------------------------------------------------------------
REPERTOIRE_STATES_BY_DIM: dict[int, int] = {3: 12, 9: 24}
MAX_CODEBOOK_POINTS_BY_DIM: dict[int, int] = {3: 40_000, 9: 60_000}
MAX_POINTS_PER_SUBJECT_FOR_FIT: dict[int, int] = {3: 256, 9: 256}
MIN_POINTS_PER_SUBJECT = 16
MIN_TRANSITIONS = 8
ACTION_JERK_WEIGHT = 1.0
ACTION_POTENTIAL_WEIGHT = 1.0
EPS = 1e-12
RNG_SEED = 20260607

ARTICLE_FACING_METRICS = ("irreversibility", "entropy_rate", "noetic_action")
SUPPORTIVE_METRICS = (
    "entropy_production",
    "self_loop_rate",
    "transition_sparsity",
    "noetic_action_kinetic",
    "noetic_action_jerk",
    "noetic_action_potential",
)
ALL_METRICS = ARTICLE_FACING_METRICS + SUPPORTIVE_METRICS

CONTRASTS = (
    ("FEP_unmedicated", "Healthy"),
    ("FEP_medicated", "Healthy"),
    ("FEP_medicated", "FEP_unmedicated"),
)
CONTRAST_LABELS = {
    ("FEP_unmedicated", "Healthy"): "FEP_unmedicated_vs_Healthy",
    ("FEP_medicated", "Healthy"): "FEP_medicated_vs_Healthy",
    ("FEP_medicated", "FEP_unmedicated"): "FEP_medicated_vs_FEP_unmedicated",
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def bh_fdr(p_values: "pd.Series[float]") -> "pd.Series[float]":
    values = pd.to_numeric(p_values, errors="coerce").to_numpy(dtype=float)
    out = np.full(values.shape, np.nan, dtype=float)
    mask = np.isfinite(values)
    if not mask.any():
        return pd.Series(out, index=p_values.index, dtype=float)
    valid = values[mask]
    order = np.argsort(valid)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(valid) + 1)
    q = valid * len(valid) / ranks
    q_sorted = np.minimum.accumulate(q[order][::-1])[::-1]
    q_final = np.empty_like(q_sorted)
    q_final[order] = np.clip(q_sorted, 0.0, 1.0)
    out[np.where(mask)[0]] = q_final
    return pd.Series(out, index=p_values.index, dtype=float)


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if a.size < 2 or b.size < 2:
        return float("nan")
    pooled = (
        (a.size - 1) * np.var(a, ddof=1) + (b.size - 1) * np.var(b, ddof=1)
    ) / (a.size + b.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / np.sqrt(pooled))


def stable_variance_metric(coords: np.ndarray) -> np.ndarray:
    var = np.nanvar(np.asarray(coords, dtype=float), axis=0, ddof=1)
    var = np.where(np.isfinite(var) & (var > EPS), var, 1.0)
    return 1.0 / var


def potential_from_coords(coords: np.ndarray) -> np.ndarray:
    arr = np.asarray(coords, dtype=float)
    if arr.shape[1] == 3:
        return arr[:, 2] - arr[:, 0] + arr[:, 1]
    if arr.shape[1] >= 9:
        m_bar = np.nanmean(arr[:, 0:3], axis=1)
        d_bar = np.nanmean(arr[:, 3:6], axis=1)
        e_bar = np.nanmean(arr[:, 6:9], axis=1)
        return e_bar - m_bar + d_bar
    raise ValueError(f"Unsupported coordinate width {arr.shape[1]}")


# ---------------------------------------------------------------------------
# H5 reading
# ---------------------------------------------------------------------------

def read_subject_h5(h5_path: Path, *, dim: int) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Return (coords, time, participant_info) or empty arrays on failure."""
    if not h5_path.exists():
        return np.empty((0, dim)), np.empty(0), {}
    with h5py.File(h5_path, "r") as f:
        key = f"coords_{dim}d_subject_anchored/values"
        if key not in f:
            return np.empty((0, dim)), np.empty(0), {}
        coords = np.asarray(f[key], dtype=float)
        coords = coords[:, :dim]

        if "time" in f:
            time = np.asarray(f["time"], dtype=float)
        elif "window_start" in f and "window_end" in f:
            ws = np.asarray(f["window_start"], dtype=float)
            we = np.asarray(f["window_end"], dtype=float)
            time = 0.5 * (ws + we)
        else:
            time = np.arange(coords.shape[0], dtype=float)

        participant: dict[str, Any] = {}
        try:
            raw = f["participant/row_json"][()]
            if isinstance(raw, (bytes, np.bytes_)):
                raw = raw.decode("utf-8")
            participant = json.loads(raw)
        except Exception:
            pass

    limit = min(len(coords), len(time))
    coords = coords[:limit]
    time = time[:limit]
    finite_mask = np.isfinite(time) & np.isfinite(coords).all(axis=1)
    return coords[finite_mask], time[finite_mask], participant


def assign_medication_group(participant: dict[str, Any]) -> str | None:
    ptype = str(participant.get("type", "")).strip()
    cpz_raw = participant.get("CPZ_at_scan", None)
    if ptype == "Control":
        return "Healthy"
    if ptype == "Psychosis":
        try:
            cpz = float(cpz_raw)  # type: ignore[arg-type]
            if np.isnan(cpz) or cpz == 0.0:
                return "FEP_unmedicated"
            return "FEP_medicated"
        except (TypeError, ValueError):
            return "FEP_unmedicated"
    return None


def discover_h5_files(dataset: str) -> list[Path]:
    for root in RAW_ROOTS.get(dataset, []):
        if root.exists():
            return sorted(root.glob(f"sub-*/{dataset}*.h5") or root.glob("sub-*/*.h5"))
    return []


def discover_h5_files_flat(dataset: str) -> list[Path]:
    """H5 files live at root/sub-XXXX_rest_Rest/sub-XXXX_rest_Rest.h5."""
    results: list[Path] = []
    for root in RAW_ROOTS.get(dataset, []):
        if not root.exists():
            continue
        for sub_dir in sorted(root.iterdir()):
            if not sub_dir.is_dir() or not sub_dir.name.startswith("sub-"):
                continue
            h5_files = list(sub_dir.glob("*.h5"))
            results.extend(h5_files)
    return results


# ---------------------------------------------------------------------------
# Metric computation (identical math to coma trajectory pipeline)
# ---------------------------------------------------------------------------

def repertoire_metrics(states: np.ndarray, *, n_states: int) -> dict[str, float]:
    states = np.asarray(states, dtype=int).reshape(-1)
    if len(states) < (MIN_TRANSITIONS + 1):
        return {m: float("nan") for m in ("entropy_rate", "irreversibility", "entropy_production", "self_loop_rate", "transition_sparsity")}
    tc = np.zeros((n_states, n_states), dtype=float)
    for src, dst in zip(states[:-1], states[1:], strict=False):
        tc[int(src), int(dst)] += 1.0
    occ = np.bincount(states, minlength=n_states).astype(float)
    if occ.sum() <= 0:
        return {m: float("nan") for m in ("entropy_rate", "irreversibility", "entropy_production", "self_loop_rate", "transition_sparsity")}
    pi = occ / occ.sum()
    row_sums = tc.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        P = np.divide(tc, row_sums, out=np.zeros_like(tc), where=row_sums > 0)
    entropy_rate = float(-np.sum(pi[:, None] * P * np.log(P + EPS)))
    flow = pi[:, None] * P
    irreversibility = float(0.5 * np.sum(np.abs(flow - flow.T)))
    entropy_production = float(np.sum(flow * np.log((flow + EPS) / (flow.T + EPS))))
    self_loop_rate = float(np.sum(pi * np.diag(P)))
    transition_sparsity = float(1.0 - np.count_nonzero(tc) / tc.size)
    return {
        "entropy_rate": entropy_rate,
        "irreversibility": irreversibility,
        "entropy_production": entropy_production,
        "self_loop_rate": self_loop_rate,
        "transition_sparsity": transition_sparsity,
    }


def noetic_action_metrics(coords: np.ndarray, time: np.ndarray, *, metric_diag: np.ndarray) -> dict[str, float]:
    nan_result = {m: float("nan") for m in ("noetic_action", "noetic_action_kinetic", "noetic_action_jerk", "noetic_action_potential")}
    if len(coords) < 3:
        return nan_result
    dt_prev = time[1:-1] - time[:-2]
    dt_next = time[2:] - time[1:-1]
    valid = np.isfinite(dt_prev) & np.isfinite(dt_next) & (dt_prev > 0) & (dt_next > 0)
    if not valid.any():
        return nan_result
    delta = coords[2:] - coords[1:-1]
    delta2 = coords[2:] - 2.0 * coords[1:-1] + coords[:-2]
    dt_c = 0.5 * (dt_prev + dt_next)
    potential = potential_from_coords(coords[1:-1])
    delta = delta[valid]
    delta2 = delta2[valid]
    dt_next_v = dt_next[valid]
    dt_c_v = dt_c[valid]
    potential_v = potential[valid]

    def _wq(vecs: np.ndarray) -> np.ndarray:
        return np.sum((vecs * vecs) * metric_diag[None, :], axis=1)

    kinetic = 0.5 * _wq(delta) / np.maximum(dt_next_v, EPS) ** 2
    jerk = ACTION_JERK_WEIGHT * _wq(delta2) / np.maximum(dt_c_v, EPS) ** 4
    pot = ACTION_POTENTIAL_WEIGHT * potential_v
    total = kinetic + jerk + pot

    def _m(arr: np.ndarray) -> float:
        arr = arr[np.isfinite(arr)]
        return float(np.median(arr)) if arr.size else float("nan")

    return {
        "noetic_action": _m(total),
        "noetic_action_kinetic": _m(kinetic),
        "noetic_action_jerk": _m(jerk),
        "noetic_action_potential": _m(pot),
    }


def sample_evenly(coords: np.ndarray, max_pts: int) -> np.ndarray:
    if len(coords) <= max_pts:
        return coords
    idx = np.linspace(0, len(coords) - 1, num=max_pts, dtype=int)
    return coords[idx]


def fit_codebook(subject_data: list[tuple[np.ndarray, np.ndarray]], *, dim: int) -> tuple[MiniBatchKMeans, np.ndarray, int]:
    blocks: list[np.ndarray] = []
    for coords, _ in subject_data:
        if len(coords) < MIN_POINTS_PER_SUBJECT:
            continue
        blocks.append(sample_evenly(coords, MAX_POINTS_PER_SUBJECT_FOR_FIT[dim]))
    if not blocks:
        raise RuntimeError(f"No usable {dim}D data for codebook fitting.")
    sampled = np.concatenate(blocks, axis=0)
    sampled = sample_evenly(sampled, MAX_CODEBOOK_POINTS_BY_DIM[dim])
    model = MiniBatchKMeans(
        n_clusters=REPERTOIRE_STATES_BY_DIM[dim],
        random_state=RNG_SEED + dim,
        n_init=10,
        batch_size=min(4096, max(512, len(sampled))),
        reassignment_ratio=0.01,
    )
    model.fit(sampled)
    return model, stable_variance_metric(sampled), len(blocks)


# ---------------------------------------------------------------------------
# Per-dataset pipeline
# ---------------------------------------------------------------------------

def process_dataset(
    dataset: str,
    *,
    output_dir: Path,
    limit: int | None = None,
    dims: tuple[int, ...] = (3, 9),
) -> dict[str, Any]:
    ensure_dir(output_dir)

    h5_files = discover_h5_files_flat(dataset)
    if not h5_files:
        raise FileNotFoundError(f"No H5 files found for {dataset}. Check RAW_ROOTS.")

    if limit is not None:
        h5_files = h5_files[:limit]

    print(f"\n[{dataset}] Found {len(h5_files)} subject H5 files")

    # First pass: collect participant info and 3D coords for group assignment
    subjects: list[dict[str, Any]] = []
    for h5_path in h5_files:
        _, _, pinfo = read_subject_h5(h5_path, dim=3)
        group = assign_medication_group(pinfo)
        if group is None:
            print(f"  SKIP {h5_path.name}: unrecognised participant type {pinfo.get('type')!r}")
            continue
        subjects.append({
            "h5_path": h5_path,
            "subject_id": pinfo.get("participant_id", h5_path.parent.name),
            "group": group,
            "cpz_at_scan": pinfo.get("CPZ_at_scan", None),
            "age": pinfo.get("age", None),
            "gender": pinfo.get("gender", None),
            "ptype": pinfo.get("type", None),
        })

    group_counts = pd.Series([s["group"] for s in subjects]).value_counts().to_dict()
    print(f"[{dataset}] Group counts: {group_counts}")

    all_metric_rows: list[dict[str, Any]] = []
    manifest_dims: dict[str, Any] = {}

    for dim in dims:
        print(f"[{dataset}] Processing dim={dim}...")
        analysis_type = f"trajectory_geometry_subject_anchored_{dim}d"

        # Load coords for all subjects
        subject_data: list[tuple[np.ndarray, np.ndarray]] = []
        for s in subjects:
            coords, time, _ = read_subject_h5(s["h5_path"], dim=dim)
            subject_data.append((coords, time))

        # Fit shared codebook on all subjects in this dataset
        model, metric_diag, n_fit_subjects = fit_codebook(subject_data, dim=dim)
        manifest_dims[str(dim)] = {
            "n_fit_subjects": n_fit_subjects,
            "n_clusters": REPERTOIRE_STATES_BY_DIM[dim],
            "analysis_type": analysis_type,
        }

        # Compute per-subject metrics
        for s, (coords, time) in zip(subjects, subject_data, strict=False):
            if len(coords) < MIN_POINTS_PER_SUBJECT:
                print(f"  SKIP {s['subject_id']} dim={dim}: only {len(coords)} points")
                continue
            states = model.predict(coords)
            rep = repertoire_metrics(states, n_states=REPERTOIRE_STATES_BY_DIM[dim])
            act = noetic_action_metrics(coords, time, metric_diag=metric_diag)
            all_metrics = {**rep, **act}
            for metric_name, value in all_metrics.items():
                all_metric_rows.append({
                    "dataset": dataset,
                    "subject_id": s["subject_id"],
                    "group": s["group"],
                    "cpz_at_scan": s["cpz_at_scan"],
                    "age": s["age"],
                    "gender": s["gender"],
                    "analysis_type": analysis_type,
                    "dim": dim,
                    "metric": metric_name,
                    "value": value,
                    "article_facing": metric_name in ARTICLE_FACING_METRICS,
                    "n_windows": len(coords),
                })

    if not all_metric_rows:
        raise RuntimeError(f"[{dataset}] No metric rows produced.")

    df_metrics = pd.DataFrame(all_metric_rows)
    metrics_path = output_dir / f"{dataset}_subject_trajectory_metrics.csv"
    df_metrics.to_csv(metrics_path, index=False)
    print(f"[{dataset}] Saved {len(df_metrics)} metric rows -> {metrics_path.name}")

    # Contrasts
    contrast_rows: list[dict[str, Any]] = []
    for group_a, group_b in CONTRASTS:
        contrast_label = CONTRAST_LABELS[(group_a, group_b)]
        for (analysis_type, metric), grp in df_metrics.groupby(["analysis_type", "metric"], dropna=False):
            vals_a = pd.to_numeric(grp.loc[grp["group"] == group_a, "value"], errors="coerce").dropna()
            vals_b = pd.to_numeric(grp.loc[grp["group"] == group_b, "value"], errors="coerce").dropna()
            if vals_a.empty or vals_b.empty:
                continue
            p = float(mannwhitneyu(vals_a, vals_b, alternative="two-sided").pvalue)
            d = cohens_d(vals_a.to_numpy(), vals_b.to_numpy())
            contrast_rows.append({
                "dataset": dataset,
                "contrast": contrast_label,
                "group_a": group_a,
                "group_b": group_b,
                "analysis_type": analysis_type,
                "metric": metric,
                "median_a": float(vals_a.median()),
                "median_b": float(vals_b.median()),
                "cohens_d": d,
                "abs_d": abs(d) if np.isfinite(d) else float("nan"),
                "mw_p": p,
                "n_a": int(vals_a.shape[0]),
                "n_b": int(vals_b.shape[0]),
                "article_facing": bool(metric in ARTICLE_FACING_METRICS),
            })

    if not contrast_rows:
        raise RuntimeError(f"[{dataset}] No contrast rows produced.")

    df_contrasts = pd.DataFrame(contrast_rows)
    df_contrasts["mw_q"] = df_contrasts.groupby(["contrast", "analysis_type"], dropna=False)["mw_p"].transform(bh_fdr)
    df_contrasts = df_contrasts.sort_values(
        ["contrast", "analysis_type", "article_facing", "abs_d"],
        ascending=[True, True, False, False],
    ).reset_index(drop=True)

    contrast_path = output_dir / f"{dataset}_trajectory_contrasts.csv"
    df_contrasts.to_csv(contrast_path, index=False)
    print(f"[{dataset}] Saved {len(df_contrasts)} contrast rows -> {contrast_path.name}")

    manifest: dict[str, Any] = {
        "dataset": dataset,
        "n_subjects_total": len(subjects),
        "group_counts": group_counts,
        "h5_files_processed": len(h5_files),
        "dimensions": manifest_dims,
        "metrics_path": str(metrics_path),
        "contrasts_path": str(contrast_path),
    }
    return manifest


def print_top_results(df: pd.DataFrame, dataset: str, top_n: int = 8) -> None:
    print(f"\n{'='*60}")
    print(f"TOP RESULTS: {dataset}")
    print(f"{'='*60}")
    for contrast_label in df["contrast"].unique():
        sub = df[df["contrast"] == contrast_label].copy()
        sub_sorted = sub.sort_values("abs_d", ascending=False)
        q_sig = sub_sorted[sub_sorted["mw_q"] <= 0.05]
        p_sig = sub_sorted[(sub_sorted["mw_p"] < 0.05) & (sub_sorted["mw_q"] > 0.05)]
        top = sub_sorted.head(min(top_n, len(sub_sorted)))

        print(f"\n  {contrast_label}")
        print(f"  q<=0.05: {len(q_sig)}  |  p<0.05 only: {len(p_sig)}")
        for _, row in top.iterrows():
            q_star = "q" if row["mw_q"] <= 0.05 else ("*" if row["mw_p"] < 0.05 else ("~" if row["mw_p"] < 0.1 else " "))
            af = "[AF]" if row["article_facing"] else "    "
            print(f"    {q_star} {af} {row['analysis_type'][:35]:35s} {row['metric']:30s}  d={row['cohens_d']:+.3f}  p={row['mw_p']:.4f}  q={row['mw_q']:.4f}  n=({row['n_a']},{row['n_b']})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Psychosis trajectory geometry metrics.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true", help="Quick smoke test (10 subjects per dataset)")
    mode.add_argument("--full", action="store_true", help="Full run (all subjects)")
    parser.add_argument("--dims", type=str, default="3,9", help="Comma-separated dimensions to compute")
    parser.add_argument("--dataset", type=str, default="both", choices=("both", "ds003944", "ds003947"))
    return parser.parse_args()


def parse_dims(raw: str) -> tuple[int, ...]:
    dims: list[int] = []
    for token in raw.split(","):
        token = token.strip()
        if token:
            dims.append(int(token))
    return tuple(dict.fromkeys(dims))


def main() -> None:
    args = parse_args()
    dims = parse_dims(args.dims)

    if args.smoke:
        limit = 10
        run_tag = f"trajectory_geometry_{RESULT_STAMP}_smoke"
    else:
        limit = None
        run_tag = f"trajectory_geometry_{RESULT_STAMP}_full"

    output_root = RESULTS_DIR / run_tag
    ensure_dir(output_root)

    datasets = ["ds003944", "ds003947"] if args.dataset == "both" else [args.dataset]

    all_manifests: dict[str, Any] = {}
    for dataset in datasets:
        ds_out = output_root / dataset
        try:
            manifest = process_dataset(dataset, output_dir=ds_out, limit=limit, dims=dims)
            all_manifests[dataset] = manifest

            df_contrasts = pd.read_csv(ds_out / f"{dataset}_trajectory_contrasts.csv")
            print_top_results(df_contrasts, dataset)
        except Exception as exc:
            print(f"[{dataset}] ERROR: {exc}", file=sys.stderr)
            raise

    combined_manifest = {
        "run_tag": run_tag,
        "smoke": bool(args.smoke),
        "limit_per_dataset": limit,
        "dims": list(dims),
        "datasets": all_manifests,
    }
    write_json(output_root / "manifest.json", combined_manifest)
    print(f"\nManifest written -> {output_root / 'manifest.json'}")
    print(f"Results in       -> {output_root}")


if __name__ == "__main__":
    main()
