"""Estimate healthy within-subject EEG--MEG concordance and paired differences."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import stats

from eeg_meg_support import (
    DATASET_ROOT,
    RESULTS_DIR,
    benjamini_hochberg,
    family_from_name,
    feature_names_and_values,
    list_h5_paths,
    parse_run_slug,
    topography_from_name,
    write_csv,
)


RNG_SEED = 3645


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default=DATASET_ROOT)
    parser.add_argument("--tables-dir", default=RESULTS_DIR / "02_modality_tables")
    parser.add_argument("--output-dir", default=RESULTS_DIR / "03_concordance")
    parser.add_argument("--permutations", type=int, default=5000)
    return parser.parse_args()


def _surface_key(name: str) -> tuple[str, str, str] | None:
    if name.startswith("eeg_"):
        modality = "EEG"
    elif name.startswith("meg_") and not name.startswith(("meg_mag_", "meg_grad_")):
        modality = "MEG"
    else:
        return None
    topology = topography_from_name(name) or "global"
    if topology == "global" and "__g_" in name:
        return None
    return modality, topology, family_from_name(name)


def _correlation_rows(dataset_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for h5_path in list_h5_paths(dataset_root):
        subject_id, run = parse_run_slug(h5_path)
        with h5py.File(h5_path, "r") as handle:
            names, values = feature_names_and_values(handle)
            columns: dict[tuple[str, str, str], np.ndarray] = {}
            for index, name in enumerate(names):
                key = _surface_key(name)
                if key is not None:
                    columns[key] = values[:, index]
            for (modality, topology, family), eeg_values in columns.items():
                if modality != "EEG":
                    continue
                meg_values = columns.get(("MEG", topology, family))
                if meg_values is None:
                    continue
                valid = np.isfinite(eeg_values) & np.isfinite(meg_values)
                if valid.sum() < 4:
                    continue
                pearson_r = float(stats.pearsonr(eeg_values[valid], meg_values[valid]).statistic)
                spearman_r = float(stats.spearmanr(eeg_values[valid], meg_values[valid]).statistic)
                rows.append(
                    {
                        "subject_id": subject_id,
                        "run": run,
                        "level": "global" if topology == "global" else "regional",
                        "topology": topology,
                        "feature_family": family,
                        "n_timepoints": int(valid.sum()),
                        "pearson_r": pearson_r,
                        "spearman_r": spearman_r,
                    }
                )
    return pd.DataFrame(rows)


def _fisher_subject_average(run_correlations: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["subject_id", "level", "topology", "feature_family"]
    rows: list[dict[str, object]] = []
    for keys, frame in run_correlations.groupby(key_cols, dropna=False):
        row = dict(zip(key_cols, keys))
        for metric in ("pearson_r", "spearman_r"):
            clipped = np.clip(frame[metric].to_numpy(float), -0.999999, 0.999999)
            row[metric] = float(np.tanh(np.mean(np.arctanh(clipped))))
        row["n_runs"] = len(frame)
        rows.append(row)
    return pd.DataFrame(rows)


def _sign_permutation_p(diff: np.ndarray, n_perm: int, rng: np.random.Generator) -> float:
    observed = abs(float(np.mean(diff)))
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, len(diff)))
    null = np.abs(np.mean(signs * diff[None, :], axis=1))
    return float((1 + np.sum(null >= observed)) / (n_perm + 1))


def _paired_tests(feature_means: pd.DataFrame, n_perm: int) -> pd.DataFrame:
    rng = np.random.default_rng(RNG_SEED)
    run_aggregate = (
        feature_means.groupby(
            ["subject_id", "level", "topology", "feature_family"], as_index=False
        )[["EEG", "MEG"]]
        .mean()
    )
    rows: list[dict[str, object]] = []
    group_cols = ["level", "topology", "feature_family"]
    for keys, frame in run_aggregate.groupby(group_cols, dropna=False):
        diff = (frame["EEG"] - frame["MEG"]).to_numpy(float)
        diff = diff[np.isfinite(diff)]
        if len(diff) < 3:
            continue
        try:
            wilcoxon_p = float(stats.wilcoxon(diff, alternative="two-sided").pvalue)
        except ValueError:
            wilcoxon_p = float("nan")
        sd = float(np.std(diff, ddof=1))
        rows.append(
            {
                **dict(zip(group_cols, keys)),
                "n_subjects": int(len(diff)),
                "eeg_mean": float(np.mean(frame["EEG"])),
                "meg_mean": float(np.mean(frame["MEG"])),
                "mean_difference_eeg_minus_meg": float(np.mean(diff)),
                "cohens_dz": float(np.mean(diff) / sd) if sd > 0 else float("nan"),
                "wilcoxon_p": wilcoxon_p,
                "permutation_p": _sign_permutation_p(diff, n_perm, rng),
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        result["wilcoxon_q"] = np.nan
        result["permutation_q"] = np.nan
        for _, indexes in result.groupby("level").groups.items():
            result.loc[indexes, "wilcoxon_q"] = benjamini_hochberg(result.loc[indexes, "wilcoxon_p"])
            result.loc[indexes, "permutation_q"] = benjamini_hochberg(result.loc[indexes, "permutation_p"])
    return result


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    run_correlations = _correlation_rows(Path(args.dataset_root))
    subject_correlations = _fisher_subject_average(run_correlations)
    feature_means = pd.read_csv(Path(args.tables_dir) / "paired_feature_means.csv")
    tests = _paired_tests(feature_means, args.permutations)
    write_csv(run_correlations, output_dir / "run_level_feature_correlations.csv")
    write_csv(subject_correlations, output_dir / "subject_level_feature_concordance.csv")
    write_csv(tests, output_dir / "paired_feature_difference_tests.csv")
    print(f"Wrote {len(subject_correlations)} subject concordance and {len(tests)} paired tests.")


if __name__ == "__main__":
    main()
