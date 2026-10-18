"""Unknown code extensibility cannot substitute custom display/equality behavior."""

import json
from enum import StrEnum

import pytest

from openverify.errors import ProtocolError
from openverify.model import Context
from openverify.provider import ProviderContractError
from openverify.relay.errors import RelayError
from openverify.serialization import decode


class HostCode(StrEnum):
    FAILURE = "com.example.failure"

    def __str__(self) -> str:
        return "INVALID_PROVIDER_OUTPUT"

    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = str.__hash__


@pytest.mark.parametrize("error_type", [ProtocolError, ProviderContractError, RelayError])
def test_extensible_codes_use_underlying_string(
    error_type: type[ProtocolError] | type[ProviderContractError],
) -> None:
    error = error_type(HostCode.FAILURE, "diagnostic", details={"nested": [False, 0, None]})
    assert type(error.code) is str
    assert error.code == "com.example.failure"
    assert error.code != "INVALID_PROVIDER_OUTPUT"
    assert json.loads(json.dumps(error.as_dict()))["code"] == "com.example.failure"
    assert str(error).startswith("com.example.failure")


def test_nested_enum_normalization_copies_changed_containers_only() -> None:
    unchanged: Context = {"safe": [False, 0, None]}
    nested: Context = {"code": HostCode.FAILURE, "unchanged": unchanged}
    original: Context = {"nested": [nested]}
    normalized = decode(original)
    assert normalized == {"nested": [{"code": "com.example.failure", "unchanged": unchanged}]}
    assert normalized is not original
    assert original["nested"] == [nested]
    assert nested["code"] is HostCode.FAILURE
    assert decode(unchanged) is unchanged
