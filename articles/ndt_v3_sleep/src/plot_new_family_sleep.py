"""Static, descriptive E1/E2 sleep-family figures.

The runner supplies the explicit long ``endpoint_rows`` contract from
``new_family_sleep_analysis.py``.  Required columns are
``recording``, ``family``, ``dimension``, ``metric``, ``value``, ``stage_key``,
``stage_code``, ``stage_label``, ``mapped_epoch_position``, ``epoch_id``,
``time``, ``center``, ``center_gap_before``,
``center_gap_before_is_nonconsecutive``, ``finite``, ``producer_finite_ok``,
``used``, ``support_count``, ``support_n``, ``producer_valid_flag``,
``psd_floor_applied``, ``raw_min_eigenvalue``, ``measurement_validity`` and
``qualification_valid``.  This script does not guess aliases or silently
accept a different grain.  Values are plotted only when ``used`` and
``finite`` are true.  Unknown stage keys (``Code8`` and ``Unknown``) stay in
explicit categories.  Jacobian center timelines use points only; there is no
line interpolation across missing or nonconsecutive centers.

Figures are descriptive recording-parent label associations.  They do not
qualify a measurement, infer stage purity, or turn a recording-level object
into a stage-level estimator.  Jacobian axes use inverse derivative-time units
until a verified seconds ``dt`` is supplied by the runner.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


STAGES: tuple[tuple[str, str], ...] = (
    ("Wake", "Wake"),
    ("N1", "N1"),
    ("N2", "N2"),
    ("N3", "N3"),
    ("REM", "REM"),
    ("Code8", "Code8 (unknown source)"),
    ("Unknown", "Unknown/other"),
)
STAGE_KEYS = {key for key, _ in STAGES}
STAGE_LABEL = dict(STAGES)
STAGE_COLORS = {
    "Wake": "#3b6ea8",
    "N1": "#73a57a",
    "N2": "#d1903b",
    "N3": "#8a5ca8",
    "REM": "#c55757",
    "Code8 (unknown source)": "#777777",
    "Unknown/other": "#b2b2b2",
}
JACOBIAN_METRICS = ("spectral_abscissa", "numerical_abscissa", "reactivity_gap")
DIFFUSION_METRICS = ("D_total", "d_diff", "c_diff")
ENDPOINT_REQUIRED = {
    "recording", "family", "dimension", "metric", "value", "stage_key",
    "stage_code", "stage_label", "mapped_epoch_position", "epoch_id", "time",
    "center", "center_gap_before", "center_gap_before_is_nonconsecutive",
    "finite", "producer_finite_ok", "used", "support_count", "support_n",
    "producer_valid_flag", "psd_floor_applied", "raw_min_eigenvalue",
    "measurement_validity", "qualification_valid",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _read_json(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        rows = value
    elif isinstance(value, dict):
        candidates = [key for key in ("rows", "jacobian_rows", "diffusion_rows", "data") if key in value]
        if len(candidates) != 1 or not isinstance(value[candidates[0]], list):
            raise ValueError(f"{path}: expected one explicit row-list key, found {candidates}")
        rows = value[candidates[0]]
    else:
        raise ValueError(f"{path}: row table must be a list or an explicit row-list object")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: every row must be an object")
    return [dict(row) for row in rows]


def read_rows(path: Path) -> list[dict[str, Any]]:
    """Read CSV, TSV, JSON or Parquet rows without changing their schema."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _read_json(path)
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8", newline="") as stream:
            return [dict(row) for row in csv.DictReader(stream, delimiter=delimiter)]
    if suffix == ".parquet":
        try:
            import pandas as pd
        except ImportError as exc:  # pragma: no cover - environment-specific
            raise RuntimeError("Parquet input requires pandas/pyarrow") from exc
        return pd.read_parquet(path).to_dict(orient="records")
    raise ValueError(f"unsupported row-table suffix: {path}")


def _bool(value: Any, *, field: str, row_number: int) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        if float(value) in (0.0, 1.0):
            return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise ValueError(f"row {row_number}: {field} must be boolean-like, got {value!r}")


def _float(value: Any, *, field: str, row_number: int, allow_none: bool = False) -> float | None:
    if value is None or value == "":
        if allow_none:
            return None
        raise ValueError(f"row {row_number}: {field} is missing")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"row {row_number}: {field} must be numeric, got {value!r}") from exc
    return result


