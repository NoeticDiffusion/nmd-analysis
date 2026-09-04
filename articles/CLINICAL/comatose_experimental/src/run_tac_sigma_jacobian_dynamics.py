"""
TAC 6, 8, 10 — Σ log-Euclidean velocity, cone-field twist, and 9D block-shear flux.

TAC 6 — Σ log-Euclidean velocity:
  For each run, partition the MNPS coordinate sequence into overlapping windows of
  ``--sigma-window`` points and compute the sample covariance Σ_i for each window.
  The log-Euclidean velocity at step i is
      v_i = ‖logm(Σ_i) − logm(Σ_{i+1})‖_F
  normalised by the number of MNPS steps between window centres.
  Patient-level summary: median velocity across all run-window steps.

TAC 8 — Cone-field twist:
  From the same Σ_i sequence, compute the mean principal angle between the
  eigenvector matrices V_i and V_{i+1}:
      twist_i = mean( subspace_angles(V_i, V_{i+1}) )
  This captures how much the orientation of the reachability ellipsoid rotates
  between windows, independently of volume changes.
  Patient-level summary: median twist (radians).

TAC 10 — 9D block-shear flux:
  For each Jacobian window in the 9D export (shape [n_windows, 9, 9]), decompose
  the matrix into 3×3 blocks corresponding to the three MNPS bands (rows/cols 0-2,
  3-5, 6-8).  Report the cross-band Frobenius norm sum, within-band norm sum, and
  their ratio.  Patient-level summary: run-median for each metric.

Usage
-----
  python run_tac_sigma_jacobian_dynamics.py \\
      --processed-root J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260605_202236 \\
      --processed-root J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260605_210700 \\
      --timeline-dir   J:/repos/NoeticDiffusion/articles/CLINICAL/comatose_ndt/results/timeline_analysis_20260606_combined_invalidityfix_primary12h \\
      --output-dir     J:/repos/NoeticDiffusion/articles/CLINICAL/comatose_experimental/results/tac_sigma_jacobian_20260803_invalidityfix_gated
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy.linalg import subspace_angles
from scipy.stats import mannwhitneyu
from sklearn.metrics import roc_auc_score

from geometry_contract_support import read_geometry_9d_validity

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
COMA_NDT_DIR = ARTICLE_DIR.parent / "comatose_ndt"

DEFAULT_PROCESSED_ROOTS: tuple[Path, ...] = (
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_202236",
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_210700",
)
DEFAULT_TIMELINE_DIR = (
    COMA_NDT_DIR / "results" / "timeline_analysis_20260606_combined_invalidityfix_primary12h"
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "tac_sigma_jacobian_20260803_invalidityfix_gated"

GOOD_CPC = 1
POOR_CPC = 5
PRIMARY_TIME_BIN = "0_12h"
EPS = 1e-9

# Coordinate source priorities (3D)
COORDS_3D_PATHS: tuple[str, ...] = (
    "/coords_3d_subject_anchored/values",
    "/coords_3d/values",
)
# Coordinate source priorities (9D)
COORDS_9D_PATHS: tuple[str, ...] = (
    "/coords_9d_subject_anchored/values",
    "/coords_9d/values",
)
JACOBIAN_9D_PATH = "/jacobian_9D/J_hat"
JACOBIAN_9D_SA_PATH = "/jacobian_9D_subject_anchored/J_hat"

OUTPUT_METRICS: tuple[str, ...] = (
    "tac6_3d_sigma_velocity_median",
    "tac6_9d_sigma_velocity_median",
    "tac8_3d_cone_twist_median",
    "tac8_9d_cone_twist_median",
    "tac10_9d_cross_band_flux_median",
    "tac10_9d_within_band_flux_median",
    "tac10_9d_cross_band_ratio_median",
)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_path(value: Any) -> str:
    return str(Path(str(value))).replace("\\", "/").lower()


def path_tail_key(value: Any, *, depth: int = 2) -> str:
    normalized = normalize_path(value)
    parts = [p for p in normalized.split("/") if p]
    return "/".join(parts[-depth:]) if parts else ""


def build_h5_lookup(processed_roots: tuple[Path, ...]) -> dict[str, Path]:
    lookup: dict[str, Path] = {}
    ambiguous: set[str] = set()
    for root in processed_roots:
        if not root.exists():
            continue
        for h5_path in sorted(root.rglob("*.h5")):
            key = path_tail_key(h5_path)
            if not key:
                continue
            prev = lookup.get(key)
            if prev is not None and prev != h5_path:
                ambiguous.add(key)
                continue
            lookup[key] = h5_path
    for key in ambiguous:
        lookup.pop(key, None)
    return lookup


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    g = good[np.isfinite(good)]
    p = poor[np.isfinite(poor)]
    if g.size < 2 or p.size < 2:
        return float("nan")
    pooled = ((g.size - 1) * np.var(g, ddof=1) + (p.size - 1) * np.var(p, ddof=1)) / (g.size + p.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(g) - np.mean(p)) / np.sqrt(pooled))


# ---------------------------------------------------------------------------
# H5 reading
# ---------------------------------------------------------------------------
def read_coords(h5: h5py.File, paths: tuple[str, ...], dim: int) -> np.ndarray | None:
    for path in paths:
        try:
            arr = np.asarray(h5[path][:], dtype=float)
            if arr.ndim == 2 and arr.shape[1] >= dim:
                finite_rows = np.isfinite(arr).all(axis=1)
                arr = arr[finite_rows, :dim]
                return arr if len(arr) >= 4 else None
        except (KeyError, Exception):
            continue
    return None


def read_jacobians_9d(h5: h5py.File) -> np.ndarray | None:
    for path in (JACOBIAN_9D_SA_PATH, JACOBIAN_9D_PATH):
        try:
            arr = np.asarray(h5[path][:], dtype=float)
            if arr.ndim == 3 and arr.shape[1] == 9 and arr.shape[2] == 9:
                finite = np.isfinite(arr).all(axis=(1, 2))
                arr = arr[finite]
                return arr if len(arr) >= 4 else None
        except (KeyError, Exception):
            continue
    return None


# ---------------------------------------------------------------------------
# TAC 6 + 8 — Σ-based metrics
# ---------------------------------------------------------------------------
def regularised_cov(block: np.ndarray) -> np.ndarray:
    """Sample covariance of a (k, d) block, regularised to ensure SPD."""
    cov = np.cov(block.T, ddof=1) if block.shape[0] > 1 else np.eye(block.shape[1])
    if cov.ndim == 0:
        cov = np.array([[float(cov)]])
    cov = 0.5 * (cov + cov.T)
    cov += EPS * np.eye(cov.shape[0])
    return cov


def safe_logm(mat: np.ndarray) -> np.ndarray | None:
    """
    Fast matrix log for symmetric positive (semi-)definite matrices.
    Uses eigendecomposition: logm(A) = V @ diag(log λ) @ V^T.
    Returns None if the matrix is not numerically well-conditioned.
    """
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(mat)
        if np.any(eigenvalues <= 0):
            eigenvalues = np.clip(eigenvalues, EPS, None)
        log_eig = np.log(eigenvalues)
        result = eigenvectors @ np.diag(log_eig) @ eigenvectors.T
        if not np.isfinite(result).all():
            return None
        return result
    except Exception:
        return None


def sigma_sequence(
    coords: np.ndarray,
    *,
    window: int,
    step: int,
    top_k_subspace: int = 2,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """
    Return list of (Σ, V_top) tuples for sliding windows over coords.
    V_top = the top-k eigenvectors (columns), sorted by descending eigenvalue.
    Using only top-k ensures subspace_angles captures meaningful orientation
    changes rather than trivially returning 0 for the full eigenspace.
    """
    n, d = coords.shape
    k = min(top_k_subspace, d)
    results: list[tuple[np.ndarray, np.ndarray]] = []
    for start in range(0, n - window + 1, step):
        block = coords[start : start + window]
        if block.shape[0] < max(d + 1, 3):
            continue
        cov = regularised_cov(block)
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(cov)
            # eigh returns ascending order; take last k for top-k descending
            v_top = eigenvectors[:, -k:]
        except np.linalg.LinAlgError:
            continue
        results.append((cov, v_top))
    return results


def tac6_velocity(sigma_seq: list[tuple[np.ndarray, np.ndarray]], step: int) -> float:
    """Log-Euclidean velocity: ‖logm(Σ_i) - logm(Σ_{i+1})‖_F / step."""
    velocities: list[float] = []
    for (s1, _), (s2, _) in zip(sigma_seq[:-1], sigma_seq[1:]):
        l1 = safe_logm(s1)
        l2 = safe_logm(s2)
        if l1 is None or l2 is None:
            continue
        dist = float(np.linalg.norm(l1 - l2, "fro"))
        velocities.append(dist / max(step, 1))
    if not velocities:
        return float("nan")
    return float(np.median(velocities))


def tac8_twist(sigma_seq: list[tuple[np.ndarray, np.ndarray]]) -> float:
    """Mean principal angle between consecutive eigenvector matrices (radians)."""
    twists: list[float] = []
    for (_, v1), (_, v2) in zip(sigma_seq[:-1], sigma_seq[1:]):
        try:
            angles = subspace_angles(v1, v2)
            twists.append(float(np.mean(angles)))
        except Exception:
            continue
    if not twists:
        return float("nan")
    return float(np.median(twists))


def compute_sigma_metrics(
    coords: np.ndarray,
    *,
    window: int,
    step: int,
    top_k_subspace: int = 2,
) -> dict[str, float]:
    seq = sigma_sequence(coords, window=window, step=step, top_k_subspace=top_k_subspace)
    if len(seq) < 2:
        return {"velocity": float("nan"), "twist": float("nan")}
    return {
        "velocity": tac6_velocity(seq, step),
        "twist": tac8_twist(seq),
    }


# ---------------------------------------------------------------------------
# TAC 10 — 9D block-shear flux
# ---------------------------------------------------------------------------
def tac10_block_shear(jacobians: np.ndarray) -> dict[str, float]:
    """
    Decompose each 9×9 Jacobian into 3×3 blocks (band × band).
    Blocks (0:3,0:3), (3:6,3:6), (6:9,6:9) = within-band.
    Remaining = cross-band.
    """
    cross_norms: list[float] = []
    within_norms: list[float] = []
    for j in jacobians:
        within = sum(
            float(np.linalg.norm(j[r * 3 : (r + 1) * 3, r * 3 : (r + 1) * 3], "fro"))
            for r in range(3)
        )
        # Sum all off-diagonal 3×3 blocks
        cross = 0.0
        for r in range(3):
            for c in range(3):
                if r != c:
                    cross += float(np.linalg.norm(j[r * 3 : (r + 1) * 3, c * 3 : (c + 1) * 3], "fro"))
        within_norms.append(within)
        cross_norms.append(cross)

    if not within_norms:
        return {
            "cross_band_flux": float("nan"),
            "within_band_flux": float("nan"),
            "cross_band_ratio": float("nan"),
        }

    cross_arr = np.array(cross_norms, dtype=float)
    within_arr = np.array(within_norms, dtype=float)
    ratio_arr = cross_arr / (within_arr + EPS)

    return {
        "cross_band_flux": float(np.nanmedian(cross_arr)),
        "within_band_flux": float(np.nanmedian(within_arr)),
        "cross_band_ratio": float(np.nanmedian(ratio_arr)),
    }


# ---------------------------------------------------------------------------
# Per-run dispatch
# ---------------------------------------------------------------------------
def process_run(
    h5_path: Path,
    *,
    sigma_window: int,
    sigma_step: int,
    top_k_3d: int = 2,
    top_k_9d: int = 3,
) -> dict[str, Any]:
    result: dict[str, Any] = {m: float("nan") for m in OUTPUT_METRICS}
    result.update(
        {
            "geometry_contract_status": None,
            "geometry_invalidity_policy": None,
            "geometry_9d_usable": False,
            "geometry_9d_degenerate_axes": "",
            "geometry_9d_jacobian_windows_retained": None,
            "geometry_9d_jacobian_invalid_windows": None,
            "geometry_9d_gate_reason": "h5_read_error",
        }
    )
    try:
        with h5py.File(h5_path, "r") as h5:
            coords3 = read_coords(h5, COORDS_3D_PATHS, 3)
            validity = read_geometry_9d_validity(h5)
            result.update(validity.as_dict())
            coords9 = read_coords(h5, COORDS_9D_PATHS, 9) if validity.usable else None
            jac9 = read_jacobians_9d(h5) if validity.usable else None
    except Exception:
        return result

    if coords3 is not None:
        m3 = compute_sigma_metrics(coords3, window=sigma_window, step=sigma_step, top_k_subspace=top_k_3d)
        result["tac6_3d_sigma_velocity_median"] = m3["velocity"]
        result["tac8_3d_cone_twist_median"] = m3["twist"]

    if coords9 is not None:
        m9 = compute_sigma_metrics(coords9, window=sigma_window, step=sigma_step, top_k_subspace=top_k_9d)
        result["tac6_9d_sigma_velocity_median"] = m9["velocity"]
        result["tac8_9d_cone_twist_median"] = m9["twist"]

    if jac9 is not None:
        t10 = tac10_block_shear(jac9)
        result["tac10_9d_cross_band_flux_median"] = t10["cross_band_flux"]
        result["tac10_9d_within_band_flux_median"] = t10["within_band_flux"]
        result["tac10_9d_cross_band_ratio_median"] = t10["cross_band_ratio"]

    return result


# ---------------------------------------------------------------------------
# Timeline loading
# ---------------------------------------------------------------------------
def load_run_table(
    timeline_dir: Path,
    h5_lookup: dict[str, Path],
    *,
    good_cpc: int,
    poor_cpc: int,
    primary_time_bin: str,
    limit_subjects: int | None,
) -> pd.DataFrame:
    frame = pd.read_csv(timeline_dir / "run_timing_metadata.csv", low_memory=False)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[
        (frame["time_bin"] == primary_time_bin)
        & (frame["cpc_numeric"].isin([float(good_cpc), float(poor_cpc)]))
    ].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(good_cpc), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, f"CPC{good_cpc}", f"CPC{poor_cpc}")

    # Remap paths via lookup (handles cross-machine path differences)
    frame["processed_h5_path"] = frame["processed_h5_path"].map(
        lambda v: str(h5_lookup.get(path_tail_key(v), Path(str(v))))
    )
    frame["processed_h5_exists"] = frame["processed_h5_path"].map(lambda v: Path(v).exists())
    frame = frame[frame["processed_h5_exists"]].copy()

    if limit_subjects:
        keep = frame["subject"].astype(str).drop_duplicates().tolist()[:limit_subjects]
        frame = frame[frame["subject"].astype(str).isin(keep)].copy()

    return frame.sort_values(["subject", "run_start_from_anchor_sec", "run", "acq"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Contrast summary
# ---------------------------------------------------------------------------
def build_contrast_summary(
    patient_metrics: pd.DataFrame,
    *,
    good_cpc: int,
    poor_cpc: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric in OUTPUT_METRICS:
        if metric not in patient_metrics.columns:
            continue
        good = pd.to_numeric(
            patient_metrics.loc[patient_metrics["label"] == 1, metric], errors="coerce"
        ).dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(
            patient_metrics.loc[patient_metrics["label"] == 0, metric], errors="coerce"
        ).dropna().to_numpy(dtype=float)
        if good.size < 4 or poor.size < 4:
            continue
        mw_p = float(mannwhitneyu(good, poor, alternative="two-sided").pvalue)
        d_val = cohens_d(good, poor)
        labels = np.concatenate([np.ones(good.size), np.zeros(poor.size)])
        scores = np.concatenate([good, poor])
        if np.isfinite(scores).all() and len(np.unique(labels)) == 2:
            try:
                auroc = float(roc_auc_score(labels, scores))
            except Exception:
                auroc = float("nan")
        else:
            auroc = float("nan")
        rows.append(
            {
                "metric": metric,
                f"cpc{good_cpc}_median": float(np.nanmedian(good)),
                f"cpc{poor_cpc}_median": float(np.nanmedian(poor)),
                "cohens_d": d_val,
                "abs_d": abs(d_val) if np.isfinite(d_val) else float("nan"),
                "mw_p": mw_p,
                "auroc": auroc,
                f"n_cpc{good_cpc}": int(good.size),
                f"n_cpc{poor_cpc}": int(poor.size),
            }
        )
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows).sort_values("abs_d", ascending=False).reset_index(drop=True)
    return out


def build_markdown(
    contrast: pd.DataFrame,
    *,
    n_subjects: int,
    n_good: int,
    n_poor: int,
    n_9d_usable_runs: int,
    n_9d_gated_runs: int,
    good_cpc: int,
    poor_cpc: int,
    sigma_window: int,
    sigma_step: int,
) -> str:
    lines = [
        "# TAC 6 / 8 / 10 — Σ dynamics and block-shear flux",
        "",
        f"- cohort: `{n_subjects}` subjects (`{n_good}` CPC{good_cpc}, `{n_poor}` CPC{poor_cpc})",
        f"- sigma window: `{sigma_window}` MNPS points, step: `{sigma_step}`",
        f"- 9D geometry-contract usable runs: `{n_9d_usable_runs}`",
        f"- 9D geometry-contract gated runs: `{n_9d_gated_runs}`",
        "",
        "## TAC 6 — Σ log-Euclidean velocity",
        "",
        "Measures how fast the local reachability covariance changes on the SPD manifold.",
        "High velocity = rapidly evolving ellipsoid (burst-suppression transients expected to dominate).",
        "",
        "## TAC 8 — Cone-field twist",
        "",
        "Measures how much the orientation of Σ's eigenvectors rotates between consecutive",
        "windows. Orthogonal to volume (velocity); captures directionality changes.",
        "",
        "## TAC 10 — 9D block-shear flux",
        "",
        "Decomposes the 9×9 Jacobian into 3×3 blocks (bands δ/θ/α). Cross-band flux",
        "= how much the bands couple to each other. Within-band flux = intra-band norm.",
        "High cross-band ratio = inter-band coupling dominates (potentially less structured).",
        "",
        "## CPC1 vs CPC5 contrasts",
        "",
    ]
    if contrast.empty:
        lines.append("No contrast rows available.")
    else:
        for _, row in contrast.iterrows():
            tac_tag = "TAC 6" if "velocity" in row["metric"] else ("TAC 8" if "twist" in row["metric"] else "TAC 10")
            lines.append(
                f"- `{row['metric']}` [{tac_tag}]: "
                f"CPC{good_cpc} med `{row[f'cpc{good_cpc}_median']:.4g}` vs "
                f"CPC{poor_cpc} med `{row[f'cpc{poor_cpc}_median']:.4g}`, "
                f"Cohen's `d = {row['cohens_d']:.3f}`, MW `p = {row['mw_p']:.3g}`, "
                f"AUROC `{row['auroc']:.3f}`, "
                f"n = `{row[f'n_cpc{good_cpc}']}/{row[f'n_cpc{poor_cpc}']}`"
            )
    lines.extend(["", "## Notes", ""])
    lines.append(
        "- TAC 6/8 use a sliding-window covariance over MNPS coordinate sequences. "
        "Each H5 row = one EEG time window. Results are sensitive to `--sigma-window`."
    )
    lines.append(
        "- TAC 10 requires `jacobian_9D/J_hat` (or `jacobian_9D_subject_anchored/J_hat`). "
        "Runs without 9D Jacobians contribute NaN for TAC 10 only."
    )
    lines.append(
        "- The 3×3 block decomposition assumes dims 0-2 = δ-band MNPS, 3-5 = θ-band, 6-8 = α-band. "
        "This is the standard NDT 9D layout."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1].strip())
    parser.add_argument(
        "--processed-root",
        type=Path,
        action="append",
        default=None,
        metavar="ROOT",
        help="H5 processed root directory. Repeat to pool part1+part2.",
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument(
        "--sigma-window",
        type=int,
        default=20,
        help="Number of consecutive MNPS points per covariance window (TAC 6 & 8).",
    )
    parser.add_argument(
        "--sigma-step",
        type=int,
        default=5,
        help="Step between consecutive covariance windows (TAC 6 & 8).",
    )
    parser.add_argument(
        "--top-k-subspace",
        type=int,
        default=2,
        help=(
            "Number of leading eigenvectors used in TAC 8 subspace-angle computation. "
            "3D coords use this value directly; 9D coords use top_k+1 to capture more structure."
        ),
    )
    parser.add_argument("--limit-subjects", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    processed_roots: tuple[Path, ...] = (
        tuple(args.processed_root) if args.processed_root else DEFAULT_PROCESSED_ROOTS
    )
    ensure_dir(args.output_dir)

    print(f"Building H5 lookup from {len(processed_roots)} root(s)...")
    h5_lookup = build_h5_lookup(processed_roots)
    print(f"  -> {len(h5_lookup)} H5 files indexed")

    run_table = load_run_table(
        args.timeline_dir,
        h5_lookup,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        primary_time_bin=args.primary_time_bin,
        limit_subjects=args.limit_subjects,
    )
    n_runs = len(run_table)
    n_subjects = run_table["subject"].nunique()
    print(f"  -> {n_runs} runs from {n_subjects} subjects after H5 filtering")

    if run_table.empty:
        raise RuntimeError("No usable runs found. Check --processed-root and --timeline-dir.")

    # Per-run computation
    run_metrics_list: list[dict[str, Any]] = []
    for i, (_, row) in enumerate(run_table.iterrows()):
        if i % 200 == 0:
            print(f"  Processing run {i + 1}/{n_runs}...")
        h5_path = Path(str(row["processed_h5_path"]))
        metrics = process_run(
            h5_path,
            sigma_window=args.sigma_window,
            sigma_step=args.sigma_step,
            top_k_3d=args.top_k_subspace,
            top_k_9d=args.top_k_subspace + 1,
        )
        run_metrics_list.append(
            {
                "subject": row["subject"],
                "run": row["run"],
                "acq": row["acq"],
                "cpc": row["cpc"],
                "cpc_numeric": row["cpc_numeric"],
                "label": row["label"],
                "label_name": row["label_name"],
                "time_bin": row["time_bin"],
                "n_windows": row.get("n_windows"),
                **metrics,
            }
        )

    run_metrics = pd.DataFrame(run_metrics_list)
    run_metrics.to_csv(args.output_dir / "run_level_metrics.csv", index=False)

    # Patient-level aggregation (median across runs)
    group_cols = ["subject", "cpc", "cpc_numeric", "label", "label_name", "time_bin"]
    patient_metrics = (
        run_metrics.groupby(group_cols, as_index=False)[list(OUTPUT_METRICS)]
        .median()
        .sort_values("subject")
        .reset_index(drop=True)
    )
    patient_metrics.to_csv(args.output_dir / "patient_level_metrics.csv", index=False)

    # Contrasts
    contrast = build_contrast_summary(
        patient_metrics,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
    )
    contrast.to_csv(args.output_dir / "contrast_summary.csv", index=False)

    n_good = int((patient_metrics["label"] == 1).sum())
    n_poor = int((patient_metrics["label"] == 0).sum())

    summary_md = build_markdown(
        contrast,
        n_subjects=int(patient_metrics["subject"].nunique()),
        n_good=n_good,
        n_poor=n_poor,
        n_9d_usable_runs=int(run_metrics["geometry_9d_usable"].fillna(False).astype(bool).sum()),
        n_9d_gated_runs=int((~run_metrics["geometry_9d_usable"].fillna(False).astype(bool)).sum()),
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        sigma_window=args.sigma_window,
        sigma_step=args.sigma_step,
    )
    (args.output_dir / "tac_summary.md").write_text(summary_md, encoding="utf-8")

    manifest = {
        "processed_roots": [str(r) for r in processed_roots],
        "timeline_dir": str(args.timeline_dir),
        "output_dir": str(args.output_dir),
        "good_cpc": args.good_cpc,
        "poor_cpc": args.poor_cpc,
        "primary_time_bin": args.primary_time_bin,
        "sigma_window": args.sigma_window,
        "sigma_step": args.sigma_step,
        "n_runs": n_runs,
        "n_subjects": n_subjects,
        "n_9d_usable_runs": int(run_metrics["geometry_9d_usable"].fillna(False).astype(bool).sum()),
        "n_9d_gated_runs": int((~run_metrics["geometry_9d_usable"].fillna(False).astype(bool)).sum()),
        "geometry_contract_gate": {
            "enabled": True,
            "rules": [
                "gate runs with non-empty coords_9d degenerate_axes",
                "gate runs with jacobian_9d windows_retained <= 0",
            ],
        },
        "output_metrics": list(OUTPUT_METRICS),
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nWrote results to {args.output_dir}")
    if not contrast.empty:
        print("\nTop contrasts:")
        for _, row in contrast.head(5).iterrows():
            print(
                f"  {row['metric']:<45} d={row['cohens_d']:+.3f}  "
                f"p={row['mw_p']:.3g}  AUROC={row['auroc']:.3f}"
            )


if __name__ == "__main__":
    main()
