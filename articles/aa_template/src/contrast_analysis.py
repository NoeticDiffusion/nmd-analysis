"""Create configuration-driven descriptive contrasts from a long-format table.

The script does not choose an inferential estimator or qualify scientific
claims. It reports descriptive summaries and, for paired designs, preserves
the unit-level condition values and their B-minus-A differences.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


DEFAULT_CONFIG = Path(__file__).with_name("contrast_config.yaml")
REQUIRED_COLUMNS = {"unit_id", "condition", "measure", "value"}
SUMMARY_COLUMNS = [
    "analysis_id",
    "contrast_id",
    "design",
    "condition_a",
    "condition_b",
    "difference_direction",
    "measure",
    "support_status",
    "n_units_a",
    "n_units_b",
    "n_finite_a",
    "n_finite_b",
    "n_missing_value_a",
    "n_missing_value_b",
    "n_complete_pairs",
    "condition_a_mean_on_contrast_support",
    "condition_b_mean_on_contrast_support",
    "condition_a_median_on_contrast_support",
    "condition_b_median_on_contrast_support",
    "mean_difference_b_minus_a",
    "median_difference_b_minus_a",
    "inferential_status",
    "scientific_qualification",
]
PAIRED_COLUMNS = [
    "contrast_id",
    "measure",
    "unit_id",
    "condition_a",
    "condition_b",
    "condition_a_value",
    "condition_b_value",
    "difference_b_minus_a",
    "unit_status",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a YAML mapping")
    return value


def _required_text(mapping: dict[str, Any], key: str, name: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}.{key} must be a non-empty string")
    return value.strip()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    config = _mapping(config, "config")

    analysis = _mapping(config.get("analysis"), "analysis")
    analysis["id"] = _required_text(analysis, "id", "analysis")
    columns = _mapping(config.get("columns"), "columns")
    for key in REQUIRED_COLUMNS:
        columns[key] = _required_text(columns, key, "columns")
    if len(set(columns[key] for key in REQUIRED_COLUMNS)) != len(REQUIRED_COLUMNS):
        raise ValueError("columns must map to four distinct input column names")

    config["dataset_folderpath"] = _required_text(config, "dataset_folderpath", "config")
    config["input_file"] = _required_text(config, "input_file", "config")
    input_format = config.get("input_format", "auto")
    if not isinstance(input_format, str) or input_format not in {"auto", "csv", "parquet"}:
        raise ValueError("input_format must be one of: auto, csv, parquet")

    contrasts = config.get("contrasts")
    if not isinstance(contrasts, list) or not contrasts:
        raise ValueError("contrasts must contain at least one comparison")
    seen_ids: set[str] = set()
    for index, raw in enumerate(contrasts):
        contrast = _mapping(raw, f"contrasts[{index}]")
        contrast_id = _required_text(contrast, "id", f"contrasts[{index}]")
        condition_a = _required_text(contrast, "condition_a", f"contrasts[{index}]")
        condition_b = _required_text(contrast, "condition_b", f"contrasts[{index}]")
        contrast["id"] = contrast_id
        contrast["condition_a"] = condition_a
        contrast["condition_b"] = condition_b
        if contrast_id in seen_ids:
            raise ValueError(f"duplicate contrast id: {contrast_id}")
        seen_ids.add(contrast_id)
        design = contrast.get("design")
        if not isinstance(design, str) or design not in {"paired", "independent"}:
            raise ValueError(
                f"contrasts[{index}].design must be 'paired' or 'independent'"
            )
        if condition_a == condition_b:
            raise ValueError(f"contrast {contrast_id} compares a condition with itself")

    measures = config.get("measures", [])
    if not isinstance(measures, list) or any(
        not isinstance(item, str) or not item.strip() for item in measures
    ):
        raise ValueError("measures must be a list of strings (or an empty list)")
    config["measures"] = [item.strip() for item in measures]
    filters = config.get("filters", {})
    if not isinstance(filters, dict):
        raise ValueError("filters must be a YAML mapping")
    for column, value in filters.items():
        if not isinstance(column, str) or not column.strip():
            raise ValueError("filter column names must be non-empty strings")
        if isinstance(value, list) and not value:
            raise ValueError(f"filter {column!r} cannot use an empty list")

    outputs = _mapping(config.get("outputs"), "outputs")
    for key in ("folderpath", "summary_file", "paired_units_file", "manifest_file"):
        _required_text(outputs, key, "outputs")
    output_names = [
        _required_text(outputs, key, "outputs")
        for key in ("summary_file", "paired_units_file", "manifest_file")
    ]
    if len(output_names) != len(set(output_names)):
        raise ValueError("outputs file names must be distinct")
    return config


def _resolve_path(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def read_input(path: Path, input_format: str, columns: dict[str, str]) -> tuple[pd.DataFrame, str]:
    fmt = input_format
    if fmt == "auto":
        suffix = path.suffix.lower()
        if suffix == ".csv":
            fmt = "csv"
        elif suffix in {".parquet", ".pq"}:
            fmt = "parquet"
        else:
            raise ValueError(f"cannot infer input format from {path.name!r}; set input_format")

    if fmt == "csv":
        string_columns = {
            columns[key]: "string" for key in ("unit_id", "condition", "measure")
        }
        frame = pd.read_csv(path, dtype=string_columns)
    else:
        frame = pd.read_parquet(path)
    return frame, fmt


def _prepare_table(
    raw: pd.DataFrame,
    *,
    columns: dict[str, str],
    filters: dict[str, Any],
    requested_measures: list[str],
    allow_missing_requested_measures: bool = False,
    allow_empty_measures: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rename = {columns[key]: key for key in REQUIRED_COLUMNS}
    missing = set(rename).difference(raw.columns)
    if missing:
        raise ValueError(f"input table is missing configured columns: {sorted(missing)}")
    if len(rename) != len(REQUIRED_COLUMNS):
        raise ValueError("columns must map to four distinct input column names")

    frame = raw.rename(columns=rename).copy()
    source_rows = len(frame)

    filter_counts: dict[str, dict[str, int]] = {}
    for column, allowed in filters.items():
        target_column = rename.get(column, column)
        if target_column not in frame.columns:
            raise ValueError(f"configured filter column {column!r} is not in the input table")
        before = len(frame)
        if isinstance(allowed, list):
            frame = frame.loc[frame[target_column].isin(allowed)].copy()
        else:
            frame = frame.loc[frame[target_column].eq(allowed)].copy()
        filter_counts[column] = {"rows_before": before, "rows_after": len(frame)}

    for field in ("unit_id", "condition", "measure"):
        frame[field] = frame[field].astype("string").str.strip()
    missing_keys = frame[["unit_id", "condition", "measure"]].isna().any(axis=1)
    missing_keys |= frame[["unit_id", "condition", "measure"]].eq("").any(axis=1)
    if missing_keys.any():
        raise ValueError(
            f"{int(missing_keys.sum())} input rows have a missing unit, condition, or measure; "
            "resolve or explicitly filter them before contrasting"
        )

    original_values = frame["value"]
    numeric_values = pd.to_numeric(original_values, errors="coerce")
    nonnumeric = original_values.notna() & numeric_values.isna()
    if nonnumeric.any():
        examples = original_values.loc[nonnumeric].astype(str).drop_duplicates().head(5).tolist()
        raise ValueError(f"value column contains non-numeric values, examples: {examples}")
    finite = np.isfinite(numeric_values.to_numpy(dtype=float, na_value=np.nan))
    nonfinite_count = int((numeric_values.notna().to_numpy() & ~finite).sum())
    frame["value"] = numeric_values.where(finite, np.nan)

    if requested_measures:
        absent = set(requested_measures).difference(frame["measure"].astype(str).unique())
        if absent and not allow_missing_requested_measures:
            raise ValueError(f"configured measures not found after filtering: {sorted(absent)}")
        measures = requested_measures
    else:
        measures = sorted(frame["measure"].astype(str).unique().tolist())
    if not measures and not allow_empty_measures:
        raise ValueError("no measures remain after filtering")

    metadata = {
        "n_source_rows": source_rows,
        "n_rows_after_filters": int(len(frame)),
        "n_rows_with_nonfinite_value_after_filters": nonfinite_count,
        "n_rows_with_missing_or_nonfinite_value_after_filters": int(frame["value"].isna().sum()),
        "filter_counts": filter_counts,
        "measures": list(measures),
    }
    return frame, metadata


def _finite_stats(values: pd.Series) -> tuple[int, float, float]:
    finite_values = pd.to_numeric(values, errors="coerce").dropna().astype(float)
    finite_values = finite_values[np.isfinite(finite_values)]
    if finite_values.empty:
        return 0, float("nan"), float("nan")
    return int(len(finite_values)), float(finite_values.mean()), float(finite_values.median())


def _paired_units(
    a_rows: pd.DataFrame,
    b_rows: pd.DataFrame,
    *,
    contrast_id: str,
    condition_a: str,
    condition_b: str,
    measure: str,
) -> pd.DataFrame:
    a = a_rows.set_index("unit_id")["value"].rename("condition_a_value")
    b = b_rows.set_index("unit_id")["value"].rename("condition_b_value")
    units = pd.concat([a, b], axis=1, join="outer")
    units["has_a"] = units.index.isin(a.index)
    units["has_b"] = units.index.isin(b.index)
    units["difference_b_minus_a"] = units["condition_b_value"] - units["condition_a_value"]

    def status(row: pd.Series) -> str:
        if not row["has_a"]:
            return "missing_condition_a"
        if not row["has_b"]:
            return "missing_condition_b"
        if pd.isna(row["condition_a_value"]) and pd.isna(row["condition_b_value"]):
            return "missing_both_values"
        if pd.isna(row["condition_a_value"]):
            return "missing_condition_a_value"
        if pd.isna(row["condition_b_value"]):
            return "missing_condition_b_value"
        return "complete_pair"

    units["unit_status"] = units.apply(status, axis=1)
    units.index.name = "unit_id"
    result = units.reset_index()
    result.insert(0, "measure", measure)
    result.insert(0, "contrast_id", contrast_id)
    result["condition_a"] = condition_a
    result["condition_b"] = condition_b
    return result[PAIRED_COLUMNS]


def summarize_contrasts(
    frame: pd.DataFrame,
    *,
    analysis_id: str,
    contrasts: list[dict[str, Any]],
    measures: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, Any]] = []
    paired_frames: list[pd.DataFrame] = []

    for contrast in contrasts:
        contrast_id = str(contrast["id"])
        condition_a = str(contrast["condition_a"])
        condition_b = str(contrast["condition_b"])
        design = str(contrast["design"])
        contrast_frame = frame.loc[
            frame["condition"].isin([condition_a, condition_b])
            & frame["measure"].isin(measures)
        ].copy()
        observed = set(contrast_frame["condition"].astype(str).unique())
        absent = {condition_a, condition_b}.difference(observed)
        if absent:
            raise ValueError(
                f"contrast {contrast_id!r} has no rows for condition(s) {sorted(absent)} "
                "after filtering"
            )

        for measure in measures:
            selected = contrast_frame.loc[contrast_frame["measure"].eq(measure)]
            a_rows = selected.loc[selected["condition"].eq(condition_a)]
            b_rows = selected.loc[selected["condition"].eq(condition_b)]
            n_a, mean_a, median_a = _finite_stats(a_rows["value"])
            n_b, mean_b, median_b = _finite_stats(b_rows["value"])
            base: dict[str, Any] = {
                "analysis_id": analysis_id,
                "contrast_id": contrast_id,
                "design": design,
                "condition_a": condition_a,
                "condition_b": condition_b,
                "difference_direction": f"{condition_b} minus {condition_a}",
                "measure": measure,
                "n_units_a": int(len(a_rows)),
                "n_units_b": int(len(b_rows)),
                "n_finite_a": n_a,
                "n_finite_b": n_b,
                "n_missing_value_a": int(len(a_rows) - n_a),
                "n_missing_value_b": int(len(b_rows) - n_b),
                "n_complete_pairs": None,
                "inferential_status": "not_computed",
                "scientific_qualification": "not_assessed",
            }

            if design == "paired":
                units = _paired_units(
                    a_rows,
                    b_rows,
                    contrast_id=contrast_id,
                    condition_a=condition_a,
                    condition_b=condition_b,
                    measure=measure,
                )
                paired_frames.append(units)
                complete = units.loc[units["unit_status"].eq("complete_pair")]
                differences = pd.to_numeric(complete["difference_b_minus_a"], errors="coerce")
                complete_a = pd.to_numeric(complete["condition_a_value"], errors="coerce")
                complete_b = pd.to_numeric(complete["condition_b_value"], errors="coerce")
                n_pairs = int(len(complete))
                base.update(
                    {
                        "n_complete_pairs": n_pairs,
                        "condition_a_mean_on_contrast_support": float(complete_a.mean()) if n_pairs else float("nan"),
                        "condition_b_mean_on_contrast_support": float(complete_b.mean()) if n_pairs else float("nan"),
                        "condition_a_median_on_contrast_support": float(complete_a.median()) if n_pairs else float("nan"),
                        "condition_b_median_on_contrast_support": float(complete_b.median()) if n_pairs else float("nan"),
                        "mean_difference_b_minus_a": float(differences.mean()) if n_pairs else float("nan"),
                        "median_difference_b_minus_a": float(differences.median()) if n_pairs else float("nan"),
                        "support_status": "available" if n_pairs else "no_complete_pairs",
                    }
                )
            else:
                has_both_groups = n_a > 0 and n_b > 0
                base.update(
                    {
                        "condition_a_mean_on_contrast_support": mean_a if has_both_groups else float("nan"),
                        "condition_b_mean_on_contrast_support": mean_b if has_both_groups else float("nan"),
                        "condition_a_median_on_contrast_support": median_a if has_both_groups else float("nan"),
                        "condition_b_median_on_contrast_support": median_b if has_both_groups else float("nan"),
                        "mean_difference_b_minus_a": mean_b - mean_a if has_both_groups else float("nan"),
                        "median_difference_b_minus_a": median_b - median_a if has_both_groups else float("nan"),
                        "support_status": "available" if has_both_groups else "no_finite_values_in_one_or_both_groups",
                    }
                )
            summary_rows.append(base)

    summary = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)
    paired = pd.concat(paired_frames, ignore_index=True) if paired_frames else pd.DataFrame(columns=PAIRED_COLUMNS)
    return summary, paired


def run(config_path: Path, *, overwrite: bool = False) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = load_config(config_path)
    base = config_path.parent
    analysis = config["analysis"]
    columns = config["columns"]
    outputs = config["outputs"]

    dataset_root = _resolve_path(base, config["dataset_folderpath"])
    input_path = _resolve_path(dataset_root, config["input_file"])
    if not input_path.is_file():
        raise FileNotFoundError(f"configured input file does not exist: {input_path}")
    raw, input_format = read_input(input_path, config["input_format"], columns)
    frame, table_metadata = _prepare_table(
        raw,
        columns=columns,
        filters=config.get("filters", {}),
        requested_measures=config.get("measures", []),
    )

    contrast_conditions = {
        str(condition)
        for contrast in config["contrasts"]
        for condition in (contrast["condition_a"], contrast["condition_b"])
    }
    selected = frame.loc[
        frame["condition"].isin(contrast_conditions)
        & frame["measure"].isin(table_metadata["measures"])
    ].copy()
    if config.get("measures"):
        missing_measures = set(config["measures"]).difference(
            selected["measure"].astype(str).unique()
        )
        if missing_measures:
            raise ValueError(
                "configured measures have no rows in the contrasted conditions: "
                f"{sorted(missing_measures)}"
            )
        measures = list(config["measures"])
    else:
        measures = sorted(selected["measure"].astype(str).unique().tolist())
        if not measures:
            raise ValueError("no measures remain in the configured contrast conditions")
    table_metadata["measures"] = measures
    selected = selected.loc[selected["measure"].isin(measures)].copy()
    duplicate_keys = ["unit_id", "condition", "measure"]
    duplicate_rows = selected.duplicated(duplicate_keys, keep=False)
    if duplicate_rows.any():
        example = selected.loc[duplicate_rows, duplicate_keys].head(5).to_dict("records")
        raise ValueError(
            "input must have one row per unit, condition, and measure; repeated rows need a "
            f"study-specific, predeclared reduction before contrasts. Examples: {example}"
        )

    summary, paired_units = summarize_contrasts(
        selected,
        analysis_id=str(analysis["id"]),
        contrasts=config["contrasts"],
        measures=measures,
    )

    output_root = _resolve_path(base, outputs["folderpath"])
    output_paths = {
        "summary": output_root / outputs["summary_file"],
        "paired_units": output_root / outputs["paired_units_file"],
        "manifest": output_root / outputs["manifest_file"],
    }
    existing = [path for path in output_paths.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "one or more output files already exist; choose a fresh outputs.folderpath or pass --overwrite: "
            + ", ".join(str(path) for path in existing)
        )

    output_root.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_paths["summary"], index=False)
    paired_units.to_csv(output_paths["paired_units"], index=False)
    manifest = {
        "schema": "nmd_article_template.contrast_analysis.v1",
        "analysis_id": str(analysis["id"]),
        "description": analysis.get("description", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "computed_unqualified",
        "scientific_qualification": "not_assessed",
        "inferential_status": "not_computed",
        "estimation_note": (
            "Descriptive summaries only. No p-values, confidence intervals, estimator selection, "
            "or biological interpretation are produced by this template."
        ),
        "contrast_definitions": config["contrasts"],
        "filters": config.get("filters", {}),
        "input": {
            "path": str(input_path),
            "sha256": sha256_file(input_path),
            "format": input_format,
            "dataset_folderpath": str(dataset_root),
            "n_source_rows": table_metadata["n_source_rows"],
            "n_rows_after_filters": table_metadata["n_rows_after_filters"],
            "n_rows_with_nonfinite_value_after_filters": table_metadata[
                "n_rows_with_nonfinite_value_after_filters"
            ],
            "n_rows_with_missing_or_nonfinite_value_after_filters": table_metadata[
                "n_rows_with_missing_or_nonfinite_value_after_filters"
            ],
            "n_rows_in_configured_conditions_and_measures": int(len(selected)),
        },
        "measures": table_metadata["measures"],
        "outputs": {key: str(path) for key, path in output_paths.items()},
        "n_summary_rows": int(len(summary)),
        "n_paired_unit_rows": int(len(paired_units)),
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "script_path": str(Path(__file__).resolve()),
        "script_sha256": sha256_file(Path(__file__).resolve()),
    }
    output_paths["manifest"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite configured output files if they already exist",
    )
    args = parser.parse_args(argv)
    manifest = run(args.config, overwrite=args.overwrite)
    print(
        json.dumps(
            {
                "analysis_id": manifest["analysis_id"],
                "n_summary_rows": manifest["n_summary_rows"],
                "n_paired_unit_rows": manifest["n_paired_unit_rows"],
                "claim_status": manifest["claim_status"],
                "outputs": manifest["outputs"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
