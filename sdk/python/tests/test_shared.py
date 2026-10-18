import json
from pathlib import Path

import pytest
from openverify_sdk import ProtocolError, parse, serialize, validate_data

ROOT = Path(__file__).resolve().parents[3] / "conformance/sdk"
CASES = [
    json.loads((ROOT / p).read_text())
    for p in json.loads((ROOT / "manifest.json").read_text())["cases"]
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_shared(case):
    def action():
        if case["operation"] == "data":
            validate_data(case["schema"], case["input"])
            return case["input"]
        return json.loads(
            serialize(parse(case["contract"], case["type"], json.dumps(case["input"])))
        )

    if case["expected"]["accepted"]:
        assert action() == case["expected"]["normalized"]
    else:
        with pytest.raises(ProtocolError) as exc:
            action()
        if case["expected"]["error"] != "*":
            assert exc.value.code == case["expected"]["error"]


def test_duplicate():
    with pytest.raises(ProtocolError, match="Duplicate"):
        parse("vcp", "result", '{"protocol":"draft","protocol":"draft"}')


@pytest.mark.parametrize("number", ["1e400", "1.234567890123456789"])
def test_unsupported_numeric_precision(number):
    with pytest.raises(ProtocolError):
        parse(
            "provider",
            "outcome",
            '{"invocation_id":"i","state":"COMPLETED","output":' + number + "}",
        )
