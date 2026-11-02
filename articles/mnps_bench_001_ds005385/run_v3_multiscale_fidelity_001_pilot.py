from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ARTICLE = Path(__file__).resolve().parent
PROTOCOL = ARTICLE / "v3_multiscale_fidelity_001_protocol_v1_20261009.md"
COVERAGE = ARTICLE / "outputs" / "v3_coverage_001_pilot_v1_20261008"
INPUT = COVERAGE / "candidate_probe_status.csv"
OUT = ARTICLE / "outputs" / "v3_multiscale_fidelity_001_pilot_v1_20261009"
PARTICIPANTS = ("sub-032", "sub-033", "sub-034", "sub-035", "sub-036", "sub-038")
SURFACES = ("native", "core19")
DURATIONS = (4, 8, 12, 20)
SCALAR_CANDIDATES = ("M1", "M2", "D1", "D3", "E1", "E2", "E3")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_value(raw: object) -> Any:
    if not isinstance(raw, str):
        raise ValueError(f"value_json is not text: {type(raw).__name__}")
    return json.loads(raw)


def safe_float(value: float) -> float | None:
    return float(value) if math.isfinite(float(value)) else None


def ccc(x: np.ndarray, y: np.ndarray) -> float | None:
    if x.size < 2 or y.size != x.size:
        return None
    variance_x = float(np.var(x, ddof=1))
    variance_y = float(np.var(y, ddof=1))
    denominator = variance_x + variance_y + float((np.mean(x) - np.mean(y)) ** 2)
    if denominator <= 0.0 or not math.isfinite(denominator):
        return None
    covariance = float(np.cov(x, y, ddof=1)[0, 1])
    return safe_float(2.0 * covariance / denominator)


