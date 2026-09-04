from __future__ import annotations

from dataclasses import dataclass

from parkinson_cognitive_workload_support import (
    COHORT_COORDINATE_CONTRACT,
    SUBJECT_COORDINATE_CONTRACT,
    get_dataset_spec,
)


CONTROL_COLOR = "#2563eb"
OFF_COLOR = "#dc2626"
ON_COLOR = "#7c3aed"


@dataclass(frozen=True)
class GroupSpec:
    label: str
    group: str
    condition: str
    color: str


@dataclass(frozen=True)
class ContrastView:
    contrast_name: str
    left: GroupSpec
    right: GroupSpec
    paired: bool


@dataclass(frozen=True)
class MetricSpec:
    label: str
    source: str
    contract: str
    contrast_name: str
    analysis_type: str
    metric: str
    network: str | None = None
    segment_kind: str | None = None
    segment_label: str | None = None
    exploratory: bool = False


@dataclass(frozen=True)
class PanelSpec:
    slug: str
    title: str
    metrics: tuple[MetricSpec, ...]


CONTROL = GroupSpec("Control", "Control", "not_applicable", CONTROL_COLOR)
PARKINSON_OFF = GroupSpec("Parkinson OFF", "Parkinson", "OFF", OFF_COLOR)
PARKINSON_ON = GroupSpec("Parkinson ON", "Parkinson", "ON", ON_COLOR)


def contrast_view(contrast_name: str) -> ContrastView:
    if contrast_name == "Control_vs_Parkinson_OFF":
        return ContrastView(contrast_name, CONTROL, PARKINSON_OFF, False)
    if contrast_name == "Control_vs_Parkinson_ON":
        return ContrastView(contrast_name, CONTROL, PARKINSON_ON, False)
    if contrast_name == "Parkinson_OFF_vs_ON":
        return ContrastView(contrast_name, PARKINSON_OFF, PARKINSON_ON, True)
    raise ValueError(f"Unsupported contrast_name {contrast_name!r}.")


