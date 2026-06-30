from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


PREFIXES = ["v2_m_a", "v2_m_e", "v2_m_o", "v2_d_n", "v2_d_l", "v2_d_s", "v2_e_e", "v2_e_s", "v2_e_m"]
SHORT_LABELS = ["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"]
FAMILY_COLORS = (["#4C78A8"] * 3) + (["#E15759"] * 3) + (["#59A14F"] * 3)


def _ensure_out(out: Path) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    return out


def _slug(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_\-]+", "_", value)
    token = re.sub(r"_+", "_", token).strip("_")
    return token.lower() or "unknown"


def _load_groupdiff(path: Path) -> Dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _comparison_label(data: Dict) -> str:
    contrast = data.get("contrast", [])
    if isinstance(contrast, (list, tuple)) and len(contrast) == 2:
        return f"{contrast[0]} vs {contrast[1]}"
    return Path(str(data.get("source_json", "stratified_mnps"))).stem


def _dataset_name(dataset: Optional[str], csv_path: Optional[Path], groupdiff_path: Path) -> str:
    if dataset:
        return dataset
    if csv_path is not None:
        csv_name = csv_path.stem
        if csv_name:
            return csv_name
    return groupdiff_path.stem.replace("_group_diff", "")


def _top_feature_rows(data: Dict, top_k: int) -> List[Tuple[str, float, float, float]]:
    features: Dict[str, Dict] = data.get("features", {})
    rows: List[Tuple[str, float, float, float]] = []
    for name, vals in features.items():
        d = float(vals.get("cohens_d", np.nan))
        lo = hi = np.nan
        ci = vals.get("cohens_d_ci")
        if isinstance(ci, list) and len(ci) == 2:
            lo = float(ci[0])
            hi = float(ci[1])
        rows.append((name, d, lo, hi))
    rows.sort(key=lambda row: (0.0 if not np.isfinite(row[1]) else abs(row[1])), reverse=True)
    return rows[: max(1, int(top_k))]


