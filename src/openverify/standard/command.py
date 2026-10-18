"""Trusted command observations and separate explicit exit/output verification."""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from openverify.model import Context, Result
from openverify.relay.adapters.process import capture
from openverify.standard.common import OBJECT, judge, object_schema, standard


@dataclass(frozen=True)
class Command:
    """Host authorization fixes argv/cwd/env; graph data cannot choose a command."""

    argv: tuple[str, ...]
    cwd: Path
    env: dict[str, str] | None = None
    timeout: float = 30
    max_output_bytes: int = 2 * 1024 * 1024


def command_provider(command: Command):
    async def observe(inputs: Context, config: Context) -> Context:
        result = await capture(
            command.argv,
            str(command.cwd.resolve()),
            env=command.env,
            timeout=command.timeout,
            limit=command.max_output_bytes,
        )
        return {
            "observation": {
                "argv": list(result.argv),
                "cwd": result.cwd,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        }

    return standard("command", "DERIVE", {}, {"observation": OBJECT}, observe)


async def verify_observation(inputs: Context, config: Context) -> Result:
    observed = cast(Context, inputs["observation"])
    expected = config["exit_code"]
    findings: list[JsonValue] = (
        []
        if observed["returncode"] == expected
        else [{"code": "unexpected_exit", "expected": expected, "actual": observed["returncode"]}]
    )
    for field in ("stdout", "stderr"):
        if field in config and cast(str, config[field]) not in str(observed[field]):
            findings.append({"code": "output_missing", "stream": field, "required": config[field]})
    return judge(findings, observations=observed)


def command_observation_provider():
    shape = object_schema(
        {
            "returncode": {"type": "integer"},
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
            "argv": {"type": "array"},
            "cwd": {"type": "string"},
        },
        optional={"argv", "cwd"},
    )
    return standard(
        "command_check",
        "EVALUATE",
        {"observation": shape},
        {},
        verify_observation,
        config=object_schema(
            {
                "exit_code": {"type": "integer"},
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
            },
            optional={"stdout", "stderr"},
        ),
    )
