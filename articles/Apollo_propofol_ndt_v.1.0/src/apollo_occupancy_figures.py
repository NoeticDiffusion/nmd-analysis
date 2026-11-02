"""Article occupancy figures: trajectory, paired deltas, match-fraction collapse."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from apollo_c3_panel import MIN_PAIRS
from apollo_common import ARTICLE_DIR
from apollo_occupancy_panel import BASELINE_PHASE, ORDERED_LATERS

OCCUPANCY_DIR = ARTICLE_DIR / "results" / "v1_occupancy_20260921"
FIGURES_DEFAULT = ARTICLE_DIR / "figures" / "occupancy"
PHASES = (BASELINE_PHASE, *ORDERED_LATERS)
PHASE_LABELS = (
    "Baseline",
    "First sedation",
    "Later sedation",
    "Recovery",
)
OCCUPANCY_COLS = [f"occupancy_{phase}" for phase in PHASES]
COLOR_LINE = "#4C78A8"
COLOR_MEDIAN = "#222222"
COLOR_POS = "#4C78A8"
COLOR_NEG = "#E45756"
COLOR_INCLUDED = "#54A24B"
COLOR_EXCLUDED = "#B279A2"


def _style(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=3)


def save_figure(fig, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    png = stem.with_suffix(".png")
    pdf = stem.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return [png, pdf]


def figure_trajectory(subjects: pd.DataFrame, output_dir: Path) -> list[Path]:
    values = subjects[OCCUPANCY_COLS].to_numpy(dtype=float)
    x = np.arange(len(PHASES), dtype=float)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for row in values:
        ax.plot(x, row, color=COLOR_LINE, alpha=0.35, lw=1.2)
        ax.scatter(x, row, color=COLOR_LINE, s=12, alpha=0.45, zorder=3)
    med = np.nanmedian(values, axis=0)
    ax.plot(x, med, color=COLOR_MEDIAN, lw=2.2, marker="o", ms=6, zorder=4, label="Cohort median")
    ax.set_xticks(x, PHASE_LABELS)
    ax.set_ylabel(r"Occupancy median $\|z\|_2$")
    ax.set_title("Baseline-fixed occupancy trajectory")
    ax.legend(frameon=False, loc="upper left")
    _style(ax)
    fig.tight_layout()
    return save_figure(fig, output_dir / "fig1_occupancy_trajectory")


def figure_paired_deltas(subjects: pd.DataFrame, output_dir: Path) -> list[Path]:
    later = pd.to_numeric(subjects["occupancy_first_protocol_sedation"], errors="coerce")
    base = pd.to_numeric(subjects["occupancy_pre_drug_baseline"], errors="coerce")
    table = pd.DataFrame(
        {
            "subject_id": subjects["subject_id"].to_numpy(),
            "delta": later - base,
        }
    ).dropna(subset=["delta"]).sort_values("delta")
    colors = [COLOR_POS if value >= 0 else COLOR_NEG for value in table["delta"]]
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    y = np.arange(len(table), dtype=float)
    ax.axvline(0.0, color="#888888", lw=1.0)
    ax.hlines(y, 0.0, table["delta"], colors=colors, lw=1.6)
    ax.scatter(table["delta"], y, c=colors, s=22, zorder=3)
    ax.set_yticks(y, table["subject_id"])
    ax.set_xlabel("Occupancy Δ (first sedation − baseline)")
    ax.set_title("Subject-level occupancy relocation")
    n_pos = int((table["delta"] > 0).sum())
    n = int(len(table))
    ax.text(
        0.98,
        0.04,
        f"{n_pos}/{n} increase",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
    )
    _style(ax)
    fig.tight_layout()
    return save_figure(fig, output_dir / "fig2_occupancy_paired_deltas")


def figure_match_collapse(support: pd.DataFrame, output_dir: Path) -> list[Path]:
    table = support.copy()
    table["n_pairs"] = pd.to_numeric(table["n_pairs"], errors="coerce")
    table["included"] = table["included"].astype(bool)
    table = table.sort_values("n_pairs")
    colors = [COLOR_INCLUDED if ok else COLOR_EXCLUDED for ok in table["included"]]
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    y = np.arange(len(table), dtype=float)
    ax.barh(y, table["n_pairs"], color=colors, height=0.72)
    ax.axvline(MIN_PAIRS, color="#222222", lw=1.2, ls="--", label=f"Gate = {MIN_PAIRS} pairs")
    ax.set_yticks(y, table["subject_id"])
    ax.set_xlabel("Matched pairs at first sedation")
    n_inc = int(table["included"].sum())
    ax.set_title(f"C3 common-support collapse ({n_inc}/20 testable)")
    ax.legend(frameon=False, loc="lower right")
    _style(ax)
    fig.tight_layout()
    return save_figure(fig, output_dir / "fig3_c3_match_collapse")


def figure_occupancy_vs_hits(joined: pd.DataFrame, output_dir: Path) -> list[Path]:
    x = pd.to_numeric(joined["n_correct_later_protocol_sedation"], errors="coerce")
    y = pd.to_numeric(joined["occupancy_later_protocol_sedation"], errors="coerce")
    status = joined["lor_status"].astype(str)
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    for label, color in (("responsive", COLOR_LINE), ("lor_impaired", COLOR_NEG)):
        mask = status.eq(label) & np.isfinite(x) & np.isfinite(y)
        ax.scatter(x[mask], y[mask], c=color, s=36, label=label.replace("_", " "), zorder=3)
    ax.set_xlabel("Correct responses / 40 at later sedation")
    ax.set_ylabel(r"Occupancy median $\|z\|_2$")
    ax.set_title("Occupancy vs behavioural hit count")
    ax.legend(frameon=False, loc="upper right")
    _style(ax)
    fig.tight_layout()
    return save_figure(fig, output_dir / "figS_occupancy_vs_hits")


def write_all(*, occupancy_root: Path, output_dir: Path) -> list[Path]:
    subjects = pd.read_csv(occupancy_root / "occupancy_subject.csv")
    support = pd.read_csv(occupancy_root / "c3_anchor_match_support.csv")
    written = []
    written.extend(figure_trajectory(subjects, output_dir))
    written.extend(figure_paired_deltas(subjects, output_dir))
    written.extend(figure_match_collapse(support, output_dir))
    lor_path = ARTICLE_DIR / "results" / "v1_lor_20260921" / "lor_occupancy_joined.csv"
    if lor_path.is_file():
        written.extend(figure_occupancy_vs_hits(pd.read_csv(lor_path), output_dir))
    return written


def main() -> int:
    written = write_all(occupancy_root=OCCUPANCY_DIR, output_dir=FIGURES_DEFAULT)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
