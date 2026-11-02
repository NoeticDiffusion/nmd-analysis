"""Locked primary-contrast mechanics for ds004100 NDT v1.1.

This module intentionally contains no data-root, output-root, or command-line
default.  Supplying a frozen, independently reviewed eligibility ledger is a
precondition for empirical scoring.  In particular, a finite H5 value is not
silently promoted to a biologically qualified measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import comb
from typing import Iterable, Literal, Mapping, Sequence

import numpy as np
from scipy.stats import beta


Label = Literal["ictal", "interictal"]
PRIMARY_ENDPOINTS = ("H1", "H2")
GATES = ("G1", "G2", "G3", "G4")


class ContrastContractError(ValueError):
    """The supplied export/ledger cannot support the registered contrast."""


def _as_bool_mask(mask: Sequence[object], *, name: str) -> np.ndarray:
    array = np.asarray(mask)
    if array.ndim != 1:
        raise ContrastContractError(f"{name} must be a one-dimensional native-grid mask")
    if not np.all(np.isin(array, (0, 1, False, True))):
        raise ContrastContractError(f"{name} must contain only boolean/0/1 values")
    return array.astype(bool)


def _native_summary(values: Sequence[float], mask: np.ndarray, *, endpoint: str) -> tuple[float, int]:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.shape != mask.shape:
        raise ContrastContractError(f"{endpoint} values and native mask must have identical 1D shape")
    usable = np.isfinite(array) & mask
    n_valid = int(usable.sum())
    if n_valid < 30 or n_valid < 0.5 * len(array):
        raise ContrastContractError(
            f"{endpoint} has {n_valid}/{len(array)} valid native centers; requires >=30 and >=50%"
        )
    return float(np.median(array[usable])), n_valid


def h1_recording_median(values: Sequence[float], valid: Sequence[object]) -> tuple[float, int]:
    """H1 uses its T-length query ``valid`` mask, including an eligible terminal row."""
    return _native_summary(values, _as_bool_mask(valid, name="H1 valid"), endpoint="H1")


def h2_recording_median(
    values: Sequence[float], source_idx: Sequence[int], n_neighbor_pairs: Sequence[float]
) -> tuple[float, int]:
    """H2 indexes its T-length series at unique supported source centers only."""
    array = np.asarray(values, dtype=float)
    pairs = np.asarray(n_neighbor_pairs)
    indices = np.asarray(source_idx)
    if array.ndim != 1 or pairs.ndim != 1 or array.shape != pairs.shape:
        raise ContrastContractError("H2 values and n_neighbor_pairs must be aligned 1D native arrays")
    if indices.ndim != 1 or not np.issubdtype(indices.dtype, np.integer):
        raise ContrastContractError("H2 source_idx must be a one-dimensional integer array")
    if len(indices) != len(np.unique(indices)):
        raise ContrastContractError("H2 source_idx contains duplicates; a source center may count once")
    if np.any(indices < 0) or np.any(indices >= len(array) - 1):
        raise ContrastContractError("H2 source_idx must refer to non-terminal native source centers")
    mask = np.zeros(len(array), dtype=bool)
    mask[indices] = True
    mask &= pairs > 0
    return _native_summary(array, mask, endpoint="H2")


@dataclass(frozen=True)
class RecordingSummary:
    """One endpoint-specific recording median plus its frozen eligibility evidence."""

    endpoint: Literal["H1", "H2"]
    subject_id: str
    session: str
    acquisition: str
    label: Label
    source_recording_id: str
    original_recording_id: str
    export_sha256: str
    crop_resolution: str
    median: float
    valid_centers: int
    native_centers: int
    metadata_eligible: bool
    gates: Mapping[str, bool]
    computation_status: str
    support_status: str
    measurement_validity: str
    claim_status: str
    temporal_support_status: str
    comparability_verdict: str
    normalization_signature: str
    feature_signature: str
    fallback_signature: str
    contact_signature: str
    reference_provenance: str

    def __post_init__(self) -> None:
        if self.endpoint not in PRIMARY_ENDPOINTS or self.label not in ("ictal", "interictal"):
            raise ContrastContractError("RecordingSummary has an unknown primary endpoint or label")
        if not all((self.subject_id, self.session, self.acquisition, self.source_recording_id,
                    self.original_recording_id, self.export_sha256, self.crop_resolution)):
            raise ContrastContractError("Recording identity, subject, session, and acquisition are required")
        if not np.isfinite(self.median):
            raise ContrastContractError("A recording median must be finite; missing is not zero")
        if self.native_centers <= 0 or self.valid_centers < 0:
            raise ContrastContractError("Native-center counts are invalid")
        if self.valid_centers < 30 or self.valid_centers < 0.5 * self.native_centers:
            raise ContrastContractError("Recording violates the registered >=30 / >=50% support threshold")
        if self.computation_status != "computed" or self.support_status != "sufficient":
            raise ContrastContractError("Endpoint-level computation/support status is not eligible")
        missing_gates = set(GATES).difference(self.gates)
        if missing_gates:
            raise ContrastContractError(f"Eligibility ledger lacks gates: {sorted(missing_gates)}")
        if not all(type(self.gates[gate]) is bool for gate in GATES):
            raise ContrastContractError("Eligibility ledger gates must be literal booleans")

    @property
    def stratum(self) -> tuple[str, str]:
        return self.session, self.acquisition

    @property
    def confirmatory_eligible(self) -> bool:
        return self.metadata_eligible and all(bool(self.gates[gate]) for gate in GATES)


@dataclass(frozen=True)
class EndpointContrast:
    endpoint: str
    selected_strata: Mapping[str, tuple[str, str]]
    participant_differences: Mapping[str, float]
    confirmatory_participant_differences: Mapping[str, float]
    descriptive_n: int
    n: int
    k_negative: int
    ties: int
    negative_fraction: float | None
    negative_fraction_ci95: tuple[float, float] | None
    median_difference: float | None
    bootstrap_ci95: tuple[float, float] | None
    raw_p: float | None
    confirmatory_test_run: bool
    test_status: str


def _select_strata(rows: Iterable[RecordingSummary]) -> dict[str, tuple[str, str]]:
    """Choose the frozen largest metadata-eligible both-label session/acq stratum."""
    grouped: dict[tuple[str, tuple[str, str]], list[RecordingSummary]] = {}
    for row in rows:
        if row.metadata_eligible:
            grouped.setdefault((row.subject_id, row.stratum), []).append(row)
    by_subject: dict[str, list[tuple[int, tuple[str, str]]]] = {}
    for (subject, stratum), group in grouped.items():
        labels = {row.label for row in group}
        if labels == {"ictal", "interictal"}:
            by_subject.setdefault(subject, []).append((len(group), stratum))
    return {
        subject: sorted(candidates, key=lambda item: (-item[0], item[1]))[0][1]
        for subject, candidates in by_subject.items()
    }


def exact_upper_tail(k_negative: int, n: int) -> float:
    if not 0 <= k_negative <= n or n <= 0:
        raise ContrastContractError("Binomial count must satisfy 0 <= K <= N and N > 0")
    return sum(comb(n, k) for k in range(k_negative, n + 1)) / 2**n


def exact_binomial_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if not 0 <= k <= n or n <= 0:
        raise ContrastContractError("Binomial interval requires 0 <= K <= N and N > 0")
    lower = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    upper = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lower, upper


def percentile_bootstrap_median(differences: Sequence[float], *, seed: int = 20260922, n_resamples: int = 10_000) -> tuple[float, float]:
    array = np.asarray(differences, dtype=float)
    if array.ndim != 1 or not len(array) or not np.all(np.isfinite(array)):
        raise ContrastContractError("Bootstrap requires one or more finite participant differences")
    generator = np.random.default_rng(seed)
    samples = generator.choice(array, size=(n_resamples, len(array)), replace=True)
    return tuple(float(x) for x in np.percentile(np.median(samples, axis=1), [2.5, 97.5]))


def build_endpoint_contrast(rows: Sequence[RecordingSummary], endpoint: Literal["H1", "H2"]) -> EndpointContrast:
    endpoint_rows = [row for row in rows if row.endpoint == endpoint]
    selected = _select_strata(endpoint_rows)
    selected_rows = [row for row in endpoint_rows if selected.get(row.subject_id) == row.stratum]
    seen_exports: set[str] = set()
    seen_originals: set[str] = set()
    for row in selected_rows:
        if row.export_sha256 in seen_exports:
            raise ContrastContractError(f"Duplicate export hash was not collapsed: {row.export_sha256}")
        if row.original_recording_id in seen_originals or row.crop_resolution != "unique":
            raise ContrastContractError(f"Original recording/crop was not resolved: {row.original_recording_id}")
        seen_exports.add(row.export_sha256)
        seen_originals.add(row.original_recording_id)

    participant_differences: dict[str, float] = {}
    confirmatory_differences: dict[str, float] = {}
    for subject, stratum in selected.items():
        pair = [row for row in selected_rows if row.subject_id == subject and row.stratum == stratum]
        by_label = {label: [row.median for row in pair if row.label == label] for label in ("ictal", "interictal")}
        if not by_label["ictal"] or not by_label["interictal"]:
            continue
        participant_differences[subject] = float(np.median(by_label["ictal"]) - np.median(by_label["interictal"]))
        signatures_match = all(
            len({getattr(row, name) for row in pair}) == 1
            for name in ("normalization_signature", "feature_signature", "fallback_signature", "contact_signature")
        )
        reference_qualified = all(row.reference_provenance not in {"", "unknown", "n/a"} for row in pair)
        ledger_comparable = all(row.comparability_verdict == "passed" for row in pair)
        if all(row.confirmatory_eligible for row in pair) and signatures_match and reference_qualified and ledger_comparable:
            confirmatory_differences[subject] = participant_differences[subject]

    differences = list(confirmatory_differences.values())
    n = len(differences)
    k = sum(value < 0 for value in differences)
    ties = sum(value == 0 for value in differences)
    test_run = n >= 20
    raw_p = exact_upper_tail(k, n) if test_run else None
    return EndpointContrast(
        endpoint=endpoint,
        selected_strata=selected,
        participant_differences=participant_differences,
        confirmatory_participant_differences=confirmatory_differences,
        descriptive_n=len(participant_differences),
        n=n,
        k_negative=k,
        ties=ties,
        negative_fraction=(k / n if n else None),
        negative_fraction_ci95=(exact_binomial_ci(k, n) if n else None),
        median_difference=(float(np.median(differences)) if n else None),
        bootstrap_ci95=(percentile_bootstrap_median(differences) if n else None),
        raw_p=raw_p,
        confirmatory_test_run=test_run,
        test_status=("RUN_PENDING_HOLM" if test_run else "NOT_RUN_METHOD_LIMITED"),
    )


def holm_adjust(primary: Sequence[EndpointContrast]) -> dict[str, float]:
    """Two-member registered family; unavailable endpoints remain p=1 only for bookkeeping."""
    if {contrast.endpoint for contrast in primary} != set(PRIMARY_ENDPOINTS) or len(primary) != 2:
        raise ContrastContractError("Holm family must contain exactly H1 and H2")
    # p=1 is solely internal multiplicity bookkeeping for an endpoint whose
    # confirmatory test was not run; the public result remains raw_p=None.
    ordered = sorted(primary, key=lambda contrast: (contrast.raw_p if contrast.raw_p is not None else 1.0, contrast.endpoint))
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, contrast in enumerate(ordered):
        p_for_holm = contrast.raw_p if contrast.raw_p is not None else 1.0
        running = max(running, min(1.0, (len(ordered) - rank) * p_for_holm))
        adjusted[contrast.endpoint] = running
    return adjusted


def primary_family_verdicts(primary: Sequence[EndpointContrast]) -> dict[str, str]:
    """Apply the preregistered PASS rule after, never before, joint Holm correction."""
    adjusted = holm_adjust(primary)
    verdicts: dict[str, str] = {}
    for contrast in primary:
        if not contrast.confirmatory_test_run:
            verdicts[contrast.endpoint] = "METHOD-LIMITED"
        elif adjusted[contrast.endpoint] <= 0.05 and contrast.median_difference is not None and contrast.median_difference < 0:
            verdicts[contrast.endpoint] = "PASS"
        else:
            verdicts[contrast.endpoint] = "INCONCLUSIVE"
    return verdicts