def _integer(value: Any, *, field: str, row_number: int, allow_none: bool = False) -> int | None:
    if value is None or value == "":
        if allow_none:
            return None
        raise ValueError(f"row {row_number}: {field} is missing")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"row {row_number}: {field} must be an integer, got {value!r}") from exc
    if not math.isfinite(numeric) or numeric != math.floor(numeric):
        raise ValueError(f"row {row_number}: {field} must be an integer, got {value!r}")
    return int(numeric)


def _validate_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Validate the runner's long endpoint-row schema exactly."""
    if not rows:
        raise ValueError("endpoint row table is empty")
    missing = sorted(ENDPOINT_REQUIRED - set(rows[0]))
    if missing:
        raise ValueError(f"endpoint row schema missing required columns: {', '.join(missing)}")
    normalized: list[dict[str, Any]] = []
    identities: set[tuple[Any, ...]] = set()
    for row_number, source in enumerate(rows, start=1):
        absent = sorted(ENDPOINT_REQUIRED - set(source))
        if absent:
            raise ValueError(f"endpoint row {row_number} missing required columns: {', '.join(absent)}")
        row = dict(source)
        row["recording"] = str(row["recording"])
        row["family"] = str(row["family"])
        row["metric"] = str(row["metric"])
        if row["family"] == "local_jacobian" and (row["dimension"] not in (3, "3", 9, "9")):
            raise ValueError(f"row {row_number}: local_jacobian dimension must be 3 or 9")
        row["dimension"] = _integer(row["dimension"], field="dimension", row_number=row_number)
        expected_metrics = JACOBIAN_METRICS if row["family"] == "local_jacobian" else DIFFUSION_METRICS
        if row["family"] not in {"local_jacobian", "diffusion_geometry"} or row["metric"] not in expected_metrics:
            raise ValueError(f"row {row_number}: unsupported family/metric pair {row['family']!r}/{row['metric']!r}")
        if row["family"] == "diffusion_geometry" and row["dimension"] != 3:
            raise ValueError(f"row {row_number}: diffusion_geometry must be 3D")
        row["stage_key"] = str(row["stage_key"])
        if row["stage_key"] not in STAGE_KEYS:
            raise ValueError(f"row {row_number}: unrecognized stage_key {row['stage_key']!r}")
        row["stage_label"] = str(row["stage_label"])
        row["stage_category"] = STAGE_LABEL[row["stage_key"]]
        row["stage_code"] = _integer(row["stage_code"], field="stage_code", row_number=row_number, allow_none=True)
        row["mapped_epoch_position"] = _integer(row["mapped_epoch_position"], field="mapped_epoch_position", row_number=row_number)
        row["center"] = _integer(row["center"], field="center", row_number=row_number, allow_none=True)
        row["epoch_id"] = _integer(row["epoch_id"], field="epoch_id", row_number=row_number)
        row["time"] = _float(row["time"], field="time", row_number=row_number)
        if row["time"] is None or not math.isfinite(row["time"]):
            raise ValueError(f"row {row_number}: time must be finite")
        row["center_gap_before"] = _integer(row["center_gap_before"], field="center_gap_before", row_number=row_number, allow_none=True)
        row["center_gap_before_is_nonconsecutive"] = _bool(row["center_gap_before_is_nonconsecutive"], field="center_gap_before_is_nonconsecutive", row_number=row_number)
        for field in ("finite", "producer_finite_ok", "used", "producer_valid_flag", "psd_floor_applied", "qualification_valid"):
            row[field] = _bool(row[field], field=field, row_number=row_number)
        for field in ("value", "support_count", "support_n", "raw_min_eigenvalue"):
            row[field] = _float(row[field], field=field, row_number=row_number, allow_none=True)
        if row["support_count"] is not None and (not math.isfinite(row["support_count"]) or row["support_count"] < 0):
            raise ValueError(f"row {row_number}: support_count must be nonnegative or null")
        row["measurement_validity"] = str(row["measurement_validity"])
        identity = (row["recording"], row["family"], row["dimension"], row["metric"], row["mapped_epoch_position"])
        if identity in identities:
            raise ValueError(f"endpoint row {row_number}: duplicate natural row identity {identity!r}; do not combine JSON and CSV exports")
        identities.add(identity)
        normalized.append(row)
    _validate_diffusion_diagnostics(normalized)
    return normalized


