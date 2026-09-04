from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import stats

ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[3]
SIBLING_ARTICLE_DIR = ARTICLE_DIR.parent / "alzheimer_ftd_photonic"
SIBLING_SRC = SIBLING_ARTICLE_DIR / "src"
if str(SIBLING_SRC) not in sys.path:
    sys.path.insert(0, str(SIBLING_SRC))

from build_esb_article_outputs import PRIMARY_SPEC, PRIMARY_STAGE, _bh_fdr, _score_contrast  # noqa: E402
from build_photonic_paper_exports import DEFAULT_SELECTION_MODE, load_stage_window_selection  # noqa: E402
from explore_esb_ds004504_baseline import DEFAULT_PHOTIC_RAW_ROOT, DEFAULT_REST_RAW_ROOT  # noqa: E402
from photic_stage_recovery import PHOTIC_STAGE_LABELS  # noqa: E402

DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results"
STAGE_ORDER = ["photo_5hz", "photo_10hz", "photo_15hz", "photo_20hz"]


@dataclass(frozen=True)
class ComparatorSpec:
    key: str
    label: str
    note: str

    def feature_name_for_stage(self, stage_label: str) -> str:
        if self.key == "stage_matched_power_proxy":
            mapping = {
                "photo_5hz": "eeg_theta__g_parietal_occipital",
                "photo_10hz": "eeg_alpha__g_parietal_occipital",
                "photo_15hz": "eeg_beta__g_parietal_occipital",
                "photo_20hz": "eeg_beta__g_parietal_occipital",
            }
            return mapping[stage_label]
        mapping = {
            "posterior_alpha_power": "eeg_alpha__g_parietal_occipital",
            "posterior_alpha_theta_ratio": "eeg_alpha_theta__g_parietal_occipital",
            "posterior_sample_entropy": "eeg_sample_entropy__g_parietal_occipital",
        }
        return mapping[self.key]


