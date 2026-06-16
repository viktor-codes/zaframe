"""AST-based architecture boundary checks beyond import-linter."""

from __future__ import annotations

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"
MODULES_ROOT = APP_ROOT / "modules"

FORBIDDEN_REPO_IMPORTS = frozenset({"service", "router", "policies"})


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


def _module_name_from_path(path: Path) -> str:
    relative = path.relative_to(APP_ROOT)
    return "app." + ".".join(relative.with_suffix("").parts)


def _top_level_domain(module_name: str) -> str | None:
    """Return top-level domain for app.modules.<domain>... paths."""
    parts = module_name.split(".")
    if len(parts) >= 3 and parts[0] == "app" and parts[1] == "modules":
        return parts[2]
    return None


def _imported_module_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            names.append(alias.name)
    elif isinstance(node, ast.ImportFrom) and node.module:
        names.append(node.module)
    return names


def _is_forbidden_repo_layer_import(module_path: str) -> bool:
    """True when a repository imports another module's service/router/policies layer."""
    if not module_path.startswith("app.modules."):
        return False
    tail = module_path.rsplit(".", 1)[-1]
    return tail in FORBIDDEN_REPO_IMPORTS


def _imported_symbol_names(node: ast.AST) -> list[str]:
    if not isinstance(node, ast.ImportFrom):
        return []
    return [alias.name for alias in node.names if alias.name != "*"]


def test_repository_files_have_no_service_or_router_imports() -> None:
    repo_files = sorted(MODULES_ROOT.rglob("repository.py"))
    assert repo_files, "expected at least one repository.py under app/modules"

    violations: list[str] = []
    for path in repo_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_name = _module_name_from_path(path)
        for node in ast.walk(tree):
            for imported in _imported_module_names(node):
                if _is_forbidden_repo_layer_import(imported):
                    violations.append(f"{module_name}: imports {imported!r}")

    assert not violations, "repository layer must not import service/router/policies:\n" + "\n".join(
        violations
    )


def test_no_private_cross_domain_imports() -> None:
    violations: list[str] = []
    for path in _iter_python_files(MODULES_ROOT):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        source_domain = _top_level_domain(_module_name_from_path(path))
        if source_domain is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if not node.module.startswith("app.modules."):
                continue

            target_domain = _top_level_domain(node.module)
            if target_domain is None or target_domain == source_domain:
                continue

            for symbol in _imported_symbol_names(node):
                if symbol.startswith("_"):
                    rel_path = path.relative_to(APP_ROOT.parent)
                    violations.append(
                        f"{rel_path}: from {node.module} import {symbol} "
                        f"(private cross-domain import)"
                    )

    assert not violations, "private names must not cross domain boundaries:\n" + "\n".join(
        violations
    )
