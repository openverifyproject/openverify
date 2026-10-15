"""Collect exactly one test per case; no SUT imports until test execution."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest
from tools.golden_v02.verify_manifest import cases, verify


def group(case):
    category = case["category"]
    if category.startswith("integrations/"):
        return "integrations"
    if category.startswith("providers/"):
        return "provider_contract"
    if category == "mutation/probes" or category.startswith("blocked/"):
        return "adversarial"
    if category == "vcp/provenance":
        return "provenance"
    if category == "relay/extension-ports":
        return "extensions"
    if category.startswith(
        (
            "relay/concurrency",
            "relay/isolation",
            "relay/cancellation",
            "relay/timeout",
            "relay/scheduling",
        )
    ):
        return "concurrency"
    if category.startswith("relay/") or case["operation"] in (
        "run",
        "policy_run",
        "metamorphic_run",
        "reducer_graph",
    ):
        return "relay_graphs"
    return "vcp"


def pytest_generate_tests(metafunc):
    if "case" in metafunc.fixturenames:
        selected = [
            c for c in cases() if group(c) == metafunc.function.__name__.removeprefix("test_")
        ]
        metafunc.parametrize("case", selected, ids=[c["id"] for c in selected])


@pytest.fixture(scope="session", autouse=True)
def integrity():
    verify()