COMPARATOR_SPECS: tuple[ComparatorSpec, ...] = (
    ComparatorSpec(
        key="stage_matched_power_proxy",
        label="Stage-matched posterior band-power proxy",
        note=(
            "Direct stimulation-frequency SSVEP amplitude is not available on the frozen feature surface, "
            "so the closest posterior band-power proxy is used: theta for 5 Hz, alpha for 10 Hz, and beta for 15/20 Hz."
        ),
    ),
    ComparatorSpec(
        key="posterior_alpha_power",
        label="Posterior alpha power",
        note="Parietal-occipital eeg_alpha feature.",
    ),
    ComparatorSpec(
        key="posterior_alpha_theta_ratio",
        label="Posterior alpha/theta ratio",
        note="Parietal-occipital eeg_alpha_theta feature from the exported contract.",
    ),
    ComparatorSpec(
        key="posterior_sample_entropy",
        label="Posterior sample entropy",
        note="Parietal-occipital eeg_sample_entropy feature used as the closest available conventional irregularity proxy.",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build conventional EEG comparator panel for the ESB article.")
    parser.add_argument("--photic-raw-root", type=Path, default=DEFAULT_PHOTIC_RAW_ROOT)
    parser.add_argument("--rest-raw-root", type=Path, default=DEFAULT_REST_RAW_ROOT)
    parser.add_argument("--selection-mode", default=DEFAULT_SELECTION_MODE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--esb-scores-path",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "esb_subject_scores.csv",
    )
    return parser.parse_args()


def _feature_map(handle: h5py.File, dataset_root: str = "features_raw") -> tuple[list[str], np.ndarray]:
    names = [value.decode("utf-8") if isinstance(value, bytes) else str(value) for value in handle[f"{dataset_root}/names"][:]]
    values = np.asarray(handle[f"{dataset_root}/values"][:], dtype=float)
    return names, values


def build_rest_feature_baseline(rest_raw_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for h5_path in sorted(rest_raw_root.glob("sub-*/sub-*.h5")):
        subject_id = h5_path.stem.split("_")[0]
        with h5py.File(h5_path, "r") as handle:
            names, values = _feature_map(handle, "features_raw")
            for feature_idx, feature_name in enumerate(names):
                column = values[:, feature_idx]
                column = column[np.isfinite(column)]
                rows.append(
                    {
                        "subject_id": subject_id,
                        "feature_name": feature_name,
                        "rest_value": float(np.median(column)) if column.size else float("nan"),
                        "rest_window_n": int(column.size),
                        "rest_h5_path": str(h5_path),
                    }
                )
    return pd.DataFrame(rows)


def build_photic_comparator_surface(
    photic_raw_root: Path,
    *,
    selection_mode: str = DEFAULT_SELECTION_MODE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    selection, _, _ = load_stage_window_selection(photic_raw_root, selection_mode=selection_mode)
    for h5_path in sorted(photic_raw_root.glob("sub-*/sub-*.h5")):
        subject_id = h5_path.stem.split("_")[0]
        subject_selection = selection.get(subject_id, {})
        with h5py.File(h5_path, "r") as handle:
            names, values = _feature_map(handle, "features_raw")
            n = min(int(values.shape[0]), int(np.asarray(handle["time"][:]).reshape(-1).size))
            values = values[:n, :]
            name_to_idx = {name: idx for idx, name in enumerate(names)}
            for stage_code, stage_label in PHOTIC_STAGE_LABELS.items():
                sample_idx = np.array(
                    sorted(idx for idx in subject_selection.get(int(stage_code), set()) if 0 <= int(idx) < n),
                    dtype=int,
                )
                if sample_idx.size == 0:
                    continue
                for spec in COMPARATOR_SPECS:
                    feature_name = spec.feature_name_for_stage(stage_label)
                    if feature_name not in name_to_idx:
                        rows.append(
                            {
                                "subject_id": subject_id,
                                "stage_label": stage_label,
                                "stage_rank": STAGE_ORDER.index(stage_label),
                                "comparator_key": spec.key,
                                "comparator_label": spec.label,
                                "feature_name": feature_name,
                                "photic_value": float("nan"),
                                "photic_window_n": int(sample_idx.size),
                                "availability_note": f"Feature `{feature_name}` missing from photic feature surface.",
                                "photic_h5_path": str(h5_path),
                            }
                        )
                        continue
                    column = values[sample_idx, name_to_idx[feature_name]]
                    column = column[np.isfinite(column)]
                    rows.append(
                        {
                            "subject_id": subject_id,
                            "stage_label": stage_label,
                            "stage_rank": STAGE_ORDER.index(stage_label),
                            "comparator_key": spec.key,
                            "comparator_label": spec.label,
                            "feature_name": feature_name,
                            "photic_value": float(np.median(column)) if column.size else float("nan"),
                            "photic_window_n": int(sample_idx.size),
                            "availability_note": spec.note,
                            "photic_h5_path": str(h5_path),
                        }
                    )
    return pd.DataFrame(rows)


def build_subject_stage_deltas(
    photic_surface: pd.DataFrame,
    rest_baseline: pd.DataFrame,
    esb_scores: pd.DataFrame,
) -> pd.DataFrame:
    primary = esb_scores[esb_scores["spec_name"] == PRIMARY_SPEC].copy()
    base_cols = [
        "subject_id",
        "group",
        "group_label",
        "mmse",
        "stage_label",
        "stage_display_label",
        "esb2_ds004504",
    ]
    merged = photic_surface.merge(
        rest_baseline[["subject_id", "feature_name", "rest_value", "rest_window_n"]],
        on=["subject_id", "feature_name"],
        how="left",
    ).merge(
        primary[base_cols],
        on=["subject_id", "stage_label"],
        how="left",
    )
    merged["delta_value"] = merged["photic_value"] - merged["rest_value"]
    return merged.sort_values(["comparator_key", "stage_rank", "subject_id"]).reset_index(drop=True)


def build_comparator_contrasts(subject_stage: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    contrasts = [("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy"), ("AD_vs_FTD", "AD", "FTD")]
    group_cols = ["comparator_key", "comparator_label", "stage_label", "stage_rank", "feature_name"]
    for keys, group in subject_stage.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, keys))
        for contrast_name, left_group, right_group in contrasts:
            row = dict(base)
            row["contrast_name"] = contrast_name
            row["left_group"] = left_group
            row["right_group"] = right_group
            row.update(_score_contrast(group, value_col="delta_value", left_group=left_group, right_group=right_group))
            rows.append(row)
    out = pd.DataFrame(rows)
    out["q_value"] = np.nan
    for _, group in out.groupby(["contrast_name", "stage_label"], dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(["contrast_name", "stage_rank", "q_value", "abs_effect"], na_position="last").reset_index(drop=True)


def _spearman(values_x: pd.Series, values_y: pd.Series) -> tuple[float, float, int]:
    frame = pd.DataFrame({"x": pd.to_numeric(values_x, errors="coerce"), "y": pd.to_numeric(values_y, errors="coerce")}).dropna()
    if len(frame) < 3:
        return float("nan"), float("nan"), int(len(frame))
    rho, p_value = stats.spearmanr(frame["x"], frame["y"])
    return float(rho), float(p_value), int(len(frame))


def build_esb2_correlations(subject_stage: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    stage = subject_stage[subject_stage["stage_label"] == PRIMARY_STAGE].copy()
    cohorts = {
        "all_subjects": stage.copy(),
        "disease_only": stage[stage["group_label"].isin(["AD", "FTD"])].copy(),
        "AD_only": stage[stage["group_label"] == "AD"].copy(),
        "FTD_only": stage[stage["group_label"] == "FTD"].copy(),
    }
    for comparator_key, group in stage.groupby(["comparator_key", "comparator_label", "feature_name"], dropna=False):
        comp_key, comp_label, feature_name = comparator_key
        for cohort_name, cohort_frame in cohorts.items():
            sub = cohort_frame[cohort_frame["comparator_key"] == comp_key].copy()
            rho, p_value, n_used = _spearman(sub["delta_value"], sub["esb2_ds004504"])
            rows.append(
                {
                    "comparator_key": comp_key,
                    "comparator_label": comp_label,
                    "feature_name": feature_name,
                    "stage_label": PRIMARY_STAGE,
                    "cohort_name": cohort_name,
                    "n_subjects": n_used,
                    "spearman_rho": rho,
                    "p_value": p_value,
                }
            )
    out = pd.DataFrame(rows)
    out["q_value"] = np.nan
    for _, group in out.groupby("cohort_name", dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["abs_rho"] = pd.to_numeric(out["spearman_rho"], errors="coerce").abs()
    return out.sort_values(["cohort_name", "q_value", "abs_rho"], ascending=[True, True, False], na_position="last").reset_index(drop=True)


def build_summary_markdown(contrasts: pd.DataFrame, correlations: pd.DataFrame) -> str:
    lines = [
        "# Conventional comparator summary",
        "",
        "This panel compares ESB-2 against conventional exported EEG features available on the frozen ds006036/ds004504 article surface.",
        "",
        "Comparator set:",
        "",
    ]
    for spec in COMPARATOR_SPECS:
        lines.append(f"- `{spec.label}`: {spec.note}")
    lines.extend(["", "## Group contrasts at PHOTO 15 Hz", ""])
    primary = contrasts[contrasts["stage_label"] == PRIMARY_STAGE].copy()
    for contrast_name in ("AD_vs_Healthy", "FTD_vs_Healthy"):
        sub = primary[primary["contrast_name"] == contrast_name].copy()
        if sub.empty:
            continue
        lines.append(f"### {contrast_name}")
        lines.append("")
        for _, row in sub.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iterrows():
            lines.append(
                f"- `{row['comparator_label']}`: d={float(row['effect_size']):.3f}, "
                f"p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
            )
        lines.append("")
    lines.extend(["## Correlation with ESB-2 at PHOTO 15 Hz", ""])
    all_sub = correlations[correlations["cohort_name"] == "all_subjects"].copy()
    for _, row in all_sub.sort_values(["q_value", "p_value", "abs_rho"], na_position="last").iterrows():
        lines.append(
            f"- `{row['comparator_label']}`: rho={float(row['spearman_rho']):.3f}, "
            f"p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}, n={int(row['n_subjects'])}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    esb_scores = pd.read_csv(args.esb_scores_path)
    photic_surface = build_photic_comparator_surface(args.photic_raw_root, selection_mode=args.selection_mode)
    rest_baseline = build_rest_feature_baseline(args.rest_raw_root)
    subject_stage = build_subject_stage_deltas(photic_surface, rest_baseline, esb_scores)
    contrasts = build_comparator_contrasts(subject_stage)
    correlations = build_esb2_correlations(subject_stage)
    summary_md = build_summary_markdown(contrasts, correlations)

    subject_stage_path = args.output_dir / "conventional_comparator_subject_stage.csv"
    contrast_path = args.output_dir / "conventional_comparator_contrasts.csv"
    correlation_path = args.output_dir / "conventional_comparator_esb2_correlations.csv"
    summary_path = args.output_dir / "conventional_comparator_summary.md"
    manifest_path = args.output_dir / "conventional_comparator_manifest.json"

    subject_stage.to_csv(subject_stage_path, index=False)
    contrasts.to_csv(contrast_path, index=False)
    correlations.to_csv(correlation_path, index=False)
    summary_path.write_text(summary_md, encoding="utf-8")

    manifest = {
        "article_dir": str(ARTICLE_DIR),
        "photic_raw_root": str(args.photic_raw_root),
        "rest_raw_root": str(args.rest_raw_root),
        "esb_scores_path": str(args.esb_scores_path),
        "primary_spec": PRIMARY_SPEC,
        "primary_stage": PRIMARY_STAGE,
        "comparator_specs": [
            {"key": spec.key, "label": spec.label, "note": spec.note} for spec in COMPARATOR_SPECS
        ],
        "output_files": {
            "subject_stage": str(subject_stage_path),
            "contrasts": str(contrast_path),
            "esb2_correlations": str(correlation_path),
            "summary_markdown": str(summary_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote conventional comparator panel to {args.output_dir}")


if __name__ == "__main__":
    main()
