"""Coverage of dynamical-family identities L0–L4 on the Apollo 80-file export.

Inventory only. Does not license Ito, Family B, consciousness, or stage contrasts.
Reuses the I-CARE 3.0.1 metric catalog so the two articles stay comparable.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from apollo_common import (
    ARTICLE_DIR,
    DEFAULT_H5_ROOT,
    REPO_ROOT,
    discover_h5_files,
    parse_run_stem,
    write_json,
)

COMA_SRC = REPO_ROOT / "articles" / "CLINICAL" / "coma_ndt_v.1.0" / "src"
if str(COMA_SRC) not in sys.path:
    sys.path.insert(0, str(COMA_SRC))

from icare_v2_v301_coverage_matrix import (  # noqa: E402
    FAMILY_ORDER,
    METRICS,
    _EMPTY,
    _aggregate,
    _fmt_frac,
    _status_fields,
    _value_stats,
)

LABELS_DEFAULT = ARTICLE_DIR / "results" / "ingest_20260920" / "g1_recording_labels.csv"
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_coverage_20260921"

# Numbered identities in the new dynamical-family register. Adjacent chart /
# jacobian / FTR objects are kept in the matrix but not rolled into L0–L4.
LEVEL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "L0",
        (
            "increment_covariance_level0",
            "realized_velocity_level0",
            "turning_angle_level0",
            "turning_rate_level0",
        ),
    ),
    (
        "L1",
        (
            "diffusion_a_hat",
            "diffusion_d_diff",
            "diffusion_D_total",
            "diffusion_A_bD",
            "diffusion_R_b_over_a",
            "chart_drift_b_hat_pooled",
            "chart_drift_b_hat_crossfit",
            "chart_drift_lag_diagnostics",
            "amplification_neighbor_gain_q90_level1",
            "amplification_neighbor_gain_rate_q90_level1",
            "amplification_neighbor_separation_rate_level1",
            "amplification_cloud_volume_change_rate_level1",
            "history_predictive_gain_level1",
        ),
    ),
    (
        "L2",
        (
            "one_step_lag1_affine_one_step_map_level2",
            "one_step_lag1_conditional_affine_mean_rate_level2",
            "one_step_lag1_innovation_covariance_level2",
            "one_step_lag1_operator_max_gain_rate_level2",
            "one_step_lag1_operator_volume_gain_rate_level2",
            "one_step_lag1_operator_rotation_rate_level2",
            "history_conditioned_operator_level2",
            "one_step_lag2_affine_one_step_map_level2",
            "one_step_lag2_conditional_affine_mean_rate_level2",
            "one_step_lag2_innovation_covariance_level2",
            "one_step_lag2_operator_max_gain_rate_level2",
            "one_step_lag2_operator_volume_gain_rate_level2",
            "one_step_lag2_operator_rotation_rate_level2",
        ),
    ),
    (
        "L3",
        (
            "one_step_lag1_spectral_abscissa_level3",
            "one_step_lag1_numerical_abscissa_level3",
            "one_step_lag1_divergence_level3",
            "one_step_lag1_generator_rotation_norm_level3",
            "one_step_lag2_spectral_abscissa_level3",
            "one_step_lag2_numerical_abscissa_level3",
            "one_step_lag2_divergence_level3",
            "one_step_lag2_generator_rotation_norm_level3",
        ),
    ),
    (
        "L4",
        (
            "one_step_lag1_iterated_horizon_map_level4",
            "resilience",
            "reach_3d",
            "reach_9d",
        ),
    ),
)
LEVEL_BY_METRIC = {metric: level for level, metrics in LEVEL_RULES for metric in metrics}
HEADLINE = (
    "increment_covariance_level0",
    "realized_velocity_level0",
    "diffusion_a_hat",
    "diffusion_A_bD",
    "chart_drift_b_hat_pooled",
    "amplification_neighbor_gain_q90_level1",
    "history_predictive_gain_level1",
    "turning_angle_level0",
    "one_step_lag1_affine_one_step_map_level2",
    "history_conditioned_operator_level2",
    "one_step_lag1_spectral_abscissa_level3",
    "one_step_lag1_iterated_horizon_map_level4",
    "one_step_lag2_affine_one_step_map_level2",
    "destination",
    "resilience",
    "reach_3d",
)


def inspect_h5(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "stem": Path(path).stem,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
    }
    try:
        import h5py

        with h5py.File(path, "r") as handle:
            row["mndm_version"] = str(handle.attrs.get("mndm_version") or "")
            for spec in METRICS:
                mid = spec["metric_id"]
                info = _status_fields(handle, spec["group"])
                row[f"{mid}__present"] = bool(info["present"])
                row[f"{mid}__status"] = info["status"]
                row[f"{mid}__qual"] = info["qual"]
                row[f"{mid}__failure"] = info["failure"]
                stats = _value_stats(handle, spec) if info["present"] else dict(_EMPTY)
                row[f"{mid}__ge1_finite"] = bool(stats["ge1_finite"])
                row[f"{mid}__finite_frac"] = stats["finite_frac"]
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def level_rollup(matrix: pd.DataFrame, by_file: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n_files = int(len(by_file))
    for level, metrics in LEVEL_RULES:
        block = matrix[matrix["metric_id"].isin(metrics)].copy()
        any_computed = np.zeros(n_files, dtype=bool)
        any_finite = np.zeros(n_files, dtype=bool)
        for mid in metrics:
            status_col = f"{mid}__status"
            finite_col = f"{mid}__ge1_finite"
            if status_col in by_file.columns:
                any_computed |= by_file[status_col].isin(["computed", "exported"]).to_numpy()
            if finite_col in by_file.columns:
                any_finite |= by_file[finite_col].fillna(False).astype(bool).to_numpy()
        rows.append(
            {
                "level": level,
                "n_identities": int(len(metrics)),
                "n_identities_with_any_finite": int((block["n_ge1_finite"] > 0).sum()),
                "n_identities_computed_on_all_files": int((block["n_computed"] == n_files).sum()),
                "median_ge1_finite_frac": float(block["ge1_finite_frac"].median()) if len(block) else float("nan"),
                "min_ge1_finite_frac": float(block["ge1_finite_frac"].min()) if len(block) else float("nan"),
                "max_ge1_finite_frac": float(block["ge1_finite_frac"].max()) if len(block) else float("nan"),
                "n_files_with_any_identity_computed": int(any_computed.sum()),
                "n_files_with_any_identity_finite": int(any_finite.sum()),
                "n_files": n_files,
            }
        )
    return pd.DataFrame(rows)


def phase_coverage(by_file: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    merged = by_file.merge(
        labels[["source_h5", "protocol_phase_label"]],
        on="source_h5",
        how="left",
    )
    headline = [
        "diffusion_a_hat",
        "one_step_lag1_affine_one_step_map_level2",
        "history_conditioned_operator_level2",
        "one_step_lag1_spectral_abscissa_level3",
        "one_step_lag1_iterated_horizon_map_level4",
        "one_step_lag2_affine_one_step_map_level2",
        "resilience",
        "reach_3d",
    ]
    rows = []
    for phase, group in merged.groupby("protocol_phase_label"):
        n = int(len(group))
        for mid in headline:
            finite = int(group[f"{mid}__ge1_finite"].fillna(False).astype(bool).sum())
            computed = int(group[f"{mid}__status"].isin(["computed", "exported"]).sum())
            status_mode = Counter(str(v) for v in group[f"{mid}__status"].tolist()).most_common(1)
            rows.append(
                {
                    "protocol_phase_label": phase,
                    "level": LEVEL_BY_METRIC.get(mid, "other"),
                    "metric_id": mid,
                    "n_recordings": n,
                    "n_computed": computed,
                    "n_ge1_finite": finite,
                    "ge1_finite_frac": finite / n if n else float("nan"),
                    "status_mode": status_mode[0][0] if status_mode else None,
                }
            )
    return pd.DataFrame(rows)


def render_md(
    matrix: pd.DataFrame,
    levels: pd.DataFrame,
    phases: pd.DataFrame,
    *,
    n_files: int,
    n_ok: int,
) -> str:
    by_id = {row["metric_id"]: row for _, row in matrix.iterrows()}
    lines = [
        "# Apollo dynamical-family coverage (L0–L4)",
        "",
        f"Export `neuralmanifolddynamics_Sedation-RestingState_20260918_075713`. Files read: {n_ok}/{n_files}.",
        "",
        "A file **has a value** when the primary series contains at least one finite number.",
        "`computed` is the group certificate. This is an inventory, not a propofol contrast,",
        "not Itô identification, and not consciousness.",
        "",
        "## Level rollup",
        "",
        "| Level | Identities | Any finite on ≥1 file | Computed on all 80 | Median file coverage | Files with any identity finite |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in levels.iterrows():
        lines.append(
            "| {level} | {n_id} | {any_id} | {all80} | {med:.1%} | {files}/{n} |".format(
                level=row["level"],
                n_id=int(row["n_identities"]),
                any_id=int(row["n_identities_with_any_finite"]),
                all80=int(row["n_identities_computed_on_all_files"]),
                med=row["median_ge1_finite_frac"],
                files=int(row["n_files_with_any_identity_finite"]),
                n=int(row["n_files"]),
            )
        )
    lines.extend(
        [
            "",
            "## Headline identities",
            "",
            "| Metric | Level | >=1 finite | Computed/exported | Status mode |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for mid in HEADLINE:
        row = by_id[mid]
        n = int(row["n_files"])
        lines.append(
            f"| `{mid}` | {LEVEL_BY_METRIC.get(mid, 'adjacent')} | "
            f"{_fmt_frac(int(row['n_ge1_finite']), n)} | "
            f"{_fmt_frac(int(row['n_computed']), n)} | `{row['status_mode']}` |"
        )
    if not phases.empty:
        lines.extend(
            [
                "",
                "## One-step / L4 by protocol phase",
                "",
                "| Phase | Metric | >=1 finite | Computed | Status mode |",
                "| --- | --- | ---: | ---: | --- |",
            ]
        )
        for _, row in phases.iterrows():
            n = int(row["n_recordings"])
            lines.append(
                f"| `{row['protocol_phase_label']}` | `{row['metric_id']}` | "
                f"{_fmt_frac(int(row['n_ge1_finite']), n)} | "
                f"{_fmt_frac(int(row['n_computed']), n)} | `{row['status_mode']}` |"
            )
    family_rank = {name: i for i, name in enumerate(FAMILY_ORDER)}
    ordered = matrix.copy()
    ordered["ndt_level"] = ordered["metric_id"].map(lambda mid: LEVEL_BY_METRIC.get(mid, "adjacent"))
    ordered["_rank"] = ordered["family"].map(lambda name: family_rank.get(name, 99))
    ordered = ordered.sort_values(["_rank"], kind="stable")
    for family, block in ordered.groupby("family", sort=False):
        lines += [
            f"## {family}",
            "",
            "| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
        for _, row in block.iterrows():
            n = int(row["n_files"])
            qual = row["qualification_mode"] or row["failure_mode"] or "-"
            mean_f = row["mean_series_finite_frac"]
            mean_s = "n/a" if not np.isfinite(mean_f) else f"{mean_f:.3f}"
            lines.append(
                f"| `{row['metric_id']}` | {row['ndt_level']} | "
                f"{_fmt_frac(int(row['n_present']), n)} | "
                f"{_fmt_frac(int(row['n_computed']), n)} | "
                f"{_fmt_frac(int(row['n_ge1_finite']), n)} | "
                f"{mean_s} | `{row['status_mode']}` | `{qual}` |"
            )
        lines.append("")
    lines += [
        "## How to read this",
        "",
        "- L0 = realized increment objects. L1 = local conditional / same-pair / history-gain.",
        "- L2 = identified one-step map and its functionals, plus history-conditioned operator.",
        "- L3 = generator proxy from a qualified one-step map. Not Family B Jacobian α.",
        "- L4 = iterated horizon map, FAR, and stochastic reachability. Destination is unnumbered `not_testable`.",
        "- `A_bD` / `R_b_over_a` can be `computed` with all-NaN series when drift_source is not supplied.",
        "- Lag-2 one-step and L4 horizon maps are not substitutes for lag-1 coverage.",
        "",
    ]
    return "\n".join(lines)


def run(*, h5_root: Path, labels_path: Path, output_root: Path, workers: int) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    paths = [str(path) for path in discover_h5_files(h5_root)]
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        rows = list(pool.map(inspect_h5, paths))
    by_file = pd.DataFrame(rows)
    by_file.to_csv(output_root / "coverage_by_file.csv", index=False)
    matrix = _aggregate(by_file)
    matrix["ndt_level"] = matrix["metric_id"].map(lambda mid: LEVEL_BY_METRIC.get(mid, "adjacent"))
    matrix.to_csv(output_root / "coverage_matrix.csv", index=False)
    levels = level_rollup(matrix, by_file)
    levels.to_csv(output_root / "coverage_by_level.csv", index=False)
    phases = pd.DataFrame()
    if labels_path.is_file():
        labels = pd.read_csv(labels_path)
        phases = phase_coverage(by_file, labels)
        phases.to_csv(output_root / "coverage_by_phase.csv", index=False)
    md = render_md(
        matrix,
        levels,
        phases,
        n_files=int(len(by_file)),
        n_ok=int(by_file["read_ok"].sum()),
    )
    (output_root / "coverage_matrix.md").write_text(md, encoding="utf-8")
    manifest = {
        "schema": "apollo_propofol_ndt_v1.coverage.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "n_files": int(len(by_file)),
        "n_read_ok": int(by_file["read_ok"].sum()),
        "h5_root": str(h5_root),
        "level_rollup": levels.to_dict("records"),
        "claim_status": "no_biological_claim",
    }
    write_json(output_root / "coverage_matrix.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_H5_ROOT)
    parser.add_argument("--labels", type=Path, default=LABELS_DEFAULT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)
    manifest = run(
        h5_root=args.input_root,
        labels_path=args.labels,
        output_root=args.output_root,
        workers=args.workers,
    )
    print(pd.DataFrame(manifest["level_rollup"]).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
