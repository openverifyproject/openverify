"""Ruff's structured diagnostics, distinct from runner failure."""

from pathlib import Path
from typing import cast

from pydantic import JsonValue

from openverify.model import Context, ExecutionObservation
from openverify.relay.adapters.process import capture
from openverify.serialization import decode, to_data
from openverify.standard.common import ARRAY, STRING, STRINGS, judge, object_schema, standard
from openverify.standard.tools import Tools


def ruff_provider(tools: Tools):
    async def check(inputs: Context, config: Context) -> ExecutionObservation:
        executable = tools.executable("ruff")
        cwd, files = tools.files(cast(str, inputs["cwd"]), cast(list[str], inputs["files"]))
        files = [f for f in files if Path(f).suffix in (".py", ".pyi")]
        if not files:
            return ExecutionObservation(
                outputs={
                    "findings": [],
                    "result": to_data(
                        judge(
                            [],
                            observations={
                                "scope": [],
                                "reason": "No Python files in explicit scope",
                            },
                        )
                    ),
                }
            )
        select = cast(list[str], config["select"])
        if any(not code.isalnum() for code in select):
            raise ValueError("Ruff select requires diagnostic codes")
        result = await capture(
            [
                executable,
                "check",
                "--isolated",
                "--output-format",
                "json",
                "--select",
                ",".join(select),
                "--",
                *files,
            ],
            str(cwd),
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"Ruff invocation failed: {result.stderr}")
        raw = cast(list[dict[str, JsonValue]], decode(result.stdout))
        findings: list[JsonValue] = []
        for entry in raw:
            start = cast(Context, entry["location"])
            end = cast(Context, entry["end_location"])
            findings.append(
                {
                    "file": Path(cast(str, entry["filename"])).relative_to(cwd).as_posix(),
                    "line": start["row"],
                    "column": start["column"],
                    "end_line": end["row"],
                    "end_column": end["column"],
                    "code": entry["code"],
                    "message": entry["message"],
                }
            )
        return ExecutionObservation(
            outputs={
                "findings": findings,
                "result": to_data(
                    judge(findings, observations={"argv": list(result.argv), "cwd": result.cwd})
                ),
            }
        )

    return standard(
        "ruff",
        "EVALUATE",
        {"cwd": STRING, "files": STRINGS},
        {"findings": ARRAY},
        check,
        config=object_schema({"select": STRINGS}),
    )
