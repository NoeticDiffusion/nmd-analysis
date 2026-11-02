"""Post-hoc residual-batch-effect (hospital) diagnostic on derived Family A metrics.

ComBat harmonization (batch_key=hospital) is applied upstream at ingest to
raw EEG features, before the diffusion-geometry metrics (H1-H3) are derived
from them. That upstream validation used eta^2 probes on raw features. This
script re-runs the same eta^2 diagnostic on the *derived* metrics themselves
(d_eff_a_median, h_tilde_a_median, e_perp_median, d_total_median) in the
primary CPC1/5 analysis table, to check whether hospital still explains a
non-trivial share of variance after harmonization + local-geometry
derivation. eta^2 > ~0.06 (medium, Cohen 1988 convention) on a metric that
also differs by hospital-CPC composition would be a flag to interpret that
metric's contrast more cautiously.
"""
from __future__ import annotations

import argparse
from typing import Any

import pandas as pd

from icare_v2_common import (
    add_common_args,
    eta_squared_oneway,
    resolve_pipeline_config,
    write_csv,
    write_json,
)

METRICS = (
    ("d_eff_a_median", "H1"),
    ("h_tilde_a_median", "H2"),
    ("e_perp_median", "H3"),
    ("d_total_median", "H4"),
)
FLAG_THRESHOLD = 0.06  # Cohen (1988) medium-effect eta^2 convention


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    table = pd.read_csv(in_dir / "icare_v2_primary_cpc15_table.csv")

    rows: list[dict[str, Any]] = []
    for metric, hyp in METRICS:
        if metric not in table.columns or "hospital" not in table.columns:
            continue
        diag = eta_squared_oneway(table[metric].to_numpy(), table["hospital"].to_numpy())
        diag["metric"] = metric
        diag["hypothesis"] = hyp
        diag["batch_key"] = "hospital"
        diag["flag_residual_batch_effect"] = bool(
            diag["eta_squared"] == diag["eta_squared"] and diag["eta_squared"] > FLAG_THRESHOLD  # nan-safe
        )
        rows.append(diag)

    # Also report hospital x CPC-group composition, since eta^2 alone can't
    # distinguish "hospital differs, but hospitals are outcome-balanced" from
    # a genuine outcome confound.
    composition = pd.DataFrame()
    if {"hospital", "contrast_group"}.issubset(table.columns):
        composition = (
            table.groupby(["hospital", "contrast_group"]).size().rename("n").reset_index()
        )

    frame = pd.DataFrame(rows)
    write_csv(out_dir / "combat_residual_batch_effect.csv", frame)
    write_csv(out_dir / "hospital_cpc_composition.csv", composition)
    write_json(
        out_dir / "combat_diagnostic_manifest.json",
        {
            "note": (
                "Post-ComBat residual hospital eta^2 on derived Family A metrics. "
                f"Flag threshold eta^2 > {FLAG_THRESHOLD} (Cohen medium-effect convention). "
                "This does not by itself imply the primary CPC1/5 contrast is confounded; "
                "see hospital_cpc_composition.csv for whether hospitals are outcome-balanced."
            ),
            "flag_threshold": FLAG_THRESHOLD,
            "bundle_id": cfg.bundle_id,
            "confirmatory_status": cfg.confirmatory_status,
        },
    )
    print(f"Wrote ComBat residual batch-effect diagnostic for {len(rows)} metrics to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
