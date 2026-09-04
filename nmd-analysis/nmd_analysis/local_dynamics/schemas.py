"""Stable table-grain and identity contracts for local-dynamics exports."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

TABLE_GRAINS = frozenset({"recording", "recording_horizon", "window", "sequence", "transition"})

UNIQUE_KEYS = {
    "recording": ("recording_uid", "coordinate_dimension", "coordinate_contract_id"),
    "recording_horizon": (
        "recording_uid",
        "coordinate_dimension",
        "coordinate_contract_id",
        "horizon_steps",
    ),
    "window": ("recording_uid", "coordinate_dimension", "coordinate_contract_id", "window_id"),
    "sequence": (
        "recording_uid",
        "coordinate_dimension",
        "coordinate_contract_id",
        "horizon_steps",
        "start_window_id",
    ),
    "transition": (
        "recording_uid",
        "coordinate_dimension",
        "coordinate_contract_id",
        "source_window_id",
        "target_window_id",
    ),
}


def _token(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text if text else fallback


def build_recording_uid(metadata: Mapping[str, Any]) -> str:
    """Build a deterministic cross-dataset recording identifier."""
    return "::".join(
        (
            _token(metadata.get("dataset_id"), "unknown_dataset"),
            _token(metadata.get("subject_id") or metadata.get("participant_id"), "unknown_participant"),
            _token(metadata.get("session"), "no_session"),
            _token(metadata.get("run"), "no_run"),
            _token(metadata.get("acq"), "no_acq"),
            _token(metadata.get("task"), "no_task"),
        )
    )


def build_coordinate_contract_id(
    coordinate_contract: Any,
    *,
    coordinate_layer: Any = None,
    anchor_hash: Any = None,
) -> str:
    """Return a stable digest that prevents silent contract mixing."""
    payload = "|".join(
        (
            _token(coordinate_contract, "unknown_contract"),
            _token(coordinate_layer, "unknown_layer"),
            _token(anchor_hash, "no_anchor_hash"),
        )
    )
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


def with_table_identity(
    base: Mapping[str, Any],
    *,
    grain: str,
    coordinate_dimension: int,
    coordinate_contract: Any,
    coordinate_layer: Any = None,
) -> dict[str, Any]:
    if grain not in TABLE_GRAINS:
        raise ValueError(f"Unsupported local-dynamics table grain: {grain}")
    row = dict(base)
    row["table_grain"] = grain
    row["coordinate_dimension"] = int(coordinate_dimension)
    row["coordinate_contract"] = coordinate_contract
    row["coordinate_layer"] = coordinate_layer
    row["recording_uid"] = build_recording_uid(row)
    row["coordinate_contract_id"] = build_coordinate_contract_id(
        coordinate_contract,
        coordinate_layer=coordinate_layer,
        anchor_hash=row.get("anchor_hash"),
    )
    return row
