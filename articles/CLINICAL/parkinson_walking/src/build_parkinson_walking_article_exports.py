from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = ARTICLE_DIR / "results" / "parkinson_walking_20260610"
EXPORT_DIR = RESULTS_DIR / "article_exports_121725"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "nan"
    try:
        return f"{float(value):.{digits}g}"
    except (TypeError, ValueError):
        return str(value)


def load_csv(*parts: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR.joinpath(*parts))


def pick_row(frame: pd.DataFrame, **filters: Any) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for column, expected in filters.items():
        mask &= frame[column] == expected
    matched = frame.loc[mask]
    if matched.empty:
        raise KeyError(f"No row matched filters: {filters}")
    if len(matched) > 1:
        raise KeyError(f"Multiple rows matched filters: {filters}")
    return matched.iloc[0]


def row_payload(
    row: pd.Series,
    *,
    status: str,
    branch: str,
    layer: str,
    contract: str,
    row_label: str,
    source_file: str,
    notes: str = "",
) -> dict[str, Any]:
    payload = {
        "status": status,
        "branch": branch,
        "layer": layer,
        "contract": contract,
        "row_label": row_label,
        "source_file": source_file,
        "notes": notes,
    }
    for key, value in row.items():
        payload[str(key)] = value
    return payload


def count_thresholds(frame: pd.DataFrame, name: str) -> dict[str, Any]:
    q_values = pd.to_numeric(frame["q_value"], errors="coerce")
    return {
        "branch": name,
        "rows_total": int(len(frame)),
        "rows_q_lt_0_05": int((q_values < 0.05).sum()),
        "rows_q_lt_0_10": int((q_values < 0.10).sum()),
    }