def _unique_metrics(metrics: tuple[MetricSpec, ...]) -> tuple[MetricSpec, ...]:
    seen: set[tuple[object, ...]] = set()
    out: list[MetricSpec] = []
    for spec in metrics:
        key = (
            spec.label,
            spec.source,
            spec.contract,
            spec.contrast_name,
            spec.analysis_type,
            spec.metric,
            spec.network,
            spec.segment_kind,
            spec.segment_label,
            spec.exploratory,
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(spec)
    return tuple(out)


def _ds003509_classical_panel() -> PanelSpec:
    return PanelSpec(
        slug="classical_eeg_ds003509",
        title="Simon conflict: classical EEG comparators",
        metrics=(
            MetricSpec(
                "Alpha SD (Control vs ON, exploratory)",
                "classical",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_ON",
                "eeg_classical_comparators",
                "eeg_classical_relative_alpha_std",
                exploratory=True,
            ),
            MetricSpec(
                "Alpha SD (Control vs OFF, exploratory)",
                "classical",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_OFF",
                "eeg_classical_comparators",
                "eeg_classical_relative_alpha_std",
                exploratory=True,
            ),
            MetricSpec(
                "Alpha mean (Control vs OFF, exploratory)",
                "classical",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_OFF",
                "eeg_classical_comparators",
                "eeg_classical_relative_alpha_mean",
                exploratory=True,
            ),
            MetricSpec(
                "Alpha median (Control vs OFF, exploratory)",
                "classical",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_OFF",
                "eeg_classical_comparators",
                "eeg_classical_relative_alpha_median",
                exploratory=True,
            ),
            MetricSpec(
                "Relative alpha mean (OFF vs ON, exploratory)",
                "classical",
                SUBJECT_COORDINATE_CONTRACT,
                "Parkinson_OFF_vs_ON",
                "eeg_classical_comparators",
                "eeg_classical_relative_alpha_mean",
                exploratory=True,
            ),
            MetricSpec(
                "PSE95 SD (OFF vs ON, exploratory)",
                "classical",
                SUBJECT_COORDINATE_CONTRACT,
                "Parkinson_OFF_vs_ON",
                "eeg_classical_comparators",
                "eeg_classical_peak_spectral_edge_95_std",
                exploratory=True,
            ),
        ),
    )


def _ds003509_mnps9d_panel() -> PanelSpec:
    return PanelSpec(
        slug="mnps9d_ds003509",
        title="Simon conflict: focal MNPS 9D metrics",
        metrics=(
            MetricSpec("PO d_s_mean", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "regional_9d", "d_s_mean", network="parietal_occipital"),
            MetricSpec("PO d_n_std", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "regional_9d", "d_n_std", network="parietal_occipital"),
            MetricSpec("Central d_n_std", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "regional_9d", "d_n_std", network="central"),
            MetricSpec("Global e_m_median", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_ON", "global_mnps_9d", "e_m_median"),
            MetricSpec("Frontal e_m_mean", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_ON", "regional_9d", "e_m_mean", network="frontal"),
            MetricSpec("PO d_s_mean", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_ON", "regional_9d", "d_s_mean", network="parietal_occipital"),
        ),
    )


def _ds003509_jacobian_panel() -> PanelSpec:
    return PanelSpec(
        slug="jacobian_reachability_ds003509",
        title="Simon conflict: Jacobian and reachability metrics",
        metrics=(
            MetricSpec("Frontal trace_median", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_ON", "regional_mnps_jacobian_3d", "trace_median", network="frontal"),
            MetricSpec("q_ratio_h4", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_ON", "adaptive_collapse", "q_ratio_h4"),
            MetricSpec("capture_gate", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_ON", "adaptive_collapse", "capture_gate"),
            MetricSpec("Temporal block_frobenius_mean", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "global_mnps_9d_block_jacobian", "block_frobenius_mean", network="temporal"),
            MetricSpec("Persistence log-eig variance", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_ON", "reachability_cones", "persistence_log_eig_var_median"),
            MetricSpec("Persistence hysteresis d_eff", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_ON", "reachability_cones", "persistence_hysteresis_d_eff_median"),
        ),
    )


def _ds003506_classical_panel() -> PanelSpec:
    return PanelSpec(
        slug="classical_eeg_ds003506",
        title="Reinforcement learning: classical EEG comparators",
        metrics=(
            MetricSpec("Alpha mean", "classical", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "eeg_classical_comparators", "eeg_classical_relative_alpha_mean"),
            MetricSpec("Alpha median", "classical", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "eeg_classical_comparators", "eeg_classical_relative_alpha_median"),
            MetricSpec("Alpha IQR", "classical", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "eeg_classical_comparators", "eeg_classical_relative_alpha_iqr"),
            MetricSpec("Alpha MAD-sigma", "classical", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "eeg_classical_comparators", "eeg_classical_relative_alpha_mad_sigma"),
            MetricSpec(
                "PSE95 delta mean-median (OFF vs ON, exploratory)",
                "classical",
                SUBJECT_COORDINATE_CONTRACT,
                "Parkinson_OFF_vs_ON",
                "eeg_classical_comparators",
                "eeg_classical_peak_spectral_edge_95_delta_mean_median",
                exploratory=True,
            ),
            MetricSpec(
                "Gamma MAD-sigma (OFF vs ON, exploratory)",
                "classical",
                SUBJECT_COORDINATE_CONTRACT,
                "Parkinson_OFF_vs_ON",
                "eeg_classical_comparators",
                "eeg_classical_relative_gamma_mad_sigma",
                exploratory=True,
            ),
        ),
    )


def _ds003506_mnps9d_panel() -> PanelSpec:
    return PanelSpec(
        slug="mnps9d_ds003506",
        title="Reinforcement learning: focal MNPS 9D metrics",
        metrics=(
            MetricSpec("Frontal d_s_mean", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "regional_9d", "d_s_mean", network="frontal"),
            MetricSpec("Frontal d_s_median", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "regional_9d", "d_s_median", network="frontal"),
            MetricSpec("Global d_s_mean", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "global_mnps_9d", "d_s_mean"),
            MetricSpec("Global d_s_median", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "global_mnps_9d", "d_s_median"),
            MetricSpec(
                "Frontal d_s_mean (Control vs ON, exploratory)",
                "standard",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_ON",
                "regional_9d",
                "d_s_mean",
                network="frontal",
                exploratory=True,
            ),
            MetricSpec(
                "Frontal e_e_median (OFF vs ON, exploratory)",
                "standard",
                SUBJECT_COORDINATE_CONTRACT,
                "Parkinson_OFF_vs_ON",
                "regional_9d",
                "e_e_median",
                network="frontal",
                exploratory=True,
            ),
        ),
    )


def _ds003506_jacobian_panel() -> PanelSpec:
    return PanelSpec(
        slug="jacobian_reachability_ds003506",
        title="Reinforcement learning: Jacobian and reachability metrics",
        metrics=(
            MetricSpec("Rotation coherence axis 2", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_OFF", "tier2_jacobian", "rotation_coherence_mean_axis_2"),
            MetricSpec("Central block_frobenius_mean", "standard", COHORT_COORDINATE_CONTRACT, "Control_vs_Parkinson_ON", "global_mnps_9d_block_jacobian", "block_frobenius_mean", network="central"),
            MetricSpec(
                "a_operator_norm (exploratory)",
                "standard",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_OFF",
                "adaptive_collapse",
                "a_operator_norm",
                exploratory=True,
            ),
            MetricSpec(
                "capture_gate (exploratory)",
                "standard",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_OFF",
                "adaptive_collapse",
                "capture_gate",
                exploratory=True,
            ),
            MetricSpec(
                "tube_log_det_split_half_a (exploratory)",
                "standard",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_OFF",
                "reachability_cones",
                "tube_log_det_split_half_a_median",
                exploratory=True,
            ),
            MetricSpec(
                "persistence_tau_log_det (exploratory)",
                "standard",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_OFF",
                "reachability_cones",
                "persistence_tau_log_det_median",
                exploratory=True,
            ),
        ),
    )


def violin_panels_for_dataset(dataset_id: str) -> tuple[PanelSpec, ...]:
    if dataset_id == "ds003509":
        return (
            _ds003509_classical_panel(),
            _ds003509_mnps9d_panel(),
            _ds003509_jacobian_panel(),
        )
    if dataset_id == "ds003506":
        return (
            _ds003506_classical_panel(),
            _ds003506_mnps9d_panel(),
            _ds003506_jacobian_panel(),
        )
    get_dataset_spec(dataset_id)
    raise ValueError(f"Unsupported dataset_id {dataset_id!r}.")


def standard_qc_specs_for_dataset(dataset_id: str) -> tuple[MetricSpec, ...]:
    panels = violin_panels_for_dataset(dataset_id)
    metrics = tuple(
        spec for panel in panels for spec in panel.metrics if spec.source in {"standard", "classical"}
    )
    return _unique_metrics(metrics)


def event_qc_specs_for_dataset(dataset_id: str) -> tuple[MetricSpec, ...]:
    if dataset_id == "ds003509":
        return (
            MetricSpec(
                "test_response_all hysteresis_area_de (best event, exploratory)",
                "event",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_ON",
                "regional_event_locked_trajectory_9d",
                "hysteresis_area_de",
                network="temporal",
                segment_kind="event_family",
                segment_label="test_response_all",
                exploratory=True,
            ),
        )
    if dataset_id == "ds003506":
        return (
            MetricSpec(
                "match_feedback_punishment hysteresis_area_de (best event, exploratory)",
                "event",
                COHORT_COORDINATE_CONTRACT,
                "Control_vs_Parkinson_OFF",
                "global_event_locked_trajectory_9d",
                "hysteresis_area_de",
                network="global",
                segment_kind="event_exact",
                segment_label="match_feedback_punishment",
                exploratory=True,
            ),
        )
    get_dataset_spec(dataset_id)
    raise ValueError(f"Unsupported dataset_id {dataset_id!r}.")
