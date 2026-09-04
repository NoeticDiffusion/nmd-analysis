from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ARTICLE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ARTICLE_DIR / "src"


def _run(script_name: str) -> None:
    script_path = SRC_DIR / script_name
    cmd = [sys.executable, str(script_path)]
    print(f"Running {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    _run("build_esb_article_outputs.py")
    _run("build_esb_comparator_panel.py")
    _run("build_esb_figures.py")


if __name__ == "__main__":
    main()
