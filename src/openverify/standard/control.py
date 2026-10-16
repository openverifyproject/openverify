"""Explicit fail-closed action policy and Result-to-Decision provider."""

from typing import cast

from openverify.model import Context, Result
from openverify.standard.common import STRING, STRINGS, judge, standard
from openverify.standard.paths import local_path
from openverify.validation import parse_result


async def action_policy(inputs: Context, config: Context) -> Result:
    target = cast(str, inputs["target"])
    try:
        path = local_path(target)
        prefixes = [local_path(p) for p in cast(list[str], inputs["allowed_prefixes"])]
        allowed = (
            not path.is_absolute()
            and bool(path.parts)
            and all(not p.is_absolute() and bool(p.parts) for p in prefixes)
            and any(path != p and path.is_relative_to(p) for p in prefixes)
        )
    except ValueError:
        allowed = False
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
