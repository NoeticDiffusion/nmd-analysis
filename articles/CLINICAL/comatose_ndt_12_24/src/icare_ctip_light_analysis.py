from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
INPUT_DIR = ARTICLE_DIR / "results" / "mnps_summary"
OUTPUT_DIR = ARTICLE_DIR / "results" / "ctip_light"
BLOCK_ANALYSIS = "global_mnps_jacobian_9d_block_jacobian"

RUN_KEY_CANDIDATES: tuple[str, ...] = (
    "dataset_id",
    "subject_id",
    "session",
    "run",
    "acq",
    "group",
    "condition",
    "task",
    "modality",
    "source_h5_path",
    "normalized_source_h5_path",
    "subject",
    "subject_numeric",
    "processed_h5_path",
    "hospital",
    "age",
    "sex",
    "rosc_minutes",
    "ohca",
    "shockable_rhythm",
    "ttm_celsius",
    "outcome",
    "cpc",
    "time_reference_status",
    "run_anchor_source",
    "time_bin",
    "run_start_from_anchor_hours",
    "run_end_from_anchor_hours",
)
PATIENT_KEY_CANDIDATES: tuple[str, ...] = (
    "subject",
    "time_bin",
    "outcome",
    "cpc",
    "hospital",
    "age",
    "sex",
    "rosc_minutes",
    "ttm_celsius",
    "time_reference_status",
    "run_anchor_source",
    "run_start_from_anchor_hours_min",
    "run_end_from_anchor_hours_max",
)
DERIVED_METRIC_COLUMNS: tuple[str, ...] = (
    "capacity_3d_spread_raw",
    "capacity_9d_spread_raw",
    "capacity_reachability_raw",
    "q_ratio_h4",
    "capture_gate",
    "cfca",
    "ati_reduced_proxy",
    "ati_full_proxy",
    "ctip_c_light",
    "ctip_ti_light",
    "ctip_p_light",
    "ctip_light_radius",
    "capacity_3d_spread_z",
    "capacity_9d_spread_z",
    "capacity_reachability_z",
    "rotation_norm_z",
    "anisotropy_z",
    "jacobian_cond_z",
    "aci_z",
    "q_ratio_h4_z",
    "capture_gate_z",
    "cfca_z",
)


@dataclass(frozen=True)
class CtipConfig:
    input_dir: Path
    output_dir: Path


def parse_args() -> CtipConfig:
    parser = argparse.ArgumentParser(
        description="Build a first coma C/TI/P-light layer from mnps_summary handoff metrics."
    )
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    return CtipConfig(input_dir=args.input_dir, output_dir=args.output_dir)


