"""Part1 extract for A_dom and within-run IQRs (sl_010 second priority)."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from icare_v2_common import (
    add_common_args,
    discover_h5_files,
    parallel_map,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    time_reference_from_handle,
    write_csv,
    write_json,
)
from icare_v2_outcome_contrast_analysis import _contrast_row
from icare_v2_v301_ddc_metrics import _finite_iqr, estimate_crossfit_coupling
from icare_v2_v301_l1_estimators import _segment_id, estimate_g90, series_median
from icare_v2_v301_l1_panel import _annotate


def extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            row.update(timing)
            xc = np.asarray(handle["/coords_3d_cohort_anchored/values"][:], dtype=float)
            time = np.asarray(handle["/time"][:], dtype=float)
            raw = handle["/row_source/raw_file"][:] if "/row_source/raw_file" in handle else None
            seg = _segment_id(raw, xc.shape[0])
            ddc = estimate_crossfit_coupling(xc, time, segment_id=seg)
            med = ddc.get("medians") or {}
            iqr = ddc.get("iqrs") or {}
            row["ddc_status"] = ddc.get("status")
            row["a_dom_median"] = med.get("a_dom", float("nan"))
            row["r_ba_within_iqr"] = iqr.get("r_ba", float("nan"))
            row["f_perp_within_iqr"] = iqr.get("f_perp", float("nan"))
            g = estimate_g90(xc, time, segment_id=seg, chart_name="coords_3d_cohort_anchored")
            series = (g.get("series") or {}).get("neighbor_gain_q90")
            row["g90_within_iqr"] = _finite_iqr(series) if series is not None else float("nan")
            row["g90_recompute_median"] = series_median(g, "neighbor_gain_q90")
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: A_dom/within-IQR extract {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="adom")
    runs = _annotate(pd.DataFrame(rows), cfg)
    write_csv(cfg.output_dir / "ddc_adom_run_level.csv", runs)
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    patients = work.groupby("subject_id", as_index=False).agg(
        cpc=("cpc", "first"),
        contrast_group=("contrast_group", "first"),
        a_dom_median=("a_dom_median", "median"),
        g90_within_iqr=("g90_within_iqr", "median"),
        r_ba_within_iqr=("r_ba_within_iqr", "median"),
    )
    specs = (
        ("adom_exploratory", "a_dom_median", "A_dom", "CPC1 < CPC5; exploratory until gate"),
        ("within_iqr", "g90_within_iqr", "G90_within", "unspecified"),
        ("within_iqr", "r_ba_within_iqr", "R_ba_within", "unspecified"),
    )
    contrast_rows = []
    for family, metric, hyp, pred in specs:
        if metric in patients.columns:
            contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family=family, hypothesis=hyp, prediction=pred))
    contrasts = pd.DataFrame(contrast_rows)
    write_csv(cfg.output_dir / "adom_patient_primary.csv", patients)
    write_csv(cfg.output_dir / "adom_contrasts.csv", contrasts)
    write_json(cfg.output_dir / "adom_part1_manifest.json", {"experiment": "A_dom_exploratory", "part2_opened": False})
    print(f"wrote {cfg.output_dir / 'ddc_adom_run_level.csv'}", flush=True)
    if not contrasts.empty:
        print(contrasts[["family", "metric", "n_cpc1", "n_cpc5", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
