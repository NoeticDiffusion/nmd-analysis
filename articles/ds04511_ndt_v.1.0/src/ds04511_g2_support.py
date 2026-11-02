"""G2: metadata/support audit of every H5. No task-grouped outcomes."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from ds04511_common import (
    MIN_VALID_FRACTION,
    MIN_VALID_TIMEPOINTS,
    json_safe,
    scalar,
)
from nmd_analysis.dynamical_families.readers import family_availability, read_family
from nmd_analysis.signal_support import read_signal_support

FAMILY_IDS = (
    "diffusion",
    "chart_drift",
    "one_step",
    "amplification",
    "history",
    "turning",
    "destination",
    "resilience",
)
METADATA_PATHS = (
    "provenance/anchoring/primary_coordinate_layer",
    "provenance/anchoring/primary_coordinate_contract",
    "provenance/normalization/status",
    "provenance/normalization/method",
    "support_signature/v1/coordinates/e_m/source",
    "support_signature/v1/coordinates/e_m/fallback_feature",
    "support_signature/v1/coordinates/e_m/semantic_equivalence",
    "support_signature/v1/axes_3d/e/source",
    "provenance/signal_support_provenance/temporal_support_status",
    "provenance/signal_support_provenance/temporal_support_reason",
    "provenance/signal_support_provenance/source_quality_status",
    "stochastic_reachability/v1/primary/n_propagator_steps",
    "stochastic_reachability/v1/primary/computation_status",
    "stochastic_reachability/v1/primary/support_status",
    "jacobian/derived_metrics/v1/computation_status",
)


def _dataset_value(handle: h5py.File, key: str) -> Any:
    if key not in handle:
        return "not_recorded"
    node = handle[key]
    if isinstance(node, h5py.Group):
        return "group"
    return scalar(node[()])


def _dt_report(time: np.ndarray) -> dict[str, Any]:
    if time.size == 0:
        return {
            "n_timepoints": 0,
            "n_steps": 0,
            "unique_dt_sec": [],
            "has_nonpositive_dt": False,
            "has_gap_vs_modal_dt": False,
            "regular_grid": False,
            "time_finite": True,
        }
    finite = np.isfinite(time)
    diff = np.diff(time.astype(float)) if time.size > 1 else np.asarray([], dtype=float)
    values, counts = (
        np.unique(np.round(diff, 12), return_counts=True) if diff.size else (np.asarray([]), np.asarray([]))
    )
    modal = float(values[int(np.argmax(counts))]) if values.size else None
    has_gap = bool(modal is not None and np.any(np.abs(diff - modal) > 1e-9))
    return {
        "n_timepoints": int(time.size),
        "n_steps": int(diff.size),
        "unique_dt_sec": [[float(value), int(count)] for value, count in zip(values.tolist(), counts.tolist())],
        "has_nonpositive_dt": bool(diff.size and np.any(diff <= 0)),
        "has_gap_vs_modal_dt": has_gap,
        "regular_grid": bool(values.size == 1 and modal is not None and modal > 0),
        "time_finite": bool(finite.all()),
        "modal_dt_sec": modal,
    }


def _h1h2_inclusion(
    *,
    computation_status: str,
    support_status: str,
    n_exported: int,
    n_valid: int,
    n_valid_no_psd_floor: int,
) -> dict[str, Any]:
    status_ok = computation_status == "computed"
    support_ok = support_status in {"sufficient", "not_recorded"}
    count_ok = n_valid >= MIN_VALID_TIMEPOINTS
    frac_ok = (n_valid / n_exported) >= MIN_VALID_FRACTION if n_exported else False
    included = bool(status_ok and support_ok and count_ok and frac_ok)
    reasons = []
    if not status_ok:
        reasons.append(f"computation_status={computation_status}")
    if support_status not in {"sufficient", "not_recorded"}:
        reasons.append(f"support_status={support_status}")
    if not count_ok:
        reasons.append(f"n_valid={n_valid}<{MIN_VALID_TIMEPOINTS}")
    if not frac_ok:
        reasons.append("valid_fraction<0.5")
    floor_ok = n_valid_no_psd_floor >= MIN_VALID_TIMEPOINTS and (
        (n_valid_no_psd_floor / n_exported) >= MIN_VALID_FRACTION if n_exported else False
    )
    return {
        "h1_h2_support_included": included,
        "h1_h2_support_reason": "ok" if included else ";".join(reasons) or "not_included",
        "h1_h2_psd_floor_excluded_included": bool(included and status_ok and support_ok and floor_ok),
        "h1_h2_psd_floor_excluded_reason": (
            "ok" if included and floor_ok else "insufficient_after_psd_floor_exclusion"
        ),
    }


def inspect_support(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {
        "source_h5": str(path.resolve()),
        "stem": path.stem,
        "read_ok": False,
        "read_error": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            time = np.asarray(handle["time"][()]) if "time" in handle else np.asarray([])
            row.update(_dt_report(time))
            for key in METADATA_PATHS:
                row[key.replace("/", "__")] = _dataset_value(handle, key)
            if "manifest" in handle.attrs:
                embedded = handle.attrs["manifest"]
                if isinstance(embedded, (bytes, np.bytes_)):
                    embedded = embedded.decode("utf-8")
                parsed = json.loads(str(embedded)) if not isinstance(embedded, dict) else embedded
                fits = sorted(
                    {
                        str(item.get("fit_scope"))
                        for item in (parsed.get("feature_baselines") or {}).values()
                        if isinstance(item, dict) and "fit_scope" in item
                    }
                )
                row["feature_fit_scopes"] = "|".join(fits) if fits else "not_recorded"
            else:
                row["feature_fit_scopes"] = "not_recorded"
            for family in FAMILY_IDS:
                payload = read_family(handle, family)
                prefix = f"{family}_"
                row[prefix + "available"] = bool(payload.get("availability"))
                row[prefix + "computation_status"] = payload.get("computation_status", "not_recorded")
                row[prefix + "support_status"] = payload.get("support_status", "not_recorded")
                row[prefix + "qualification_status"] = payload.get("qualification_status", "not_recorded")
                row[prefix + "measurement_validity"] = payload.get("measurement_validity", "not_recorded")
                row[prefix + "claim_status"] = payload.get("claim_status", "not_recorded")
                row[prefix + "failure_reason"] = payload.get("failure_reason", "not_recorded")
                if family == "diffusion":
                    series = payload.get("series") or {}
                    valid = np.asarray(series.get("valid", []), dtype=float).reshape(-1)
                    floor = np.asarray(series.get("psd_floor_applied", []), dtype=float).reshape(-1)
                    n_exported = int(valid.size) if valid.size else int(row.get("n_timepoints") or 0)
                    n_valid = int(np.sum(valid == 1)) if valid.size else 0
                    n_floor = int(np.sum(floor == 1)) if floor.size else 0
                    n_valid_no_floor = (
                        int(np.sum((valid == 1) & (floor != 1))) if valid.size and floor.size == valid.size else n_valid
                    )
                    summary = payload.get("summary") or {}
                    row["diffusion_n_exported"] = n_exported
                    row["diffusion_n_valid"] = n_valid
                    row["diffusion_n_psd_floor_applied"] = n_floor
                    row["diffusion_n_valid_no_psd_floor"] = n_valid_no_floor
                    row["diffusion_valid_fraction"] = (
                        float(n_valid / n_exported) if n_exported else float("nan")
                    )
                    row["diffusion_summary_n_valid_timepoints"] = scalar(summary.get("n_valid_timepoints"))
                    row.update(
                        _h1h2_inclusion(
                            computation_status=str(payload.get("computation_status", "not_recorded")),
                            support_status=str(payload.get("support_status", "not_recorded")),
                            n_exported=n_exported,
                            n_valid=n_valid,
                            n_valid_no_psd_floor=n_valid_no_floor,
                        )
                    )
            availability = {item["family_id"]: item for item in family_availability(handle)}
            row["family_availability_json"] = json.dumps(
                json_safe({key: value.get("available") for key, value in availability.items()}),
                sort_keys=True,
            )
        support = read_signal_support(path)
        row["signal_support_reader_status"] = support.get("status", "unknown")
        row["signal_support_validation_status"] = (support.get("validation") or {}).get("status", "unknown")
        row["signal_support_temporal_status"] = (support.get("temporal_support") or {}).get("status", "unknown")
        row["signal_support_source_quality_status"] = support.get("source_quality_status", "not_recorded")
        row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001 - audit must keep going
        row["read_error"] = f"{type(exc).__name__}: {exc}"
        row["h1_h2_support_included"] = False
        row["h1_h2_support_reason"] = f"read_error:{type(exc).__name__}"
    return row


def build_support_table(files: list[Path]) -> pd.DataFrame:
    return pd.DataFrame([inspect_support(path) for path in files])


def support_audit(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {"gate": "G2", "status": "blocked", "failure_reason": "no_rows"}
    counts = {
        "n_recordings": int(len(frame)),
        "n_read_ok": int(frame["read_ok"].eq(True).sum()),
        "n_regular_grid": int(frame.get("regular_grid", pd.Series(dtype=bool)).eq(True).sum()),
        "n_nonpositive_dt": int(frame.get("has_nonpositive_dt", pd.Series(dtype=bool)).eq(True).sum()),
        "n_h1_h2_support_included": int(frame.get("h1_h2_support_included", pd.Series(dtype=bool)).eq(True).sum()),
    }
    unique_fields = {}
    for column in (
        "provenance__normalization__status",
        "provenance__normalization__method",
        "provenance__anchoring__primary_coordinate_contract",
        "feature_fit_scopes",
        "support_signature__v1__coordinates__e_m__source",
        "support_signature__v1__coordinates__e_m__semantic_equivalence",
        "signal_support_temporal_status",
        "diffusion_computation_status",
        "destination_computation_status",
        "resilience_computation_status",
        "stochastic_reachability__v1__primary__computation_status",
        "jacobian__derived_metrics__v1__computation_status",
    ):
        if column in frame:
            unique_fields[column] = sorted(frame[column].dropna().astype(str).unique().tolist())
    propagator = []
    if "stochastic_reachability__v1__primary__n_propagator_steps" in frame:
        propagator = sorted(
            Counter(frame["stochastic_reachability__v1__primary__n_propagator_steps"].dropna().astype(str)).items()
        )
    scaling_common = "cohort_anchored" in unique_fields.get(
        "provenance__anchoring__primary_coordinate_contract", []
    )
    return {
        "gate": "G2",
        "status": "audited",
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "confirmatory_contrasts": False,
        "counts": counts,
        "unique_metadata": unique_fields,
        "n_propagator_steps_counts": propagator,
        "scaling_gate": {
            "primary_contract_values": unique_fields.get(
                "provenance__anchoring__primary_coordinate_contract", []
            ),
            "normalization_status_values": unique_fields.get("provenance__normalization__status", []),
            "amplitude_claim_status": (
                "exploratory_local_chart_geometry"
                if not scaling_common
                else "common_anchor_not_automatically_licensed"
            ),
            "note": (
                "subject_anchored local fits do not license confirmatory absolute amplitude "
                "comparisons across subjects. Within-subject task contrasts remain exploratory "
                "until G3/G4."
            ),
        },
        "read_errors": frame.loc[frame["read_ok"].ne(True), "read_error"].dropna().astype(str).tolist(),
    }
