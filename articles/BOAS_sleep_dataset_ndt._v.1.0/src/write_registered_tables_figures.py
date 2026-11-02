"""Write descriptive tables and static figures from the frozen BOAS v5 output.

This script is downstream of the frozen registered reanalysis. It does not
refit measurements, alter eligibility, fill missing values, or add inferential
tests. Article outputs are written outside the frozen result directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ARTICLE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ARTICLE_ROOT / "results" / "registered_reanalysis_20260923_frozen_v5"
DEFAULT_TABLES = ARTICLE_ROOT / "results" / "article_tables_20260924_v5"
DEFAULT_FIGURES = ARTICLE_ROOT / "figures" / "registered_v5"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(root: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(root / name)


def _write_markdown(frame: pd.DataFrame, path: Path) -> None:
    columns = list(frame.columns)
    rows = [[str(value) for value in row] for row in frame.itertuples(index=False, name=None)]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_table(frame: pd.DataFrame, tables_root: Path, stem: str) -> list[Path]:
    csv_path = tables_root / f"{stem}.csv"
    md_path = tables_root / f"{stem}.md"
    frame.to_csv(csv_path, index=False)
    _write_markdown(frame, md_path)
    return [csv_path, md_path]


def _fmt(value: object, digits: int = 6) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "NA"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}g}"
    return str(value)


def _coverage_table(source: pd.DataFrame, gaps: pd.DataFrame) -> pd.DataFrame:
    stage_counts: dict[str, int] = {}
    for encoded in source["stage_counts_json"].dropna():
        for key, value in json.loads(encoded).items():
            label = {"0": "Wake", "1": "N1", "2": "N2", "3": "N3", "4": "REM"}.get(key, key)
            stage_counts[label] = stage_counts.get(label, 0) + int(value)
    rows = [
        {"section": "coverage", "item": "recordings", "value": len(source), "note": "HDF5 recording IDs"},
        {"section": "coverage", "item": "biological pids", "value": source["pid"].nunique(), "note": "repeated recordings retained"},
        {"section": "coverage", "item": "selected windows", "value": int(source["n_selected_windows"].sum()), "note": "30-second sampled windows"},
        {"section": "coverage", "item": "sampling gaps", "value": int(source["n_gap_intervals"].sum()), "note": "within-recording omitted intervals"},
        {"section": "coverage", "item": "omitted seconds", "value": int(source["total_omitted_seconds"].sum()), "note": "not imputed or joined"},
        {"section": "coverage", "item": "median gap seconds", "value": int(gaps["omitted_seconds"].median()), "note": "positive gaps only"},
        {"section": "coverage", "item": "maximum gap seconds", "value": int(gaps["omitted_seconds"].max()), "note": "positive gaps only"},
    ]
    rows.extend(
        {"section": "stage", "item": label, "value": stage_counts.get(label, 0), "note": "selected-window count"}
        for label in ("Wake", "N1", "N2", "N3", "REM")
        if label in stage_counts
    )
    fallback_counts = source.groupby("fallback_feature")["recording_id"].nunique().to_dict()
    rows.extend(
        {"section": "fallback", "item": fallback, "value": int(count), "note": "recordings with fallback"}
        for fallback, count in sorted(fallback_counts.items())
    )
    return pd.DataFrame(rows)


def _primary_table(summary: pd.DataFrame, boundary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for pass_name, frame in (("full", summary), ("boundary_only", boundary)):
        selected = frame[(frame["fallback_feature"] == "ppg_rate_bpm") & (frame["dimension"] == 3)]
        for row in selected.itertuples(index=False):
            for endpoint in ("spectral_abscissa", "numerical_abscissa"):
                rows.append(
                    {
                        "pass": pass_name,
                        "contrast": row.contrast_id,
                        "endpoint": endpoint,
                        "n_people": int(row.n_people_eligible),
                        "n_recordings": int(row.n_recordings_eligible),
                        "median": _fmt(getattr(row, f"{endpoint}_median"), 8),
                        "q25": _fmt(getattr(row, f"{endpoint}_q25"), 8),
                        "q75": _fmt(getattr(row, f"{endpoint}_q75"), 8),
                        "bootstrap_q025": _fmt(getattr(row, f"{endpoint}_bootstrap_q025"), 8),
                        "bootstrap_q975": _fmt(getattr(row, f"{endpoint}_bootstrap_q975"), 8),
                        "unit": "reported abscissa units",
                    }
                )
    return pd.DataFrame(rows)


def _ftr_table(ftr_summary: pd.DataFrame, ftr_recording: pd.DataFrame) -> pd.DataFrame:
    usable = (
        ftr_recording.groupby(["fallback_feature", "dimension", "horizon_name"], dropna=False)
        .agg(
            n_recordings_zero_valid=("n_sequences_valid", lambda values: int((values == 0).sum())),
            n_recordings_unusable=("registered_horizon_usable", lambda values: int((~values).sum())),
        )
        .reset_index()
    )
    columns = [
        "fallback_feature", "dimension", "horizon_name", "n_people_eligible", "n_recordings_eligible",
        "mean_log_g_max_median", "mean_d_resp_median", "mean_c_1_median", "actual_horizon_sec_median",
    ]
    result = ftr_summary[columns].merge(usable, on=["fallback_feature", "dimension", "horizon_name"], how="left")
    return result.sort_values(["fallback_feature", "dimension", "horizon_name"]).reset_index(drop=True)


def _family_table(ledger: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        ledger.groupby(
            ["family", "family_role", "computation_status", "measurement_validity", "support_status", "claim_status"],
            dropna=False,
        )
        .agg(n_rows=("recording_id", "size"), n_recordings=("recording_id", "nunique"))
        .reset_index()
    )
    return grouped.sort_values(["family", "family_role", "computation_status"]).reset_index(drop=True)


def _figure_primary(summary: pd.DataFrame, boundary: pd.DataFrame, output: Path) -> None:
    labels = [("N2_minus_Wake", "N2"), ("N3_minus_Wake", "N3"), ("REM_minus_Wake", "REM")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), sharex=True)
    colors = {"full": "#1f5a85", "boundary_only": "#c46b27"}
    markers = {"full": "o", "boundary_only": "s"}
    for axis, endpoint in zip(axes, ("spectral_abscissa", "numerical_abscissa")):
        for pass_name, frame, offset in (("full", summary, -0.08), ("boundary_only", boundary, 0.08)):
            selected = frame[(frame["fallback_feature"] == "ppg_rate_bpm") & (frame["dimension"] == 3)]
            selected = selected.set_index("contrast_id").loc[[item[0] for item in labels]]
            x = np.arange(len(labels), dtype=float) + offset
            y = selected[f"{endpoint}_median"].to_numpy(float)
            lower = y - selected[f"{endpoint}_bootstrap_q025"].to_numpy(float)
            upper = selected[f"{endpoint}_bootstrap_q975"].to_numpy(float) - y
            axis.errorbar(
                x, y, yerr=np.vstack([lower, upper]), fmt=markers[pass_name], color=colors[pass_name],
                capsize=3, linewidth=1.2, markersize=5, label=pass_name.replace("_", " "),
            )
        axis.axhline(0, color="#666666", linewidth=0.8)
        axis.set_xticks(np.arange(len(labels)), [item[1] for item in labels])
        axis.set_ylabel("Target minus Wake (reported units)")
        axis.set_title(endpoint.replace("_", " ").title())
        axis.grid(axis="y", color="#dddddd", linewidth=0.6)
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, loc="best")
    fig.suptitle("Registered A1 contrasts: PPG fallback, subject-anchored 3D", y=1.02)
    fig.tight_layout()
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _figure_support(source: pd.DataFrame, gaps: pd.DataFrame, ftr: pd.DataFrame, ledger: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5))

    stage_counts: dict[str, int] = {}
    for encoded in source["stage_counts_json"].dropna():
        for key, value in json.loads(encoded).items():
            label = {"0": "Wake", "1": "N1", "2": "N2", "3": "N3", "4": "REM"}.get(key, key)
            stage_counts[label] = stage_counts.get(label, 0) + int(value)
    stage_labels = ["Wake", "N2", "N3", "REM"]
    axes[0, 0].bar(stage_labels, [stage_counts.get(label, 0) for label in stage_labels], color="#537a9d")
    axes[0, 0].set_title("Selected stage windows")
    axes[0, 0].set_ylabel("Count")

    axes[0, 1].hist(gaps["omitted_seconds"], bins=24, color="#8c6d9f", edgecolor="none")
    axes[0, 1].set_xscale("log")
    axes[0, 1].set_title("Sampling-gap durations")
    axes[0, 1].set_xlabel("Omitted seconds, log scale")
    axes[0, 1].set_ylabel("Gap count")

    usable = ftr.groupby(["dimension", "horizon_name"])["registered_horizon_usable"].sum().unstack("horizon_name")
    usable.plot(kind="bar", ax=axes[1, 0], color=["#537a9d", "#c46b27", "#6b9d71"], width=0.75)
    axes[1, 0].set_title("FTR usable recording horizons")
    axes[1, 0].set_xlabel("Coordinate dimension")
    axes[1, 0].set_ylabel("Usable recordings")
    axes[1, 0].legend(title="Horizon", frameon=False)

    statuses = ledger["computation_status"].value_counts()
    axes[1, 1].bar(statuses.index.astype(str), statuses.values, color="#6b9d71")
    axes[1, 1].set_title("A3 ledger row statuses")
    axes[1, 1].set_ylabel("Ledger rows")
    axes[1, 1].tick_params(axis="x", rotation=35)

    for axis in axes.flat:
        axis.grid(axis="y", color="#dddddd", linewidth=0.6)
        axis.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Coverage and qualification status in the frozen v5 package", y=1.02)
    fig.tight_layout()
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)


def run(input_root: Path, tables_root: Path, figures_root: Path) -> dict[str, object]:
    input_root = input_root.resolve()
    tables_root = tables_root.resolve()
    figures_root = figures_root.resolve()
    tables_root.mkdir(parents=True, exist_ok=True)
    figures_root.mkdir(parents=True, exist_ok=True)
    source = _load(input_root, "source_inventory.csv")
    gaps = _load(input_root, "gap_intervals.csv")
    summary = _load(input_root, "a1_summary.csv")
    boundary = _load(input_root, "a1_boundary_summary.csv")
    ftr_summary = _load(input_root, "a2_ftr_summary.csv")
    ftr_recording = _load(input_root, "a2_ftr_recording_horizons.csv")
    ledger = _load(input_root, "a3_family_ledger.csv")

    outputs: list[Path] = []
    outputs.extend(_write_table(_coverage_table(source, gaps), tables_root, "table_1_coverage"))
    outputs.extend(_write_table(_primary_table(summary, boundary), tables_root, "table_2_a1_primary_contrasts"))
    outputs.extend(_write_table(_ftr_table(ftr_summary, ftr_recording), tables_root, "table_3_a2_ftr_support"))
    outputs.extend(_write_table(_family_table(ledger), tables_root, "table_4_a3_family_status"))

    primary_figure = figures_root / "figure_1_a1_primary_contrasts.png"
    support_figure = figures_root / "figure_2_coverage_and_status.png"
    _figure_primary(summary, boundary, primary_figure)
    _figure_support(source, gaps, ftr_recording, ledger, support_figure)
    outputs.extend([primary_figure, support_figure])

    manifest = {
        "input_root": str(input_root.resolve()),
        "input_analysis_manifest_sha256": _sha256(input_root / "analysis_manifest.json"),
        "input_freeze_marker_sha256": _sha256(input_root / "FREEZE.md"),
        "outputs": {str(path.relative_to(ARTICLE_ROOT)): _sha256(path) for path in outputs},
        "scientific_status": "descriptive_exploratory_method_limited",
        "no_inference_or_refit": True,
    }
    manifest_path = tables_root / "article_outputs_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    outputs.append(manifest_path)
    print(json.dumps({"tables_root": str(tables_root), "figures_root": str(figures_root), "n_outputs": len(outputs)}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--tables-root", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--figures-root", type=Path, default=DEFAULT_FIGURES)
    args = parser.parse_args()
    run(args.input_root, args.tables_root, args.figures_root)


if __name__ == "__main__":
    main()
