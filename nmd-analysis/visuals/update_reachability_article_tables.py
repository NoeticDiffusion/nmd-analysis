from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTICLE_PATH = (
    REPO_ROOT
    / "articles"
    / "Reachability Cones as Local Capacity Geometry in Noetic Diffusion Theory"
    / "Reachability Cones as Local Capacity Geometry in Noetic Diffusion Theory.typ"
)
CONFIG_DIR = REPO_ROOT / "nmd-analysis" / "config"
ANALYSIS_DIR = REPO_ROOT / "data" / "analysis"
SECTION_ORDER = ["GLOBAL_TUBE", "GLOBAL_PER_H", "BLOCK_TUBE", "BLOCK_PER_H"]
CONTROL_CONFIGS = [
    "analysis-ds003059.yaml",
    "analysis-ds003478.yaml",
    "analysis-ds003947.yaml",
    "analysis-ds004100.yaml",
    "analysis-ds004504.yaml",
    "analysis-ds004511.yaml",
    "analysis-ds005555.yaml",
    "analysis-ds005917.yaml",
    "analysis-ds006623.yaml",
]
DATASET_HEADINGS = [
    ("analysis-ds004504.yaml", "=== ds004504"),
    ("analysis-ds005555.yaml", "=== ds005555"),
    ("analysis-ds003478.yaml", "=== ds003478"),
    ("analysis-ds003947.yaml", "=== ds003947"),
    ("analysis-ds004100.yaml", "=== ds004100"),
    ("analysis-ds005917.yaml", "=== ds005917"),
    ("analysis-ds003059.yaml", "=== 2.7 ds003059"),
    ("analysis-ds004511.yaml", "=== 2.9 ds004511"),
]


def _read_rows(path: Path) -> List[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _parse_section_rows(path: Path) -> Dict[str, List[str]]:
    sections = {key: [] for key in SECTION_ORDER}
    current = None
    for raw in _read_rows(path):
        line = raw.rstrip()
        if line.startswith("[") and line.endswith("]"):
            label = line[1:-1].strip()
            current = label if label in sections else None
            continue
        if current and line.strip().startswith("["):
            sections[current].append(line)
    return sections


def _find_next(lines: List[str], start: int, predicate) -> int:
    for idx in range(start, len(lines)):
        if predicate(lines[idx]):
            return idx
    raise ValueError("Could not locate expected table block in article.")


def _replace_next_table(lines: List[str], start_idx: int, new_rows: List[str], *, skip_if_empty: bool) -> int:
    table_start = _find_next(lines, start_idx, lambda text: text.lstrip().startswith("#table("))
    header_start = _find_next(lines, table_start, lambda text: "table.header(" in text)
    header_end = _find_next(lines, header_start, lambda text: text.strip() == "),")
    table_end = _find_next(lines, header_end, lambda text: text.strip() == ")")
    rows_start = header_end + 1
    rows_end = table_end
    if new_rows or not skip_if_empty:
        lines[rows_start:rows_end] = new_rows
        table_end = rows_start + len(new_rows)
    return table_end + 1


def _replace_tables_in_section(lines: List[str], heading: str, section_rows: Dict[str, List[str]]) -> None:
    start = _find_next(lines, 0, lambda text: heading in text) + 1
    try:
        end = _find_next(lines, start, lambda text: text.startswith("==="))
    except ValueError:
        end = len(lines)
    cursor = start
    for key in SECTION_ORDER:
        try:
            table_idx = _find_next(lines, cursor, lambda text: text.lstrip().startswith("#table("))
        except ValueError:
            break
        if table_idx >= end:
            break
        cursor = _replace_next_table(lines, cursor, section_rows.get(key, []), skip_if_empty=True)


def _run_script(script_name: str, args: Iterable[str]) -> subprocess.CompletedProcess[str]:
    script_path = REPO_ROOT / "nmd-analysis" / "visuals" / script_name
    cmd = [sys.executable, str(script_path), *list(args)]
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def _collect_control_rows(table_name: str, analysis_dir: Path, tmp_dir: Path) -> List[str]:
    rows: List[str] = []
    for config_name in CONTROL_CONFIGS:
        out_path = tmp_dir / f"{table_name}_{config_name}.txt"
        result = _run_script(
            "export_reachability_controls_typst.py",
            [
                "--table",
                table_name,
                "--config",
                str(CONFIG_DIR / config_name),
                "--analysis-dir",
                str(analysis_dir),
                "--out",
                str(out_path),
            ],
        )
        if result.returncode != 0:
            continue
        rows.extend(_read_rows(out_path))
    return rows


def _replace_control_tables(lines: List[str], analysis_dir: Path) -> None:
    start = _find_next(lines, 0, lambda text: "=== Validity & controls" in text) + 1
    with tempfile.TemporaryDirectory() as tmp_raw:
        tmp_dir = Path(tmp_raw)
        control_rows = {
            "validity": _collect_control_rows("validity", analysis_dir, tmp_dir),
            "incremental": _collect_control_rows("incremental", analysis_dir, tmp_dir),
            "q_vs_a": _collect_control_rows("q_vs_a", analysis_dir, tmp_dir),
        }
    cursor = _replace_next_table(lines, start, control_rows["validity"], skip_if_empty=True)
    cursor = _replace_next_table(lines, cursor, control_rows["incremental"], skip_if_empty=True)
    _replace_next_table(lines, cursor, control_rows["q_vs_a"], skip_if_empty=True)


def _replace_dataset_tables(lines: List[str], analysis_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp_raw:
        tmp_dir = Path(tmp_raw)
        for config_name, heading in DATASET_HEADINGS:
            out_path = tmp_dir / f"{config_name}_tables.txt"
            result = _run_script(
                "export_reachability_typst_tables.py",
                [
                    "--config",
                    str(CONFIG_DIR / config_name),
                    "--analysis-dir",
                    str(analysis_dir),
                    "--out",
                    str(out_path),
                    "--p-threshold",
                    "0.1",
                ],
            )
            if result.returncode != 0:
                continue
            section_rows = _parse_section_rows(out_path)
            _replace_tables_in_section(lines, heading, section_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh reachability article tables from nmd-analysis outputs.")
    parser.add_argument("--analysis-dir", default=str(ANALYSIS_DIR))
    parser.add_argument("--article", default=str(ARTICLE_PATH))
    args = parser.parse_args()

    article_path = Path(args.article).resolve()
    analysis_dir = Path(args.analysis_dir).resolve()
    lines = article_path.read_text(encoding="utf-8").splitlines()

    _replace_control_tables(lines, analysis_dir)
    _replace_dataset_tables(lines, analysis_dir)

    article_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated {article_path}")


if __name__ == "__main__":
    main()
