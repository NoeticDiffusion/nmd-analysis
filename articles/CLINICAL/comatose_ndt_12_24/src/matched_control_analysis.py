from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


ARTICLE_DIR = Path(__file__).resolve().parents[1]
INPUT_ROOT = ARTICLE_DIR.parents[1] / "data" / "raw" / "neuralmanifolddynamics_ds005555_20260508_164627"
RESULT_DIR = ARTICLE_DIR / "results" / "matched_control"
FIG_DIR = ARTICLE_DIR / "figures"

CHANNELS = ("psg_c3", "psg_f3")
CHANNEL_LABELS = {"psg_c3": "PSG_C3", "psg_f3": "PSG_F3"}
CHANNEL_COLORS = {"psg_c3": "#1f77b4", "psg_f3": "#d62728"}
METRICS = ("m", "d", "e", "m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")


def bootstrap_median(values: np.ndarray, *, seed: int, samples: int = 10000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(samples, values.size), replace=True)
    med = np.median(draws, axis=1)
    return float(np.quantile(med, 0.025)), float(np.quantile(med, 0.975))


def summarize_subject_file(path: Path, channel: str) -> Dict[str, object]:
    columns = [
        "subject_id",
        "condition",
        "bin_label",
        "window_id",
        "event_id",
        "rate_per_min",
        *METRICS,
    ]
    available = pd.read_parquet(path, columns=None).columns
    columns = [col for col in columns if col in available]
    frame = pd.read_parquet(path, columns=columns)
    subject = str(frame["subject_id"].iloc[0]) if not frame.empty and "subject_id" in frame else path.parent.name.split("_", 1)[0]

    event = frame[(frame["condition"].astype(str) == "spindle_event") & (frame["bin_label"].astype(str) == "event")]
    control = frame[(frame["condition"].astype(str) == "matched_control") & (frame["bin_label"].astype(str) == "control")]
    pre_far = frame[(frame["condition"].astype(str) == "spindle_event") & (frame["bin_label"].astype(str) == "pre_far")]

    event_window_ids = set(pd.to_numeric(event["window_id"], errors="coerce").dropna().astype(int).tolist())
    pre_far_window_ids = pd.to_numeric(pre_far["window_id"], errors="coerce").dropna().astype(int)
    contamination = pre_far_window_ids.isin(event_window_ids)

    row: Dict[str, object] = {
        "subject": subject,
        "channel": channel,
        "n_event_rows": int(len(event)),
        "n_control_rows": int(len(control)),
        "n_pre_far_rows": int(len(pre_far)),
        "pre_far_event_window_contamination_frac": float(contamination.mean()) if len(contamination) else np.nan,
        "rate_per_min": float(pd.to_numeric(frame.get("rate_per_min", pd.Series(dtype=float)), errors="coerce").median())
        if "rate_per_min" in frame
        else np.nan,
    }
    for metric in METRICS:
        if metric not in frame.columns:
            continue
        event_mean = pd.to_numeric(event[metric], errors="coerce").mean()
        control_mean = pd.to_numeric(control[metric], errors="coerce").mean()
        pre_far_mean = pd.to_numeric(pre_far[metric], errors="coerce").mean()
        row[f"{metric}_event_mean"] = float(event_mean)
        row[f"{metric}_control_mean"] = float(control_mean)
        row[f"{metric}_pre_far_mean"] = float(pre_far_mean)
        row[f"{metric}_event_minus_control"] = float(event_mean - control_mean)
        row[f"{metric}_event_minus_pre_far"] = float(event_mean - pre_far_mean)
    return row


def build_subject_table() -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for channel in CHANNELS:
        for path in sorted(INPUT_ROOT.rglob(f"*event_locked_v1_{channel}.parquet")):
            rows.append(summarize_subject_file(path, channel))
    return pd.DataFrame(rows)


