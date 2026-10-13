import json
from typing import cast

import pytest
from jsonschema import Draft202012Validator
from pydantic import JsonValue

from openverify.conformance import check_manifest
from openverify.errors import ProtocolError
from openverify.serialization import serialize
from openverify.validation import load_schema, parse_object, validate_wire
from tests.helpers import ROOT

CASES: list[dict[str, JsonValue]] = json.loads(
    (ROOT / "conformance/manifest.json").read_text(encoding="utf-8")
)["cases"]


@pytest.mark.parametrize("case", CASES, ids=[cast(str, c["id"]) for c in CASES])
def test_portable_case(case: dict[str, JsonValue]) -> None:
    name = cast(str, case["object_type"])
    path = ROOT / "conformance" / cast(str, case["input"])
    raw = cast(JsonValue, json.loads(path.read_text(encoding="utf-8")))
    expected = json.loads(
        (ROOT / "conformance" / cast(str, case["expected"])).read_text(encoding="utf-8")
    )
    assert expected["valid"] == case["valid"]
    if case["valid"]:
        validate_wire(name, raw)
        value = parse_object(name, raw)
        assert parse_object(name, serialize(value)) == value
    else:
        if case["stage"] == "semantic":
            validate_wire(name, raw)
        else:
            with pytest.raises(ProtocolError):
                validate_wire(name, raw)
        with pytest.raises(ProtocolError) as error:
            parse_object(name, raw)
        assert error.value.code == case["error_code"] == expected["error_code"]


def test_all_schemas_and_packaged_copies() -> None:
    for path in (ROOT / "schemas/draft").glob("*.schema.json"):
        name = path.name.removesuffix(".schema.json")
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert load_schema(name) == schema
    assert json.loads(
        (ROOT / "profiles/standard-draft/profile.json").read_text(encoding="utf-8")
    ) == json.loads((ROOT / "src/openverify/data/profile.json").read_text(encoding="utf-8"))
    assert check_manifest(ROOT / "conformance") == []
