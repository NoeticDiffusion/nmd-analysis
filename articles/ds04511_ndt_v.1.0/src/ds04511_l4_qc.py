"""QC the three invalid L4 reachability recordings and the degenerate d_eff readout.

Inventory / certificate audit. Does not recompute reachability or license
occupancy, MNJ, or confirmatory amplitude claims.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from ds04511_common import ARTICLE_DIR, DEFAULT_H5_ROOT, json_safe, scalar, sha256_file, write_json

RUN_LEVEL_DEFAULT = ARTICLE_DIR / "results" / "v1_task_20260921" / "task_run_level.csv"
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_l4_qc_20260921"
DE_EFF_NEAR_ONE = 1e-6
CERT_FIELDS = (
    "computation_status",
    "support_status",
    "qualification_status",
    "failure_reason",
    "claim_status",
    "n_propagator_steps",
)


def _h5_for_stem(stem: str, h5_root: Path) -> Path:
    return h5_root / stem / f"{stem}.h5"


def inspect_reach_certificate(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {
        "source_h5": str(path.resolve()),
        "stem": path.stem,
        "read_ok": False,
        "read_error": None,
        "a_q_present": False,
        "d_eff_present": False,
        "v_norm_present": False,
        "a_q": float("nan"),
        "d_eff": float("nan"),
        "v_norm": float("nan"),
        "provenance_gate": None,
        "propagator_source": None,
        "q_source": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            prim = handle["stochastic_reachability/v1/primary"]
            for field in CERT_FIELDS:
                row[field] = scalar(prim[field][()]) if field in prim else "absent"
            for name in ("a_q", "d_eff", "v_norm"):
                if name in prim:
                    value = float(np.asarray(prim[name][()], dtype=float).reshape(-1)[0])
                    row[f"{name}_present"] = True
                    row[name] = value
            prov = prim["provenance"] if "provenance" in prim else None
            if prov is not None:
                if "gate" in prov:
                    row["provenance_gate"] = scalar(prov["gate"][()])
                if "propagator_source" in prov:
                    row["propagator_source"] = scalar(prov["propagator_source"][()])
                if "q_source" in prov:
                    row["q_source"] = scalar(prov["q_source"][()])
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def d_eff_report(values: pd.Series) -> dict[str, Any]:
    array = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    finite = array[np.isfinite(array)]
    near_one = np.abs(finite - 1.0) < DE_EFF_NEAR_ONE if finite.size else np.asarray([], dtype=bool)
    return {
        "n_finite": int(finite.size),
        "n_near_one": int(np.sum(near_one)),
        "near_one_fraction": float(np.mean(near_one)) if finite.size else float("nan"),
        "median": float(np.median(finite)) if finite.size else float("nan"),
        "min": float(np.min(finite)) if finite.size else float("nan"),
        "max": float(np.max(finite)) if finite.size else float("nan"),
        "max_abs_deviation_from_one": float(np.max(np.abs(finite - 1.0))) if finite.size else float("nan"),
        "n_unique_rounded_12": int(np.unique(np.round(finite, 12)).size) if finite.size else 0,
        "note": (
            "d_eff pinned at 1 is a rank-degenerate ellipsoid summary, not a "
            "capacity-dimension contrast. Wilcoxon on 1e-8 residuals is method-limited."
        ),
    }


def write_md(
    path: Path,
    *,
    missing: pd.DataFrame,
    certificates: pd.DataFrame,
    deff: dict[str, Any],
    task_counts: dict[str, int],
) -> None:
    lines = [
        "# ds004511 L4 reachability QC",
        "",
        "Certificate audit of recordings without a finite included `reach_a_q` median, "
        "plus a degeneracy check on `d_eff`. This is not a new task contrast and not "
        "occupancy or MNJ.",
        "",
        f"Missing finite L4 `a_q`: **{int(len(missing))} / {int(task_counts.get('n_recordings', 0))}**.",
        "Task split of missing recordings: "
        + ", ".join(f"{task}={count}" for task, count in sorted(task_counts.items()) if task != "n_recordings")
        + ".",
        "",
        "## Invalid certificates",
        "",
        "| Subject | Task | n timepoints | status | failure | gate |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    merged = missing.merge(certificates, on="stem", how="left", suffixes=("", "_cert"))
    for _, row in merged.iterrows():
        lines.append(
            "| {sub} | `{task}` | {n} | `{status}` | `{fail}` | `{gate}` |".format(
                sub=row["subject_id"],
                task=row["task_label"],
                n=int(row["n_timepoints"]) if pd.notna(row.get("n_timepoints")) else 0,
                status=row.get("computation_status") or row.get("reach_a_q_computation_status"),
                fail=row.get("failure_reason") or "not_recorded",
                gate=row.get("provenance_gate") or "not_recorded",
            )
        )
    lines.extend(
        [
            "",
            "All three share `failure_reason=post_dtype_psd_failure` on gate F "
            "(Lyapunov propagation of the residual-covariance proxy). "
            "They are one Rest, one CC, and one GG recording from different subjects, "
            "so the gap is not a single-task dropout.",
            "",
            "## `d_eff` degeneracy",
            "",
            f"- finite recordings: {deff['n_finite']}",
            f"- `|d_eff - 1| < {DE_EFF_NEAR_ONE:g}`: {deff['n_near_one']} "
            f"({deff['near_one_fraction']:.1%})",
            f"- median / min / max: {deff['median']:.6g} / {deff['min']:.6g} / {deff['max']:.6g}",
            f"- max |d_eff − 1|: {deff['max_abs_deviation_from_one']:.3g}",
            "",
            deff["note"],
            "",
            "Read `reach_a_q` and `reach_v_norm` as the L4 amplitude summaries. "
            "Do not report `reach_d_eff` Wilcoxon as a dimension result.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, run_level_path: Path, h5_root: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    recordings = pd.read_csv(run_level_path)
    missing = recordings.loc[recordings["reach_a_q_included"] != True].copy()  # noqa: E712
    certificates = pd.DataFrame(
        [inspect_reach_certificate(_h5_for_stem(str(stem), h5_root)) for stem in missing["stem"].astype(str)]
    )
    missing.to_csv(output_root / "l4_missing_recordings.csv", index=False)
    certificates.to_csv(output_root / "l4_missing_certificates.csv", index=False)
    deff = d_eff_report(recordings["reach_d_eff_median"])
    write_json(output_root / "l4_deff_degeneracy.json", deff)
    task_counts = {
        "n_recordings": int(len(recordings)),
        **{str(task): int(count) for task, count in missing["task_label"].value_counts().items()},
    }
    write_md(
        output_root / "l4_qc.md",
        missing=missing,
        certificates=certificates,
        deff=deff,
        task_counts=task_counts,
    )
    reasons = sorted(certificates["failure_reason"].dropna().astype(str).unique().tolist()) if not certificates.empty else []
    manifest = {
        "schema": "ds004511_ndt_v1.l4_qc.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "n_recordings": int(len(recordings)),
        "n_l4_a_q_missing": int(len(missing)),
        "missing_stems": missing["stem"].astype(str).tolist(),
        "failure_reasons": reasons,
        "d_eff": deff,
        "run_level_sha256": sha256_file(run_level_path) if run_level_path.is_file() else None,
        "h5_root": str(h5_root),
        "note": (
            "Three recordings fail L4 with post_dtype_psd_failure. "
            "d_eff is degenerate at 1; do not treat its Wilcoxon as a dimension effect."
        ),
    }
    write_json(output_root / "l4_qc_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-level", type=Path, default=RUN_LEVEL_DEFAULT)
    parser.add_argument("--h5-root", type=Path, default=DEFAULT_H5_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args(argv)
    manifest = run(run_level_path=args.run_level, h5_root=args.h5_root, output_root=args.output_root)
    print(
        json.dumps(
            {
                "output_root": str(args.output_root),
                "n_l4_a_q_missing": manifest.get("n_l4_a_q_missing"),
                "failure_reasons": manifest.get("failure_reasons"),
                "d_eff_near_one_fraction": (manifest.get("d_eff") or {}).get("near_one_fraction"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
