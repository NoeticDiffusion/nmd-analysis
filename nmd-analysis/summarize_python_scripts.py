from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
}


@dataclass
class FunctionSummary:
    name: str
    args: List[str]
    doc: str | None


@dataclass
class ClassSummary:
    name: str
    bases: List[str]
    methods: int
    doc: str | None


@dataclass
class ModuleSummary:
    relative_path: str
    line_count: int
    module_doc: str | None
    imports: List[str]
    classes: List[ClassSummary]
    functions: List[FunctionSummary]
    parse_error: str | None = None


def should_skip(path: Path, root: Path, exclude_dirs: set[str]) -> bool:
    rel = path.relative_to(root)
    return any(part in exclude_dirs for part in rel.parts)


def iter_python_files(root: Path, exclude_dirs: set[str]) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if path.is_file() and not should_skip(path, root, exclude_dirs):
            yield path


def _node_to_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_node_to_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        return _node_to_name(node.value)
    if isinstance(node, ast.Call):
        return _node_to_name(node.func)
    return node.__class__.__name__


def _arg_list(args: ast.arguments) -> List[str]:
    out: List[str] = []
    for a in args.posonlyargs:
        out.append(a.arg)
    for a in args.args:
        out.append(a.arg)
    if args.vararg:
        out.append(f"*{args.vararg.arg}")
    for a in args.kwonlyargs:
        out.append(f"{a.arg}")
    if args.kwarg:
        out.append(f"**{args.kwarg.arg}")
    return out


def summarize_file(path: Path, root: Path) -> ModuleSummary:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(root)).replace("\\", "/")
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return ModuleSummary(
            relative_path=rel,
            line_count=lines,
            module_doc=None,
            imports=[],
            classes=[],
            functions=[],
            parse_error=f"SyntaxError: {exc}",
        )

    module_doc = ast.get_docstring(tree)
    imports: List[str] = []
    classes: List[ClassSummary] = []
    functions: List[FunctionSummary] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend([alias.name for alias in node.names])
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = ", ".join(alias.name for alias in node.names)
            imports.append(f"from {mod} import {names}")
        elif isinstance(node, ast.ClassDef):
            methods = sum(isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)) for ch in node.body)
            classes.append(
                ClassSummary(
                    name=node.name,
                    bases=[_node_to_name(base) for base in node.bases],
                    methods=methods,
                    doc=ast.get_docstring(node),
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                FunctionSummary(
                    name=node.name,
                    args=_arg_list(node.args),
                    doc=ast.get_docstring(node),
                )
            )

    return ModuleSummary(
        relative_path=rel,
        line_count=lines,
        module_doc=module_doc,
        imports=imports,
        classes=classes,
        functions=functions,
    )


def first_line(text: str | None) -> str:
    if not text:
        return "-"
    return text.strip().splitlines()[0].strip() or "-"


def render_summary(all_summaries: List[ModuleSummary], root: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out: List[str] = []
    out.append("Python Script Summary")
    out.append(f"Generated: {now}")
    out.append(f"Root: {root}")
    out.append(f"Files: {len(all_summaries)}")
    out.append("")

    for item in all_summaries:
        out.append("=" * 88)
        out.append(f"FILE: {item.relative_path}")
        out.append("=" * 88)
        out.append(f"Line count: {item.line_count}")
        if item.parse_error:
            out.append(f"Parse error: {item.parse_error}")
            out.append("")
            continue

        out.append(f"Module doc: {first_line(item.module_doc)}")
        out.append("")

        out.append("Imports:")
        if item.imports:
            for imp in sorted(set(item.imports)):
                out.append(f"- {imp}")
        else:
            out.append("- -")
        out.append("")

        out.append("Classes:")
        if item.classes:
            for cls in item.classes:
                bases = ", ".join(cls.bases) if cls.bases else "-"
                out.append(
                    f"- {cls.name} (bases: {bases}, methods: {cls.methods}) | {first_line(cls.doc)}"
                )
        else:
            out.append("- -")
        out.append("")

        out.append("Functions:")
        if item.functions:
            for fn in item.functions:
                sig = f"{fn.name}({', '.join(fn.args)})"
                out.append(f"- {sig} | {first_line(fn.doc)}")
        else:
            out.append("- -")
        out.append("")

        source_path = root / Path(item.relative_path)
        out.append("Full source code:")
        out.append("```python")
        try:
            source_text = source_path.read_text(encoding="utf-8", errors="replace")
            out.append(source_text.rstrip("\n"))
        except OSError as exc:
            out.append(f"# Failed to read source: {exc}")
        out.append("```")
        out.append("")

    return "\n".join(out) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize Python files for architecture review."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("python_scripts_summary.txt"),
        help="Output txt path (default: python_scripts_summary.txt).",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude (can be repeated).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS) | set(args.exclude_dir)

    files = sorted(iter_python_files(root, exclude_dirs), key=lambda p: str(p).lower())
    summaries = [summarize_file(path, root) for path in files]
    text = render_summary(summaries, root)

    output = args.output
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(f"Wrote summary: {output}")


if __name__ == "__main__":
    main()
