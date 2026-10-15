"""Explicit fail-closed action policy and Result-to-Decision provider."""

from pathlib import PurePosixPath
from typing import cast

from openverify.model import Context, Result
from openverify.standard.common import STRING, STRINGS, judge, standard
from openverify.validation import parse_result


async def action_policy(inputs: Context, config: Context) -> Result:
    target = cast(str, inputs["target"]).replace("\\", "/")
    path = PurePosixPath(target)
    safe = not path.is_absolute() and ".." not in path.parts and ":" not in target
    allowed = safe and any(
        target.startswith(prefix) and prefix.endswith("/")
        for prefix in cast(list[str], inputs["allowed_prefixes"])
    )
    return judge(
        []
        if inputs["action"] == "delete" and allowed
        else [{"code": "action_denied", "action": inputs["action"], "target": target}]
    )


async def gate_decision(inputs: Context, config: Context) -> Context:
    result = parse_result(inputs["checked"])
    passed = (
        result.disposition == "EXECUTED"
        and result.execution_outcome == "SUCCESS"
        and result.applicability == "APPLICABLE"
        and result.determination == "KNOWN"
        and result.verdict == "PASS"
    )
    return {"decision": {"protocol": "draft", "kind": "CONTINUE" if passed else "STOP_FAILURE"}}


def control_providers():
    return [
        standard(
            "action_policy",
            "EVALUATE",
            {"action": STRING, "target": STRING, "allowed_prefixes": STRINGS},
            {},
            action_policy,
        ),
        standard("gate", "CONTROL", {"checked": {"type": "object"}}, {}, gate_decision),
    ]
