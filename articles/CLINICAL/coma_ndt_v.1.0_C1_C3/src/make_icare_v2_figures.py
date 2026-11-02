"""Summary figures for I-CARE v2 CPC1 vs CPC5 smoke/full outputs."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from icare_v2_common import add_common_args, resolve_pipeline_config


def _boxplot(ax, frame: pd.DataFrame, metric: str, cfg) -> None:
    groups = [cfg.good_label, cfg.poor_label]
    data = [
        pd.to_numeric(frame.loc[frame["contrast_group"] == label, metric], errors="coerce").dropna().to_numpy()
        for label in groups
    ]
    try:
        ax.boxplot(data, tick_labels=groups, showfliers=True)
    except TypeError:
        ax.boxplot(data, labels=groups, showfliers=True)
    ax.set_title(metric)
    ax.set_ylabel(metric)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    fig_dir = Path(cfg.output_dir) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    table = pd.read_csv(in_dir / "icare_v2_primary_cpc15_table.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    if "d_eff_a_median" in table.columns:
        _boxplot(axes[0], table, "d_eff_a_median", cfg)
    else:
        axes[0].set_title("d_eff_a_median missing")
    if "f_reactive" in table.columns:
        _boxplot(axes[1], table, "f_reactive", cfg)
    else:
        axes[1].set_title("f_reactive missing")
    fig.suptitle(f"I-CARE v2 {'smoke' if cfg.smoke else 'full'} CPC1 vs CPC5 ({cfg.primary_window})")
    fig.tight_layout()
    fig.savefig(fig_dir / "cpc15_d_eff_a_and_f_reactive.svg")
    fig.savefig(fig_dir / "cpc15_d_eff_a_and_f_reactive.png", dpi=150)
    plt.close(fig)

    subtypes_path = in_dir / "cpc5_regime_subtypes.csv"
    if subtypes_path.exists():
        subtypes = pd.read_csv(subtypes_path)
        if not subtypes.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(subtypes["majority_regime"].astype(str), subtypes["n"])
            ax.set_title("CPC5 majority-regime subtypes")
            ax.set_ylabel("n patients")
            fig.tight_layout()
            fig.savefig(fig_dir / "cpc5_regime_subtypes.svg")
            fig.savefig(fig_dir / "cpc5_regime_subtypes.png", dpi=150)
            plt.close(fig)
    print(f"Wrote figures to {fig_dir}", flush=True)


if __name__ == "__main__":
    main()
