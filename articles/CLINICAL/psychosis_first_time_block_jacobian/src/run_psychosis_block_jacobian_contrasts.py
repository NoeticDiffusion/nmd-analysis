"""
run_psychosis_block_jacobian_contrasts.py

Contrast the 9x9 block-Jacobian cross-family coupling metrics against
medication-stratified FEP groups for ds003944 and ds003947.

The block Jacobians describe how each MNPS family (m, d, e) drives the
others. Off-diagonal blocks (e.g. m->e, e->m) capture directed coupling
between functional families. Diagonal blocks (m->m, d->d, e->e) capture
self-coupling / auto-regulation.

Available metrics (from stratified_block_jacobians CSV):
  Diagonal blocks (out_group == in_group):
    block_trace_mean      -- signed trace of diagonal block
    block_frobenius_mean  -- Frobenius norm of diagonal block
    block_anisotropy_mean -- anisotropy of diagonal block
  Off-diagonal blocks (out_group != in_group):
    block_frobenius_mean  -- coupling strength
    c_sym_mean            -- symmetric (mutual) coupling
    c_rot_mean            -- rotational (directed) coupling

Groups: Healthy / FEP_unmedicated / FEP_medicated
Contrasts: FEP_unmedicated vs Healthy, FEP_medicated vs Healthy,
           FEP_medicated vs FEP_unmedicated

Usage:
  cd articles/CLINICAL/psychosis_first_time_geometric_trajectory/src
  python run_psychosis_block_jacobian_contrasts.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
RESULT_STAMP = "20260607"

RAW_ROOTS = {
    "ds003944": REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003944_20260520_121126",
    "ds003947": REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003947_20260520_114135",
}
BLOCK_JAC_CSVS = {
    "ds003944": RAW_ROOTS["ds003944"] / "stratified_block_jacobians_subjects_121126.csv",
    "ds003947": RAW_ROOTS["ds003947"] / "stratified_block_jacobians_subjects_114135.csv",
}
OUTPUT_DIR = ARTICLE_DIR / "results" / f"block_jacobian_contrasts_{RESULT_STAMP}"

CONTRASTS = [
    ("FEP_unmedicated", "Healthy"),
    ("FEP_medicated", "Healthy"),
    ("FEP_medicated", "FEP_unmedicated"),
]
CONTRAST_LABELS = {
    ("FEP_unmedicated", "Healthy"): "FEP_unmedicated_vs_Healthy",
    ("FEP_medicated", "Healthy"): "FEP_medicated_vs_Healthy",
    ("FEP_medicated", "FEP_unmedicated"): "FEP_medicated_vs_FEP_unmedicated",
}

DIAGONAL_METRICS = ["block_trace_mean", "block_frobenius_mean", "block_anisotropy_mean"]
OFFDIAG_METRICS = ["block_frobenius_mean", "c_sym_mean", "c_rot_mean"]
EPS = 1e-12


def bh_fdr(p_values: pd.Series) -> pd.Series:
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
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if a.size < 2 or b.size < 2:
        return float("nan")
    pooled = ((a.size - 1) * np.var(a, ddof=1) + (b.size - 1) * np.var(b, ddof=1)) / (a.size + b.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / np.sqrt(pooled))


def load_participant_groups(dataset: str) -> pd.DataFrame:
    """Read all H5 files, extract participant type + CPZ, assign group."""
    root = RAW_ROOTS[dataset]
    rows = []
    for sub_dir in sorted(root.iterdir()):
        if not sub_dir.is_dir() or not sub_dir.name.startswith("sub-"):
            continue
        h5_files = list(sub_dir.glob("*.h5"))
        if not h5_files:
            continue
        h5_path = h5_files[0]
        try:
            with h5py.File(h5_path, "r") as f:
                raw = f["participant/row_json"][()]
                if isinstance(raw, (bytes, np.bytes_)):
                    raw = raw.decode("utf-8")
                pinfo = json.loads(raw)
        except Exception as exc:
            print(f"  WARN: could not read {h5_path}: {exc}", file=sys.stderr)
            continue
        ptype = str(pinfo.get("type", "")).strip()
        cpz_raw = pinfo.get("CPZ_at_scan", None)
        try:
            cpz = float(cpz_raw)  # type: ignore[arg-type]
            is_nan = np.isnan(cpz)
        except (TypeError, ValueError):
            cpz = float("nan")
            is_nan = True
        if ptype == "Control":
            group = "Healthy"
        elif ptype == "Psychosis":
            group = "FEP_unmedicated" if (is_nan or cpz == 0.0) else "FEP_medicated"
        else:
            continue
        rows.append({
            "subject_id": pinfo.get("participant_id", sub_dir.name),
            "group": group,
            "cpz_at_scan": cpz,
        })
    return pd.DataFrame(rows)


def build_subject_wide(bj: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot block-Jacobian long table to one row per subject.
    Column names: <out_group>_to_<in_group>__<metric>
    """
    rows: list[dict] = []
    for subject_id, grp in bj.groupby("subject_id", sort=True):
        row: dict = {"subject_id": subject_id}
        for _, r in grp.iterrows():
            pair = f"{r['out_group']}_to_{r['in_group']}"
            is_diag = r["out_group"] == r["in_group"]
            metrics = DIAGONAL_METRICS if is_diag else OFFDIAG_METRICS
            for m in metrics:
                val = r.get(m, float("nan"))
                if val is not None:
                    row[f"{pair}__{m}"] = float(val) if pd.notna(val) else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def run_contrasts(wide: pd.DataFrame, participants: pd.DataFrame) -> pd.DataFrame:
    merged = wide.merge(participants[["subject_id", "group"]], on="subject_id", how="inner")
    metric_cols = [c for c in wide.columns if c != "subject_id"]

    rows = []
    for group_a, group_b in CONTRASTS:
        label = CONTRAST_LABELS[(group_a, group_b)]
        mask_a = merged["group"] == group_a
        mask_b = merged["group"] == group_b
        for col in metric_cols:
            vals_a = pd.to_numeric(merged.loc[mask_a, col], errors="coerce").dropna()
            vals_b = pd.to_numeric(merged.loc[mask_b, col], errors="coerce").dropna()
            if vals_a.empty or vals_b.empty or len(vals_a) < 2 or len(vals_b) < 2:
                continue
            # Parse pair and metric from column name
            parts = col.split("__", 1)
            pair = parts[0]
            metric = parts[1] if len(parts) > 1 else col
            out_grp, in_grp = (pair.split("_to_") + ["?"])[:2]
            is_diag = out_grp == in_grp
            p = float(mannwhitneyu(vals_a, vals_b, alternative="two-sided").pvalue)
            d = cohens_d(vals_a.to_numpy(dtype=float), vals_b.to_numpy(dtype=float))
            rows.append({
                "contrast": label,
                "group_a": group_a,
                "group_b": group_b,
                "block_pair": pair,
                "out_group": out_grp,
                "in_group": in_grp,
                "is_diagonal": is_diag,
                "metric": metric,
                "cohens_d": d,
                "abs_d": abs(d) if np.isfinite(d) else float("nan"),
                "mw_p": p,
                "median_a": float(vals_a.median()),
                "median_b": float(vals_b.median()),
                "n_a": int(len(vals_a)),
                "n_b": int(len(vals_b)),
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["mw_q"] = df.groupby(["contrast"])["mw_p"].transform(bh_fdr)
    df = df.sort_values(["contrast", "abs_d"], ascending=[True, False]).reset_index(drop=True)
    return df


def print_top(df: pd.DataFrame, dataset: str, top_n: int = 10) -> None:
    print(f"\n{'='*65}")
    print(f"BLOCK JACOBIAN CONTRASTS: {dataset}")
    print(f"{'='*65}")
    for contrast_label in df["contrast"].unique():
        sub = df[df["contrast"] == contrast_label]
        q_sig = sub[sub["mw_q"] <= 0.05]
        p_sig = sub[(sub["mw_p"] < 0.05) & (sub["mw_q"] > 0.05)]
        print(f"\n  {contrast_label}")
        print(f"  q<=0.05: {len(q_sig)}  |  p<0.05 (uncorr): {len(p_sig)}")
        top = sub.head(top_n)
        for _, row in top.iterrows():
            if row["mw_q"] <= 0.05:
                sig = "q"
            elif row["mw_p"] < 0.05:
                sig = "*"
            elif row["mw_p"] < 0.1:
                sig = "~"
            else:
                sig = " "
            diag = "[diag]" if row["is_diagonal"] else "      "
            arrow = f"{row['out_group']}->{row['in_group']}"
            print(f"    {sig} {diag} {arrow:6s} {row['metric']:25s}  d={row['cohens_d']:+.3f}  p={row['mw_p']:.4f}  q={row['mw_q']:.4f}  n=({row['n_a']},{row['n_b']})")


def summarize_coupling_pattern(df: pd.DataFrame) -> None:
    """Print a structured view of off-diagonal coupling directions."""
    print("\n--- Cross-family coupling summary (Frobenius norm, all contrasts) ---")
    offdiag = df[~df["is_diagonal"] & (df["metric"] == "block_frobenius_mean")].copy()
    if offdiag.empty:
        print("  (no off-diagonal Frobenius results)")
        return
    pivot = offdiag.pivot_table(
        index=["block_pair", "out_group", "in_group"],
        columns="contrast",
        values=["cohens_d", "mw_p"],
        aggfunc="first",
    )
    print(pivot.to_string())


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_dfs: list[pd.DataFrame] = []
    for dataset, csv_path in BLOCK_JAC_CSVS.items():
        if not csv_path.exists():
            print(f"[{dataset}] WARN: CSV not found at {csv_path}", file=sys.stderr)
            continue

        print(f"\n[{dataset}] Loading block Jacobians from {csv_path.name}")
        bj = pd.read_csv(csv_path)
        bj["subject_id"] = bj["subject_id"].astype(str)
        print(f"  {len(bj)} rows, {bj['subject_id'].nunique()} subjects")

        print(f"[{dataset}] Loading participant groups from H5 files...")
        participants = load_participant_groups(dataset)
        print(f"  {len(participants)} subjects with valid group assignments")
        gc = participants["group"].value_counts().to_dict()
        print(f"  Groups: {gc}")

        wide = build_subject_wide(bj)
        print(f"[{dataset}] Wide format: {wide.shape} ({len(wide)} subjects, {wide.shape[1]-1} metric columns)")

        df_contrasts = run_contrasts(wide, participants)
        df_contrasts["dataset"] = dataset
        all_dfs.append(df_contrasts)

        out_path = OUTPUT_DIR / f"{dataset}_block_jacobian_contrasts.csv"
        df_contrasts.to_csv(out_path, index=False)
        print(f"[{dataset}] Saved -> {out_path.name}")

        print_top(df_contrasts, dataset, top_n=12)
        summarize_coupling_pattern(df_contrasts)

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined.to_csv(OUTPUT_DIR / "combined_block_jacobian_contrasts.csv", index=False)
        print(f"\nCombined results -> {OUTPUT_DIR / 'combined_block_jacobian_contrasts.csv'}")

    print(f"\nResults in -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