def robust_z(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    finite = values[np.isfinite(values)]
    out = pd.Series(np.nan, index=series.index, dtype=float)
    if finite.empty:
        return out
    if finite.size == 1:
        out.loc[np.isfinite(values)] = 0.0
        return out
    median = float(finite.median())
    mad = float(np.median(np.abs(finite.to_numpy(dtype=float) - median)))
    if mad <= 1e-12 or not np.isfinite(mad):
        out.loc[np.isfinite(values)] = 0.0
        return out
    out.loc[np.isfinite(values)] = (values.loc[np.isfinite(values)] - median) / (1.4826 * mad)
    return out


def mean_of_columns(frame: pd.DataFrame, columns: Iterable[str]) -> pd.Series:
    present = [column for column in columns if column in frame.columns]
    if not present:
        return pd.Series(np.nan, index=frame.index, dtype=float)
    values = frame[present].apply(pd.to_numeric, errors="coerce")
    return values.mean(axis=1, skipna=True)


def first_non_null(frame: pd.DataFrame, columns: Iterable[str]) -> pd.Series:
    present = [column for column in columns if column in frame.columns]
    if not present:
        return pd.Series(np.nan, index=frame.index, dtype=float)
    out = pd.Series(np.nan, index=frame.index, dtype=float)
    for column in present:
        candidate = pd.to_numeric(frame[column], errors="coerce")
        out = out.where(np.isfinite(out), candidate)
    return out


def numeric_series_from_wide(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(np.nan, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def load_metric_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame


def select_key_columns(frame: pd.DataFrame, key_candidates: tuple[str, ...]) -> list[str]:
    selected: list[str] = []
    for column in key_candidates:
        if column not in frame.columns:
            continue
        series = frame[column]
        if series.notna().any():
            selected.append(column)
    return selected


def build_cfca_frame(frame: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    source = frame[
        (frame["analysis_type"] == BLOCK_ANALYSIS)
        & (frame["metric"] == "block_frobenius_mean")
    ].copy()
    if source.empty:
        return pd.DataFrame(columns=[*key_cols, "cfca"])
    for column in ("source_group", "target_group"):
        if column not in source.columns:
            source[column] = None
    source["block_key"] = source["target_group"].astype(str) + "_" + source["source_group"].astype(str)
    wide = source.pivot_table(index=key_cols, columns="block_key", values="value", aggfunc="first").reset_index()
    components = []
    for left, right in (("m_d", "d_m"), ("m_e", "e_m"), ("d_e", "e_d")):
        left_vals = numeric_series_from_wide(wide, left)
        right_vals = numeric_series_from_wide(wide, right)
        comp = (left_vals - right_vals).abs() / (left_vals.abs() + right_vals.abs() + 1e-12)
        components.append(comp.rename(f"cfca_{left}_{right}"))
    comp_frame = pd.concat(components, axis=1)
    wide["cfca"] = comp_frame.sum(axis=1, min_count=1)
    return wide[key_cols + ["cfca"]]


def build_base_wide_frame(frame: pd.DataFrame, key_candidates: tuple[str, ...]) -> pd.DataFrame:
    key_cols = select_key_columns(frame, key_candidates)
    base = frame[frame["analysis_type"] != BLOCK_ANALYSIS].copy()
    wide = base.pivot_table(index=key_cols, columns="metric", values="value", aggfunc="first").reset_index()
    cfca = build_cfca_frame(frame, key_cols)
    if not cfca.empty:
        wide = wide.merge(cfca, on=key_cols, how="left")
    return wide


def derive_ctip_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "cfca" not in out.columns:
        out["cfca"] = np.nan
    out["capacity_3d_spread_raw"] = mean_of_columns(out, ("m_std", "d_std", "e_std"))
    out["capacity_9d_spread_raw"] = mean_of_columns(
        out,
        ("m_a_std", "m_e_std", "m_o_std", "d_n_std", "d_l_std", "d_s_std", "e_e_std", "e_s_std", "e_m_std"),
    )
    out["capacity_reachability_raw"] = first_non_null(out, ("tube_d_eff_median", "cone_d_eff_h4_median"))
    out["q_ratio_h4"] = first_non_null(out, ("q_ratio_h4_median", "tube_q_ratio_h4_median"))
    out["capture_gate"] = first_non_null(out, ("tube_capture_gate_median",))

    out["capacity_3d_spread_z"] = robust_z(out["capacity_3d_spread_raw"])
    out["capacity_9d_spread_z"] = robust_z(out["capacity_9d_spread_raw"])
    out["capacity_reachability_z"] = robust_z(out["capacity_reachability_raw"])
    out["rotation_norm_z"] = robust_z(first_non_null(out, ("rotation_norm_median",)))
    out["anisotropy_z"] = robust_z(first_non_null(out, ("anisotropy_abs_eig_median",)))
    out["jacobian_cond_z"] = robust_z(first_non_null(out, ("jacobian_cond_median",)))
    out["aci_z"] = robust_z(first_non_null(out, ("aci_median",)))
    out["q_ratio_h4_z"] = robust_z(out["q_ratio_h4"])
    out["capture_gate_z"] = robust_z(out["capture_gate"])
    out["cfca_z"] = robust_z(out["cfca"])

    out["ati_reduced_proxy"] = mean_of_columns(out, ("capacity_3d_spread_z", "rotation_norm_z"))
    out["ati_full_proxy"] = out["ati_reduced_proxy"] - out["anisotropy_z"]
    out["ctip_c_light"] = mean_of_columns(
        out,
        ("capacity_3d_spread_z", "capacity_9d_spread_z", "capacity_reachability_z"),
    )
    out["ctip_ti_light"] = mean_of_columns(
        out.assign(
            ati_component=out["ati_full_proxy"].where(np.isfinite(out["ati_full_proxy"]), out["ati_reduced_proxy"]),
            anti_q_ratio=-out["q_ratio_h4_z"],
            anti_capture=-out["capture_gate_z"],
        ),
        ("ati_component", "anti_q_ratio", "anti_capture"),
    )
    out["ctip_p_light"] = mean_of_columns(
        out,
        ("jacobian_cond_z", "aci_z", "anisotropy_z", "cfca_z"),
    )
    out["ctip_light_radius"] = np.sqrt(
        np.square(pd.to_numeric(out["ctip_c_light"], errors="coerce"))
        + np.square(pd.to_numeric(out["ctip_ti_light"], errors="coerce"))
        + np.square(pd.to_numeric(out["ctip_p_light"], errors="coerce"))
    )
    return out


def build_long_metric_frame(frame: pd.DataFrame, *, summary_level: str) -> pd.DataFrame:
    key_cols = [column for column in frame.columns if column not in DERIVED_METRIC_COLUMNS]
    rows: List[pd.DataFrame] = []
    for metric in DERIVED_METRIC_COLUMNS:
        if metric not in frame.columns:
            continue
        metric_frame = frame[key_cols].copy()
        metric_frame["metric"] = metric
        metric_frame["value"] = pd.to_numeric(frame[metric], errors="coerce")
        metric_frame = metric_frame[np.isfinite(metric_frame["value"].to_numpy(dtype=float))]
        if metric_frame.empty:
            continue
        metric_frame["summary_level"] = summary_level
        metric_frame["metric_family"] = "ctip_light"
        rows.append(metric_frame)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def build_manifest(patient_long: pd.DataFrame, run_long: pd.DataFrame) -> dict[str, Any]:
    def available_metrics(frame: pd.DataFrame) -> list[str]:
        if frame.empty:
            return []
        return sorted(frame["metric"].dropna().astype(str).unique().tolist())

    return {
        "patient_timebin_metrics_file": "patient_timebin_ctip_light_metrics.csv",
        "run_level_metrics_file": "run_level_ctip_light_metrics.csv",
        "wide_patient_timebin_file": "patient_timebin_ctip_light_wide.csv",
        "wide_run_level_file": "run_level_ctip_light_wide.csv",
        "available_metrics_patient_timebin": available_metrics(patient_long),
        "available_metrics_run_level": available_metrics(run_long),
        "axis_direction_note": {
            "ctip_c_light": "higher means greater residual capacity / spread / reachability",
            "ctip_ti_light": "higher means more innovation-dominated and less capture-dominated",
            "ctip_p_light": "higher means stronger pathological lock-in proxy",
        },
        "construction_note": (
            "This is a first paper-facing C/TI/P-light layer derived from existing mnps_summary outputs. "
            "It reuses reachability aliases (q_ratio_h4, capture_gate), block asymmetry (cfca), and Jacobian proxies "
            "without claiming full theory validation."
        ),
    }


def build_qc_summary(patient_wide: pd.DataFrame, run_wide: pd.DataFrame) -> dict[str, Any]:
    def axis_counts(frame: pd.DataFrame) -> dict[str, int]:
        if frame.empty:
            return {}
        return {
            "rows_total": int(len(frame)),
            "rows_with_capacity_reachability_raw": int(
                pd.to_numeric(frame.get("capacity_reachability_raw"), errors="coerce").notna().sum()
            ),
            "rows_with_q_ratio_h4": int(pd.to_numeric(frame.get("q_ratio_h4"), errors="coerce").notna().sum()),
            "rows_with_capture_gate": int(pd.to_numeric(frame.get("capture_gate"), errors="coerce").notna().sum()),
            "rows_with_cfca": int(pd.to_numeric(frame.get("cfca"), errors="coerce").notna().sum()),
            "rows_with_ctip_c_light": int(pd.to_numeric(frame["ctip_c_light"], errors="coerce").notna().sum()),
            "rows_with_ctip_ti_light": int(pd.to_numeric(frame["ctip_ti_light"], errors="coerce").notna().sum()),
            "rows_with_ctip_p_light": int(pd.to_numeric(frame["ctip_p_light"], errors="coerce").notna().sum()),
            "rows_with_full_ctip_triplet": int(
                (
                    pd.to_numeric(frame["ctip_c_light"], errors="coerce").notna()
                    & pd.to_numeric(frame["ctip_ti_light"], errors="coerce").notna()
                    & pd.to_numeric(frame["ctip_p_light"], errors="coerce").notna()
                ).sum()
            ),
        }

    return {
        "patient_timebin": axis_counts(patient_wide),
        "run_level": axis_counts(run_wide),
    }


def build_summary_markdown(qc_summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# C/TI/P-light summary",
            "",
            "## Coverage",
            "",
            f"- patient_timebin: {qc_summary.get('patient_timebin', {})}",
            f"- run_level: {qc_summary.get('run_level', {})}",
            "",
            "## Note",
            "",
            "This layer is intended as a first paper-facing synthesis built from existing handoff metrics.",
            "It is not a claim of full C/TI/P validation, but a reusable derived space for later outcome contrasts and figure generation.",
            "",
        ]
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_outputs(
    config: CtipConfig,
    patient_wide: pd.DataFrame,
    run_wide: pd.DataFrame,
    patient_long: pd.DataFrame,
    run_long: pd.DataFrame,
    qc_summary: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    ensure_dir(config.output_dir)
    patient_wide.to_csv(config.output_dir / "patient_timebin_ctip_light_wide.csv", index=False)
    run_wide.to_csv(config.output_dir / "run_level_ctip_light_wide.csv", index=False)
    patient_long.to_csv(config.output_dir / "patient_timebin_ctip_light_metrics.csv", index=False)
    run_long.to_csv(config.output_dir / "run_level_ctip_light_metrics.csv", index=False)
    (config.output_dir / "ctip_light_qc.json").write_text(json.dumps(qc_summary, indent=2), encoding="utf-8")
    (config.output_dir / "ctip_light_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (config.output_dir / "ctip_light_summary.md").write_text(build_summary_markdown(qc_summary), encoding="utf-8")


def main() -> None:
    config = parse_args()
    patient_metrics = load_metric_frame(config.input_dir / "patient_timebin_signal_metrics.csv")
    run_metrics = load_metric_frame(config.input_dir / "run_level_signal_metrics.csv")

    patient_wide = derive_ctip_columns(build_base_wide_frame(patient_metrics, PATIENT_KEY_CANDIDATES))
    run_wide = derive_ctip_columns(build_base_wide_frame(run_metrics, RUN_KEY_CANDIDATES))
    patient_long = build_long_metric_frame(patient_wide, summary_level="patient_timebin")
    run_long = build_long_metric_frame(run_wide, summary_level="run_level")
    qc_summary = build_qc_summary(patient_wide, run_wide)
    manifest = build_manifest(patient_long, run_long)
    write_outputs(config, patient_wide, run_wide, patient_long, run_long, qc_summary, manifest)

    print(f"Wrote patient C/TI/P-light metrics to {config.output_dir / 'patient_timebin_ctip_light_metrics.csv'}")
    print(f"Wrote run-level C/TI/P-light metrics to {config.output_dir / 'run_level_ctip_light_metrics.csv'}")
    print(f"Wrote QC summary to {config.output_dir / 'ctip_light_qc.json'}")


if __name__ == "__main__":
    main()
