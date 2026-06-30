from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "nmd-analysis" / "config"
ANALYSIS_DIR = REPO_ROOT / "data" / "analysis"
OUTPUT_DIR = REPO_ROOT / "nmd-analysis" / "visuals" / "output" / "adaptive_collapse"
CONFIGS = [
    "analysis-ANPHY.yaml",
    "analysis-ds004100.yaml",
    "analysis-Sedation-RestingState.yaml",
]


def _run(table: str, config_name: str) -> None:
    out_name = f"{Path(config_name).stem}_{table}_rows.txt"
    out_path = OUTPUT_DIR / out_name
    script = REPO_ROOT / "nmd-analysis" / "visuals" / "export_adaptive_collapse_typst.py"
    shim = (
        "import sys, types, runpy; "
        f"sys.path.insert(0, r'{REPO_ROOT / 'nmd-analysis'}'); "
        "m=types.ModuleType('numexpr'); m.__version__='2.8.8'; sys.modules['numexpr']=m; "
        "b=types.ModuleType('bottleneck'); b.__version__='1.3.8'; sys.modules['bottleneck']=b; "
        "import pandas as pd; pd.set_option('compute.use_bottleneck', False); pd.set_option('compute.use_numexpr', False); "
        f"sys.argv=['export_adaptive_collapse_typst.py','--table','{table}','--config',r'{CONFIG_DIR / config_name}',"
        f"'--analysis-dir',r'{ANALYSIS_DIR}','--out',r'{out_path}']; "
        f"runpy.run_path(r'{script}', run_name='__main__')"
    )
    cmd = [
        sys.executable,
        "-c",
        shim,
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"Failed for {config_name} [{table}]")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for config_name in CONFIGS:
        for table in ("panel", "incremental"):
            _run(table, config_name)
    print(f"Wrote adaptive collapse tables to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
