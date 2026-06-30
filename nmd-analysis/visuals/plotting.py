from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns


def set_global_style() -> None:
    """Apply a consistent plotting style for NDT figures."""
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.size"] = 10
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["xtick.major.width"] = 0.8
    plt.rcParams["ytick.major.width"] = 0.8
    plt.rcParams["legend.frameon"] = True
    plt.rcParams["legend.fancybox"] = False
    plt.rcParams["legend.shadow"] = False
    sns.set_palette("viridis")
