"""Optional event-locked APPLESEED MNPS analysis, isolated from primary tests."""
from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from appleseed_support import EVENT_COORDINATE_CONTRACT, DEFAULT_DATA_ROOT, DEFAULT_RESULTS_ROOT, bh_fdr, h5_paths, session_identity
from ndt_analysis.h5_contract import resolve_coords_3d

EVENTS = ("object", "water", "speech", "face")
AXES = ("m", "d", "e")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT / "03_event_locked_exploratory")
    parser.add_argument("--n-permutations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _text(values: np.ndarray) -> np.ndarray:
    return np.asarray([x.decode() if isinstance(x, bytes) else str(x) for x in values])


def _sign_flip(values: np.ndarray, n_permutations: int, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 5:
        return np.nan
    rng = np.random.default_rng(seed)
    observed = abs(values.mean())
    signs = rng.choice((-1.0, 1.0), size=(n_permutations, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((1 + np.sum(null >= observed)) / (n_permutations + 1))


def extract_h5(h5_path: Path) -> list[dict]:
    identity = session_identity(h5_path)
    with h5py.File(h5_path, "r") as handle:
        resolved = resolve_coords_3d(handle, EVENT_COORDINATE_CONTRACT)
        if resolved is None or "event_windows" not in handle:
            return []
        coords = np.asarray(resolved.values, dtype=float)
        event_windows = handle["event_windows"]
        labels = _text(event_windows["event_label"][:])
        bins = _text(event_windows["bin_label"][:])
        event_ids = event_windows["event_id"][:]
        windows = event_windows["window_id"][:]
        stage_fraction_labeled = float(handle.attrs.get("stage_frac_labeled", np.nan))
    rows = []
    for label in EVENTS:
        for event_id in np.unique(event_ids[labels == label]):
            event_values: dict[str, np.ndarray] = {}
            for bin_label in ("event", "pre_near"):
                mask = (labels == label) & (event_ids == event_id) & (bins == bin_label)
                idx = windows[mask]
                idx = idx[(idx >= 0) & (idx < len(coords))]
                if len(idx):
                    event_values[bin_label] = np.nanmedian(coords[idx], axis=0)
            if {"event", "pre_near"} <= set(event_values):
                for axis_index, axis in enumerate(AXES):
                    rows.append(
                        {
                            **identity,
                            "stage_fraction_labeled": stage_fraction_labeled,
                            "event_label": label,
                            "event_id": int(event_id),
                            "axis": axis,
                            "event_minus_pre_near": float(event_values["event"][axis_index] - event_values["pre_near"][axis_index]),
                        }
                    )
    return rows


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = [row for path in h5_paths(args.data_root) for row in extract_h5(path)]
    event_rows = pd.DataFrame(rows)
    event_rows.to_csv(args.output_dir / "event_level_deltas.csv", index=False)
    # Pool session-level event summaries within child before inference. This
    # prevents four recordings from one child acting as four independent tests.
    subject_rows = (
        event_rows.groupby(["subject_id", "event_label", "axis"], as_index=False)
        .agg(
            event_minus_pre_near=("event_minus_pre_near", "mean"),
            n_sessions=("session", "nunique"),
            min_stage_fraction_labeled=("stage_fraction_labeled", "min"),
        )
    )
    subject_rows.to_csv(args.output_dir / "subject_event_deltas.csv", index=False)
    tests = []
    for index, ((label, axis), group) in enumerate(subject_rows.groupby(["event_label", "axis"])):
        values = group["event_minus_pre_near"].to_numpy()
        tests.append(
            {
                "event_label": label,
                "axis": axis,
                "n_subjects": len(values),
                "n_subject_sessions": int(group["n_sessions"].sum()),
                "min_stage_fraction_labeled": float(group["min_stage_fraction_labeled"].min()),
                "mean_subject_delta": float(np.mean(values)),
                "permutation_p_raw": _sign_flip(values, args.n_permutations, args.seed + index),
            }
        )
    tests = pd.DataFrame(tests)
    tests["permutation_p_fdr"] = bh_fdr(tests["permutation_p_raw"])
    tests.to_csv(args.output_dir / "event_exploratory_tests.csv", index=False)
    print(f"Wrote {len(event_rows)} event rows and {len(tests)} exploratory tests to {args.output_dir}")


if __name__ == "__main__":
    main()
