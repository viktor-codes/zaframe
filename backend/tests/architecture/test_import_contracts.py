"""Architecture checks for import-linter contract configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_PATH = BACKEND_ROOT / "pyproject.toml"

REQUIRED_CONTRACT_NAMES = frozenset(
    {
        "Core infra does not import modules",
        "Models import nothing but core",
        "catalog does not depend on booking/payment/auth",
        "identity is a leaf",
        "search is read-only leaf",
        "payment only reaches booking and identity (not catalog/auth)",
        "Nothing imports the API layer",
    }
)


def test_import_linter_contracts_are_configured() -> None:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))

    importlinter_config = pyproject["tool"]["importlinter"]
    contracts = importlinter_config["contracts"]
    contract_names = {contract["name"] for contract in contracts}

    assert importlinter_config["root_package"] == "app"
    assert REQUIRED_CONTRACT_NAMES.issubset(contract_names)
