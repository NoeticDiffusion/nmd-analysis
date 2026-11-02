"""Audit expected unit-condition-measure coverage for an article contrast."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from contrast_analysis import (
    DEFAULT_CONFIG,
    _prepare_table,
    _resolve_path,
    load_config,
    read_input,
    sha256_file,
)


CELL_KEYS = ["contrast_id", "unit_id", "condition", "measure"]
ISSUE_COLUMNS = CELL_KEYS + ["n_observed_rows", "n_finite_values", "coverage_status"]
UNEXPECTED_COLUMNS = CELL_KEYS + ["n_observed_rows", "n_finite_values", "coverage_status"]


def _coverage_options(config: dict[str, Any]) -> dict[str, Any]:
    options = config.get("coverage", {})
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise ValueError("coverage must be a YAML mapping")
    inventory_file = options.get("expected_inventory_file")
    if inventory_file is not None and (
        not isinstance(inventory_file, str) or not inventory_file.strip()
    ):
        raise ValueError("coverage.expected_inventory_file must be a path or null")
    inventory_format = options.get("inventory_format", "auto")
    if not isinstance(inventory_format, str) or inventory_format not in {
        "auto",
        "csv",
        "parquet",
    }:
        raise ValueError("coverage.inventory_format must be auto, csv, or parquet")
    names = {
        "summary_file": options.get("summary_file", "coverage_summary.csv"),
        "issues_file": options.get("issues_file", "coverage_issues.csv"),
        "unexpected_file": options.get("unexpected_file", "coverage_unexpected.csv"),
        "manifest_file": options.get("manifest_file", "coverage_manifest.json"),
    }
    if any(not isinstance(name, str) or not name.strip() for name in names.values()):
        raise ValueError("coverage output file names must be non-empty strings")
    if len(set(names.values())) != len(names):
        raise ValueError("coverage output file names must be distinct")
    return {
        **options,
        "expected_inventory_file": inventory_file.strip() if inventory_file else None,
        "inventory_format": inventory_format,
        **names,
    }


def _read_inventory(
    path: Path,
    input_format: str,
    columns: dict[str, str],
) -> tuple[pd.DataFrame, str, bool]:
    fmt = input_format
    if fmt == "auto":
        suffix = path.suffix.lower()
        if suffix == ".csv":
            fmt = "csv"
        elif suffix in {".parquet", ".pq"}:
            fmt = "parquet"
        else:
            raise ValueError(f"cannot infer inventory format from {path.name!r}")

    if fmt == "csv":
        header = pd.read_csv(path, nrows=0).columns
        string_columns = {
            columns[key]: "string"
            for key in ("unit_id", "condition", "measure")
            if columns[key] in header
        }
        raw = pd.read_csv(path, dtype=string_columns)
    else:
        raw = pd.read_parquet(path)

    source_unit = columns["unit_id"]
    source_condition = columns["condition"]
    source_measure = columns["measure"]
    missing = {source_unit, source_condition}.difference(raw.columns)
    if missing:
        raise ValueError(
            "expected inventory must contain the configured unit and condition columns: "
            f"{sorted(missing)}"
        )
    has_measure = source_measure in raw.columns
    rename = {source_unit: "unit_id", source_condition: "condition"}
    if has_measure:
        rename[source_measure] = "measure"
    inventory = raw.rename(columns=rename).copy()
    for field in ("unit_id", "condition"):
        inventory[field] = inventory[field].astype("string").str.strip()
    missing_keys = inventory[["unit_id", "condition"]].isna().any(axis=1)
    missing_keys |= inventory[["unit_id", "condition"]].eq("").any(axis=1)
    if missing_keys.any():
        raise ValueError(
            f"expected inventory has {int(missing_keys.sum())} rows without a unit or condition"
        )
    if has_measure:
        inventory["measure"] = inventory["measure"].astype("string").str.strip()
        missing_measure = inventory["measure"].isna() | inventory["measure"].eq("")
        if missing_measure.any():
            raise ValueError("expected inventory has rows with a missing measure")
    return inventory, fmt, has_measure


def _expected_cells(
    *,
    contrasts: list[dict[str, Any]],
    measures: list[str],
    observed: pd.DataFrame,
    inventory: pd.DataFrame | None,
    inventory_has_measure: bool,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for contrast in contrasts:
        contrast_id = str(contrast["id"])
        conditions = [str(contrast["condition_a"]), str(contrast["condition_b"])]
        design = str(contrast["design"])

        if inventory is not None:
            assignments = inventory.loc[inventory["condition"].isin(conditions)]
            rows: list[dict[str, str]] = []
            for item in assignments.itertuples(index=False):
                condition = str(item.condition)
                unit_id = str(item.unit_id)
                if inventory_has_measure:
                    measure = str(item.measure)
                    if measure in measures:
                        rows.append(
                            {
                                "contrast_id": contrast_id,
                                "unit_id": unit_id,
                                "condition": condition,
                                "measure": measure,
                            }
                        )
                else:
                    rows.extend(
                        {
                            "contrast_id": contrast_id,
                            "unit_id": unit_id,
                            "condition": condition,
                            "measure": measure,
                        }
                        for measure in measures
                    )
            frames.append(pd.DataFrame(rows, columns=CELL_KEYS))
            continue

        in_scope = observed.loc[observed["condition"].isin(conditions)]
        if design == "paired":
            units = in_scope["unit_id"].drop_duplicates().astype(str).tolist()
            rows = [
                {
                    "contrast_id": contrast_id,
                    "unit_id": unit_id,
                    "condition": condition,
                    "measure": measure,
                }
                for unit_id in units
                for condition in conditions
                for measure in measures
            ]
        else:
            assignments = in_scope[["unit_id", "condition"]].drop_duplicates()
            rows = [
                {
                    "contrast_id": contrast_id,
                    "unit_id": str(item.unit_id),
                    "condition": str(item.condition),
                    "measure": measure,
                }
                for item in assignments.itertuples(index=False)
                for measure in measures
            ]
        frames.append(pd.DataFrame(rows, columns=CELL_KEYS))

    expected = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=CELL_KEYS)
    duplicates = expected.duplicated(CELL_KEYS, keep=False)
    if duplicates.any():
        example = expected.loc[duplicates, CELL_KEYS].head(5).to_dict("records")
        raise ValueError(f"expected inventory repeats coverage keys; examples: {example}")
    return expected


def _observed_cells(
    frame: pd.DataFrame,
    contrasts: list[dict[str, Any]],
    measures: list[str],
) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    for contrast in contrasts:
        conditions = [str(contrast["condition_a"]), str(contrast["condition_b"])]
        rows = frame.loc[
            frame["condition"].isin(conditions) & frame["measure"].isin(measures),
            ["unit_id", "condition", "measure", "value"],
        ].copy()
        rows.insert(0, "contrast_id", str(contrast["id"]))
        rows["is_finite"] = np.isfinite(pd.to_numeric(rows["value"], errors="coerce"))
        grouped = (
            rows.groupby(CELL_KEYS, dropna=False)
            .agg(n_observed_rows=("value", "size"), n_finite_values=("is_finite", "sum"))
            .reset_index()
        )
        pieces.append(grouped)
    if not pieces:
        return pd.DataFrame(columns=CELL_KEYS + ["n_observed_rows", "n_finite_values"])
    return pd.concat(pieces, ignore_index=True)


def _coverage_table(expected: pd.DataFrame, observed: pd.DataFrame) -> pd.DataFrame:
    table = expected.merge(observed, on=CELL_KEYS, how="left")
    for column in ("n_observed_rows", "n_finite_values"):
        table[column] = table[column].fillna(0).astype(int)
    conditions = [
        table["n_observed_rows"].eq(0),
        table["n_observed_rows"].gt(1),
        table["n_finite_values"].eq(0),
    ]
    table["coverage_status"] = np.select(
        conditions,
        ["missing_row", "duplicate_rows", "missing_value"],
        default="present",
    )
    return table


def _summarize_coverage(
    table: pd.DataFrame,
    unexpected: pd.DataFrame,
    contrasts: list[dict[str, Any]],
    measures: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for contrast in contrasts:
        contrast_id = str(contrast["id"])
        for condition in (str(contrast["condition_a"]), str(contrast["condition_b"])):
            for measure in measures:
                cells = table.loc[
                    table["contrast_id"].eq(contrast_id)
                    & table["condition"].eq(condition)
                    & table["measure"].eq(measure)
                ]
                extra = unexpected.loc[
                    unexpected["contrast_id"].eq(contrast_id)
                    & unexpected["condition"].eq(condition)
                    & unexpected["measure"].eq(measure)
                ]
                n_expected = int(len(cells))
                n_present = int(cells["coverage_status"].eq("present").sum())
                if n_expected == 0:
                    status = "no_expected_assignments"
                    fraction = float("nan")
                else:
                    status = "complete" if n_present == n_expected else "incomplete"
                    fraction = float(n_present / n_expected)
                rows.append(
                    {
                        "contrast_id": contrast_id,
                        "design": str(contrast["design"]),
                        "condition": condition,
                        "measure": measure,
                        "n_expected_cells": n_expected,
                        "n_present_cells": n_present,
                        "n_missing_rows": int(cells["coverage_status"].eq("missing_row").sum()),
                        "n_cells_with_no_finite_value": int(
                            (cells["n_observed_rows"].gt(0) & cells["n_finite_values"].eq(0)).sum()
                        ),
                        "n_cells_with_any_missing_value_row": int(
                            cells["n_observed_rows"].gt(cells["n_finite_values"]).sum()
                        ),
                        "n_duplicate_cells": int(cells["coverage_status"].eq("duplicate_rows").sum()),
                        "n_unexpected_cells": int(len(extra)),
                        "coverage_fraction": fraction,
                        "coverage_status": status,
                    }
                )
    return pd.DataFrame(rows)


def run(config_path: Path, *, overwrite: bool = False) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = load_config(config_path)
    coverage_options = _coverage_options(config)
    base = config_path.parent
    columns = config["columns"]
    dataset_root = _resolve_path(base, config["dataset_folderpath"])
    input_path = _resolve_path(dataset_root, config["input_file"])
    if not input_path.is_file():
        raise FileNotFoundError(f"configured input file does not exist: {input_path}")
    raw, input_format = read_input(input_path, config["input_format"], columns)

    inventory_path = None
    inventory = None
    inventory_has_measure = False
    inventory_format = None
    if coverage_options["expected_inventory_file"]:
        inventory_path = _resolve_path(base, coverage_options["expected_inventory_file"])
        if not inventory_path.is_file():
            raise FileNotFoundError(f"expected inventory file does not exist: {inventory_path}")
        inventory, inventory_format, inventory_has_measure = _read_inventory(
            inventory_path,
            coverage_options["inventory_format"],
            columns,
        )

    frame, table_metadata = _prepare_table(
        raw,
        columns=columns,
        filters=config.get("filters", {}),
        requested_measures=config.get("measures", []),
        allow_missing_requested_measures=True,
        allow_empty_measures=True,
    )
    conditions = {
        str(condition)
        for contrast in config["contrasts"]
        for condition in (contrast["condition_a"], contrast["condition_b"])
    }
    observed_scope = frame.loc[frame["condition"].isin(conditions)]
    if config["measures"]:
        measures = list(config["measures"])
    else:
        measures = sorted(observed_scope["measure"].astype(str).unique().tolist())
        if inventory is not None and inventory_has_measure:
            inventory_measures = inventory.loc[
                inventory["condition"].isin(conditions), "measure"
            ].astype(str).unique().tolist()
            measures = sorted(set(measures).union(inventory_measures))
        if not measures:
            raise ValueError(
                "coverage cannot infer expected measures; list them in config.measures "
                "or include the configured measure column in the expected inventory"
            )

    selected = observed_scope.loc[observed_scope["measure"].isin(measures)].copy()
    expected = _expected_cells(
        contrasts=config["contrasts"],
        measures=measures,
        observed=selected,
        inventory=inventory,
        inventory_has_measure=inventory_has_measure,
    )
    observed_cells = _observed_cells(selected, config["contrasts"], measures)
    for key in CELL_KEYS:
        expected[key] = expected[key].astype(str)
        observed_cells[key] = observed_cells[key].astype(str)
    table = _coverage_table(expected, observed_cells)
    issues = table.loc[table["coverage_status"].ne("present"), ISSUE_COLUMNS].copy()
    expected_keys = expected[CELL_KEYS]
    unexpected = observed_cells.merge(
        expected_keys,
        on=CELL_KEYS,
        how="left",
        indicator=True,
    )
    unexpected = unexpected.loc[unexpected["_merge"].eq("left_only")].drop(columns="_merge")
    unexpected["coverage_status"] = "unexpected_cell"
    unexpected = unexpected.reindex(columns=UNEXPECTED_COLUMNS)
    summary = _summarize_coverage(table, unexpected, config["contrasts"], measures)

    inferred_support_complete = bool(
        not summary.empty
        and summary["coverage_status"].eq("complete").all()
        and unexpected.empty
    )
    complete = bool(inventory is not None and inferred_support_complete)
    if complete:
        coverage_status = "complete_against_inventory"
    elif inventory is None and inferred_support_complete:
        coverage_status = "inferred_support_complete_inventory_missing"
    else:
        coverage_status = "incomplete"
    outputs = config["outputs"]
    output_root = _resolve_path(base, outputs["folderpath"])
    paths = {
        "summary": output_root / coverage_options["summary_file"],
        "issues": output_root / coverage_options["issues_file"],
        "unexpected": output_root / coverage_options["unexpected_file"],
        "manifest": output_root / coverage_options["manifest_file"],
    }
    collisions = set(path.name for path in paths.values()).intersection(
        {
            outputs["summary_file"],
            outputs["paired_units_file"],
            outputs["manifest_file"],
        }
    )
    if collisions:
        raise ValueError(f"coverage output names collide with contrast outputs: {sorted(collisions)}")
    existing = [path for path in paths.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "coverage output files already exist; choose new names or pass --overwrite: "
            + ", ".join(str(path) for path in existing)
        )

    output_root.mkdir(parents=True, exist_ok=True)
    summary.to_csv(paths["summary"], index=False)
    issues.to_csv(paths["issues"], index=False)
    unexpected.to_csv(paths["unexpected"], index=False)
    manifest = {
        "schema": "nmd_article_template.coverage_audit.v1",
        "analysis_id": str(config["analysis"]["id"]),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "coverage_complete": complete,
        "coverage_status": coverage_status,
        "inferred_support_complete": inferred_support_complete,
        "expected_assignment_source": (
            "configured_inventory" if inventory is not None else "inferred_from_observed_data"
        ),
        "inventory_limitation": (
            "Without an expected inventory, wholly absent units cannot be detected. Paired "
            "contrasts infer both condition assignments for each observed unit; independent "
            "contrasts can audit only observed unit-condition assignments."
            if inventory is None
            else "The configured inventory is treated as the complete expected unit-condition roster."
        ),
        "inventory_filter_note": (
            "The expected inventory must already reflect the cohort/session filters in the analysis config."
            if inventory is not None
            else None
        ),
        "input": {
            "path": str(input_path),
            "sha256": sha256_file(input_path),
            "format": input_format,
            "n_source_rows": table_metadata["n_source_rows"],
            "n_rows_after_filters": table_metadata["n_rows_after_filters"],
        },
        "expected_inventory": (
            {
                "path": str(inventory_path),
                "sha256": sha256_file(inventory_path),
                "format": inventory_format,
                "n_rows": int(len(inventory)),
                "has_measure_column": inventory_has_measure,
            }
            if inventory_path is not None and inventory is not None
            else None
        ),
        "contrasts": config["contrasts"],
        "measures": measures,
        "filters": config.get("filters", {}),
        "n_expected_cells": int(len(expected)),
        "n_present_cells": int(table["coverage_status"].eq("present").sum()),
        "n_issue_cells": int(len(issues)),
        "n_unexpected_cells": int(len(unexpected)),
        "outputs": {key: str(path) for key, path in paths.items()},
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "script_path": str(Path(__file__).resolve()),
        "script_sha256": sha256_file(Path(__file__).resolve()),
    }
    paths["manifest"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False, default=str) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--fail-on-incomplete",
        action="store_true",
        help="return exit status 1 after saving reports if any expected cell is missing, duplicated, or unexpected",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite configured coverage outputs if they already exist",
    )
    args = parser.parse_args(argv)
    manifest = run(args.config, overwrite=args.overwrite)
    print(
        json.dumps(
            {
                "analysis_id": manifest["analysis_id"],
                "coverage_complete": manifest["coverage_complete"],
                "coverage_status": manifest["coverage_status"],
                "n_expected_cells": manifest["n_expected_cells"],
                "n_issue_cells": manifest["n_issue_cells"],
                "n_unexpected_cells": manifest["n_unexpected_cells"],
                "outputs": manifest["outputs"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 1 if args.fail_on_incomplete and not manifest["coverage_complete"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
