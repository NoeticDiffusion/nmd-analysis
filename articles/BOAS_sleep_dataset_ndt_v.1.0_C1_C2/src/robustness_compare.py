"""Compare precomputed primary contrast results with sensitivity variants.

This is a descriptive comparison only. It does not create a sensitivity
variant, select an estimator, or decide whether an effect is scientifically
robust.
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


DEFAULT_CONFIG = Path(__file__).with_name("robustness_config.yaml")


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


def _text(mapping: dict[str, Any], key: str, name: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}.{key} must be a non-empty string")
    return value.strip()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = _mapping(yaml.safe_load(handle), "config")
    analysis = _mapping(config.get("analysis"), "analysis")
    analysis["id"] = _text(analysis, "id", "analysis")

    primary = _mapping(config.get("primary"), "primary")
    primary["id"] = _text(primary, "id", "primary")
    primary["file"] = _text(primary, "file", "primary")
    if primary.get("unit_support_file") is not None:
        primary["unit_support_file"] = _text(primary, "unit_support_file", "primary")

    variants = config.get("variants")
    if not isinstance(variants, list) or not variants:
        raise ValueError("variants must contain at least one sensitivity result table")
    seen: set[str] = {primary["id"]}
    for index, raw in enumerate(variants):
        variant = _mapping(raw, f"variants[{index}]")
        variant_id = _text(variant, "id", f"variants[{index}]")
        variant_file = _text(variant, "file", f"variants[{index}]")
        variant["id"] = variant_id
        variant["file"] = variant_file
        if variant.get("unit_support_file") is not None:
            variant["unit_support_file"] = _text(variant, "unit_support_file", f"variants[{index}]")
        if variant_id in seen:
            raise ValueError(f"variant id is duplicated or equals the primary id: {variant_id}")
        seen.add(variant_id)

    unit_support = config.get("unit_support")
    if unit_support is not None:
        unit_support = _mapping(unit_support, "unit_support")
        support_keys = unit_support.get("keys")
        if not isinstance(support_keys, list) or any(
            not isinstance(item, str) or not item.strip() for item in support_keys
        ):
            raise ValueError("unit_support.keys must be a list of column names")
        unit_support["keys"] = [item.strip() for item in support_keys]
        if not unit_support["keys"]:
            raise ValueError("unit_support.keys must identify the comparison unit rows")
        if len(set(unit_support["keys"])) != len(unit_support["keys"]):
            raise ValueError("unit_support.keys contains duplicate columns")
        unit_support["status_column"] = _text(unit_support, "status_column", "unit_support")
        if unit_support["status_column"] in unit_support["keys"]:
            raise ValueError("unit_support.status_column cannot also be one of its keys")
        included = unit_support.get("included_statuses")
        if not isinstance(included, list) or any(
            not isinstance(item, str) or not item.strip() for item in included
        ):
            raise ValueError("unit_support.included_statuses must be a non-empty list of statuses")
        unit_support["included_statuses"] = [item.strip() for item in included]
        if not unit_support["included_statuses"]:
            raise ValueError("unit_support.included_statuses must not be empty")
        if primary.get("unit_support_file") is None or any(
            variant.get("unit_support_file") is None for variant in variants
        ):
            raise ValueError(
                "unit_support requires unit_support_file paths for the primary and every variant"
            )
    elif primary.get("unit_support_file") is not None or any(
        variant.get("unit_support_file") is not None for variant in variants
    ):
        raise ValueError("configure unit_support keys and statuses when unit_support_file paths are used")

    for key in ("keys", "effect_columns", "support_columns"):
        value = config.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError(f"{key} must be a list of non-empty column names")
        config[key] = [item.strip() for item in value]
    if not config["keys"]:
        raise ValueError("keys must identify rows in both primary and variant tables")
    if not config["effect_columns"]:
        raise ValueError("effect_columns must include at least one precomputed contrast estimate")
    if not config["support_columns"]:
        raise ValueError("support_columns must include at least one support or coverage count")
    if len(set(config["keys"])) != len(config["keys"]):
        raise ValueError("keys contains duplicate column names")
    if len(set(config["effect_columns"])) != len(config["effect_columns"]):
        raise ValueError("effect_columns contains duplicate column names")
    if len(set(config["support_columns"])) != len(config["support_columns"]):
        raise ValueError("support_columns contains duplicate column names")
    if set(config["keys"]).intersection(config["effect_columns"] + config["support_columns"]):
        raise ValueError("keys cannot also be configured as effect or support columns")

    outputs = _mapping(config.get("outputs"), "outputs")
    for key in (
        "folderpath",
        "effects_file",
        "support_file",
        "join_audit_file",
        "manifest_file",
    ):
        outputs[key] = _text(outputs, key, "outputs")
    if unit_support is not None:
        outputs["unit_support_audit_file"] = _text(outputs, "unit_support_audit_file", "outputs")
    config["unit_support"] = unit_support
    output_keys = ["effects_file", "support_file", "join_audit_file", "manifest_file"]
    if unit_support is not None:
        output_keys.append("unit_support_audit_file")
    filenames = [outputs[key] for key in output_keys]
    if len(set(filenames)) != len(filenames):
        raise ValueError("robustness output filenames must be distinct")
    if any(Path(filename).name != filename for filename in filenames):
        raise ValueError("robustness output filenames must be file names; configure subfolders in folderpath")
    return config


def _resolve(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _read_result_table(
    path: Path,
    *,
    keys: list[str],
    numeric_columns: list[str],
    label: str,
) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        header = pd.read_csv(path, nrows=0).columns
        dtype = {key: "string" for key in keys if key in header}
        frame = pd.read_csv(path, dtype=dtype)
    elif suffix in {".parquet", ".pq"}:
        frame = pd.read_parquet(path)
    else:
        raise ValueError(f"{label} must be a CSV or Parquet file: {path}")
    if frame.empty:
        raise ValueError(f"{label} has no result rows: {path}")

    required = set(keys + numeric_columns)
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{label} is missing configured columns: {sorted(missing)}")
    for key in keys:
        frame[key] = frame[key].astype("string").str.strip()
        invalid_key = frame[key].isna() | frame[key].eq("")
        if invalid_key.any():
            raise ValueError(f"{label} has {int(invalid_key.sum())} rows with a missing key {key!r}")
    duplicated = frame.duplicated(keys, keep=False)
    if duplicated.any():
        example = frame.loc[duplicated, keys].head(5).to_dict("records")
        raise ValueError(f"{label} has duplicate configured keys; examples: {example}")

    for column in numeric_columns:
        source = frame[column]
        parsed = pd.to_numeric(source, errors="coerce")
        invalid = source.notna() & parsed.isna()
        if invalid.any():
            examples = source.loc[invalid].astype(str).drop_duplicates().head(5).tolist()
            raise ValueError(f"{label}.{column} has non-numeric values: {examples}")
        frame[column] = parsed
    return frame


def _finite_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    number = float(value)
    return number if np.isfinite(number) else None


def _join_tables(
    primary: pd.DataFrame,
    variant: pd.DataFrame,
    *,
    keys: list[str],
    columns: list[str],
) -> pd.DataFrame:
    left = primary[keys + columns].rename(columns={column: f"primary__{column}" for column in columns})
    right = variant[keys + columns].rename(columns={column: f"variant__{column}" for column in columns})
    joined = left.merge(right, on=keys, how="outer", indicator=True, validate="one_to_one")
    joined["row_status"] = joined["_merge"].map(
        {"both": "matched", "left_only": "missing_variant_row", "right_only": "missing_primary_row"}
    )
    return joined.drop(columns="_merge")


def _read_unit_support(
    path: Path,
    *,
    keys: list[str],
    status_column: str,
    label: str,
) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        header = pd.read_csv(path, nrows=0).columns
        dtype = {key: "string" for key in keys if key in header}
        frame = pd.read_csv(path, dtype=dtype)
    elif suffix in {".parquet", ".pq"}:
        frame = pd.read_parquet(path)
    else:
        raise ValueError(f"{label} unit-support table must be CSV or Parquet: {path}")

    required = set(keys + [status_column])
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{label} unit-support table is missing columns: {sorted(missing)}")
    for key in keys:
        frame[key] = frame[key].astype("string").str.strip()
        invalid_key = frame[key].isna() | frame[key].eq("")
        if invalid_key.any():
            raise ValueError(f"{label} unit-support table has missing key {key!r}")
    frame[status_column] = frame[status_column].astype("string").str.strip()
    if frame[status_column].isna().any() or frame[status_column].eq("").any():
        raise ValueError(f"{label} unit-support table has missing inclusion statuses")
    duplicated = frame.duplicated(keys, keep=False)
    if duplicated.any():
        example = frame.loc[duplicated, keys].head(5).to_dict("records")
        raise ValueError(f"{label} unit-support table has duplicate keys: {example}")
    return frame[keys + [status_column]]


def _compare_unit_support(
    primary: pd.DataFrame,
    variant: pd.DataFrame,
    *,
    keys: list[str],
    status_column: str,
    included_statuses: list[str],
) -> tuple[pd.DataFrame, dict[str, int]]:
    left = primary.rename(columns={status_column: "primary_unit_status"})
    right = variant.rename(columns={status_column: "variant_unit_status"})
    joined = left.merge(right, on=keys, how="outer", indicator=True, validate="one_to_one")
    joined["primary_row_present"] = joined["_merge"].ne("right_only")
    joined["variant_row_present"] = joined["_merge"].ne("left_only")
    joined["primary_included"] = joined["primary_unit_status"].isin(included_statuses)
    joined["variant_included"] = joined["variant_unit_status"].isin(included_statuses)

    def state(row: pd.Series) -> str:
        if row["primary_included"] and row["variant_included"]:
            return "common_included_unit"
        if row["primary_included"]:
            return "primary_only_included_unit"
        if row["variant_included"]:
            return "variant_only_included_unit"
        if not row["primary_row_present"]:
            return "variant_row_only_excluded"
        if not row["variant_row_present"]:
            return "primary_row_only_excluded"
        if row["primary_unit_status"] == row["variant_unit_status"]:
            return "same_excluded_status"
        return "excluded_status_changed"

    joined["support_state"] = joined.apply(state, axis=1)
    joined = joined.drop(columns="_merge")
    joined = joined[keys + [
        "primary_unit_status",
        "variant_unit_status",
        "primary_row_present",
        "variant_row_present",
        "primary_included",
        "variant_included",
        "support_state",
    ]]
    states = joined["support_state"]
    summary = {
        "n_primary_included_units": int(joined["primary_included"].sum()),
        "n_variant_included_units": int(joined["variant_included"].sum()),
        "n_common_included_units": int(states.eq("common_included_unit").sum()),
        "n_primary_only_included_units": int(states.eq("primary_only_included_unit").sum()),
        "n_variant_only_included_units": int(states.eq("variant_only_included_unit").sum()),
        "n_status_changes": int(states.eq("excluded_status_changed").sum()),
    }
    return joined, summary


def _effect_rows(
    joined: pd.DataFrame,
    *,
    keys: list[str],
    columns: list[str],
    primary_id: str,
    variant_id: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, item in joined.iterrows():
        base = {key: item[key] for key in keys}
        for column in columns:
            primary_value = _finite_float(item[f"primary__{column}"])
            variant_value = _finite_float(item[f"variant__{column}"])
            both_finite = primary_value is not None and variant_value is not None
            delta = variant_value - primary_value if both_finite else None
            relative = delta / abs(primary_value) if both_finite and primary_value != 0 else None
            same_sign = (
                bool(np.sign(primary_value) == np.sign(variant_value))
                if both_finite and primary_value != 0 and variant_value != 0
                else None
            )
            if item["row_status"] != "matched":
                status = item["row_status"]
            else:
                status = "available" if both_finite else "missing_or_nonfinite_effect"
            rows.append(
                {
                    **base,
                    "primary_id": primary_id,
                    "variant_id": variant_id,
                    "effect_column": column,
                    "primary_value": primary_value,
                    "variant_value": variant_value,
                    "delta_variant_minus_primary": delta,
                    "absolute_delta": abs(delta) if delta is not None else None,
                    "relative_delta_over_abs_primary": relative,
                    "same_nonzero_sign": same_sign,
                    "comparison_status": status,
                }
            )
    return rows


def _support_rows(
    joined: pd.DataFrame,
    *,
    keys: list[str],
    columns: list[str],
    primary_id: str,
    variant_id: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, item in joined.iterrows():
        base = {key: item[key] for key in keys}
        for column in columns:
            primary_value = _finite_float(item[f"primary__{column}"])
            variant_value = _finite_float(item[f"variant__{column}"])
            both_finite = primary_value is not None and variant_value is not None
            delta = variant_value - primary_value if both_finite else None
            ratio = variant_value / primary_value if both_finite and primary_value != 0 else None
            if item["row_status"] != "matched":
                status = item["row_status"]
            else:
                status = "available" if both_finite else "missing_or_nonfinite_support"
            rows.append(
                {
                    **base,
                    "primary_id": primary_id,
                    "variant_id": variant_id,
                    "support_column": column,
                    "primary_value": primary_value,
                    "variant_value": variant_value,
                    "delta_variant_minus_primary": delta,
                    "ratio_variant_over_primary": ratio,
                    "comparison_status": status,
                }
            )
    return rows


def run(config_path: Path, *, overwrite: bool = False) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = load_config(config_path)
    base = config_path.parent
    keys = config["keys"]
    effect_columns = config["effect_columns"]
    support_columns = config["support_columns"]
    numeric_columns = list(dict.fromkeys(effect_columns + support_columns))
    primary_path = _resolve(base, config["primary"]["file"])
    if not primary_path.is_file():
        raise FileNotFoundError(f"primary result table does not exist: {primary_path}")
    primary = _read_result_table(
        primary_path,
        keys=keys,
        numeric_columns=numeric_columns,
        label="primary",
    )

    effect_rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []
    join_rows: list[dict[str, Any]] = []
    unit_support_frames: list[pd.DataFrame] = []
    variant_manifest: list[dict[str, Any]] = []
    input_paths = [primary_path]
    unit_support_config = config["unit_support"]
    primary_unit_support = None
    primary_unit_support_path = None
    if unit_support_config is not None:
        primary_unit_support_path = _resolve(base, config["primary"]["unit_support_file"])
        if not primary_unit_support_path.is_file():
            raise FileNotFoundError(
                f"primary unit-support table does not exist: {primary_unit_support_path}"
            )
        primary_unit_support = _read_unit_support(
            primary_unit_support_path,
            keys=unit_support_config["keys"],
            status_column=unit_support_config["status_column"],
            label="primary",
        )
        input_paths.append(primary_unit_support_path)

    for variant_spec in config["variants"]:
        variant_path = _resolve(base, variant_spec["file"])
        if not variant_path.is_file():
            raise FileNotFoundError(f"variant result table does not exist: {variant_path}")
        variant = _read_result_table(
            variant_path,
            keys=keys,
            numeric_columns=numeric_columns,
            label=f"variant {variant_spec['id']!r}",
        )
        joined = _join_tables(
            primary,
            variant,
            keys=keys,
            columns=numeric_columns,
        )
        variant_id = str(variant_spec["id"])
        effect_rows.extend(
            _effect_rows(
                joined,
                keys=keys,
                columns=effect_columns,
                primary_id=str(config["primary"]["id"]),
                variant_id=variant_id,
            )
        )
        support_rows.extend(
            _support_rows(
                joined,
                keys=keys,
                columns=support_columns,
                primary_id=str(config["primary"]["id"]),
                variant_id=variant_id,
            )
        )
        join_rows.extend(
            {
                **{key: item[key] for key in keys},
                "primary_id": str(config["primary"]["id"]),
                "variant_id": variant_id,
                "row_status": item["row_status"],
            }
            for _, item in joined.iterrows()
        )
        variant_info = {
            "id": variant_id,
            "description": variant_spec.get("description", ""),
            "path": str(variant_path),
            "sha256": sha256_file(variant_path),
            "n_rows": int(len(variant)),
            "n_matched_keys": int(joined["row_status"].eq("matched").sum()),
            "n_missing_variant_rows": int(joined["row_status"].eq("missing_variant_row").sum()),
            "n_missing_primary_rows": int(joined["row_status"].eq("missing_primary_row").sum()),
        }
        if unit_support_config is not None:
            variant_unit_path = _resolve(base, variant_spec["unit_support_file"])
            if not variant_unit_path.is_file():
                raise FileNotFoundError(
                    f"variant {variant_id!r} unit-support table does not exist: {variant_unit_path}"
                )
            variant_unit_support = _read_unit_support(
                variant_unit_path,
                keys=unit_support_config["keys"],
                status_column=unit_support_config["status_column"],
                label=f"variant {variant_id!r}",
            )
            unit_audit, unit_summary = _compare_unit_support(
                primary_unit_support,
                variant_unit_support,
                keys=unit_support_config["keys"],
                status_column=unit_support_config["status_column"],
                included_statuses=unit_support_config["included_statuses"],
            )
            unit_audit.insert(0, "variant_id", variant_id)
            unit_audit.insert(0, "primary_id", str(config["primary"]["id"]))
            unit_support_frames.append(unit_audit)
            variant_info["unit_support"] = {
                "path": str(variant_unit_path),
                "sha256": sha256_file(variant_unit_path),
                **unit_summary,
            }
            input_paths.append(variant_unit_path)
        variant_manifest.append(variant_info)
        input_paths.append(variant_path)

    effects = pd.DataFrame(effect_rows)
    supports = pd.DataFrame(support_rows)
    joins = pd.DataFrame(join_rows)
    unit_support_audit = (
        pd.concat(unit_support_frames, ignore_index=True)
        if unit_support_frames
        else pd.DataFrame()
    )
    outputs = config["outputs"]
    output_root = _resolve(base, outputs["folderpath"])
    paths = {
        "effects": output_root / outputs["effects_file"],
        "support": output_root / outputs["support_file"],
        "join_audit": output_root / outputs["join_audit_file"],
        "manifest": output_root / outputs["manifest_file"],
    }
    if unit_support_config is not None:
        paths["unit_support_audit"] = output_root / outputs["unit_support_audit_file"]
    resolved_output_paths = [path.resolve() for path in paths.values()]
    if len(set(resolved_output_paths)) != len(resolved_output_paths):
        raise ValueError("robustness output paths resolve to the same file")
    if set(resolved_output_paths).intersection(path.resolve() for path in input_paths):
        raise ValueError("robustness outputs must not overwrite the primary or variant input tables")
    existing = [path for path in paths.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "robustness output files already exist; choose a new outputs.folderpath or pass --overwrite: "
            + ", ".join(str(path) for path in existing)
        )

    output_root.mkdir(parents=True, exist_ok=True)
    effects.to_csv(paths["effects"], index=False)
    supports.to_csv(paths["support"], index=False)
    joins.to_csv(paths["join_audit"], index=False)
    if unit_support_config is not None:
        unit_support_audit.to_csv(paths["unit_support_audit"], index=False)
    manifest = {
        "schema": "nmd_article_template.robustness_comparison.v1",
        "analysis_id": str(config["analysis"]["id"]),
        "description": config["analysis"].get("description", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "assessment_status": "descriptive_sensitivity_comparison_only",
        "robustness_qualification": "not_assessed",
        "inferential_status": "not_computed",
        "interpretation_note": (
            "Effect deltas, sign agreement, support changes, and key mismatches are diagnostics. "
            "No thresholds, p-values, confidence intervals, or scientific robustness claim are assigned."
        ),
        "primary": {
            "id": str(config["primary"]["id"]),
            "path": str(primary_path),
            "sha256": sha256_file(primary_path),
            "n_rows": int(len(primary)),
        },
        "variants": variant_manifest,
        "keys": keys,
        "effect_columns": effect_columns,
        "support_columns": support_columns,
        "unit_support": (
            {
                "keys": unit_support_config["keys"],
                "status_column": unit_support_config["status_column"],
                "included_statuses": unit_support_config["included_statuses"],
                "primary_path": str(primary_unit_support_path),
                "primary_sha256": sha256_file(primary_unit_support_path),
                "n_audit_rows": int(len(unit_support_audit)),
            }
            if unit_support_config is not None
            else None
        ),
        "outputs": {key: str(path) for key, path in paths.items()},
        "output_sha256": {
            key: sha256_file(path) for key, path in paths.items() if key != "manifest"
        },
        "n_effect_comparisons": int(len(effects)),
        "n_support_comparisons": int(len(supports)),
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
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    manifest = run(args.config, overwrite=args.overwrite)
    print(
        json.dumps(
            {
                "analysis_id": manifest["analysis_id"],
                "n_effect_comparisons": manifest["n_effect_comparisons"],
                "n_support_comparisons": manifest["n_support_comparisons"],
                "assessment_status": manifest["assessment_status"],
                "outputs": manifest["outputs"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
