"""Event-onset pilot, subject-level NDT v1.0 frequency reanalysis for ds006036.

This is deliberately an analysis-layer reader.  It never changes the H5
measurements and it only summarizes finite, overlay-contained sequences already
exported by NeuralManifoldDynamics. The units of inference are subjects, not
windows. ds004504 is used solely for matched-rest reference exports.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import h5py
import numpy as np
from scipy.stats import mannwhitneyu


STAGES = {50: "photo_5hz", 51: "photo_10hz", 52: "photo_15hz", 53: "photo_20hz"}
GROUPS = {"A": "AD", "F": "FTD", "C": "Healthy", "H": "Healthy"}
FTR_METRICS = ("log_g_max", "d_resp", "c_1", "transfer_self", "transfer_cross")
JACOBIAN_METRICS = (
    "spectral_abscissa", "numerical_abscissa", "reactivity_gap", "rotation_norm",
)


def scalar(value):
    value = value[()]
    return value.decode() if isinstance(value, bytes) else value.item() if hasattr(value, "item") else value


def h5_files(root: Path):
    return sorted(root.glob("sub-*/*.h5"))


def group_of(h5: h5py.File) -> str:
    raw = h5.attrs.get("group", "")
    raw = raw.decode() if isinstance(raw, bytes) else str(raw)
    return GROUPS.get(raw.strip(), raw.strip() or "Unknown")


def finite_median(values: np.ndarray) -> tuple[float, int]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return (float(np.median(values)), int(values.size)) if values.size else (float("nan"), 0)


def add_row(rows, *, subject, group, frequency, family, metric, values):
    value, n = finite_median(values)
    rows.append({
        "subject_id": subject, "group": group, "frequency": frequency,
        "family": family, "metric": metric, "value": value,
        "n_sequences_valid": n,
    })


def event_onset_pilot_stage(h5: h5py.File, block_windows: int = 5):
    """Return a transparent 20-second, event-onset pilot overlay.

    The canonical labels/stage layer does not retain the 10/15/20 Hz blocks in
    this export.  The overlay is derived only from the versioned raw frequency
    onsets and is intentionally never presented as a canonical stage layer.
    """
    time = np.asarray(h5["time"], dtype=float)
    stage = np.full(time.shape, -1, dtype=int)
    audit = []
    for code, frequency in STAGES.items():
        event_path = f"events/raw_{frequency}_onset_sec"
        if event_path not in h5:
            audit.append({"frequency": frequency, "raw_onset_count": 0,
                          "selected_onset_sec": float("nan"), "assigned_windows": 0})
            continue
        onsets = np.sort(np.asarray(h5[event_path], dtype=float))
        finite_onsets = onsets[np.isfinite(onsets)]
        # The protocol has one frequency step per recording. Retaining all
        # repeated onset markers would silently lengthen some blocks, so the
        # first versioned onset is the sole eligible anchor and repeats remain
        # visible in the audit rather than being pooled as observations.
        assigned = 0
        if finite_onsets.size:
            start = int(np.searchsorted(time, finite_onsets[0], side="left"))
            stop = min(start + block_windows, len(stage))
            if start < len(stage):
                stage[start:stop] = code
                assigned = stop - start
        audit.append({"frequency": frequency, "raw_onset_count": int(finite_onsets.size),
                      "selected_onset_sec": float(finite_onsets[0]) if finite_onsets.size else float("nan"),
                      "assigned_windows": assigned})
    return stage, audit


def photic_rows(path: Path):
    rows, audit_rows = [], []
    with h5py.File(path, "r") as h5:
        subject, group = str(h5.attrs["subject_id"]), group_of(h5)
        stage, stage_audit = event_onset_pilot_stage(h5)
        audit_rows.extend({"subject_id": subject, "group": group, **row} for row in stage_audit)
        # A one-step FTR sequence is eligible only when both endpoints stay in
        # one explicitly labelled photic block.  This excludes transitions at
        # block boundaries rather than assigning them to a frequency.
        ftr_h1 = h5["finite_time_response/v1/stratified_9d/horizons/h1"]
        ftr = ftr_h1["series"]
        starts = np.asarray(ftr_h1["start_windows"], dtype=int)
        valid_start = (starts >= 0) & (starts + 1 < len(stage))
        for code, frequency in STAGES.items():
            mask = valid_start.copy()
            mask[valid_start] = (stage[starts[valid_start]] == code) & (stage[starts[valid_start] + 1] == code)
            for metric in FTR_METRICS:
                add_row(rows, subject=subject, group=group, frequency=frequency,
                        family="finite_time_response_9d_h1", metric=metric,
                        values=np.asarray(ftr[metric])[mask])

        jac = h5["jacobian_9D/derived_metrics/v1/series"]
        centers = np.asarray(h5["jacobian_9D/centers"], dtype=int)
        valid_center = (centers >= 0) & (centers < len(stage))
        for code, frequency in STAGES.items():
            mask = valid_center.copy()
            mask[valid_center] = stage[centers[valid_center]] == code
            for metric in JACOBIAN_METRICS:
                add_row(rows, subject=subject, group=group, frequency=frequency,
                        family="jacobian_9d", metric=metric,
                        values=np.asarray(jac[metric])[mask])
    return rows, audit_rows


def rest_rows(path: Path):
    rows = []
    with h5py.File(path, "r") as h5:
        subject, group = str(h5.attrs["subject_id"]), group_of(h5)
        ftr = h5["finite_time_response/v1/stratified_9d/horizons/h1/series"]
        for metric in FTR_METRICS:
            add_row(rows, subject=subject, group=group, frequency="rest", family="finite_time_response_9d_h1", metric=metric, values=np.asarray(ftr[metric]))
        jac = h5["jacobian_9D/derived_metrics/v1/series"]
        for metric in JACOBIAN_METRICS:
            add_row(rows, subject=subject, group=group, frequency="rest", family="jacobian_9d", metric=metric, values=np.asarray(jac[metric]))
    return rows


def bh(values):
    order = np.argsort(values)
    adjusted = np.empty(len(values), dtype=float)
    running = 1.0
    for rank in range(len(values), 0, -1):
        idx = order[rank - 1]
        running = min(running, values[idx] * len(values) / rank)
        adjusted[idx] = running
    return adjusted


def contrasts(rows):
    output = []
    keys = sorted({(r["frequency"], r["family"], r["metric"]) for r in rows})
    for frequency, family, metric in keys:
        selected = [r for r in rows if (r["frequency"], r["family"], r["metric"]) == (frequency, family, metric) and np.isfinite(r["value"])]
        for case in ("AD", "FTD"):
            x = np.array([r["value"] for r in selected if r["group"] == case])
            y = np.array([r["value"] for r in selected if r["group"] == "Healthy"])
            if len(x) < 2 or len(y) < 2:
                continue
            statistic, p = mannwhitneyu(x, y, alternative="two-sided")
            # Rank-biserial correlation is orientation-preserving (case vs Healthy).
            effect = 2 * statistic / (len(x) * len(y)) - 1
            output.append({"frequency": frequency, "family": family, "metric": metric,
                           "contrast": f"{case}_vs_Healthy", "n_case": len(x), "n_healthy": len(y),
                           "median_case": float(np.median(x)), "median_healthy": float(np.median(y)),
                           "rank_biserial": float(effect), "p_uncorrected": float(p)})
    if output:
        adjusted = bh(np.array([r["p_uncorrected"] for r in output]))
        for row, p in zip(output, adjusted):
            row["p_fdr_bh_full_exploratory_family"] = float(p)
    return output


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photic-root", type=Path, required=True)
    parser.add_argument("--rest-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    photic, stage_audit = [], []
    for path in h5_files(args.photic_root):
        rows, audit = photic_rows(path)
        photic.extend(rows)
        stage_audit.extend(audit)
    rest = [row for path in h5_files(args.rest_root) for row in rest_rows(path)]
    write_csv(args.output_root / "subject_frequency_v10_metrics.csv", photic)
    write_csv(args.output_root / "event_onset_pilot_stage_audit.csv", stage_audit)
    write_csv(args.output_root / "subject_rest_v10_metrics.csv", rest)
    results = contrasts(photic)
    write_csv(args.output_root / "group_frequency_v10_exploratory_contrasts.csv", results)
    manifest = {
        "analysis": "event-onset pilot NDT v1.0 frequency reanalysis (non-canonical temporal overlay)",
        "unit_of_inference": "subject",
        "photic_input": str(args.photic_root), "rest_input": str(args.rest_root),
        "photic_h5_count": len(h5_files(args.photic_root)), "rest_h5_count": len(h5_files(args.rest_root)),
        "frequency_codes": STAGES,
        "stage_assignment": "non-canonical event-onset overlay: five 4-s windows from each versioned raw frequency onset",
        "ftr_horizon": "h1; both endpoints must share a photic code",
        "statistical_family": "all 9 metrics x 4 frequencies x 2 disease contrasts",
        "claim_boundary": "exploratory measurement contrasts; not clinical validation or future-state inference",
    }
    (args.output_root / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
