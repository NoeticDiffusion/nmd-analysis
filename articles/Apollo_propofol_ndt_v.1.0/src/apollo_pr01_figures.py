"""Figures for the PR-01 exploratory geometric dissection."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from apollo_common import ARTICLE_DIR
from apollo_occupancy_panel import BASELINE_PHASE, ORDERED_LATERS

ROOT = ARTICLE_DIR / "results" / "v1_pr01_geometric_20260922_final2"
OUT = ARTICLE_DIR / "figures" / "pr01"
PHASES = (BASELINE_PHASE, *ORDERED_LATERS)
PHASE_LABELS = ("Baseline", "First\nsedation", "Later\nsedation", "Recovery")
FEATURE_LABELS = {"eeg_delta": "delta", "eeg_theta": "theta", "eeg_alpha": "alpha", "eeg_beta": "beta", "eeg_gamma": "gamma", "eeg_alpha_theta": "alpha/theta", "eeg_beta_alpha": "beta/alpha", "eeg_sample_entropy": "sample entropy"}


def _save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def feature_heatmap(table: pd.DataFrame) -> None:
    ordered_features = list(FEATURE_LABELS)
    matrix = table.pivot(index="feature", columns="phase", values="cohort_median_baseline_z").reindex(index=ordered_features, columns=PHASES)
    bound = max(1.0, float(np.nanmax(np.abs(matrix.to_numpy(dtype=float)))))
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    image = ax.imshow(matrix.to_numpy(dtype=float), cmap="coolwarm", vmin=-bound, vmax=bound, aspect="auto")
    ax.set_xticks(range(len(PHASES)), PHASE_LABELS)
    ax.set_yticks(range(len(ordered_features)), [FEATURE_LABELS[x] for x in ordered_features])
    ax.set_title("Median feature displacement in the baseline-fixed frame")
    for i in range(len(ordered_features)):
        for j in range(len(PHASES)):
            value = matrix.iloc[i, j]
            ax.text(j, i, f"{value:.1f}", ha="center", va="center", fontsize=8, color="black" if abs(value) < bound * .65 else "white")
    cbar = fig.colorbar(image, ax=ax, pad=.02)
    cbar.set_label("Cohort median of participant phase medians (baseline z)")
    fig.tight_layout()
    _save(fig, "fig2_feature_phase_heatmap")


def caliper_curve(table: pd.DataFrame) -> None:
    summary = table.groupby("caliper_multiplier", as_index=False)["included_at_20_pairs"].sum()
    fig, ax = plt.subplots(figsize=(6.4, 4.1))
    ax.plot(summary["caliper_multiplier"], summary["included_at_20_pairs"], marker="o", lw=2, color="#4C78A8")
    ax.axhline(10, ls="--", lw=1.2, color="#555555", label="Cohort gate = 10")
    ax.set_xticks(summary["caliper_multiplier"])
    ax.set_xlabel("Frozen subject caliper multiplier")
    ax.set_ylabel("Participants with >=20 matched pairs")
    ax.set_title("C3 common-support sensitivity")
    ax.set_ylim(0, 20)
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, "fig4_caliper_sensitivity")


def main() -> int:
    feature_heatmap(pd.read_csv(ROOT / "feature_phase_cohort_medians.csv"))
    caliper_curve(pd.read_csv(ROOT / "caliper_sensitivity.csv"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