def main() -> None:
    if not PROTOCOL.is_file() or not INPUT.is_file():
        raise FileNotFoundError("frozen fidelity protocol or coverage output is missing")
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite existing fidelity output: {OUT}")
    coverage_manifest_path = COVERAGE / "run_manifest.json"
    coverage_manifest = json.loads(coverage_manifest_path.read_text(encoding="utf-8"))
    expected_input_hash = coverage_manifest["outputs"][INPUT.name]["sha256"]
    if sha256_file(INPUT) != expected_input_hash:
        raise ValueError("coverage candidate status table does not match its manifest")

    frame = pd.read_csv(INPUT, keep_default_na=False)
    paired = frame.loc[
        frame["load"].astype(int).eq(13)
        & frame["duration_sec"].astype(int).isin(DURATIONS)
    ].copy()
    paired["duration_sec"] = paired["duration_sec"].astype(int)
    paired["load"] = paired["load"].astype(int)
    paired["measurement_supported"] = paired["measurement_supported"].astype(str).str.casefold().eq("true")
    if not paired["measurement_supported"].all():
        raise ValueError("load-13 duration pair contains an unsupported candidate")
    if not paired["computed"].astype(str).str.casefold().eq("true").all():
        raise ValueError("load-13 duration pair contains a non-computed candidate")
    if not paired["valid"].astype(str).str.casefold().eq("true").all():
        raise ValueError("load-13 duration pair contains an invalid candidate")
    if not paired["finite_value"].astype(str).str.casefold().eq("true").all():
        raise ValueError("load-13 duration pair contains a nonfinite candidate")
    if paired.duplicated(["subject", "surface", "trial_id", "candidate_id", "duration_sec"]).any():
        raise ValueError("duplicate trial/surface/candidate/duration key")

    expected_rows = 324 * len(SURFACES) * 8 * len(DURATIONS)
    if len(paired) != expected_rows:
        raise ValueError(f"expected {expected_rows} load-13 candidate rows, found {len(paired)}")
    for (candidate, duration), subset in paired.groupby(["candidate_id", "duration_sec"]):
        if len(subset) != 324 * len(SURFACES):
            raise ValueError(f"unexpected support count for {candidate}/{duration}s: {len(subset)}")

    paired["parsed_value"] = paired["value_json"].map(parse_value)
    key_columns = ["subject", "surface", "trial_id", "candidate_id"]
    scalar_rows: list[dict[str, object]] = []
    ar_rows: list[dict[str, object]] = []

    for (subject, surface, candidate), subset in paired.groupby(key_columns[0:1] + key_columns[1:2] + key_columns[3:4]):
        by_trial = subset.pivot(index="trial_id", columns="duration_sec", values="parsed_value")
        if set(by_trial.columns) != set(DURATIONS) or len(by_trial) != 54:
            raise ValueError(f"expected 54 paired load-13 trials for {subject}/{surface}/{candidate}")
        if candidate in SCALAR_CANDIDATES:
            for duration in (4, 8, 12):
                short_values = by_trial[duration].map(lambda value: float(value) if not isinstance(value, list) else math.nan).to_numpy(dtype=float)
                twenty_values = by_trial[20].map(lambda value: float(value) if not isinstance(value, list) else math.nan).to_numpy(dtype=float)
                if not np.isfinite(short_values).all() or not np.isfinite(twenty_values).all():
                    raise ValueError(f"scalar value parse failure for {subject}/{surface}/{candidate}/{duration}s")
                x = short_values
                y = twenty_values
                rank = pd.Series(x).corr(pd.Series(y), method="spearman")
                scalar_rows.append({
                    "subject": subject,
                    "surface": surface,
                    "candidate_id": candidate,
                    "duration_sec": duration,
                    "reference_duration_sec": 20,
                    "paired_trial_count": int(len(x)),
                    "spearman_rank_correlation": safe_float(rank),
                    "lin_concordance_correlation": ccc(x, y),
                    "median_signed_difference_short_minus_20s": safe_float(float(np.median(x - y))),
                    "median_absolute_difference": safe_float(float(np.median(np.abs(x - y)))),
                    "short_median": safe_float(float(np.median(x))),
                    "reference_20s_median": safe_float(float(np.median(y))),
                })
        elif candidate == "M3":
            expected_lengths = {4: 1, 8: 3, 12: 5, 20: 9}
            for duration in (4, 8, 12):
                compared_components = 0
                exact_components = 0
                near_equal_components = 0
                mismatched_windows = 0
                max_abs_difference = 0.0
                for short, long in zip(by_trial[duration], by_trial[20], strict=True):
                    short_array = np.asarray(short, dtype=np.float64).reshape(-1)
                    long_array = np.asarray(long, dtype=np.float64).reshape(-1)
                    if short_array.size != expected_lengths[duration] or long_array.size != 9:
                        raise ValueError(f"unexpected AR value length for {subject}/{surface}/{duration}s")
                    prefix = long_array[:short_array.size]
                    differences = np.abs(short_array - prefix)
                    compared_components += int(short_array.size)
                    exact_components += int(np.count_nonzero(short_array == prefix))
                    near_equal_components += int(np.count_nonzero(np.isclose(short_array, prefix, rtol=0.0, atol=1e-12)))
                    max_abs_difference = max(max_abs_difference, float(np.max(differences)))
                    if not np.allclose(short_array, prefix, rtol=0.0, atol=1e-12):
                        mismatched_windows += 1
                ar_rows.append({
                    "subject": subject,
                    "surface": surface,
                    "candidate_id": candidate,
                    "duration_sec": duration,
                    "reference_duration_sec": 20,
                    "paired_trial_count": int(len(by_trial)),
                    "short_vector_length": expected_lengths[duration],
                    "reference_vector_length": 9,
                    "component_comparisons": compared_components,
                    "exact_component_matches": exact_components,
                    "near_equal_component_matches_at_1e-12": near_equal_components,
                    "mismatched_window_count_at_1e-12": mismatched_windows,
                    "max_absolute_component_difference": max_abs_difference,
                })
        else:
            raise ValueError(f"unexpected candidate id: {candidate}")

    scalar_df = pd.DataFrame(scalar_rows)
    group_rows: list[dict[str, object]] = []
    statistics = (
        "spearman_rank_correlation",
        "lin_concordance_correlation",
        "median_signed_difference_short_minus_20s",
        "median_absolute_difference",
    )
    for (surface, candidate, duration), group in scalar_df.groupby(["surface", "candidate_id", "duration_sec"]):
        result: dict[str, object] = {
            "surface": surface,
            "candidate_id": candidate,
            "duration_sec": int(duration),
            "participant_count": int(group["subject"].nunique()),
        }
        for statistic in statistics:
            values = group[statistic].dropna().astype(float)
            result[f"{statistic}_participant_median"] = safe_float(float(values.median())) if len(values) else None
            result[f"{statistic}_participant_min"] = safe_float(float(values.min())) if len(values) else None
            result[f"{statistic}_participant_max"] = safe_float(float(values.max())) if len(values) else None
        group_rows.append(result)
    group_df = pd.DataFrame(group_rows)
    ar_df = pd.DataFrame(ar_rows)

    ed_rows = []
    for duration in DURATIONS:
        sample_count = duration * 250
        for surface, channel_count in (("native", 63), ("core19", 19)):
            ed_rows.append({
                "duration_sec": duration,
                "surface": surface,
                "channel_count": channel_count,
                "sample_count": sample_count,
                "samples_per_channel_dimension": sample_count / channel_count,
                "temporal_effective_sample_size": "unknown_unassessed",
            })
    ed_df = pd.DataFrame(ed_rows)

    OUT.mkdir(parents=True, exist_ok=False)
    scalar_df.to_csv(OUT / "scalar_paired_agreement_by_participant.csv", index=False)
    group_df.to_csv(OUT / "scalar_paired_agreement_summary.csv", index=False)
    ar_df.to_csv(OUT / "ar_prefix_agreement.csv", index=False)
    ed_df.to_csv(OUT / "ed_sample_support.csv", index=False)

    report = [
        "# V3-MULTISCALE-FIDELITY-001 results",
        "",
        "Exploratory paired-duration characterization on the six-participant ds003838 pilot.",
        "No estimator was changed, no condition contrast or classifier was run, and no duration was qualified.",
        "",
        f"- Paired population: load 13, {len(PARTICIPANTS)} participants, two surfaces, 54 trial windows per participant/surface.",
        "- Short 4/8/12-second windows and their 20-second comparators share the same trial start and nested samples.",
        "- The 20-second realization is a frozen comparator, not a gold standard.",
        "- Scalar summaries are per participant and surface; the summary file reports the six-participant median and range. No pooled inferential statistics or thresholds are applied.",
        "",
        "## Scalar candidate agreement summary",
        "",
        "See `scalar_paired_agreement_summary.csv` and `scalar_paired_agreement_by_participant.csv` for rank correlation, Lin concordance, and paired differences.",
        "These descriptive statistics characterize this pilot only. Nested support, condition composition, and six-participant scope prevent interpreting them as independent validation or equivalence.",
        "",
        "## AR/M3 prefix check",
        "",
        "See `ar_prefix_agreement.csv`. Shorter AR vectors are compared component-wise with the corresponding prefix of the 20-second vector, without collapsing duration-dependent vector lengths.",
        "",
        "## ED sample support and unresolved fidelity",
        "",
        "See `ed_sample_support.csv`. Participation ratios are computed at all four durations, but the nominal samples/channel ratio does not estimate effective sample size under temporal autocorrelation and does not resolve short-window covariance bias.",
        "",
        "## Limitations and decision boundary",
        "",
        "PCV's window-local alpha IIR and Hilbert edge fidelity remains unassessed; upstream filter edge safety and bad-interval-free provenance remain unknown. SC uses 32 duration-bound exact-multiset shuffles, so its seeded reference realization changes with duration. Positive agreement is not sufficient to establish that durations have interchangeable meanings or to qualify a separately versioned estimator.",
        "",
        "This pilot may motivate a separate scientific definition and independent validation plan. It does not authorize a full-cohort run. BENCH-002 should distinguish the 4-second fast-core path from full-v3 coverage; a load-13-only full-v3 contrast is the only current path preserving the 20-second contract.",
        "",
        "## Outputs",
        "",
        "- `scalar_paired_agreement_by_participant.csv`: candidate/duration agreement per participant and surface.",
        "- `scalar_paired_agreement_summary.csv`: participant-level medians and ranges.",
        "- `ar_prefix_agreement.csv`: vector-prefix consistency by participant/surface.",
        "- `ed_sample_support.csv`: duration and nominal samples/channel counts.",
        "- `run_manifest.json`: input, protocol, code, and output hashes.",
    ]
    (OUT / "results.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    outputs = {}
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name != "run_manifest.json":
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    manifest = {
        "schema": "mndm.v3_multiscale_fidelity_001_pilot_manifest.v1",
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "participants": list(PARTICIPANTS),
        "surfaces": list(SURFACES),
        "comparison_load": 13,
        "duration_sec": list(DURATIONS),
        "paired_window_policy": "same trial start; nested duration prefixes",
        "coverage_manifest_path": str(coverage_manifest_path),
        "coverage_manifest_sha256": sha256_file(coverage_manifest_path),
        "coverage_candidate_table_sha256": sha256_file(INPUT),
        "protocol_path": str(PROTOCOL),
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_path": str(Path(__file__).resolve()),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "scalar_pair_count": int(len(scalar_df)),
        "ar_prefix_pair_count": int(len(ar_df)),
        "claim_ceiling": "descriptive paired-duration agreement only; no fidelity qualification, equivalence, condition contrast, classification, or full-cohort authorization",
        "outputs": outputs,
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": manifest["status"],
        "output": str(OUT),
        "scalar_pair_count": manifest["scalar_pair_count"],
        "ar_prefix_pair_count": manifest["ar_prefix_pair_count"],
        "ar_mismatch_count": int(ar_df["mismatched_window_count_at_1e-12"].sum()),
        "outputs": outputs,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