def write_summary(
    path: Path,
    *,
    counts: pd.DataFrame,
    focal_rows: pd.DataFrame,
    context_rows: pd.DataFrame,
    supportive_rows: pd.DataFrame,
    exploratory_rows: pd.DataFrame,
) -> None:
    lines: list[str] = []
    lines.append("# Parkinson walking article exports")
    lines.append("")
    lines.append("## Retained counts")
    lines.append("")
    for row in counts.to_dict(orient="records"):
        lines.append(
            f"- `{row['branch']}`: total={row['rows_total']}, q<0.05={row['rows_q_lt_0_05']}, q<0.1={row['rows_q_lt_0_10']}"
        )

    def emit_table(title: str, frame: pd.DataFrame) -> None:
        lines.append("")
        lines.append(f"## {title}")
        lines.append("")
        for row in frame.to_dict(orient="records"):
            q_value = row.get("q_value")
            effect_size = row.get("effect_size", row.get("rho"))
            if "rho" in row:
                effect_part = f"rho={fmt(row['rho'])}"
            else:
                effect_part = f"d={fmt(effect_size)}"
            line = (
                f"- `{row['branch']}` / `{row['row_label']}`: "
                f"{effect_part}, q={fmt(q_value)}, "
                f"left={fmt(row.get('left_median'))}, right={fmt(row.get('right_median'))}"
            )
            if row.get("clinical_variable"):
                line += f", clinical=`{row['clinical_variable']}`"
            if row.get("network") and str(row["network"]) != "nan":
                line += f", network=`{row['network']}`"
            if row.get("dimension") and str(row["dimension"]) != "nan":
                line += f", dim=`{row['dimension']}`"
            if row.get("notes"):
                line += f" ({row['notes']})"
            lines.append(line)

    emit_table("Main-text focal rows", focal_rows)
    emit_table("Secondary/context rows", context_rows)
    emit_table("Supportive supplement rows", supportive_rows)
    emit_table("Exploratory-only rows", exploratory_rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dir(EXPORT_DIR)

    cohort_group = load_csv("contrasts_cohort_121725", "group_contrasts.csv")
    subject_paired = load_csv("contrasts_subject_121725", "paired_task_contrasts.csv")
    cohort_regional = load_csv("regional_cohort_121725", "regional_group_contrasts.csv")
    cohort_reachability = load_csv("reachability_cohort_121725", "reachability_group_contrasts.csv")
    cohort_trajectory = load_csv("trajectory_cohort_121725", "trajectory_group_contrasts.csv")
    cohort_clinical = load_csv("clinical_cohort_121725", "pd_clinical_associations.csv")
    subject_clinical = load_csv("clinical_subject_121725", "pd_clinical_associations.csv")
    cohort_regional_clinical = load_csv("regional_cohort_121725", "regional_pd_clinical_associations.csv")
    cohort_trajectory_clinical = load_csv("trajectory_cohort_121725", "trajectory_pd_clinical_associations.csv")

    counts_rows = [
        count_thresholds(cohort_group.loc[cohort_group["contrast_name"] == "HC_vs_PD_walk"], "cohort_walk_standard"),
        count_thresholds(
            subject_paired.loc[subject_paired["contrast_name"] == "PD_walk_vs_rest"], "pd_subject_standard"
        ),
        count_thresholds(
            subject_paired.loc[subject_paired["contrast_name"] == "HC_walk_vs_rest"], "hc_subject_context"
        ),
        count_thresholds(
            cohort_regional.loc[cohort_regional["contrast_name"] == "HC_vs_PD_walk_regional"], "cohort_walk_regional"
        ),
        count_thresholds(
            cohort_reachability.loc[
                cohort_reachability["contrast_name"] == "HC_vs_PD_rest_global_reachability"
            ],
            "cohort_rest_reachability",
        ),
        count_thresholds(
            cohort_trajectory.loc[cohort_trajectory["contrast_name"].str.contains("HC_vs_PD_rest")],
            "cohort_rest_trajectory",
        ),
        count_thresholds(cohort_clinical.loc[cohort_clinical["task"] == "rest"], "cohort_rest_global_rho"),
        count_thresholds(subject_clinical, "subject_anchor_global_rho"),
        count_thresholds(cohort_regional_clinical.loc[cohort_regional_clinical["task"] == "rest"], "cohort_rest_regional_rho"),
        count_thresholds(
            cohort_trajectory_clinical.loc[cohort_trajectory_clinical["task"] == "rest"],
            "cohort_rest_trajectory_rho",
        ),
    ]

    subject_reachability_dir = RESULTS_DIR / "reachability_subject_121725"
    subject_reachability_csv = subject_reachability_dir / "reachability_group_contrasts.csv"
    if subject_reachability_csv.exists():
        subject_reach_group = pd.read_csv(subject_reachability_csv)
        counts_rows.append(
            count_thresholds(
                subject_reach_group.loc[subject_reach_group["contrast_name"] == "PD_walk_vs_rest"],
                "subject_reachability",
            )
        )
    counts = pd.DataFrame(counts_rows)

    focal_rows = [
        row_payload(
            pick_row(cohort_group, contrast_name="HC_vs_PD_walk", metric="d_n_mean"),
            status="main_text",
            branch="cohort_walk",
            layer="global_mnps",
            contract="cohort",
            row_label="Global walk d_n_mean",
            source_file="contrasts_cohort_121725/group_contrasts.csv",
            notes="Primary between-group headline row",
        ),
        row_payload(
            pick_row(cohort_group, contrast_name="HC_vs_PD_walk", metric="d_n_median"),
            status="main_text",
            branch="cohort_walk",
            layer="global_mnps",
            contract="cohort",
            row_label="Global walk d_n_median",
            source_file="contrasts_cohort_121725/group_contrasts.csv",
            notes="Median companion to d_n_mean",
        ),
        row_payload(
            pick_row(cohort_group, contrast_name="HC_vs_PD_walk", metric="d_mean"),
            status="main_text",
            branch="cohort_walk",
            layer="global_mnps",
            contract="cohort",
            row_label="Global walk d_mean",
            source_file="contrasts_cohort_121725/group_contrasts.csv",
            notes="Signed family shift in walk task",
        ),
        row_payload(
            pick_row(cohort_group, contrast_name="HC_vs_PD_walk", metric="d_median"),
            status="main_text",
            branch="cohort_walk",
            layer="global_mnps",
            contract="cohort",
            row_label="Global walk d_median",
            source_file="contrasts_cohort_121725/group_contrasts.csv",
            notes="Median companion to d_mean",
        ),
        row_payload(
            pick_row(subject_paired, contrast_name="PD_walk_vs_rest", metric="d_n_mean"),
            status="main_text",
            branch="pd_walk_vs_rest",
            layer="global_mnps",
            contract="subject",
            row_label="PD paired d_n_mean",
            source_file="contrasts_subject_121725/paired_task_contrasts.csv",
            notes="Primary paired headline row",
        ),
        row_payload(
            pick_row(subject_paired, contrast_name="PD_walk_vs_rest", metric="d_mean"),
            status="main_text",
            branch="pd_walk_vs_rest",
            layer="global_mnps",
            contract="subject",
            row_label="PD paired d_mean",
            source_file="contrasts_subject_121725/paired_task_contrasts.csv",
            notes="Companion paired family shift",
        ),
        row_payload(
            pick_row(subject_paired, contrast_name="PD_walk_vs_rest", metric="jac9_anisotropy_abs_eig_median"),
            status="main_text",
            branch="pd_walk_vs_rest",
            layer="global_jacobian_9d",
            contract="subject",
            row_label="PD paired jac9 anisotropy",
            source_file="contrasts_subject_121725/paired_task_contrasts.csv",
            notes="Paired Jacobian adjunct retained at q<0.05",
        ),
    ]
    focal_df = pd.DataFrame(focal_rows)

    context_rows = [
        row_payload(
            pick_row(subject_paired, contrast_name="HC_walk_vs_rest", metric="m_a_mean"),
            status="secondary_context",
            branch="hc_walk_vs_rest",
            layer="global_mnps",
            contract="subject",
            row_label="HC paired m_a_mean",
            source_file="contrasts_subject_121725/paired_task_contrasts.csv",
            notes="Only HC paired row at q<0.05",
        ),
        row_payload(
            pick_row(subject_paired, contrast_name="HC_walk_vs_rest", metric="m_mean"),
            status="secondary_context",
            branch="hc_walk_vs_rest",
            layer="global_mnps",
            contract="subject",
            row_label="HC paired m_mean",
            source_file="contrasts_subject_121725/paired_task_contrasts.csv",
            notes="Secondary context near the q<0.1 boundary",
        ),
        row_payload(
            pick_row(subject_paired, contrast_name="HC_walk_vs_rest", metric="d_l_mean"),
            status="secondary_context",
            branch="hc_walk_vs_rest",
            layer="global_mnps",
            contract="subject",
            row_label="HC paired d_l_mean",
            source_file="contrasts_subject_121725/paired_task_contrasts.csv",
            notes="Secondary context near the q<0.1 boundary",
        ),
    ]
    context_df = pd.DataFrame(context_rows)

    supportive_rows = [
        row_payload(
            pick_row(cohort_regional, contrast_name="HC_vs_PD_walk_regional", network="frontal", metric="d_n_mean"),
            status="supportive",
            branch="cohort_walk_regional",
            layer="regional_9d",
            contract="cohort",
            row_label="Frontal walk d_n_mean",
            source_file="regional_cohort_121725/regional_group_contrasts.csv",
            notes="Strongest regional walk replication",
        ),
        row_payload(
            pick_row(cohort_regional, contrast_name="HC_vs_PD_walk_regional", network="frontal", metric="d_n_median"),
            status="supportive",
            branch="cohort_walk_regional",
            layer="regional_9d",
            contract="cohort",
            row_label="Frontal walk d_n_median",
            source_file="regional_cohort_121725/regional_group_contrasts.csv",
            notes="Median companion regional walk replication",
        ),
        row_payload(
            pick_row(
                cohort_reachability,
                contrast_name="HC_vs_PD_rest_global_reachability",
                block_scope="global",
                network="global",
                metric="pred_err_h2",
            ),
            status="supportive",
            branch="cohort_rest_reachability",
            layer="reachability",
            contract="cohort",
            row_label="Rest global pred_err_h2",
            source_file="reachability_cohort_121725/reachability_group_contrasts.csv",
            notes="Best corrected reachability row",
        ),
        row_payload(
            pick_row(
                cohort_reachability,
                contrast_name="HC_vs_PD_rest_global_reachability",
                block_scope="global",
                network="global",
                metric="tube_log_det_mean",
            ),
            status="supportive",
            branch="cohort_rest_reachability",
            layer="reachability",
            contract="cohort",
            row_label="Rest global tube_log_det_mean",
            source_file="reachability_cohort_121725/reachability_group_contrasts.csv",
            notes="Volume-style companion reachability row",
        ),
        row_payload(
            pick_row(cohort_clinical, task="rest", clinical_variable="age", metric="d_s_mean"),
            status="supportive",
            branch="cohort_rest_global_rho",
            layer="global_rho",
            contract="cohort",
            row_label="Rest age vs d_s_mean",
            source_file="clinical_cohort_121725/pd_clinical_associations.csv",
            notes="Strongest global age association",
        ),
        row_payload(
            pick_row(cohort_clinical, task="rest", clinical_variable="ctt", metric="d_s_mean"),
            status="supportive",
            branch="cohort_rest_global_rho",
            layer="global_rho",
            contract="cohort",
            row_label="Rest CTT vs d_s_mean",
            source_file="clinical_cohort_121725/pd_clinical_associations.csv",
            notes="Strongest global executive-function association",
        ),
        row_payload(
            pick_row(cohort_clinical, task="rest", clinical_variable="moca", metric="d_s_mean"),
            status="supportive",
            branch="cohort_rest_global_rho",
            layer="global_rho",
            contract="cohort",
            row_label="Rest MoCA vs d_s_mean",
            source_file="clinical_cohort_121725/pd_clinical_associations.csv",
            notes="Strongest global cognition association",
        ),
        row_payload(
            pick_row(cohort_regional_clinical, task="rest", clinical_variable="ctt", network="central", metric="d_s_mean"),
            status="supportive",
            branch="cohort_rest_regional_rho",
            layer="regional_rho",
            contract="cohort",
            row_label="Rest central d_s_mean vs CTT",
            source_file="regional_cohort_121725/regional_pd_clinical_associations.csv",
            notes="Strongest regional executive-function association",
        ),
        row_payload(
            pick_row(cohort_regional_clinical, task="rest", clinical_variable="age", network="frontal", metric="d_s_mean"),
            status="supportive",
            branch="cohort_rest_regional_rho",
            layer="regional_rho",
            contract="cohort",
            row_label="Rest frontal d_s_mean vs age",
            source_file="regional_cohort_121725/regional_pd_clinical_associations.csv",
            notes="Strongest regional age association",
        ),
        row_payload(
            pick_row(subject_clinical, task="rest", clinical_variable="moca", metric="e_mean"),
            status="supportive",
            branch="subject_global_rho",
            layer="global_rho",
            contract="subject",
            row_label="Subject rest e_mean vs MoCA",
            source_file="clinical_subject_121725/pd_clinical_associations.csv",
            notes="Only subject-anchor rest global rho at q<0.05",
        ),
        row_payload(
            pick_row(subject_clinical, task="walk", clinical_variable="age", metric="jac9_spectral_radius_median"),
            status="supportive",
            branch="subject_global_rho",
            layer="global_rho",
            contract="subject",
            row_label="Subject walk jac9 spectral radius vs age",
            source_file="clinical_subject_121725/pd_clinical_associations.csv",
            notes="Only subject-anchor walk global rho at q<0.05",
        ),
    ]
    supportive_df = pd.DataFrame(supportive_rows)

    exploratory_rows = [
        row_payload(
            pick_row(cohort_trajectory, contrast_name="HC_vs_PD_rest_trajectory_3d", dimension=3, metric="noetic_action_kinetic"),
            status="exploratory",
            branch="cohort_rest_trajectory",
            layer="trajectory",
            contract="cohort",
            row_label="Rest 3D noetic_action_kinetic",
            source_file="trajectory_cohort_121725/trajectory_group_contrasts.csv",
            notes="Best exploratory trajectory row",
        ),
        row_payload(
            pick_row(cohort_trajectory, contrast_name="HC_vs_PD_rest_trajectory_3d", dimension=3, metric="path_length"),
            status="exploratory",
            branch="cohort_rest_trajectory",
            layer="trajectory",
            contract="cohort",
            row_label="Rest 3D path_length",
            source_file="trajectory_cohort_121725/trajectory_group_contrasts.csv",
            notes="Exploratory trajectory companion row",
        ),
        row_payload(
            pick_row(
                cohort_trajectory_clinical,
                task="rest",
                dimension=3,
                clinical_variable="ctt",
                metric="noetic_action",
            ),
            status="exploratory",
            branch="cohort_rest_trajectory_rho",
            layer="trajectory_rho",
            contract="cohort",
            row_label="Rest 3D noetic_action vs CTT",
            source_file="trajectory_cohort_121725/trajectory_pd_clinical_associations.csv",
            notes="Strongest exploratory trajectory rho row",
        ),
        row_payload(
            pick_row(
                cohort_trajectory_clinical,
                task="rest",
                dimension=9,
                clinical_variable="moca",
                metric="tortuosity",
            ),
            status="exploratory",
            branch="cohort_rest_trajectory_rho",
            layer="trajectory_rho",
            contract="cohort",
            row_label="Rest 9D tortuosity vs MoCA",
            source_file="trajectory_cohort_121725/trajectory_pd_clinical_associations.csv",
            notes="Strongest exploratory 9D trajectory cognition row",
        ),
    ]
    exploratory_df = pd.DataFrame(exploratory_rows)

    ledger = pd.concat([focal_df, context_df, supportive_df, exploratory_df], ignore_index=True)

    counts.to_csv(EXPORT_DIR / "retained_counts.csv", index=False)
    focal_df.to_csv(EXPORT_DIR / "focal_rows.csv", index=False)
    context_df.to_csv(EXPORT_DIR / "context_rows.csv", index=False)
    supportive_df.to_csv(EXPORT_DIR / "supportive_rows.csv", index=False)
    exploratory_df.to_csv(EXPORT_DIR / "exploratory_rows.csv", index=False)
    ledger.to_csv(EXPORT_DIR / "evidence_ledger.csv", index=False)

    numbers = {
        "dataset": {
            "dataset_root": "data/raw/neuralmanifolddynamics_ds007526_20260610_121725",
            "participants_total": 144,
            "participants_pd": 116,
            "participants_hc": 28,
            "runs_rest": 144,
            "runs_walk": 133,
        },
        "retained_counts": counts.to_dict(orient="records"),
        "main_text_row_count": int(len(focal_df)),
        "supportive_row_count": int(len(supportive_df)),
        "exploratory_row_count": int(len(exploratory_df)),
        "secondary_context_row_count": int(len(context_df)),
    }
    (EXPORT_DIR / "manuscript_numbers.json").write_text(json.dumps(numbers, indent=2), encoding="utf-8")
    write_summary(
        EXPORT_DIR / "article_evidence_summary.md",
        counts=counts,
        focal_rows=focal_df,
        context_rows=context_df,
        supportive_rows=supportive_df,
        exploratory_rows=exploratory_df,
    )

    print(f"Wrote article exports to {EXPORT_DIR}")
    print(f"Main rows: {len(focal_df)} | Context rows: {len(context_df)} | Supportive rows: {len(supportive_df)}")


if __name__ == "__main__":
    main()
