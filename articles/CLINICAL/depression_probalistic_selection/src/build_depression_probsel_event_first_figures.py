from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from depression_probsel_event_support import (
    BDI_CORRELATIONS_CSV,
    BDI_GROUP_CONTRASTS_CSV,
    RESULTS_DIR,
    WITHIN_SUBJECT_CONTRASTS_CSV,
    ensure_dir,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build simple figures for the ds003474 event-first wrapper.")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--figures-dir", type=Path, default=Path(__file__).resolve().parents[1] / "figures")
    return parser.parse_args()


def _top_rows(frame: pd.DataFrame, *, score_col: str, n: int = 10) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = frame.copy()
    out["_score"] = pd.to_numeric(out[score_col], errors="coerce").abs()
    if "q_value" in out.columns:
        out["_q"] = pd.to_numeric(out["q_value"], errors="coerce")
    else:
        out["_q"] = np.nan
    if "p_value" in out.columns:
        out["_p"] = pd.to_numeric(out["p_value"], errors="coerce")
    else:
        out["_p"] = np.nan
    out = out.sort_values(
        ["_q", "_p", "_score"],
        ascending=[True, True, False],
        na_position="last",
    ).head(n)
    return out.reset_index(drop=True)


def _label(row: pd.Series, *, value_key: str) -> str:
    return f"{row['contrast_name']}\n{row['analysis_type']}\n{row['metric']}\n{value_key}={float(row[value_key]):.3f}"


def _plot_horizontal(frame: pd.DataFrame, *, value_col: str, title: str, out_path: Path) -> None:
    if frame.empty:
        return
    labels = [_label(row, value_key=value_col) for _, row in frame.iterrows()]
    values = pd.to_numeric(frame[value_col], errors="coerce").to_numpy(dtype=float)
    q_values = pd.to_numeric(frame.get("q_value"), errors="coerce").to_numpy(dtype=float)
    colors = ["#7b3294" if np.isfinite(q) and q <= 0.05 else "#008837" for q in q_values]

    fig, ax = plt.subplots(figsize=(11, max(5.5, 0.6 * len(frame) + 2)))
    ypos = np.arange(len(frame))
    ax.barh(ypos, values, color=colors, alpha=0.85)
    ax.axvline(0.0, color="black", linewidth=1.0)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title(title)
    ax.set_xlabel(value_col)
    ax.invert_yaxis()

    for idx, (_, row) in enumerate(frame.iterrows()):
        q_text = f"q={float(row['q_value']):.3g}" if pd.notna(row.get("q_value")) else "q=nan"
        p_text = f"p={float(row['p_value']):.3g}" if pd.notna(row.get("p_value")) else "p=nan"
        ax.text(values[idx], idx, f"  {p_text}, {q_text}", va="center", ha="left", fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    ensure_dir(args.figures_dir)

    within_subject = pd.read_csv(args.results_dir / WITHIN_SUBJECT_CONTRASTS_CSV, low_memory=False)
    bdi_groups = pd.read_csv(args.results_dir / BDI_GROUP_CONTRASTS_CSV, low_memory=False)
    bdi_corr = pd.read_csv(args.results_dir / BDI_CORRELATIONS_CSV, low_memory=False)

    _plot_horizontal(
        _top_rows(within_subject, score_col="effect_size", n=12),
        value_col="effect_size",
        title="Top event-first within-subject PST contrasts",
        out_path=args.figures_dir / "draft2_within_subject_contrasts.png",
    )
    _plot_horizontal(
        _top_rows(bdi_groups, score_col="effect_size", n=12),
        value_col="effect_size",
        title="Top BDI low-vs-high modulation of PST contrasts",
        out_path=args.figures_dir / "draft2_bdi_group_modulation.png",
    )
    _plot_horizontal(
        _top_rows(bdi_corr, score_col="spearman_rho", n=12),
        value_col="spearman_rho",
        title="Top continuous-BDI modulation of PST contrasts",
        out_path=args.figures_dir / "draft2_bdi_correlation_modulation.png",
    )


if __name__ == "__main__":
    main()
