"""Run the I-CARE v2 pipeline in smoke or full mode."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from icare_v2_common import ARTICLE_DIR

SCRIPTS = [
    ("inventory", "icare_v2_run_inventory.py", []),
    ("timebin", "icare_v2_timebin_assignment.py", []),
    ("qc_inventory", "icare_v2_qc_summary.py", ["--mode", "inventory"]),
    ("diffusion", "icare_v2_diffusion_family_extraction.py", []),
    ("mnj", "icare_v2_mnj_v3_extraction.py", []),
    ("reachability", "icare_v2_reachability_horizon_extraction.py", []),
    ("merge", "icare_v2_merge_cohort.py", []),
    ("qc_merged", "icare_v2_qc_summary.py", ["--mode", "merged"]),
    ("contrasts", "icare_v2_outcome_contrast_analysis.py", []),
    ("loso", "icare_v2_loso_sensitivity.py", []),
    ("mixed_effects", "icare_v2_mixed_effects_check.py", []),
    ("combat_diagnostic", "icare_v2_combat_diagnostic.py", []),
    ("qualified_drift", "icare_v2_qualified_drift_extraction.py", []),
    ("auroc", "icare_v2_auroc_analysis.py", []),
    ("local_dynamics_coverage", "icare_v2_local_dynamics_coverage.py", []),
    ("figures", "make_icare_v2_figures.py", []),
]
# 3.0.1 part1 work is separate from the 09-11 article pipeline:
#   icare_v2_v301_coverage_matrix.py
#   icare_v2_v301_l1_panel.py --config .../icare_v2_v301_part1_config.yaml



def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--start-from", type=str, default=None)
    parser.add_argument("--only", type=str, nargs="*", default=None)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--smoke-config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    src = Path(__file__).resolve().parent
    started = args.start_from is None
    timings = []
    for name, script, extra in SCRIPTS:
        if args.only and name not in args.only:
            continue
        if not started:
            if name == args.start_from:
                started = True
            else:
                continue
        command = [sys.executable, str(src / script), "--workers", str(args.workers), *extra]
        if args.smoke:
            command.append("--smoke")
        if args.config:
            command += ["--config", str(args.config)]
        if args.smoke_config:
            command += ["--smoke-config", str(args.smoke_config)]
        if args.output_dir:
            command += ["--output-dir", str(args.output_dir)]
        print(f"\n=== {name}: {' '.join(command)} ===", flush=True)
        t0 = time.perf_counter()
        subprocess.run(command, check=True, cwd=str(src))
        elapsed = time.perf_counter() - t0
        timings.append((name, elapsed))
        print(f"=== {name} done in {elapsed:.1f}s ===", flush=True)
    print("\nTiming summary:", flush=True)
    for name, elapsed in timings:
        print(f"  {name:16s} {elapsed:8.1f}s", flush=True)


if __name__ == "__main__":
    main()