def _same_diagnostic_value(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    if isinstance(left, (bool, np.bool_)) or isinstance(right, (bool, np.bool_)):
        return bool(left) == bool(right)
    try:
        return bool(np.isclose(float(left), float(right), rtol=0.0, atol=1e-12))
    except (TypeError, ValueError):
        return left == right


def _validate_diffusion_diagnostics(rows: Sequence[Mapping[str, Any]]) -> None:
    """Ensure repeated producer diagnostics agree across E2 endpoint metrics."""
    diagnostic_fields = (
        "stage_key", "stage_code", "stage_label", "epoch_id", "time",
        "support_count", "support_n", "producer_valid_flag",
        "psd_floor_applied", "raw_min_eigenvalue",
    )
    seen: dict[tuple[str, int, int], Mapping[str, Any]] = {}
    for row in rows:
        if row["family"] != "diffusion_geometry":
            continue
        key = (row["recording"], row["dimension"], row["mapped_epoch_position"])
        prior = seen.get(key)
        if prior is None:
            seen[key] = row
            continue
        mismatches = [field for field in diagnostic_fields if not _same_diagnostic_value(prior.get(field), row.get(field))]
        if mismatches:
            raise ValueError(f"diffusion producer diagnostics disagree at query {key!r}: {', '.join(mismatches)}")


def _unique_diffusion_queries(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Collapse the three repeated E2 metric rows to one diagnostic row/query."""
    unique: dict[tuple[str, int, int], dict[str, Any]] = {}
    for row in rows:
        if row["family"] != "diffusion_geometry":
            continue
        key = (row["recording"], row["dimension"], row["mapped_epoch_position"])
        unique.setdefault(key, dict(row))
    return list(unique.values())


def _plot_values(rows: Iterable[Mapping[str, Any]], metric: str) -> dict[str, list[float]]:
    values = {label: [] for _, label in STAGES}
    for row in rows:
        if row.get("metric") != metric or row.get("used") is not True or row.get("finite") is not True:
            continue
        value = row.get("value")
        if value is not None and math.isfinite(float(value)):
            values[row["stage_category"]].append(float(value))
    return values


def _boxplot(ax: Any, values: Mapping[str, Sequence[float]], *, ylabel: str, title: str) -> None:
    labels = [label for _, label in STAGES]
    data = [list(values[label]) for label in labels]
    positions = np.arange(1, len(labels) + 1)
    nonempty = [(position, label, sample) for position, label, sample in zip(positions, labels, data) if sample]
    if nonempty:
        bp = ax.boxplot([sample for _, _, sample in nonempty], positions=[position for position, _, _ in nonempty], widths=0.55, patch_artist=True, showfliers=False)
        for patch, (_, label, _) in zip(bp["boxes"], nonempty):
            patch.set_facecolor(STAGE_COLORS[label])
            patch.set_alpha(0.55)
            patch.set_edgecolor("#333333")
        for median in bp["medians"]:
            median.set_color("#202020")
            median.set_linewidth(1.2)
    else:
        ax.text(0.5, 0.5, "no finite computed rows", ha="center", va="center", transform=ax.transAxes, color="#666666")
    ax.set_xticks(positions, labels, rotation=35, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontsize=10)
    ax.grid(axis="y", alpha=0.18)
    ax.set_axisbelow(True)


def _style(fig: Any, axes: Iterable[Any], *, footer: str) -> None:
    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.text(0.01, 0.01, footer, fontsize=7.5, color="#5d6670", ha="left")
    fig.tight_layout(rect=(0, 0.045, 1, 0.95))


def _safe_name(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("_")
    return result or "recording"


def _save(fig: Any, output_root: Path, stem: str) -> list[str]:
    paths = []
    for suffix in (".png", ".pdf", ".svg"):
        path = output_root / f"{stem}{suffix}"
        fig.savefig(path, dpi=200 if suffix == ".png" else None, bbox_inches="tight")
        paths.append(str(path))
    plt.close(fig)
    return paths


def plot_abscissa_distributions(rows: Sequence[Mapping[str, Any]], output_root: Path, recording_id: str, dimension: int) -> list[str]:
    selected = [row for row in rows if row["recording"] == recording_id and row["family"] == "local_jacobian" and row["dimension"] == dimension]
    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.8), sharex=True)
    unit = "inverse derivative-time units"
    for ax, metric in zip(axes, JACOBIAN_METRICS):
        _boxplot(ax, _plot_values(selected, metric), ylabel=unit, title=metric.replace("_", " "))
    fig.suptitle(f"E1 local-Jacobian distributions · {recording_id} · {dimension}D", x=0.02, ha="left", fontsize=14, weight="bold")
    _style(fig, axes, footer="Recorded-center label associations; validity and qualification remain unassessed.")
    return _save(fig, output_root, f"abscissa_distributions_{_safe_name(recording_id)}_{dimension}d")


def plot_abscissa_timeline(rows: Sequence[Mapping[str, Any]], output_root: Path, recording_id: str, dimension: int) -> list[str]:
    selected = [row for row in rows if row["recording"] == recording_id and row["family"] == "local_jacobian" and row["dimension"] == dimension]
    selected = sorted(selected, key=lambda row: (row["time"], row["mapped_epoch_position"], row["center"] if row["center"] is not None else -1))
    fig, axes = plt.subplots(3, 1, figsize=(13.8, 8.0), sharex=True)
    for ax, metric in zip(axes, JACOBIAN_METRICS):
        for _, label in STAGES:
            stage_rows = [row for row in selected if row["stage_category"] == label and row["metric"] == metric and row["used"] is True and row["finite"] is True and row["value"] is not None and math.isfinite(float(row["value"]))]
            if stage_rows:
                # Scatter only: no polyline can bridge nonconsecutive centers or gaps.
                ax.scatter([row["time"] for row in stage_rows], [row["value"] for row in stage_rows], s=10, alpha=0.72, color=STAGE_COLORS[label], label=label)
        ax.set_ylabel("inverse derivative-time units")
        ax.set_title(metric.replace("_", " "), loc="left", fontsize=10)
        ax.grid(axis="y", alpha=0.17)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[-1].set_xlabel("Actual center timestamp (recording time)")
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        axes[0].legend(handles, labels, frameon=False, ncol=4, fontsize=8, loc="upper right")
    fig.suptitle(f"E1 actual-center timeline · {recording_id} · {dimension}D", x=0.02, ha="left", fontsize=14, weight="bold")
    _style(fig, axes, footer="Points are mapped from explicit centers; missing/nonconsecutive centers are left unconnected.")
    return _save(fig, output_root, f"abscissa_timeline_{_safe_name(recording_id)}_{dimension}d")


def _indicator_values(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, list[float]]:
    result = {label: [] for _, label in STAGES}
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        result[row["stage_category"]].append(float(bool(value)))
    return result


def plot_diffusion(rows: Sequence[Mapping[str, Any]], output_root: Path, recording_id: str) -> list[str]:
    selected = [row for row in rows if row["recording"] == recording_id and row["family"] == "diffusion_geometry" and row["dimension"] == 3]
    diagnostic_rows = [row for row in _unique_diffusion_queries(selected)]
    fig, axes = plt.subplots(2, 3, figsize=(14.2, 8.4))
    for ax, metric in zip(axes[0], DIFFUSION_METRICS):
        _boxplot(ax, _plot_values(selected, metric), ylabel=metric, title=metric)
    support_values = {label: [float(row["support_count"]) for row in diagnostic_rows if row["stage_category"] == label and row["support_count"] is not None] for _, label in STAGES}
    _boxplot(axes[1, 0], support_values, ylabel="support count", title="Producer support")
    floor = _indicator_values(diagnostic_rows, "psd_floor_applied")
    labels = [label for _, label in STAGES]
    fractions = [float(np.mean(floor[label])) if floor[label] else np.nan for label in labels]
    counts = [len(floor[label]) for label in labels]
    positions = np.arange(1, len(labels) + 1)
    axes[1, 1].bar(positions, np.nan_to_num(fractions, nan=0.0), color=[STAGE_COLORS[label] for label in labels], alpha=0.68)
    for position, fraction, count in zip(positions, fractions, counts):
        axes[1, 1].text(position, 0.02 if np.isnan(fraction) else fraction + 0.02, f"n={count}", ha="center", va="bottom", fontsize=7)
    axes[1, 1].set_ylim(0, 1.08)
    axes[1, 1].set_xticks(positions, labels, rotation=35, ha="right")
    axes[1, 1].set_ylabel("fraction with PSD floor flag")
    axes[1, 1].set_title("PSD-floor indicator", loc="left", fontsize=10)
    axes[1, 1].grid(axis="y", alpha=0.18)
    axes[1, 1].set_axisbelow(True)
    axes[1, 2].axis("off")
    axes[1, 2].text(0.02, 0.95, "Recording-level display notes", transform=axes[1, 2].transAxes, va="top", fontsize=10, weight="bold")
    notes = [
        "Rows are query/epoch observations.",
        "Unknown stage labels remain visible.",
        "Support and floor flags are producer diagnostics.",
        "No stage-conditioned refit or qualification is implied.",
        "D_total uses the stored producer unit contract.",
    ]
    axes[1, 2].text(0.02, 0.82, "\n".join(f"• {note}" for note in notes), transform=axes[1, 2].transAxes, va="top", fontsize=9, linespacing=1.6)
    fig.suptitle(f"E2 diffusion geometry by recorded query label · {recording_id}", x=0.02, ha="left", fontsize=14, weight="bold")
    _style(fig, [*axes[0], axes[1, 0], axes[1, 1]], footer="Global state-neighborhood covariance summarized by recorded labels; no stage-intrinsic diffusion claim.")
    return _save(fig, output_root, f"diffusion_distributions_{_safe_name(recording_id)}_3d")


def _resolve_inputs(args: argparse.Namespace) -> list[Path]:
    paths = [Path(path).resolve() for path in (args.endpoint_rows or [])]
    if args.input_manifest:
        manifest_path = Path(args.input_manifest).resolve()
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or "endpoint_rows" not in value:
            raise ValueError("input manifest must contain endpoint_rows")
        listed = value["endpoint_rows"]
        if isinstance(listed, str):
            paths.append((manifest_path.parent / listed).resolve())
        elif isinstance(listed, list) and all(isinstance(item, str) for item in listed):
            paths.extend((manifest_path.parent / item).resolve() for item in listed)
        else:
            raise ValueError("input manifest endpoint_rows must be a string or list of strings")
    if args.input_root:
        root = Path(args.input_root).resolve()
        # endpoint_rows.json is the authoritative full-fidelity export.  The
        # CSV is a convenience export with fewer metadata fields; use it only
        # when the authoritative JSON is absent.
        for suffix in (".json", ".csv", ".tsv", ".parquet"):
            candidate = root / f"endpoint_rows{suffix}"
            if candidate.is_file():
                paths.append(candidate)
                break
    if not paths:
        raise ValueError("provide --endpoint-rows, an --input-manifest, or --input-root")
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).lower()
        if key in seen:
            raise ValueError(f"duplicate endpoint row source path: {path}")
        seen.add(key)
        unique.append(path)
    return unique


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint-rows", action="append", type=Path)
    parser.add_argument("--input-manifest", type=Path)
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    source_paths = _resolve_inputs(args)
    rows = _validate_rows([row for path in source_paths for row in read_rows(path)])
    output_root = Path(args.output_root).resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty figure output root: {output_root}")
    output_root.mkdir(parents=True, exist_ok=False)
    artifacts: list[str] = []
    recordings = sorted({row["recording"] for row in rows})
    for recording_id in recordings:
        for dimension in (3, 9):
            if any(row["recording"] == recording_id and row["family"] == "local_jacobian" and row["dimension"] == dimension for row in rows):
                artifacts.extend(plot_abscissa_distributions(rows, output_root, recording_id, dimension))
                artifacts.extend(plot_abscissa_timeline(rows, output_root, recording_id, dimension))
        if any(row["recording"] == recording_id and row["family"] == "diffusion_geometry" for row in rows):
            artifacts.extend(plot_diffusion(rows, output_root, recording_id))
    source_paths = sorted(set(source_paths))
    manifest = {
        "schema": "ndt.sleep.new_family_figures.v1",
        "status": "descriptive_unqualified",
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "stage_purity_status": "not_assessed",
        "jacobian_units": "inverse_derivative_time_units; seconds dt not verified by plotter",
        "plot_code": {"path": str(Path(__file__).resolve()), "sha256": _sha256(Path(__file__).resolve())},
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "matplotlib": importlib.metadata.version("matplotlib"),
            "numpy": importlib.metadata.version("numpy"),
        },
        "source_tables": [{"path": str(path), "sha256": _sha256(path)} for path in source_paths],
        "recording_ids": recordings,
        "artifact_paths": artifacts,
        "artifact_hashes": [{"path": path, "sha256": _sha256(Path(path))} for path in artifacts],
    }
    (output_root / "plot_manifest.json").write_text(json.dumps(_json_safe(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(_json_safe(manifest), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
