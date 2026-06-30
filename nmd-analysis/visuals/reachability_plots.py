from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


GROUP_COLORS = ["#1f77b4", "#ff7f0e"]


def _slug(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_\-]+", "_", value)
    token = re.sub(r"_+", "_", token).strip("_")
    return token.lower() or "unknown"


def _parse_groups(groups: str) -> Tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
    parts = [part.strip() for part in groups.split(",") if part.strip()]
    if len(parts) != 2:
        raise ValueError("Expected --groups in format 'Group[:Condition],Group[:Condition]'.")

    def _parse(spec: str) -> Dict[str, Optional[str]]:
        tokens = spec.split(":")
        return {"group": tokens[0], "condition": None if len(tokens) == 1 else tokens[1]}

    return _parse(parts[0]), _parse(parts[1])


def _display_name(spec: Dict[str, Optional[str]]) -> str:
    return str(spec["group"]) if spec.get("condition") in (None, "") else f"{spec['group']}:{spec['condition']}"


def _subset_for_spec(df: pd.DataFrame, spec: Dict[str, Optional[str]]) -> pd.DataFrame:
    frame = df[df["group"] == spec["group"]]
    condition = spec.get("condition")
    if condition is not None and "condition" in frame.columns:
        candidate = frame[frame["condition"] == condition]
        if not candidate.empty:
            return candidate
    return frame


def _dataset_name(dataset: Optional[str], csv_path: Path) -> str:
    if dataset:
        return dataset
    if "reachability_cones_subjects" in csv_path.stem and csv_path.parent.name:
        return csv_path.parent.name
    return csv_path.stem


def _max_horizon(df: pd.DataFrame) -> int:
    pattern = re.compile(r"^cone_kappa_h(\d+)_median$")
    horizons = []
    for column in df.columns:
        match = pattern.match(column)
        if match:
            horizons.append(int(match.group(1)))
    if not horizons:
        raise ValueError("Could not detect final reachability horizon from cone_kappa_h*_median columns.")
    return max(horizons)


def _derive_shape_frame(df: pd.DataFrame, final_horizon: int) -> pd.DataFrame:
    work = df.copy()
    endpoint_kappa_col = f"cone_kappa_h{final_horizon}_median"
    endpoint_deff_col = f"cone_d_eff_h{final_horizon}_median"
    for required in (endpoint_kappa_col, "tube_kappa_median", "tube_d_eff_median", "tube_log_det_median", "dims"):
        if required not in work.columns:
            raise ValueError(f"Missing required reachability column: {required}")

    dims = pd.to_numeric(work["dims"], errors="coerce")
    endpoint_kappa = pd.to_numeric(work[endpoint_kappa_col], errors="coerce")
    tube_kappa = pd.to_numeric(work["tube_kappa_median"], errors="coerce")
    tube_deff = pd.to_numeric(work["tube_d_eff_median"], errors="coerce")
    tube_log_det = pd.to_numeric(work["tube_log_det_median"], errors="coerce")
    endpoint_deff = pd.to_numeric(work[endpoint_deff_col], errors="coerce") if endpoint_deff_col in work.columns else np.nan

    work["endpoint_ovality_index"] = np.log10(np.clip(endpoint_kappa.to_numpy(dtype=float), 1.0, np.inf))
    compactness = tube_deff.to_numpy(dtype=float) / np.clip(dims.to_numpy(dtype=float), 1.0, np.inf)
    work["tube_compactness_ratio"] = np.clip(compactness, 0.0, 1.0)
    work["tube_elongation_index"] = np.log10(np.clip(tube_kappa.to_numpy(dtype=float), 1.0, np.inf))
    work["tube_likeness_index"] = work["tube_elongation_index"] * (1.0 - work["tube_compactness_ratio"])
    work["reachability_size"] = tube_log_det.to_numpy(dtype=float)
    work["endpoint_compactness_ratio"] = np.clip(endpoint_deff.to_numpy(dtype=float) / np.clip(dims.to_numpy(dtype=float), 1.0, np.inf), 0.0, 1.0)
    return work


