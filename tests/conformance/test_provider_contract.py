import json
from typing import cast

import pytest
from jsonschema import Draft202012Validator
from pydantic import JsonValue

from openverify.provider import (
    ProviderContractError,
    load_provider_schema,
    parse_provider_object,
    serialize,
)
from openverify.provider.conformance import check_case, check_manifest
from openverify.serialization import json_equal
from tests.helpers import ROOT

DIRECTORY = ROOT / "provider-contract/conformance"
CASES: list[dict[str, JsonValue]] = json.loads(
    (DIRECTORY / "manifest.json").read_text(encoding="utf-8")
)["cases"]


@pytest.mark.parametrize("case", CASES, ids=[cast(str, c["id"]) for c in CASES])
def test_provider_case(case: dict[str, JsonValue]) -> None:
    raw = cast(
        JsonValue, json.loads((DIRECTORY / cast(str, case["input"])).read_text(encoding="utf-8"))
    )
    expected = json.loads((DIRECTORY / cast(str, case["expected"])).read_text(encoding="utf-8"))
    assert expected["valid"] == case["valid"]
    name = cast(str, case["object_type"])
    if case["valid"]:
        check_case(name, raw)
        if name not in ("lifecycle", "stdio-session", "framing"):
            value = parse_provider_object(name, raw)
            assert json_equal(raw, cast(JsonValue, json.loads(serialize(value))))
    else:
        with pytest.raises(ProviderContractError) as exc:
            check_case(name, raw)
        assert exc.value.code == expected["error_code"] == case["error_code"]


def test_provider_schema_copies_and_suite() -> None:
    for path in (ROOT / "provider-contract/schemas/draft").glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert load_provider_schema(path.name.removesuffix(".schema.json")) == schema
    assert check_manifest(DIRECTORY) == []