def lollipop_from_groupdiff(groupdiff_json: Path, out_dir: Path, top_k: int = 10) -> Path:
    out_dir = _ensure_out(out_dir)
    data = _load_groupdiff(groupdiff_json)
    comparison_label = _comparison_label(data)
    rows = _top_feature_rows(data, top_k=top_k)

    if not rows:
        fig = plt.figure(figsize=(8, 4))
        plt.title(f"No features available\n({comparison_label})")
        out_path = out_dir / f"stratified_mnps_lollipop_{_slug(comparison_label)}.png"
        fig.tight_layout()
        fig.savefig(out_path, dpi=180)
        plt.close(fig)
        return out_path

    names = [row[0] for row in rows]
    dvals = np.array([row[1] for row in rows], dtype=float)
    dlos = np.array([row[2] for row in rows], dtype=float)
    dhis = np.array([row[3] for row in rows], dtype=float)
    y = np.arange(len(names))[::-1]

    fig, ax = plt.subplots(figsize=(10, max(4, 0.45 * len(names) + 2)))
    ax.hlines(y=y, xmin=0, xmax=dvals, color="#999999", lw=2)
    ax.scatter(dvals, y, color=np.where(dvals >= 0, "#2ca02c", "#d62728"), s=40, zorder=3)
    for idx, (lo, hi) in enumerate(zip(dlos, dhis)):
        if np.isfinite(lo) and np.isfinite(hi):
            ax.plot([lo, hi], [y[idx], y[idx]], color="#555555", lw=1.5)
    ax.axvline(0.0, color="#333333", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel("Cohen's d")
    ax.set_title(f"Stratified MNPS lollipop\n{comparison_label}")
    ax.grid(axis="x", linestyle=":", alpha=0.35)
    fig.tight_layout()
    out_path = out_dir / f"stratified_mnps_lollipop_{_slug(comparison_label)}.png"
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    return out_path


def grouped_bar_profile(
    groupdiff_json: Path,
    out_dir: Path,
    *,
    stat_type: str = "mean",
    metric: str = "cohens_d",
) -> Path:
    out_dir = _ensure_out(out_dir)
    data = _load_groupdiff(groupdiff_json)
    comparison_label = _comparison_label(data)
    features = data.get("features", {})
    subcoords = [f"{prefix}_{stat_type}" for prefix in PREFIXES]
    values = np.array([features.get(key, {}).get(metric, 0.0) for key in subcoords], dtype=float)
    ci_key = f"{metric}_ci"
    cis = np.array(
        [
            features.get(key, {}).get(ci_key, [features.get(key, {}).get(metric, 0.0)] * 2)
            for key in subcoords
        ],
        dtype=float,
    )
    has_ci = np.isfinite(cis).all()

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(SHORT_LABELS))
    if has_ci:
        errors = np.abs(cis.T - values)
        ax.bar(x, values, yerr=errors, capsize=5, color=FAMILY_COLORS, alpha=0.85, edgecolor="black", linewidth=1)
    else:
        ax.bar(x, values, color=FAMILY_COLORS, alpha=0.85, edgecolor="black", linewidth=1)
    ax.axhline(0, color="black", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(SHORT_LABELS, fontsize=11)
    ax.set_ylabel("Cohen's d" if metric == "cohens_d" else metric)
    ax.set_title(f"Stratified profile ({stat_type})\n{comparison_label}")
    for xpos in [2.5, 5.5]:
        ax.axvline(xpos, color="gray", linestyle="--", alpha=0.5)
    y_top = ax.get_ylim()[1]
    ax.text(1, y_top * 0.9, "m-family", ha="center", fontweight="bold", color="#4C78A8")
    ax.text(4, y_top * 0.9, "d-family", ha="center", fontweight="bold", color="#E15759")
    ax.text(7, y_top * 0.9, "e-family", ha="center", fontweight="bold", color="#59A14F")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out_path = out_dir / f"stratified_mnps_profile_{stat_type}_{metric}_{_slug(comparison_label)}.png"
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    return out_path


def nightingale_rose_plot(
    groupdiff_json: Path,
    out_dir: Path,
    *,
    stat_type: str = "mean",
    metric: str = "cohens_d",
) -> Path:
    out_dir = _ensure_out(out_dir)
    data = _load_groupdiff(groupdiff_json)
    comparison_label = _comparison_label(data)
    features = data.get("features", {})
    subcoords = [f"{prefix}_{stat_type}" for prefix in PREFIXES]
    values = np.array([features.get(key, {}).get(metric, 0.0) for key in subcoords], dtype=float)
    radii = np.abs(values)
    angles = np.linspace(0, 2 * np.pi, len(subcoords), endpoint=False)
    width = 2 * np.pi / len(subcoords)

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection="polar"))
    bars = ax.bar(angles, radii, width=width, bottom=0.0, color=FAMILY_COLORS, alpha=0.7, edgecolor="white", lw=2)
    for bar, value in zip(bars, values):
        if value < 0:
            bar.set_hatch("//")
            bar.set_alpha(0.5)
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2.0)
    ax.set_xticks(angles)
    ax.set_xticklabels(SHORT_LABELS, fontsize=12, fontweight="bold")
    max_r = np.max(radii) if radii.size and not np.all(np.isnan(radii)) else 1.0
    ax.set_ylim(0, max_r * 1.1)
    ax.set_title(f"{comparison_label}\n({stat_type.upper()})", pad=30, fontsize=14)
    legend_elements = [
        patches.Patch(facecolor="#4C78A8", alpha=0.7, label="m-family"),
        patches.Patch(facecolor="#E15759", alpha=0.7, label="d-family"),
        patches.Patch(facecolor="#59A14F", alpha=0.7, label="e-family"),
        patches.Patch(facecolor="gray", alpha=0.3, hatch="//", label="Negative value"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(1.3, 1.1))
    fig.tight_layout()
    out_path = out_dir / f"stratified_mnps_rose_{stat_type}_{metric}_{_slug(comparison_label)}.png"
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    return out_path


def stratified_dual_rose_plot(
    groupdiff_json: Path,
    out_dir: Path,
    *,
    stat_type: str = "mean",
    metric: str = "cohens_d",
) -> Path:
    out_dir = _ensure_out(out_dir)
    data = _load_groupdiff(groupdiff_json)
    comparison_label = _comparison_label(data)
    features = data.get("features", {})
    subcoords = [f"{prefix}_{stat_type}" for prefix in PREFIXES]
    effect_values = np.array([features.get(key, {}).get(metric, 0.0) for key in subcoords], dtype=float)
    p_values = np.array([features.get(key, {}).get("p", 1.0) for key in subcoords], dtype=float)
    sig_values = np.clip(-np.log10(p_values + 1e-12), 0, 10)
    angles = np.linspace(0, 2 * np.pi, len(subcoords), endpoint=False)
    width = 2 * np.pi / len(subcoords)

    fig = plt.figure(figsize=(16, 8))
    ax1 = fig.add_subplot(121, projection="polar")
    bars1 = ax1.bar(angles, np.abs(effect_values), width=width, bottom=0.0, color=FAMILY_COLORS, alpha=0.7, edgecolor="white", lw=2)
    for bar, value in zip(bars1, effect_values):
        if value < 0:
            bar.set_hatch("//")
            bar.set_alpha(0.5)
    ax1.set_theta_direction(-1)
    ax1.set_theta_offset(np.pi / 2.0)
    ax1.set_xticks(angles)
    ax1.set_xticklabels(SHORT_LABELS, fontsize=10, fontweight="bold")
    ax1.set_title("Effect size", pad=20, fontsize=12)

    ax2 = fig.add_subplot(122, projection="polar")
    ax2.bar(angles, sig_values, width=width, bottom=0.0, color=FAMILY_COLORS, alpha=0.7, edgecolor="white", lw=2)
    p05_level = -np.log10(0.05)
    ax2.plot(np.linspace(0, 2 * np.pi, 100), [p05_level] * 100, color="red", linestyle="--", lw=1.5, label="p=0.05")
    ax2.set_theta_direction(-1)
    ax2.set_theta_offset(np.pi / 2.0)
    ax2.set_xticks(angles)
    ax2.set_xticklabels(SHORT_LABELS, fontsize=10, fontweight="bold")
    ax2.set_title("-log10(p)", pad=20, fontsize=12)
    ax2.legend(loc="lower right", bbox_to_anchor=(1.2, 0))

    fig.suptitle(f"{comparison_label} ({stat_type.upper()})", fontsize=16, y=1.02)
    fig.tight_layout()
    out_path = out_dir / f"stratified_mnps_dual_rose_{stat_type}_{metric}_{_slug(comparison_label)}.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _parse_groups(groups: str) -> Tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
    parts = [part.strip() for part in groups.split(",") if part.strip()]
    if len(parts) != 2:
        raise ValueError("Expected --groups in format 'Group[:Condition],Group[:Condition]'.")

    def _parse(spec: str) -> Dict[str, Optional[str]]:
        tokens = spec.split(":")
        if len(tokens) == 1:
            return {"group": tokens[0], "condition": None}
        return {"group": tokens[0], "condition": tokens[1]}

    return _parse(parts[0]), _parse(parts[1])


def _display_name(spec: Dict[str, Optional[str]]) -> str:
    if spec.get("condition") in (None, ""):
        return str(spec["group"])
    return f"{spec['group']}:{spec['condition']}"


def _subset_for_spec(df: pd.DataFrame, spec: Dict[str, Optional[str]]) -> pd.DataFrame:
    frame = df[df["group"] == spec["group"]]
    condition = spec.get("condition")
    if condition is not None and "condition" in frame.columns:
        filtered = frame[frame["condition"] == condition]
        if not filtered.empty:
            return filtered
    return frame


def boxplots_from_csv(
    csv_path: Path,
    groups: str,
    features: Sequence[str],
    out_dir: Path,
) -> Path:
    out_dir = _ensure_out(out_dir)
    df = pd.read_csv(csv_path)
    spec_a, spec_b = _parse_groups(groups)
    frame_a = _subset_for_spec(df, spec_a)
    frame_b = _subset_for_spec(df, spec_b)
    labels = [_display_name(spec_a), _display_name(spec_b)]

    fig, axes = plt.subplots(1, len(features), figsize=(4 * len(features), 4), sharey=False)
    if len(features) == 1:
        axes = [axes]
    for ax, feat in zip(axes, features):
        if feat not in df.columns:
            ax.text(0.5, 0.5, f"Missing: {feat}", ha="center", va="center", transform=ax.transAxes)
            continue
        data = [frame_a[feat].dropna().to_numpy(), frame_b[feat].dropna().to_numpy()]
        ax.boxplot(data, tick_labels=labels, widths=0.5)
        ax.set_title(feat)
        ax.tick_params(axis="x", rotation=25)
    comparison = f"{labels[0]} vs {labels[1]}"
    fig.suptitle(f"Stratified MNPS boxplots\n{comparison}")
    fig.tight_layout()
    out_path = out_dir / f"stratified_mnps_boxplots_{_slug(comparison)}.png"
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    return out_path


def comparison_report_from_inputs(
    csv_path: Path,
    group_diff_json: Path,
    groups: str,
    out_dir: Path,
    *,
    top_k: int = 6,
) -> Path:
    out_dir = _ensure_out(out_dir)
    df = pd.read_csv(csv_path)
    diff = _load_groupdiff(group_diff_json)
    features = diff.get("features", {})
    fdr_rejected = set(diff.get("fdr", {}).get("rejected", []))
    spec_a, spec_b = _parse_groups(groups)
    frame_a = _subset_for_spec(df, spec_a)
    frame_b = _subset_for_spec(df, spec_b)
    if frame_a.empty or frame_b.empty:
        raise ValueError("One of the requested groups has zero rows after filtering.")

    rows = []
    for feat, vals in features.items():
        d_val = vals.get("cohens_d")
        if not isinstance(d_val, (int, float)):
            continue
        rows.append(
            {
                "feature": feat,
                "cohens_d": float(d_val),
                "p": float(vals.get("p")) if isinstance(vals.get("p"), (int, float)) else np.nan,
                "ci": vals.get("cohens_d_ci") if isinstance(vals.get("cohens_d_ci"), (list, tuple)) else None,
            }
        )
    rows.sort(key=lambda row: abs(row["cohens_d"]) if np.isfinite(row["cohens_d"]) else -np.inf, reverse=True)
    top_rows = rows[: max(1, int(top_k))]

    fig = plt.figure(figsize=(15, 9))
    gs = fig.add_gridspec(2, 4, height_ratios=[3.2, 1.3], width_ratios=[1.6, 1.4, 1.2, 1.2], hspace=0.45, wspace=0.4)

    ax_effect = fig.add_subplot(gs[0, 0:2])
    positions = np.arange(len(top_rows))[::-1]
    ci_extents: List[float] = []
    for idx, row in enumerate(top_rows):
        lo = hi = np.nan
        if row["ci"] and len(row["ci"]) == 2:
            lo = float(row["ci"][0])
            hi = float(row["ci"][1])
            ax_effect.plot([lo, hi], [positions[idx], positions[idx]], color="#6b6b6b", lw=2.0, zorder=1, alpha=0.9)
            ci_extents.extend([abs(lo), abs(hi)])
        color = "#e15759" if row["feature"] in fdr_rejected else "#4e79a7"
        ax_effect.scatter(row["cohens_d"], positions[idx], color=color, s=65, zorder=2, edgecolor="white", linewidth=0.6)
    ax_effect.axvline(0.0, color="#333333", linewidth=1.0, linestyle="--", alpha=0.7)
    ax_effect.set_xlabel("Cohen's d")
    ax_effect.set_yticks(positions)
    ax_effect.set_yticklabels([row["feature"] + (" *" if row["feature"] in fdr_rejected else "") for row in top_rows])
    ax_effect.set_title("Top-|d| features with 95% CI")
    ax_effect.grid(axis="x", linestyle=":", alpha=0.4)
    span = max(ci_extents + [abs(row["cohens_d"]) for row in top_rows] + [1.0])
    ax_effect.set_xlim(-1.1 * span, 1.1 * span)

    violin_count = min(len(top_rows), 4)
    violin_spec = gs[0, 2:].subgridspec(int(math.ceil(violin_count / 2)), 2, hspace=0.5, wspace=0.45)
    group_labels = [_display_name(spec_a), _display_name(spec_b)]
    rng = np.random.default_rng(42)
    for idx in range(violin_count):
        row = top_rows[idx]
        ax = fig.add_subplot(violin_spec[idx // 2, idx % 2])
        feat = row["feature"]
        if feat not in df.columns:
            ax.text(0.5, 0.5, "Missing in CSV", ha="center", va="center", transform=ax.transAxes)
            ax.set_xticks([])
            continue
        data_a = frame_a[feat].dropna().to_numpy(dtype=float)
        data_b = frame_b[feat].dropna().to_numpy(dtype=float)
        datasets = [data_a, data_b]
        if data_a.size >= 6 and data_b.size >= 6:
            vp = ax.violinplot(datasets, positions=[1, 2], widths=0.75, showmeans=False, showextrema=False, showmedians=False)
            for body, color in zip(vp["bodies"], ["#1f77b4", "#ff7f0e"]):
                body.set_facecolor(color)
                body.set_alpha(0.28)
                body.set_edgecolor("none")
        box = ax.boxplot(
            datasets,
            positions=[1, 2],
            widths=0.4,
            patch_artist=True,
            medianprops={"color": "#333333", "linewidth": 1.2},
        )
        for patch, color in zip(box["boxes"], ["#1f77b4", "#ff7f0e"]):
            patch.set_facecolor(color)
            patch.set_alpha(0.45)
            patch.set_edgecolor(color)
        for pos, values, color in zip([1, 2], datasets, ["#1f77b4", "#ff7f0e"]):
            if values.size:
                jitter = rng.normal(0.0, 0.035, size=values.size)
                ax.scatter(np.full(values.size, pos) + jitter, values, s=18, color=color, alpha=0.7, edgecolor="white", linewidth=0.4)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(group_labels, rotation=25, ha="right")
        ax.set_title(feat + (" *" if feat in fdr_rejected else ""))
        ax.grid(axis="y", linestyle=":", alpha=0.3)

    ax_table = fig.add_subplot(gs[1, :])
    ax_table.axis("off")
    table_rows = []
    for idx, row in enumerate(top_rows):
        feat = row["feature"]
        n_a = int(frame_a[feat].dropna().size) if feat in frame_a.columns else 0
        n_b = int(frame_b[feat].dropna().size) if feat in frame_b.columns else 0
        ci_text = "—"
        if row["ci"] and len(row["ci"]) == 2:
            ci_text = f"[{float(row['ci'][0]):.2f}, {float(row['ci'][1]):.2f}]"
        table_rows.append(
            [
                str(idx + 1),
                feat,
                f"{row['cohens_d']:.2f}",
                ci_text,
                f"{row['p']:.3g}" if np.isfinite(row["p"]) else "NA",
                "yes" if feat in fdr_rejected else "no",
                str(n_a),
                str(n_b),
            ]
        )
    table = ax_table.table(
        cellText=table_rows,
        colLabels=["Rank", "Feature", "Cohen's d", "d CI", "p", "FDR", f"n ({group_labels[0]})", f"n ({group_labels[1]})"],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.4)

    comparison = _comparison_label(diff)
    fig.suptitle(f"Stratified MNPS report\n{comparison}", fontsize=16, y=0.98)
    out_path = out_dir / f"stratified_mnps_report_{_slug(comparison)}.png"
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_outputs(
    *,
    kind: str,
    dataset: Optional[str],
    output_root: Path,
    group_diff_json: Path,
    csv_path: Optional[Path],
    groups: Optional[str],
    top_k: int,
    stat_type: str,
    metric: str,
) -> List[Path]:
    dataset_name = _dataset_name(dataset, csv_path, group_diff_json)
    base_dir = output_root / dataset_name
    written: List[Path] = []

    if kind in {"lollipop", "all"}:
        written.append(lollipop_from_groupdiff(group_diff_json, base_dir / "lollipop", top_k=top_k))
    if kind in {"rose", "all"}:
        written.append(nightingale_rose_plot(group_diff_json, base_dir / "rose", stat_type=stat_type, metric=metric))
    if kind in {"dual-rose", "all"}:
        written.append(stratified_dual_rose_plot(group_diff_json, base_dir / "rose", stat_type=stat_type, metric=metric))
    if kind in {"profile", "all"}:
        written.append(grouped_bar_profile(group_diff_json, base_dir / "profile", stat_type=stat_type, metric=metric))
    if kind in {"boxplots", "all"}:
        if csv_path is None or groups is None:
            raise ValueError("--csv and --groups are required for boxplots.")
        top_features = [row[0] for row in _top_feature_rows(_load_groupdiff(group_diff_json), top_k=min(top_k, 4))]
        written.append(boxplots_from_csv(csv_path, groups, top_features, base_dir / "boxplots"))
    if kind in {"report", "all"}:
        if csv_path is None or groups is None:
            raise ValueError("--csv and --groups are required for report.")
        written.append(comparison_report_from_inputs(csv_path, group_diff_json, groups, base_dir / "report", top_k=min(top_k, 8)))
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stratified/group-diff plots into visuals/output/<dataset>/<figure-type>/")
    parser.add_argument("--group-diff-json", required=True, help="Path to group_diff JSON.")
    parser.add_argument("--csv", help="Optional CSV with per-subject feature columns.")
    parser.add_argument("--groups", help="Contrast string 'Group[:Condition],Group[:Condition]' for report/boxplots.")
    parser.add_argument("--dataset", help="Override dataset folder name.")
    parser.add_argument(
        "--output-root",
        default=str(Path(__file__).resolve().parent / "output"),
        help="Root output directory. Dataset and figure-type folders are added automatically.",
    )
    parser.add_argument("--kind", choices=("all", "lollipop", "boxplots", "report", "rose", "dual-rose", "profile"), default="all")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--stat-type", default="mean")
    parser.add_argument("--metric", default="cohens_d")
    args = parser.parse_args()

    written = generate_outputs(
        kind=args.kind,
        dataset=args.dataset,
        output_root=Path(args.output_root).resolve(),
        group_diff_json=Path(args.group_diff_json).resolve(),
        csv_path=Path(args.csv).resolve() if args.csv else None,
        groups=args.groups,
        top_k=args.top_k,
        stat_type=args.stat_type,
        metric=args.metric,
    )
    for path in written:
        print(f" - {path}")


if __name__ == "__main__":
    main()
