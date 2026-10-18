"""Actual Provider error categories and sequence relations, not vocabulary-only checks."""

import pytest

from openverify.provider import LifecycleValidator, ProviderContractError, parse_provider_manifest
from tests.unit.test_provider_contract import invocation_data, manifest_data


@pytest.mark.parametrize(
    "code",
    [
        "CONTRACT_VERSION_UNSUPPORTED",
        "CAPABILITY_UNAVAILABLE",
        "CAPABILITY_VERSION_UNSUPPORTED",
        "INVALID_INVOCATION",
        "INVALID_CONFIG",
        "INVALID_INPUT",
        "INVALID_PROVIDER_OUTPUT",
        "PROTOCOL_VIOLATION",
    ],
)
def test_error_category_has_exact_observable_code(code, request):
    lifecycle = LifecycleValidator(parse_provider_manifest(manifest_data()))
    initialize = {"supported_contract_versions": ["0.1"], "supported_vcp_versions": ["draft"]}
    if code == "CONTRACT_VERSION_UNSUPPORTED":
        operation = lambda: lifecycle.initialize(
            {**initialize, "supported_contract_versions": ["0.2"]}
        )
    else:
        assert lifecycle.initialize(initialize) == "0.1"
        invocation = invocation_data()
        if code in ("INVALID_PROVIDER_OUTPUT", "PROTOCOL_VIOLATION"):
            assert lifecycle.accept(invocation) is None
            if code == "INVALID_PROVIDER_OUTPUT":
                operation = lambda: lifecycle.outcome(
                    {"invocation_id": "attempt-1", "state": "COMPLETED", "output": 17}
                )
            else:
                event = {
                    "invocation_id": "attempt-1",
                    "sequence": 1,
                    "kind": "progress",
                    "payload": None,
                }
                assert lifecycle.event(event) is None
                operation = lambda: lifecycle.event(event)
        else:
            mutation = {
                "CAPABILITY_UNAVAILABLE": {"capability_id": "com.example.unadvertised"},
                "CAPABILITY_VERSION_UNSUPPORTED": {"capability_version": "not-advertised"},
                "INVALID_INVOCATION": {"vcp_version": "unsupported"},
                "INVALID_INPUT": {"input": 17},
                "INVALID_CONFIG": {"config": {"undeclared": 17}},
            }[code]
            operation = lambda: lifecycle.accept({**invocation, **mutation})
    with pytest.raises(ProviderContractError) as caught:
        operation()
    assert str(caught.value.code) == code
    assert caught.value.as_dict()["code"] == code
    request.node.expected = {"code": code}
    request.node.actual = {"code": str(caught.value.code)}
    request.node.canonical_ids = ["CM.PROVIDER.ERROR." + code]


@pytest.mark.parametrize(
    "sequences,accepted",
    [
        ([1], True),
        ([2], False),
        ([1, 1], False),
        ([1, 3, 2], False),
        ([1, 3, 9007199254740991], True),
    ],
    ids=["FIRST", "FIRST_NOT_ONE", "DUPLICATE", "REORDER", "GAP_TO_MAX"],
)
def test_sequence_relations(sequences, accepted, request):
    lifecycle = LifecycleValidator(parse_provider_manifest(manifest_data()))
    assert (
        lifecycle.initialize({"supported_contract_versions": ["0.1"], "supported_vcp_versions": []})
        == "0.1"
    )
    assert lifecycle.accept(invocation_data()) is None

    def events():
        for sequence in sequences:
            assert (
                lifecycle.event(
                    {
                        "invocation_id": "attempt-1",
                        "sequence": sequence,
                        "kind": "progress",
                        "payload": None,
                    }
                )
                is None
            )

    if accepted:
        events()
    else:
        with pytest.raises(ProviderContractError, match="PROTOCOL_VIOLATION"):
            events()
    request.node.canonical_ids = [
        "CM.PROVIDER.LIFE.SEQUENCE."
        + {
            "FIRST": "FIRST",
            "FIRST_NOT_ONE": "FIRST",
            "DUPLICATE": "DUPLICATE",
            "REORDER": "REORDER",
            "GAP_TO_MAX": "GAPS",
        }[request.node.callspec.id]
    ]


def test_two_invocations_interleave_without_sharing_sequence(request):
    lifecycle = LifecycleValidator(parse_provider_manifest(manifest_data()))
    assert (
        lifecycle.initialize({"supported_contract_versions": ["0.1"], "supported_vcp_versions": []})
        == "0.1"
    )
    for identity in ["a", "b"]:
        assert lifecycle.accept({**invocation_data(), "invocation_id": identity}) is None
    for identity, seq in [("a", 1), ("b", 1), ("a", 3), ("b", 2)]:
        assert (
            lifecycle.event(
                {"invocation_id": identity, "sequence": seq, "kind": "progress", "payload": None}
            )
            is None
        )
    for identity in ["b", "a"]:
        assert (
            lifecycle.outcome({"invocation_id": identity, "state": "COMPLETED", "output": "hello"})
            is None
        )
    assert lifecycle.finish() is None
    request.node.canonical_ids = ["CM.PROVIDER.LIFE.INTERLEAVING"]
