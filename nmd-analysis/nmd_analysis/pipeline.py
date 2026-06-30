from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import h5py

from .adapters import AnalysisAdapter, build_adapters
from .config import DatasetConfig, load_dataset_config
from .io_tables import write_parquet_table
from .naming import build_output_filename

_WORKER_ADAPTERS: Dict[str, AnalysisAdapter] = {}


def _discover_h5_files(input_root: Path) -> List[Path]:
    return sorted(input_root.rglob("*.h5"))


def _read_modality(h5_path: Path) -> Optional[str]:
    try:
        with h5py.File(h5_path, "r") as handle:
            modality = handle.attrs.get("modality")
            if modality is None:
                return None
            if isinstance(modality, (bytes, bytearray)):
                return bytes(modality).decode("utf-8", errors="ignore")
            return str(modality)
    except Exception:
        return None


def _should_skip_for_modality(
    analysis_type: str,
    modality: Optional[str],
    cfg: DatasetConfig,
) -> bool:
    if modality is None:
        return False
    rules = cfg.modality_rules or {}
    modality_cfg = rules.get(str(modality).lower()) or {}
    if not isinstance(modality_cfg, dict):
        return False
    force_disable = modality_cfg.get("force_disable") or []
    if not isinstance(force_disable, list):
        return False
    return analysis_type in {str(item) for item in force_disable}


def _resolve_workers(cli_workers: Optional[int], cfg: DatasetConfig) -> int:
    if cli_workers is not None and cli_workers > 0:
        return int(cli_workers)
    if cfg.runtime.workers is not None and cfg.runtime.workers > 0:
        return int(cfg.runtime.workers)
    cpu_count = os.cpu_count() or 2
    return max(1, cpu_count - 1)


def _init_worker(config_path: str) -> None:
    # Prevent nested thread explosions in NumPy/scikit-learn per process.
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    global _WORKER_ADAPTERS
    _WORKER_ADAPTERS = build_adapters(Path(config_path))


def _collect_rows_worker(analysis_type: str, h5_path: str) -> List[Dict[str, Any]]:
    adapter = _WORKER_ADAPTERS.get(analysis_type)
    if adapter is None:
        raise ValueError(f"No adapter available for analysis_type={analysis_type}")
    rows = adapter.collect_rows(Path(h5_path))
    for row in rows:
        row["analysis_type"] = analysis_type
    return rows


def run_dataset_pipeline(
    config_path: str | Path,
    input_root: str | Path | None = None,
    output_root: str | Path | None = None,
    analyses_filter: Optional[Sequence[str]] = None,
    workers: Optional[int] = None,
) -> Dict[str, Any]:
    config_file = Path(config_path)
    cfg = load_dataset_config(config_file)
    adapters = build_adapters(config_file)
    n_workers = _resolve_workers(workers, cfg)

    resolved_input = Path(input_root) if input_root else Path(cfg.h5_root or "")
    if not str(resolved_input):
        raise ValueError("No input root provided. Set input.h5_root in config or pass --input-root.")
    if not resolved_input.exists():
        if cfg.runtime.fail_on_missing_input:
            raise FileNotFoundError(f"Input root does not exist: {resolved_input}")
        return {"dataset": cfg.dataset, "written_files": {}, "skipped": ["missing_input_root"]}

    h5_files = _discover_h5_files(resolved_input)
    if not h5_files:
        if cfg.runtime.fail_on_missing_input:
            raise FileNotFoundError(f"No .h5 files found under: {resolved_input}")
        return {"dataset": cfg.dataset, "written_files": {}, "skipped": ["no_h5_files"]}

    out_root = Path(output_root) if output_root else Path(cfg.output.directory)
    out_root.mkdir(parents=True, exist_ok=True)

    written_files: Dict[str, str] = {}
    skipped: List[str] = []
    errors: List[str] = []

    allowed = {str(a).strip() for a in (analyses_filter or []) if str(a).strip()}
    modality_by_file = {h5_path: _read_modality(h5_path) for h5_path in h5_files}

    for analysis_type, enabled in cfg.analyses.items():
        if allowed and analysis_type not in allowed:
            skipped.append(f"{analysis_type}:filtered_out")
            continue
        if not enabled and cfg.runtime.skip_disabled_analyses:
            skipped.append(analysis_type)
            continue
        adapter = adapters.get(analysis_type)
        if adapter is None:
            errors.append(f"{analysis_type}: no adapter available")
            if not cfg.runtime.continue_on_analysis_error:
                raise ValueError(errors[-1])
            continue

        candidate_files = [
            h5_path
            for h5_path in h5_files
            if not _should_skip_for_modality(analysis_type, modality_by_file.get(h5_path), cfg)
        ]
        if not candidate_files:
            skipped.append(f"{analysis_type}:no_candidate_files")
            continue

        rows: List[Dict[str, Any]] = []
        if n_workers <= 1:
            for idx, h5_path in enumerate(candidate_files, start=1):
                try:
                    file_rows = adapter.collect_rows(h5_path)
                    for row in file_rows:
                        row["analysis_type"] = analysis_type
                    rows.extend(file_rows)
                except Exception as exc:  # noqa: BLE001
                    msg = f"{analysis_type}:{h5_path} -> {exc}"
                    errors.append(msg)
                    if not cfg.runtime.continue_on_analysis_error:
                        raise RuntimeError(msg) from exc
                if idx % 50 == 0 or idx == len(candidate_files):
                    print(
                        f"[nmd-analysis] {analysis_type}: processed {idx}/{len(candidate_files)} H5 files"
                    )
        else:
            with ProcessPoolExecutor(
                max_workers=n_workers,
                initializer=_init_worker,
                initargs=(str(config_file),),
            ) as executor:
                futures = {
                    executor.submit(_collect_rows_worker, analysis_type, str(h5_path)): h5_path
                    for h5_path in candidate_files
                }
                processed = 0
                total = len(candidate_files)
                for future in as_completed(futures):
                    h5_path = futures[future]
                    processed += 1
                    try:
                        rows.extend(future.result())
                    except Exception as exc:  # noqa: BLE001
                        msg = f"{analysis_type}:{h5_path} -> {exc}"
                        errors.append(msg)
                        if not cfg.runtime.continue_on_analysis_error:
                            raise RuntimeError(msg) from exc
                    if processed % 50 == 0 or processed == total:
                        print(
                            f"[nmd-analysis] {analysis_type}: processed {processed}/{total} H5 files"
                        )

        if not rows:
            skipped.append(f"{analysis_type}:no_rows")
            continue

        output_name = build_output_filename(
            dataset=cfg.dataset,
            analysis_type=analysis_type,
            pattern=cfg.output.filename_pattern,
            timestamp_format=cfg.output.timestamp_format,
        )
        out_path = out_root / output_name
        write_parquet_table(
            rows=rows,
            output_path=out_path,
            compression=cfg.output.parquet_compression,
            index=cfg.output.parquet_index,
        )
        written_files[analysis_type] = str(out_path)

    return {
        "dataset": cfg.dataset,
        "input_root": str(resolved_input),
        "n_h5_files": len(h5_files),
        "workers": n_workers,
        "written_files": written_files,
        "skipped": skipped,
        "errors": errors,
    }
