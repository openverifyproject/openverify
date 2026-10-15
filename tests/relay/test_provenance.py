"""Adversarial contradictions through the unchanged VCP SDK validation boundary."""

from copy import deepcopy
from typing import cast

import pytest
from pydantic import JsonValue

from openverify import ProtocolError, Relay, parse_run_record
from openverify.model import Context
from openverify.relay.templates import text_graph
from openverify.serialization import to_data


@pytest.mark.parametrize(
    "mutation",
    [
        "input",
        "bool_number",
        "provider",
        "capability",
        "upstream",
        "membership",
        "reason",
        "worktree",
    ],
)
def test_inconsistent_provenance_rejected(mutation: str) -> None:
    record = Relay().run_sync(text_graph(), inputs={"text": "Migration Rollback"}).record
    raw = cast(Context, deepcopy(to_data(record)))
    nodes = cast(list[Context], raw["nodes"])
    first, _, aggregate = nodes
    if mutation == "input":
        cast(Context, first["input_values"])["text"] = "different"
    elif mutation == "bool_number":
        cast(Context, first["input_values"])["text"] = True
    elif mutation == "provider":
        cast(Context, first["provider_binding"])["provider_id"] = "com.example.substituted"
    elif mutation == "capability":
        cast(Context, first["provider_binding"])["capability_version"] = "other"
    elif mutation == "upstream":
        cast(Context, cast(Context, aggregate["input_values"])["required"])["verdict"] = "FAIL"
    elif mutation == "membership":
        cast(Context, aggregate["input_values"])["members"] = ["prohibited", "required"]
    elif mutation == "reason":
        first.update(state="NONEXECUTED", reason="CONTROL_STOP")
    elif mutation == "worktree":
        # A different checked identity cannot replace one consumed snapshot alone.
        cast(Context, first["input_values"])["subject"] = {
            "id": "another-worktree",
            "type": "git",
            "locator": "elsewhere",
        }
    with pytest.raises(ProtocolError):
        parse_run_record(raw)


def test_unauthenticated_annotations_do_not_claim_authentication() -> None:
    run = Relay().run_sync(text_graph(), inputs={"text": "Migration Rollback"})
    extension = run.record.extensions[0]
    assert isinstance(extension.data, dict)
    invocations = cast(Context, extension.data["invocations"])
    ids: list[JsonValue] = []
    for node_id, value in invocations.items():
        trace = cast(Context, value)
        invocation = cast(Context, trace["invocation"])
        outcome = cast(Context, trace["outcome"])
        ids.append(invocation["invocation_id"])
        assert outcome["invocation_id"] == invocation["invocation_id"]
        assert trace["provider_id"] == run.record.provider_bindings[node_id].provider_id
    assert len(ids) == len(set(cast(list[str], ids))) == 3
