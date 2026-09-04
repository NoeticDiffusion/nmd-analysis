from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import h5py
import numpy as np
import pandas as pd

PHOTIC_STAGE_LABELS: dict[int, str] = {
    50: "photo_5hz",
    51: "photo_10hz",
    52: "photo_15hz",
    53: "photo_20hz",
}
EYE_STAGE_LABELS: dict[int, str] = {
    60: "open_eyes",
    61: "closed_eyes",
    62: "eye_movement",
}
DEFAULT_BLOCK_LENGTH_WINDOWS = 5
DEFAULT_DUPLICATE_GAP_WINDOWS = 1


@dataclass(frozen=True)
class PhoticBlock:
    subject_id: str
    stage_code: int
    stage_label: str
    onset_idx: int
    end_idx: int
    onset_time_sec: float
    end_time_sec: float
    onset_window_start_sec: float
    end_window_end_sec: float
    recovered_window_count: int
    cluster_size: int
    gap_to_next_onset_windows: int | None
    source_h5_path: str


def _iter_h5_paths(raw_root: Path) -> list[Path]:
    return sorted(raw_root.glob("sub-*/sub-*.h5"))


def _subject_id_from_h5_path(h5_path: Path) -> str:
    return h5_path.stem.split("_")[0]


def _load_stage_series(h5_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    with h5py.File(h5_path, "r") as handle:
        stage = np.asarray(handle["labels/stage"][:], dtype=int).reshape(-1)
        time = np.asarray(handle["time"][:], dtype=float).reshape(-1)
        window_start = np.asarray(handle["window_start"][:], dtype=float).reshape(-1)
        window_end = np.asarray(handle["window_end"][:], dtype=float).reshape(-1)
    n = min(stage.size, time.size, window_start.size, window_end.size)
    return stage[:n], time[:n], window_start[:n], window_end[:n]


def _collapse_photic_onsets(
    stage: np.ndarray,
    *,
    duplicate_gap_windows: int = DEFAULT_DUPLICATE_GAP_WINDOWS,
) -> list[dict[str, int | list[int]]]:
    photic_mask = np.isin(stage, list(PHOTIC_STAGE_LABELS))
    photic_idx = np.flatnonzero(photic_mask)
    if photic_idx.size == 0:
        return []

    collapsed: list[dict[str, int | list[int]]] = []
    cursor = 0
    while cursor < photic_idx.size:
        start_idx = int(photic_idx[cursor])
        stage_code = int(stage[start_idx])
        cluster = [start_idx]
        cursor += 1
        while cursor < photic_idx.size:
            next_idx = int(photic_idx[cursor])
            next_code = int(stage[next_idx])
            if next_code != stage_code:
                break
            if next_idx - cluster[-1] > int(duplicate_gap_windows):
                break
            cluster.append(next_idx)
            cursor += 1
        collapsed.append(
            {
                "stage_code": stage_code,
                "onset_idx": start_idx,
                "cluster_indices": cluster,
            }
        )
    return collapsed


def recover_photic_blocks(
    stage: np.ndarray,
    time: np.ndarray,
    window_start: np.ndarray,
    window_end: np.ndarray,
    *,
    subject_id: str,
    source_h5_path: Path,
    block_length_windows: int = DEFAULT_BLOCK_LENGTH_WINDOWS,
    duplicate_gap_windows: int = DEFAULT_DUPLICATE_GAP_WINDOWS,
) -> tuple[np.ndarray, list[PhoticBlock]]:
    recovered_stage = np.full(stage.shape, -1, dtype=int)
    collapsed = _collapse_photic_onsets(stage, duplicate_gap_windows=duplicate_gap_windows)
    blocks: list[PhoticBlock] = []

    for idx, item in enumerate(collapsed):
        stage_code = int(item["stage_code"])
        onset_idx = int(item["onset_idx"])
        next_onset_idx = int(collapsed[idx + 1]["onset_idx"]) if idx + 1 < len(collapsed) else stage.size
        end_idx = min(onset_idx + int(block_length_windows) - 1, next_onset_idx - 1, stage.size - 1)
        if end_idx < onset_idx:
            end_idx = onset_idx
        recovered_stage[onset_idx : end_idx + 1] = stage_code
        stage_label = PHOTIC_STAGE_LABELS.get(stage_code, f"stage_{stage_code}")
        cluster_indices = [int(value) for value in item["cluster_indices"]]  # type: ignore[index]
        blocks.append(
            PhoticBlock(
                subject_id=subject_id,
                stage_code=stage_code,
                stage_label=stage_label,
                onset_idx=onset_idx,
                end_idx=end_idx,
                onset_time_sec=float(time[onset_idx]),
                end_time_sec=float(time[end_idx]),
                onset_window_start_sec=float(window_start[onset_idx]),
                end_window_end_sec=float(window_end[end_idx]),
                recovered_window_count=int(end_idx - onset_idx + 1),
                cluster_size=int(len(cluster_indices)),
                gap_to_next_onset_windows=(int(next_onset_idx - onset_idx) if idx + 1 < len(collapsed) else None),
                source_h5_path=str(source_h5_path),
            )
        )

    return recovered_stage, blocks


def _count_stage_values(stage: np.ndarray, codes: Iterable[int]) -> dict[int, int]:
    return {int(code): int(np.sum(stage == int(code))) for code in codes}


def build_stage_qc_tables(
    raw_root: Path,
    *,
    block_length_windows: int = DEFAULT_BLOCK_LENGTH_WINDOWS,
    duplicate_gap_windows: int = DEFAULT_DUPLICATE_GAP_WINDOWS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    subject_rows: list[dict[str, object]] = []
    block_rows: list[dict[str, object]] = []
    gap_rows: list[dict[str, object]] = []

    h5_paths = _iter_h5_paths(raw_root)
    for h5_path in h5_paths:
        subject_id = _subject_id_from_h5_path(h5_path)
        stage, time, window_start, window_end = _load_stage_series(h5_path)
        recovered_stage, blocks = recover_photic_blocks(
            stage,
            time,
            window_start,
            window_end,
            subject_id=subject_id,
            source_h5_path=h5_path,
            block_length_windows=block_length_windows,
            duplicate_gap_windows=duplicate_gap_windows,
        )

        original_counts = _count_stage_values(stage, PHOTIC_STAGE_LABELS)
        recovered_counts = _count_stage_values(recovered_stage, PHOTIC_STAGE_LABELS)
        eye_counts = _count_stage_values(stage, EYE_STAGE_LABELS)
        duplicate_cluster_count = int(sum(1 for block in blocks if block.cluster_size > 1))

        row: dict[str, object] = {
            "subject_id": subject_id,
            "source_h5_path": str(h5_path),
            "n_epochs": int(stage.size),
            "block_length_windows": int(block_length_windows),
            "block_length_seconds": float(block_length_windows * 4.0),
            "duplicate_gap_windows": int(duplicate_gap_windows),
            "stage_frac_labeled_original": float(np.mean(stage != -1)) if stage.size else float("nan"),
            "photic_frac_recovered": float(np.mean(recovered_stage != -1)) if recovered_stage.size else float("nan"),
            "n_original_unmapped": int(np.sum(stage == -1)),
            "n_original_photic_markers": int(sum(original_counts.values())),
            "n_recovered_photic_windows": int(sum(recovered_counts.values())),
            "n_recovered_blocks": int(len(blocks)),
            "n_duplicate_clusters": duplicate_cluster_count,
            "has_any_photic_marker": bool(sum(original_counts.values()) > 0),
            "has_any_recovered_photic": bool(sum(recovered_counts.values()) > 0),
        }
        for code, label in PHOTIC_STAGE_LABELS.items():
            row[f"original_{label}_n"] = int(original_counts[code])
            row[f"recovered_{label}_n"] = int(recovered_counts[code])
            row[f"has_original_{label}"] = bool(original_counts[code] > 0)
            row[f"has_recovered_{label}"] = bool(recovered_counts[code] > 0)
        for code, label in EYE_STAGE_LABELS.items():
            row[f"original_{label}_n"] = int(eye_counts[code])
        subject_rows.append(row)

        for block in blocks:
            block_rows.append(asdict(block))

        for left, right in zip(blocks, blocks[1:], strict=False):
            gap_rows.append(
                {
                    "subject_id": subject_id,
                    "from_stage_label": left.stage_label,
                    "to_stage_label": right.stage_label,
                    "gap_windows": int(right.onset_idx - left.onset_idx),
                    "gap_seconds": float(right.onset_time_sec - left.onset_time_sec),
                    "from_h5_path": str(h5_path),
                }
            )

    subject_frame = pd.DataFrame(subject_rows).sort_values("subject_id").reset_index(drop=True)
    block_frame = pd.DataFrame(block_rows).sort_values(["subject_id", "onset_idx"]).reset_index(drop=True)
    gap_frame = pd.DataFrame(gap_rows).sort_values(["subject_id", "gap_windows"]).reset_index(drop=True)

    summary_rows: list[dict[str, object]] = []
    if not subject_frame.empty:
        summary_rows.append(
            {
                "stage_label": "all_photic",
                "stage_code": "all",
                "subjects_with_original_markers": int(subject_frame["has_any_photic_marker"].sum()),
                "subjects_with_recovered_windows": int(subject_frame["has_any_recovered_photic"].sum()),
                "total_original_markers": int(subject_frame["n_original_photic_markers"].sum()),
                "total_recovered_windows": int(subject_frame["n_recovered_photic_windows"].sum()),
                "median_recovered_windows_when_present": float(
                    subject_frame.loc[subject_frame["n_recovered_photic_windows"] > 0, "n_recovered_photic_windows"].median()
                ),
                "recovery_multiplier": float(
                    subject_frame["n_recovered_photic_windows"].sum()
                    / max(1, int(subject_frame["n_original_photic_markers"].sum()))
                ),
            }
        )
        for code, label in PHOTIC_STAGE_LABELS.items():
            recovered_col = f"recovered_{label}_n"
            original_col = f"original_{label}_n"
            present = subject_frame[subject_frame[recovered_col] > 0]
            summary_rows.append(
                {
                    "stage_label": label,
                    "stage_code": int(code),
                    "subjects_with_original_markers": int((subject_frame[original_col] > 0).sum()),
                    "subjects_with_recovered_windows": int((subject_frame[recovered_col] > 0).sum()),
                    "total_original_markers": int(subject_frame[original_col].sum()),
                    "total_recovered_windows": int(subject_frame[recovered_col].sum()),
                    "median_recovered_windows_when_present": float(present[recovered_col].median()) if not present.empty else float("nan"),
                    "recovery_multiplier": float(subject_frame[recovered_col].sum() / max(1, int(subject_frame[original_col].sum()))),
                }
            )

    summary_frame = pd.DataFrame(summary_rows)
    return subject_frame, block_frame, gap_frame, summary_frame


def write_stage_qc_outputs(
    raw_root: Path,
    results_root: Path,
    *,
    block_length_windows: int = DEFAULT_BLOCK_LENGTH_WINDOWS,
    duplicate_gap_windows: int = DEFAULT_DUPLICATE_GAP_WINDOWS,
) -> dict[str, str]:
    results_root.mkdir(parents=True, exist_ok=True)
    subject_frame, block_frame, gap_frame, summary_frame = build_stage_qc_tables(
        raw_root,
        block_length_windows=block_length_windows,
        duplicate_gap_windows=duplicate_gap_windows,
    )

    subject_path = results_root / "photic_stage_qc_subjects.csv"
    block_path = results_root / "photic_stage_recovered_blocks.csv"
    gap_path = results_root / "photic_stage_gap_audit.csv"
    summary_path = results_root / "photic_stage_qc_summary.csv"
    manifest_path = results_root / "photic_stage_qc_manifest.json"

    subject_frame.to_csv(subject_path, index=False)
    block_frame.to_csv(block_path, index=False)
    gap_frame.to_csv(gap_path, index=False)
    summary_frame.to_csv(summary_path, index=False)

    manifest = {
        "raw_root": str(raw_root),
        "results_root": str(results_root),
        "block_length_windows": int(block_length_windows),
        "duplicate_gap_windows": int(duplicate_gap_windows),
        "n_subjects": int(subject_frame["subject_id"].nunique()) if not subject_frame.empty else 0,
        "n_blocks": int(len(block_frame)),
        "output_files": {
            "photic_stage_qc_subjects": str(subject_path),
            "photic_stage_recovered_blocks": str(block_path),
            "photic_stage_gap_audit": str(gap_path),
            "photic_stage_qc_summary": str(summary_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "subject_path": str(subject_path),
        "block_path": str(block_path),
        "gap_path": str(gap_path),
        "summary_path": str(summary_path),
        "manifest_path": str(manifest_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover photic block labels and write QC tables for ds006036.")
    repo_root = Path(__file__).resolve().parents[4]
    article_dir = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=repo_root / "data" / "raw" / "neuralmanifolddynamics_ds006036_20260604_132747",
    )
    parser.add_argument("--results-root", type=Path, default=article_dir / "results")
    parser.add_argument("--block-length-windows", type=int, default=DEFAULT_BLOCK_LENGTH_WINDOWS)
    parser.add_argument("--duplicate-gap-windows", type=int, default=DEFAULT_DUPLICATE_GAP_WINDOWS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = write_stage_qc_outputs(
        args.raw_root,
        args.results_root,
        block_length_windows=args.block_length_windows,
        duplicate_gap_windows=args.duplicate_gap_windows,
    )
    print(f"Wrote subject QC to {outputs['subject_path']}")
    print(f"Wrote recovered blocks to {outputs['block_path']}")
    print(f"Wrote gap audit to {outputs['gap_path']}")
    print(f"Wrote summary QC to {outputs['summary_path']}")


if __name__ == "__main__":
    main()
