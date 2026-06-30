from __future__ import annotations

import ast
import unittest
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


FORBIDDEN_TOKENS: Sequence[str] = (
    "noeticdiffusion-toolkit",
    "scientific_validation",
)

SCAN_ROOTS: Sequence[str] = (
    "nmd_analysis",
    "visuals",
)


def _iter_python_files(repo_root: Path) -> Iterable[Path]:
    for relative in SCAN_ROOTS:
        root = repo_root / relative
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            yield path


def _docstring_expr_nodes(tree: ast.AST) -> set[int]:
    nodes: set[int] = set()
    stacks: List[ast.AST] = [tree]
    while stacks:
        node = stacks.pop()
        body = getattr(node, "body", None)
        if isinstance(body, list) and body:
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                nodes.add(id(first))
        for child in ast.iter_child_nodes(node):
            stacks.append(child)
    return nodes


def _contains_forbidden(text: str) -> str | None:
    lowered = text.lower()
    for token in FORBIDDEN_TOKENS:
        if token in lowered:
            return token
    return None


class StandaloneCouplingTests(unittest.TestCase):
    def test_runtime_python_has_no_toolkit_coupling_tokens(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        violations: List[Tuple[str, int, str, str]] = []

        for file_path in _iter_python_files(repo_root):
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
            docstring_nodes = _docstring_expr_nodes(tree)
            relative = file_path.relative_to(repo_root).as_posix()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        token = _contains_forbidden(alias.name)
                        if token:
                            violations.append((relative, node.lineno, "import", token))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        token = _contains_forbidden(node.module)
                        if token:
                            violations.append((relative, node.lineno, "from-import", token))
                elif isinstance(node, ast.Expr) and id(node) in docstring_nodes:
                    continue
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    token = _contains_forbidden(node.value)
                    if token:
                        violations.append((relative, node.lineno, "string", token))

        if violations:
            rendered = "\n".join(
                f"- {path}:{line} [{kind}] contains `{token}`"
                for path, line, kind, token in violations
            )
            self.fail(
                "Standalone coupling guard failed. Remove toolkit references from runtime Python modules:\n"
                f"{rendered}"
            )


if __name__ == "__main__":
    unittest.main()