def paired_summary(subjects: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    contrasts = ("event_minus_control", "event_minus_pre_far")
    for channel in CHANNELS:
        channel_frame = subjects[subjects["channel"] == channel]
        for metric in METRICS:
            for contrast in contrasts:
                col = f"{metric}_{contrast}"
                if col not in channel_frame.columns:
                    continue
                vals = pd.to_numeric(channel_frame[col], errors="coerce").dropna().to_numpy(dtype=float)
                if vals.size == 0:
                    continue
                positive = int(np.sum(vals > 0))
                negative = int(np.sum(vals < 0))
                nonzero = positive + negative
                t_stat, p_value = stats.ttest_1samp(vals, 0.0, nan_policy="omit") if vals.size > 1 else (np.nan, np.nan)
                sd = float(np.std(vals, ddof=1)) if vals.size > 1 else np.nan
                ci_low, ci_high = bootstrap_median(vals, seed=20260509 + len(rows))
                rows.append(
                    {
                        "channel": channel,
                        "metric": metric,
                        "contrast": contrast,
                        "n_subjects": int(vals.size),
                        "n_positive": positive,
                        "n_negative": negative,
                        "mean_delta": float(np.mean(vals)),
                        "median_delta": float(np.median(vals)),
                        "sd_delta": sd,
                        "cohens_dz": float(np.mean(vals) / sd) if np.isfinite(sd) and sd > 0 else np.nan,
                        "t": float(t_stat),
                        "p": float(p_value),
                        "binom_p": float(stats.binomtest(positive, nonzero, 0.5).pvalue) if nonzero else np.nan,
                        "median_boot_ci_low": ci_low,
                        "median_boot_ci_high": ci_high,
                    }
                )
    return pd.DataFrame(rows)


def contamination_summary(subjects: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for channel in CHANNELS:
        sub = subjects[subjects["channel"] == channel].copy()
        contam = pd.to_numeric(sub["pre_far_event_window_contamination_frac"], errors="coerce")
        d_delta = pd.to_numeric(sub["d_event_minus_pre_far"], errors="coerce")
        mask = np.isfinite(contam) & np.isfinite(d_delta)
        rho, rho_p = stats.spearmanr(contam[mask], d_delta[mask]) if int(mask.sum()) >= 3 else (np.nan, np.nan)
        rows.append(
            {
                "channel": channel,
                "n_subjects": int(contam.notna().sum()),
                "contamination_mean": float(contam.mean()),
                "contamination_median": float(contam.median()),
                "contamination_p90": float(contam.quantile(0.90)),
                "contamination_p95": float(contam.quantile(0.95)),
                "spearman_rho_contam_vs_delta_d": float(rho),
                "spearman_p_contam_vs_delta_d": float(rho_p),
            }
        )
    return pd.DataFrame(rows)


def contamination_sensitivity(subjects: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    thresholds = (0.10, 0.20, 0.25, 0.30)
    for channel in CHANNELS:
        sub = subjects[subjects["channel"] == channel].copy()
        for threshold in thresholds:
            keep = sub[pd.to_numeric(sub["pre_far_event_window_contamination_frac"], errors="coerce") <= threshold]
            vals = pd.to_numeric(keep["d_event_minus_pre_far"], errors="coerce").dropna().to_numpy(dtype=float)
            if vals.size == 0:
                continue
            positive = int(np.sum(vals > 0))
            negative = int(np.sum(vals < 0))
            nonzero = positive + negative
            rows.append(
                {
                    "channel": channel,
                    "threshold": threshold,
                    "n_subjects": int(vals.size),
                    "n_positive": positive,
                    "n_negative": negative,
                    "median_delta_d": float(np.median(vals)),
                    "mean_delta_d": float(np.mean(vals)),
                    "binom_p": float(stats.binomtest(positive, nonzero, 0.5).pvalue) if nonzero else np.nan,
                }
            )
    return pd.DataFrame(rows)


def write_figures(subjects: pd.DataFrame, summary: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0), sharey=True)
    rng = np.random.default_rng(21)
    for ax, channel in zip(axes, CHANNELS):
        sub = subjects[subjects["channel"] == channel]
        vals = pd.to_numeric(sub["d_event_minus_control"], errors="coerce").dropna().to_numpy(dtype=float)
        x = rng.normal(0, 0.04, size=vals.size)
        ax.scatter(x, vals, s=16, alpha=0.62, color=CHANNEL_COLORS[channel], edgecolor="none")
        ax.axhline(0, color="#777777", linestyle="--", linewidth=0.9)
        ax.plot([-0.18, 0.18], [np.median(vals), np.median(vals)], color="#111111", linewidth=2)
        ax.set_title(CHANNEL_LABELS[channel])
        ax.set_xticks([])
        ax.text(0, np.nanmax(vals) * 0.92, f"{int((vals > 0).sum())}/{vals.size} positive", ha="center", fontsize=9)
        ax.spines[["top", "right", "bottom"]].set_visible(False)
    axes[0].set_ylabel("MNPS-d event minus matched control")
    fig.suptitle("Matched-control contrast for spindle event windows")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_matched_control_delta_d.svg", format="svg", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for channel in CHANNELS:
        sub = subjects[subjects["channel"] == channel]
        ax.scatter(
            pd.to_numeric(sub["pre_far_event_window_contamination_frac"], errors="coerce"),
            pd.to_numeric(sub["d_event_minus_pre_far"], errors="coerce"),
            s=18,
            alpha=0.65,
            color=CHANNEL_COLORS[channel],
            label=CHANNEL_LABELS[channel],
            edgecolor="none",
        )
    ax.axhline(0, color="#777777", linestyle="--", linewidth=0.9)
    ax.set_xlabel("pre_far windows overlapping event windows")
    ax.set_ylabel("MNPS-d event minus pre_far")
    ax.set_title("Baseline contamination sensitivity")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_prefar_contamination_vs_delta_d.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    subjects = build_subject_table()
    summary = paired_summary(subjects)
    contam = contamination_summary(subjects)
    sensitivity = contamination_sensitivity(subjects)

    subjects.to_csv(RESULT_DIR / "matched_control_subjects.csv", index=False)
    summary.to_csv(RESULT_DIR / "matched_control_summary.csv", index=False)
    contam.to_csv(RESULT_DIR / "baseline_contamination_summary.csv", index=False)
    sensitivity.to_csv(RESULT_DIR / "baseline_contamination_sensitivity.csv", index=False)
    write_figures(subjects, summary)

    primary = summary[(summary["metric"] == "d") & (summary["contrast"] == "event_minus_control")]
    payload = {
        "matched_control_primary_d": primary.to_dict(orient="records"),
        "baseline_contamination": contam.to_dict(orient="records"),
        "notes": [
            "matched_control rows are present in the event parquet exports",
            "pre_far contamination is estimated as pre_far window_id overlap with event-bin window_id within subject/channel",
        ],
    }
    (RESULT_DIR / "matched_control_claim_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote matched-control outputs to {RESULT_DIR}")


if __name__ == "__main__":
    main()
