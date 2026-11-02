"""Render PID-level N2-minus-Wake contrast panels for the sleep cohort.

The input is the article-local ``participant_n2_minus_wake.json`` emitted by
``sleep_cohort_analysis``.  Each panel contains one point per PID with a
finite participant-level contrast, a median/IQR summary, and a zero line.
The analysis manifest is required so that pilot output cannot be silently
presented as a full-cohort result and historical sampled output is rejected.
No hypothesis tests or pooled-window quantities are computed here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402


EXPECTED_ENDPOINTS: tuple[tuple[str, int, str], ...] = (
    ("local_jacobian", 3, "spectral_abscissa"),
    ("local_jacobian", 3, "numerical_abscissa"),
    ("local_jacobian", 3, "reactivity_gap"),
    ("local_jacobian", 9, "spectral_abscissa"),
    ("local_jacobian", 9, "numerical_abscissa"),
    ("local_jacobian", 9, "reactivity_gap"),
    ("diffusion_geometry", 3, "D_total"),
    ("diffusion_geometry", 3, "d_diff"),
    ("diffusion_geometry", 3, "c_diff"),
)
EXPECTED_CONTRAST = "N2_minus_Wake"
OUTPUT_STEM = "sleep_cohort_pid_n2_minus_wake_contrasts"


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_scope(input_path: Path, manifest_path: Path | None) -> tuple[str, Mapping[str, Any], Path]:
    resolved_manifest = manifest_path or input_path.parent / "analysis_manifest.json"
    if not resolved_manifest.is_file():
        raise FileNotFoundError(
            f"analysis_manifest.json is required beside the participant input; missing {resolved_manifest}"
        )
    manifest = _read_json(resolved_manifest)
    if not isinstance(manifest, Mapping) or manifest.get("status") not in {"completed", "completed_with_failures"}:
        raise ValueError("analysis manifest must have status=completed or completed_with_failures")
    provenance = manifest.get("source_provenance", {})
    if not isinstance(provenance, Mapping):
        raise ValueError("analysis manifest has no source provenance")

    # Direct H5 manifests carry their scope and continuity marker in a nested
    # ``manifest`` object.  The full ingest route carries the execution
    # manifest directly and records the delivery-specific continuity marker.
    source_manifest = provenance.get("manifest")
    if isinstance(source_manifest, Mapping):
        scope = source_manifest.get("scope")
        if source_manifest.get("continuous_fullnight") is not True:
            raise ValueError("direct figure input must be marked continuous_fullnight")
        if scope == "pilot":
            return "pilot", manifest, resolved_manifest
        if scope == "full":
            review = source_manifest.get("coordinator_review", {})
            if source_manifest.get("status") != "reviewed_for_descriptive_analysis":
                raise ValueError("full direct figure input is not marked reviewed_for_descriptive_analysis")
            if not isinstance(review, Mapping) or review.get("status") != "PASS_FOR_DESCRIPTIVE_ARTIFACT_ANALYSIS":
                raise ValueError("full direct figure input lacks coordinator descriptive-analysis approval")
            if source_manifest.get("recording_count") != 128 or source_manifest.get("unique_pid_count") != 100:
                raise ValueError("reviewed full direct manifest must bind 128 recordings and 100 PIDs")
            _validate_full_output(manifest, input_path)
            return "full", manifest, resolved_manifest
        raise ValueError(f"unsupported direct source scope: {scope!r}")

    execution = provenance.get("execution")
    if not isinstance(execution, Mapping):
        raise ValueError("analysis manifest has neither direct pilot nor full execution provenance")
    if execution.get("scope") != "full":
        raise ValueError(f"unsupported full execution scope: {execution.get('scope')!r}")
    if execution.get("status") != "completed":
        raise ValueError("full figure input requires a completed ingest execution manifest")
    if execution.get("config_contains_continuous_delivery") is not True:
        raise ValueError("full execution is not marked as continuous delivery")
    _validate_full_output(manifest, input_path)
    return "full", manifest, resolved_manifest


def _finite_value(row: Mapping[str, Any]) -> float | None:
    value = row.get("n2_minus_wake_median")
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if np.isfinite(numeric) else None


def _validate_full_output(manifest: Mapping[str, Any], input_path: Path) -> None:
    if manifest.get("recording_count") != 128 or manifest.get("source_count_expected") != 128:
        raise ValueError("full figure input must contain all 128 expected recordings")
    if manifest.get("participant_count_expected") != 100 or len(manifest.get("participant_ids", [])) != 100:
        raise ValueError("full figure input must bind the expected 100 participant PIDs")
    outcomes_path = input_path.parent / "source_outcomes.json"
    if not outcomes_path.is_file():
        raise FileNotFoundError(f"full figure input is missing source outcomes: {outcomes_path}")
    outcomes = _read_json(outcomes_path)
    if not isinstance(outcomes, list) or len(outcomes) != 128:
        raise ValueError("full source outcomes must retain one explicit outcome per recording")
    successful_h5 = [item for item in outcomes if isinstance(item, Mapping) and item.get("status") == "ok"]
    if not successful_h5 or any(not isinstance(item.get("fullnight_evidence"), Mapping) for item in successful_h5):
        raise ValueError("full figure input lacks H5 full-night evidence for a successful recording")


def _panel_values(rows: Sequence[Mapping[str, Any]], endpoint: tuple[str, int, str]) -> list[tuple[str, float]]:
    family, dimension, metric = endpoint
    values: list[tuple[str, float]] = []
    seen: set[str] = set()
    for row in rows:
        if (
            row.get("contrast") != EXPECTED_CONTRAST
            or row.get("family") != family
            or row.get("dimension") != dimension
            or row.get("metric") != metric
        ):
            continue
        participant_id = str(row.get("participant_id", "")).strip()
        value = _finite_value(row)
        if not participant_id or value is None:
            continue
        if participant_id in seen:
            raise ValueError(f"duplicate finite PID row for {family}/{dimension}/{metric}: {participant_id}")
        seen.add(participant_id)
        values.append((participant_id, value))
    return sorted(values, key=lambda item: item[0])


def _panel_title(endpoint: tuple[str, int, str], n: int) -> str:
    family, dimension, metric = endpoint
    family_label = family.replace("_", " ")
    return f"{family_label} {dimension}D\n{metric}\nn={n}"


def render_figure(
    input_path: Path,
    output_dir: Path,
    *,
    manifest_path: Path | None = None,
    dpi: int = 300,
) -> dict[str, Any]:
    """Render the fixed nine-panel descriptive contrast figure."""
    scope, analysis_manifest, resolved_manifest = _load_scope(input_path, manifest_path)
    rows = _read_json(input_path)
    if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
        raise ValueError("participant contrast input must be a JSON list of objects")

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "png": output_dir / f"{OUTPUT_STEM}.png",
        "pdf": output_dir / f"{OUTPUT_STEM}.pdf",
        "svg": output_dir / f"{OUTPUT_STEM}.svg",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite existing figure files: {existing}")
    fig, axes = plt.subplots(3, 3, figsize=(7, 7.5), squeeze=False)
    scope_label = "Pilot (development only; no cohort inference)" if scope == "pilot" else "Full local cohort descriptive"
    fig.suptitle(f"Sleep cohort PID-level N2 − Wake contrasts\n{scope_label}", fontsize=9, y=0.995)

    panel_counts: dict[str, int] = {}
    for axis, endpoint in zip(axes.flat, EXPECTED_ENDPOINTS):
        values = _panel_values(rows, endpoint)
        numbers = np.asarray([value for _, value in values], dtype=float)
        n = int(numbers.size)
        endpoint_key = f"{endpoint[0]}_{endpoint[1]}D_{endpoint[2]}"
        panel_counts[endpoint_key] = n
        axis.axhline(0.0, color="0.25", linewidth=0.9, linestyle="--", zorder=0)
        axis.set_title(_panel_title(endpoint, n), fontsize=8, pad=3)
        axis.set_xlim(-0.45, 0.45)
        axis.set_xticks([])
        axis.set_ylabel("N2 − Wake", fontsize=8, labelpad=2)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=4, min_n_ticks=2))
        axis.tick_params(axis="y", labelsize=7, pad=1)
        axis.grid(axis="y", color="0.88", linewidth=0.6)
        if n == 0:
            axis.text(0.5, 0.5, "No finite PID contrast", ha="center", va="center", transform=axis.transAxes, fontsize=7)
            continue
        offsets = np.asarray([-0.18]) if n == 1 else np.linspace(-0.24, 0.06, n)
        axis.scatter(offsets, numbers, s=24, color="#3b6ea8", alpha=0.82, edgecolor="white", linewidth=0.35, zorder=2)
        median = float(np.median(numbers))
        q25, q75 = (float(item) for item in np.quantile(numbers, [0.25, 0.75]))
        axis.errorbar(
            [0.24],
            [median],
            yerr=[[median - q25], [q75 - median]],
            fmt="D",
            color="#111111",
            markerfacecolor="#f5a623",
            markeredgecolor="#111111",
            markersize=6,
            capsize=5,
            linewidth=1.25,
            zorder=3,
        )

    fig.text(
        0.5,
        0.012,
        "Points are valid PID-level contrasts; diamond and bar show the median and IQR. No p-values or inferential comparisons.",
        ha="center",
        fontsize=7,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94), w_pad=0.7, h_pad=0.9)
    for path in paths.values():
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return {
        "input": str(input_path),
        "analysis_manifest": str(resolved_manifest),
        "analysis_status": analysis_manifest.get("status"),
        "scope": scope,
        "panel_counts": panel_counts,
        "outputs": {kind: str(path) for kind, path in paths.items()},
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="participant_n2_minus_wake.json from sleep_cohort_analysis")
    parser.add_argument("--output-dir", required=True, type=Path, help="fresh or dedicated figure output directory")
    parser.add_argument("--analysis-manifest", type=Path, help="optional explicit analysis_manifest.json path")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args(argv)
    result = render_figure(args.input.resolve(), args.output_dir.resolve(), manifest_path=args.analysis_manifest.resolve() if args.analysis_manifest else None, dpi=args.dpi)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
