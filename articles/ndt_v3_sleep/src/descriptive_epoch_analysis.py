"""Bounded descriptive summaries for the verified sub-99 epoch table.

This module deliberately does not estimate stage-conditioned dynamics.  It
reports row counts, finite/QC eligibility, coordinate summaries, trajectories,
and a fixed immediate-neighbour boundary diagnostic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import importlib.metadata
import yaml
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


MASKS = {
    "coverage_ok": "producer_mask_coverage_ok",
    "retained_after_qc": "producer_mask_retained_after_qc",
    "geometry_valid": "producer_mask_geometry_valid",
    "coords_9d_valid": "producer_mask_coords_9d_valid",
}
COORDS = {
    "3d": ["mnps_3d_m", "mnps_3d_d", "mnps_3d_e"],
    "9d": [
        "mnps_9d_m_a", "mnps_9d_m_e", "mnps_9d_m_o", "mnps_9d_d_n",
        "mnps_9d_d_l", "mnps_9d_d_s", "mnps_9d_e_e", "mnps_9d_e_s", "mnps_9d_e_m",
    ],
}
KNOWN_STAGES = ((0, "Wake"), (1, "N1"), (2, "N2"), (3, "N3"), (4, "REM"))


def _package_present(name: str) -> bool:
    try:
        importlib.metadata.version(name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _mask_true(series: pd.Series) -> pd.Series:
    return series.notna() & (series == 1)


def _mask_state(series: pd.Series) -> pd.Series:
    return pd.Series(np.where(series.isna(), "unknown", np.where(series == 1, "true", np.where(series == 0, "false", "invalid"))), index=series.index)


def eligibility(frame: pd.DataFrame, representation: str) -> tuple[pd.Series, pd.DataFrame]:
    coords = COORDS[representation]
    required = [MASKS["coverage_ok"], MASKS["retained_after_qc"], MASKS["geometry_valid" if representation == "3d" else "coords_9d_valid"]]
    known_stage = frame["stage_label_status"].eq("recorded")
    finite = frame[coords].notna().all(axis=1) & np.isfinite(frame[coords].to_numpy(dtype=float)).all(axis=1)
    parts = {"known_stage": known_stage, "finite_coordinates": finite}
    for name in required:
        parts[name.removeprefix("producer_mask_")] = _mask_true(frame[name])
    reasons = pd.DataFrame(parts, index=frame.index)
    return reasons.all(axis=1), reasons


def stage_counts(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.groupby(["stage_code", "stage_label", "stage_label_status"], dropna=False).size().reset_index(name="n_rows")
    catalog = pd.DataFrame(KNOWN_STAGES, columns=["stage_code", "stage_label"])
    catalog["stage_label_status"] = "recorded"
    out = catalog.merge(out, on=["stage_code", "stage_label", "stage_label_status"], how="outer")
    out["n_rows"] = out["n_rows"].fillna(0).astype(int)
    out["fraction_rows"] = out["n_rows"] / len(frame) if len(frame) else np.nan
    return out.sort_values("stage_code")


def coordinate_summary(frame: pd.DataFrame, representation: str, eligible: pd.Series, policy: str = "primary") -> pd.DataFrame:
    rows = []
    known = pd.DataFrame(KNOWN_STAGES, columns=["stage_code", "stage_label"])
    selected = frame.loc[eligible]
    for code, label in known.itertuples(index=False):
        group = selected.loc[(selected["stage_code"] == code) & (selected["stage_label"] == label)]
        for column in COORDS[representation]:
            values = group[column].to_numpy(dtype=float)
            rows.append({"representation": representation, "stage_code": code, "stage_label": label,
                         "stage_label_status": "recorded", "policy": policy, "coordinate": column, "n": len(values),
                         "median": float(np.median(values)) if len(values) else np.nan,
                         "q1": float(np.quantile(values, .25)) if len(values) else np.nan,
                         "q3": float(np.quantile(values, .75)) if len(values) else np.nan,
                         "iqr": float(np.quantile(values, .75) - np.quantile(values, .25)) if len(values) else np.nan})
    return pd.DataFrame(rows)


def boundary_diagnostic(frame: pd.DataFrame, representation: str, eligible: pd.Series) -> pd.DataFrame:
    coords = COORDS[representation]
    rows = []
    for i in range(len(frame)):
        current = frame.iloc[i]
        record = {"representation": representation, "window_id": int(current.window_id), "stage_code": int(current.stage_code),
                  "left_supported": False, "right_supported": False,
                  "central_eligible": bool(eligible.iloc[i]), "diagnostic_status": "not_assessed"}
        for side, j in (("left", i - 1), ("right", i + 1)):
            if j < 0 or j >= len(frame):
                continue
            neighbor = frame.iloc[j]
            consecutive = int(neighbor.window_id) == int(current.window_id) + (-1 if side == "left" else 1)
            touching = abs(float(current.window_start if side == "left" else neighbor.window_start) - float(neighbor.window_end if side == "left" else current.window_end)) <= 1e-9
            same_known_label = (current.stage_label_status == "recorded" and neighbor.stage_label_status == "recorded" and current.stage_label == neighbor.stage_label)
            if consecutive and touching and same_known_label:
                record[f"{side}_supported"] = True
        rows.append(record)
    return pd.DataFrame(rows)


def _figures(frame: pd.DataFrame, output: Path, eligible: dict[str, pd.Series]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    breaks = frame["time_gap_before"].fillna(False).to_numpy(dtype=bool) | frame["window_overlap_before"].fillna(False).to_numpy(dtype=bool)
    breaks[1:] |= (
        np.diff(frame["window_id"].to_numpy()) != 1
    ) | ~np.isclose(
        frame["window_start"].to_numpy()[1:], frame["window_end"].to_numpy()[:-1],
        rtol=0, atol=1e-9,
    )
    x = frame["timestamp"].to_numpy(dtype=float)
    fig, axes = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
    valid = eligible["3d"].to_numpy()
    i = 0
    while i < len(frame):
        if not valid[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(frame) and valid[j + 1] and not breaks[j + 1] and int(frame.iloc[j + 1].window_id) == int(frame.iloc[j].window_id) + 1 and abs(float(frame.iloc[j + 1].window_start) - float(frame.iloc[j].window_end)) <= 1e-9:
            j += 1
        segment = frame.iloc[i:j + 1]
        for ax, column in zip(axes[:3], COORDS["3d"]):
            ax.plot(segment["timestamp"], segment[column], linewidth=.8, marker=".", markersize=2)
        i = j + 1
    for ax, column in zip(axes[:3], COORDS["3d"]):
        ax.set_ylabel(column.rsplit("_", 1)[-1], fontsize=11)
    axes[0].set_title("Sub-99 3D MNPS time trajectory; gaps and invalid rows break lines", fontsize=12)
    ax2 = axes[3]
    stage_values = frame["stage_code"].to_numpy(dtype=float)
    edges = np.unique(np.r_[0, np.flatnonzero(breaks), len(frame)])
    for start, end in zip(edges[:-1], edges[1:]):
        ax2.step(x[start:end], stage_values[start:end], where="mid", linewidth=.7, marker=".", markersize=2)
    ax2.set_yticks([0, 1, 2, 3, 4, 8], ["Wake", "N1", "N2", "N3", "REM", "Unknown"])
    ax2.set(xlabel="time (s)", ylabel="stage code", title="Recorded stage labels; purity not assessed")
    fig.tight_layout(); fig.savefig(output / "trajectory_3d_and_stage.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(3, 4, figsize=(14, 9), sharex=False)
    for ax, column in zip(axes.flat, COORDS["3d"] + COORDS["9d"]):
        rep = "3d" if column in COORDS["3d"] else "9d"
        values = []
        labels = []
        for (code, label), group in frame.loc[eligible[rep]].groupby(["stage_code", "stage_label"], dropna=False):
            values.append(group[column].to_numpy(dtype=float)); labels.append(str(label) if pd.notna(label) else f"code {code}")
        if values: ax.boxplot(values, tick_labels=labels, showfliers=False)
        ax.set_title(column.replace("mnps_", "")); ax.tick_params(axis="x", labelrotation=70, labelsize=6)
    fig.suptitle("Primary descriptive MNPS distributions; no inferential contrasts\n"
                 "e_m uses PPG fallback; boxes: IQR, whiskers: 1.5 IQR, outliers not drawn")
    fig.tight_layout(); fig.savefig(output / "coordinate_distributions_3d_9d.png", dpi=150); plt.close(fig)


def run(table: Path, output: Path, config: Path | None = None) -> dict:
    table = table.resolve()
    if config is not None:
        config = config.resolve()
        cfg = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        code_path = Path(__file__).resolve()
        if Path(str(cfg.get("source_table", ""))).resolve() != table:
            raise ValueError("configured source table mismatch")
        if str(cfg.get("source_table_sha256", "")).lower() != sha256(table):
            raise ValueError("source table SHA mismatch")
        if Path(str(cfg.get("analysis_code", ""))).resolve() != code_path:
            raise ValueError("configured analysis code mismatch")
        if str(cfg.get("analysis_code_sha256", "")).lower() != sha256(code_path):
            raise ValueError("analysis code SHA mismatch")
        manifest = Path(str(cfg.get("source_manifest", ""))).resolve()
        if not manifest.is_file() or str(cfg.get("source_manifest_sha256", "")).lower() != sha256(manifest):
            raise ValueError("source epoch manifest missing or SHA mismatch")
        source_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        if source_manifest.get("output", {}).get("table_sha256") != sha256(table):
            raise ValueError("source epoch manifest table SHA mismatch")
        expected_policy = {"require_known_stage": True, "require_finite_full_vector": True, "require_coverage_ok": True,
                           "require_retained_after_qc": True, "require_geometry_valid_for_3d": True,
                           "require_coords_9d_valid_for_9d": True, "unknown_masks": "exclude_and_count"}
        if cfg.get("mask_policy") != expected_policy:
            raise ValueError("unsupported mask policy")
        if cfg.get("boundary_diagnostic", {}).get("neighbor_offsets") != [-1, 1] or not cfg.get("boundary_diagnostic", {}).get("require_consecutive_window_id") or not cfg.get("boundary_diagnostic", {}).get("require_touching_bounds"):
            raise ValueError("unsupported boundary policy")
    frame = pd.read_parquet(table).sort_values("window_id").reset_index(drop=True)
    required = set(["window_id", "epoch_id", "timestamp", "window_start", "window_end", "stage_code", "stage_label", "stage_label_status"]) | set(MASKS.values()) | set(sum(COORDS.values(), []))
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing required epoch columns: {missing}")
    output.mkdir(parents=True, exist_ok=False)
    counts = stage_counts(frame)
    counts.to_csv(output / "stage_counts.csv", index=False)
    trajectory = frame[["window_id", "epoch_id", "timestamp", "window_start", "window_end", "stage_code", "stage_label", "stage_label_status", "time_gap_before", "window_overlap_before"]].copy()
    for name, column in MASKS.items():
        trajectory[f"{name}_state"] = _mask_state(frame[column])
    for rep in COORDS:
        good, reasons = eligibility(frame, rep)
        trajectory[f"eligible_{rep}"] = good
        for column in COORDS[rep]:
            trajectory[column] = frame[column]
        reasons.to_csv(output / f"eligibility_{rep}.csv", index=False)
        coordinate_summary(frame, rep, good, "primary").to_csv(output / f"coordinate_summary_{rep}.csv", index=False)
        boundary = boundary_diagnostic(frame, rep, good)
        boundary.to_csv(output / f"boundary_diagnostic_{rep}.csv", index=False)
        boundary_good = good & (boundary.set_index(frame.index)["left_supported"].fillna(False) & boundary.set_index(frame.index)["right_supported"].fillna(False))
        coordinate_summary(frame, rep, boundary_good, "boundary_same_known_stage").to_csv(output / f"coordinate_summary_boundary_{rep}.csv", index=False)
    trajectory.to_csv(output / "epoch_trajectory.csv", index=False)
    _figures(frame, output, {rep: eligibility(frame, rep)[0] for rep in COORDS})
    output_hashes = {p.name: sha256(p) for p in output.iterdir() if p.is_file()}
    manifest = {"status": "descriptive_development_pilot", "claim_status": "no_biological_claim",
                "source_table": str(table), "source_sha256": sha256(table), "n_rows": len(frame),
                "mask_policy": {"known_stage": True, "finite_full_vector": True, "coverage_ok": True,
                                "retained_after_qc": True, "geometry_valid_for_3d": True,
                                "coords_9d_valid_for_9d": True, "unknown_masks": "excluded_and_counted"},
                "stage_purity_status": "not_assessed", "filter_support_status": "not_assessed",
                "diffusion_neighbor_stage_purity": "not_assessed", "boundary_diagnostic": "fixed_immediate_touching_neighbors_only",
                "outputs": sorted(p.name for p in output.iterdir()) + ["analysis_manifest.json"],
                "analysis_code": str(Path(__file__).resolve()), "analysis_code_sha256": sha256(Path(__file__).resolve()),
                "config": ({"path": str(config.resolve()), "sha256": sha256(config.resolve())} if config is not None else None),
                "source_epoch_manifest": (str(manifest) if config is not None else None),
                "source_epoch_manifest_sha256": (sha256(manifest) if config is not None else None),
                "package_versions": {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "pyarrow", "matplotlib", "PyYAML") if _package_present(name)},
                "python": sys.version, "command": " ".join(sys.argv), "output_sha256": output_hashes}
    manifest_path = output / "analysis_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output / "analysis_manifest.sha256").write_text(sha256(manifest_path) + "  analysis_manifest.json\n", encoding="utf-8")
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.table, args.output, args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
