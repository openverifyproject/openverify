import asyncio
import pytest
from tools.golden_v02.execution import execute_case


def check(case):
    row = asyncio.run(execute_case(case))
    if row["status"] == "ENVIRONMENT_UNAVAILABLE":
        pytest.skip("ENVIRONMENT_UNAVAILABLE: " + row["detail"])
    if row["status"] == "BLOCKED_BY_SPEC":
        pytest.xfail("BLOCKED_BY_SPEC: " + row["detail"])
    assert row["status"] == "PASS", row
