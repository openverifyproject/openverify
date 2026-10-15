"""Enforce dependency direction without importing/reading Reference Engine internals."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src" / "openverify"


def test_dependency_direction_and_no_hidden_globals() -> None:
    for package in ("relay", "authoring", "standard"):
        for path in (ROOT / package).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    imports.append(node.module or "")
                elif isinstance(node, ast.Import):
                    imports.extend(a.name for a in node.names)
            assert not any(
                i.startswith(("openverify.engine", "openverify.adapters")) for i in imports
            ), path
            if "core" in path.parts or "ports" in path.parts:
                assert not any(
                    i.startswith(
                        (
                            "openverify.relay.application",
                            "openverify.relay.adapters",
                            "openverify.relay.entrypoints",
                            "openverify.standard",
                        )
                    )
                    for i in imports
                ), path
            if "application" in path.parts:
                assert not any(
                    i.startswith(
                        (
                            "openverify.relay.adapters",
                            "openverify.relay.entrypoints",
                            "openverify.standard",
                        )
                    )
                    for i in imports
                ), path
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    assert not isinstance(node.value, (ast.Dict, ast.List, ast.Set)), path


def test_no_import_cycles() -> None:
    graph: dict[str, set[str]] = {}
    for package in ("relay", "authoring", "standard"):
        for path in (ROOT / package).rglob("*.py"):
            name = "openverify." + ".".join(path.relative_to(ROOT).with_suffix("").parts)
            name = name.removesuffix(".__init__")
            tree = ast.parse(path.read_text())
            # Runtime imports at function scope are composition, not module initialization edges.
            graph[name] = {
                n.module for n in tree.body if isinstance(n, ast.ImportFrom) and n.module
            }

    def visit(name: str, chain: set[str]) -> None:
        assert name not in chain, f"Import cycle through {name}"
        for dependency in graph.get(name, set()):
            if dependency in graph:
                visit(dependency, chain | {name})

    for name in graph:
        visit(name, set())
