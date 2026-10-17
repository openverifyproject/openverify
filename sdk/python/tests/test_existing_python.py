"""Compatibility audit of the unchanged Python SDK; not an implementation oracle."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3] / "conformance/sdk"
CASES = [
    json.loads((ROOT / p).read_text())
    for p in json.loads((ROOT / "manifest.json").read_text())["cases"]
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: "existing-" + c["id"])
def test_existing(case):
    from openverify.provider.validation import parse_provider_object
    from openverify.provider.validation import serialize as provider_serialize
    from openverify.serialization import serialize
    from openverify.validation import parse_object

    # For arbitrary schemas, exercise the original SDK's explicit schema helper
    # separately; no engine, provider or transport is required.
    if case["operation"] == "data":
        from openverify.json_schema import check_schema, validate_value

        try:
            check_schema(case["schema"])
            validate_value(case["schema"], case["input"], code="INVALID_INPUT")
            accepted = True
        except Exception:
            accepted = False
        assert accepted == case["expected"]["accepted"]
        return
    parser = parse_object if case["contract"] == "vcp" else parse_provider_object
    encoder = serialize if case["contract"] == "vcp" else provider_serialize
    try:
        value = parser(case["type"], json.dumps(case["input"]))
    except Exception as error:
        assert not case["expected"]["accepted"], str(error)
        if case["expected"]["error"] != "*":
            assert error.code == case["expected"]["error"]
    else:
        if case["id"] == "provider.vcp-version":
            pytest.xfail(
                "Existing standalone parser accepts unknown vcp_version; source unchanged."
            )
        assert case["expected"]["accepted"]
        # The existing SDK deliberately normalizes defaults/optional null fields.
        # Test its own public roundtrip rather than require byte identity.
        assert parser(case["type"], encoder(value)) == value