def _bubble_sizes(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(values)
    if not mask.any():
        return np.full(values.shape, 120.0)
    lo = float(np.nanmin(values[mask]))
    hi = float(np.nanmax(values[mask]))
    if hi <= lo:
        return np.full(values.shape, 160.0)
    scaled = (values - lo) / (hi - lo)
    return 80.0 + 240.0 * np.clip(scaled, 0.0, 1.0)


def generate_reachability_shape_comparison(csv_path: Path, groups: str, dataset: Optional[str], output_root: Path) -> Tuple[Path, Path]:
    df = pd.read_csv(csv_path)
    spec_a, spec_b = _parse_groups(groups)
    frame_a = _subset_for_spec(df, spec_a)
    frame_b = _subset_for_spec(df, spec_b)
    if frame_a.empty or frame_b.empty:
        raise ValueError("One of the requested groups has zero rows after filtering.")

    final_horizon = _max_horizon(df)
    combined = pd.concat([frame_a, frame_b], ignore_index=True)
    combined = _derive_shape_frame(combined, final_horizon)
    label_a = _display_name(spec_a)
    label_b = _display_name(spec_b)
    comparison = f"{label_a} vs {label_b}"
    dataset_name = _dataset_name(dataset, csv_path)
    out_dir = output_root / dataset_name / "reachability"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.25], hspace=0.35, wspace=0.28)
    ax_ovality = fig.add_subplot(gs[0, 0])
    ax_tube = fig.add_subplot(gs[0, 1])
    ax_scatter = fig.add_subplot(gs[1, 0])
    ax_text = fig.add_subplot(gs[1, 1])

    for ax, column, ylabel in (
        (ax_ovality, "endpoint_ovality_index", "log10(kappa_H)"),
        (ax_tube, "tube_likeness_index", "tube-likeness index"),
    ):
        data_a = pd.to_numeric(combined.loc[: len(frame_a) - 1, column], errors="coerce").dropna().to_numpy(dtype=float)
        data_b = pd.to_numeric(combined.loc[len(frame_a) :, column], errors="coerce").dropna().to_numpy(dtype=float)
        datasets = [data_a, data_b]
        vp = ax.violinplot(datasets, positions=[1, 2], widths=0.75, showmeans=False, showextrema=False, showmedians=False)
        for body, color in zip(vp["bodies"], GROUP_COLORS):
            body.set_facecolor(color)
            body.set_alpha(0.28)
            body.set_edgecolor("none")
        box = ax.boxplot(datasets, positions=[1, 2], widths=0.4, patch_artist=True, medianprops={"color": "#333333", "linewidth": 1.2})
        for patch, color in zip(box["boxes"], GROUP_COLORS):
            patch.set_facecolor(color)
            patch.set_alpha(0.45)
            patch.set_edgecolor(color)
        rng = np.random.default_rng(42)
        for pos, values, color in zip([1, 2], datasets, GROUP_COLORS):
            if values.size:
                ax.scatter(np.full(values.size, pos) + rng.normal(0.0, 0.035, size=values.size), values, s=18, color=color, alpha=0.75, edgecolor="white", linewidth=0.4)
        ax.set_xticks([1, 2])
        ax.set_xticklabels([label_a, label_b], rotation=20, ha="right")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", linestyle=":", alpha=0.3)
    ax_ovality.set_title(f"Endpoint ovality at H={final_horizon}")
    ax_tube.set_title("Tube-like vs compact geometry")

    sizes = _bubble_sizes(combined["reachability_size"])
    group_labels = np.array([label_a] * len(frame_a) + [label_b] * len(frame_b), dtype=object)
    for idx, label in enumerate([label_a, label_b]):
        sub = combined[group_labels == label]
        if sub.empty:
            continue
        ax_scatter.scatter(
            sub["endpoint_ovality_index"],
            sub["tube_compactness_ratio"],
            s=sizes[group_labels == label],
            color=GROUP_COLORS[idx],
            alpha=0.6,
            edgecolor="white",
            linewidth=0.6,
            label=label,
        )
        ax_scatter.scatter(
            [float(pd.to_numeric(sub["endpoint_ovality_index"], errors="coerce").median())],
            [float(pd.to_numeric(sub["tube_compactness_ratio"], errors="coerce").median())],
            s=220,
            color=GROUP_COLORS[idx],
            edgecolor="black",
            linewidth=1.2,
            marker="X",
            zorder=5,
        )
    ax_scatter.axhline(0.5, color="#999999", linestyle="--", linewidth=1.0)
    ax_scatter.set_xlabel("Endpoint ovality index: log10(kappa_H)")
    ax_scatter.set_ylabel("Tube compactness ratio: d_eff / dims")
    ax_scatter.set_title("Group shape map\nHigher y = more compact, lower y = more tube-like")
    ax_scatter.grid(True, linestyle=":", alpha=0.25)
    ax_scatter.legend()

    ax_text.axis("off")
    medians = []
    for label in [label_a, label_b]:
        sub = combined[group_labels == label]
        medians.append(
            {
                "label": label,
                "n": int(len(sub)),
                "endpoint_ovality_index": float(pd.to_numeric(sub["endpoint_ovality_index"], errors="coerce").median()),
                "tube_compactness_ratio": float(pd.to_numeric(sub["tube_compactness_ratio"], errors="coerce").median()),
                "tube_elongation_index": float(pd.to_numeric(sub["tube_elongation_index"], errors="coerce").median()),
                "tube_likeness_index": float(pd.to_numeric(sub["tube_likeness_index"], errors="coerce").median()),
                "reachability_size": float(pd.to_numeric(sub["reachability_size"], errors="coerce").median()),
            }
        )
    notes = [
        f"Final horizon: H={final_horizon}",
        "Ovality index: higher means more anisotropic/oval cone-end.",
        "Compactness ratio: higher means fuller/more isotropic tube volume.",
        "Tube-likeness index: heuristic = log10(tube_kappa) * (1 - compactness).",
        "Bubble size in scatter: median tube_log_det reachability size.",
        "",
    ]
    for row in medians:
        notes.append(
            f"{row['label']}: n={row['n']}, ovality={row['endpoint_ovality_index']:.2f}, compactness={row['tube_compactness_ratio']:.2f}, tube-likeness={row['tube_likeness_index']:.2f}"
        )
    ax_text.text(0.0, 1.0, "\n".join(notes), ha="left", va="top", fontsize=10)

    fig.suptitle(f"Reachability shape comparison\n{comparison}", fontsize=16, y=0.98)
    image_path = out_dir / f"reachability_shape_comparison_{_slug(comparison)}.png"
    fig.savefig(image_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    payload = {
        "dataset": dataset_name,
        "comparison": comparison,
        "input_csv": str(csv_path),
        "final_horizon": final_horizon,
        "metric_notes": {
            "endpoint_ovality_index": "log10(cone_kappa_hH_median)",
            "tube_compactness_ratio": "tube_d_eff_median / dims",
            "tube_elongation_index": "log10(tube_kappa_median)",
            "tube_likeness_index": "log10(tube_kappa_median) * (1 - tube_d_eff_median / dims)",
            "reachability_size": "tube_log_det_median",
        },
        "group_medians": medians,
        "output_image": str(image_path),
    }
    json_path = out_dir / f"reachability_shape_comparison_{_slug(comparison)}.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return image_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reachability cone shape comparisons under visuals/output/<dataset>/reachability/")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--groups", required=True)
    parser.add_argument("--dataset")
    parser.add_argument("--output-root", default=str(Path(__file__).resolve().parent / "output"))
    args = parser.parse_args()
    written = generate_reachability_shape_comparison(
        csv_path=Path(args.csv).resolve(),
        groups=args.groups,
        dataset=args.dataset,
        output_root=Path(args.output_root).resolve(),
    )
    for path in written:
        print(f" - {path}")


if __name__ == "__main__":
    main()
