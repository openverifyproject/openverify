"""Explicit configured tests; absence of a test selection means full test scope."""

from typing import cast

from openverify.model import Context, Result
from openverify.relay.adapters.process import capture
from openverify.standard.common import STRING, STRINGS, judge, object_schema, standard
from openverify.standard.tools import Tools


def pytest_provider(tools: Tools):
    async def check(inputs: Context, config: Context) -> Result:
        executable = tools.executable("pytest")
        cwd = tools.access.path(cast(str, inputs["cwd"]))
        tests = cast(list[str], config.get("tests", []))
        for test in tests:
            if test.startswith("-"):
                raise ValueError("Test scope cannot contain command options")
            tools.access.path(test.split("::", 1)[0], base=cwd)
        result = await capture([executable, "-q", "--", *tests], str(cwd), timeout=120)
        if result.returncode not in (0, 1):
            raise RuntimeError(
                f"pytest runner failed (exit {result.returncode}): {result.stdout}\n{result.stderr}"
            )
        return judge(
            []
            if result.returncode == 0
            else [{"code": "tests_failed", "stdout": result.stdout, "stderr": result.stderr}],
            observations={
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "scope": [str(t) for t in tests],
            },
        )

    return standard(
        "pytest",
        "EVALUATE",
        {"cwd": STRING},
        {},
        check,
        config=object_schema({"tests": STRINGS}, optional={"tests"}),
    )
