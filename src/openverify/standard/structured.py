"""Strict JSON parsing and offline SDK JSON Schema checks."""

from typing import cast

from openverify.errors import ProtocolError
from openverify.json_schema import check_schema, validate_value
from openverify.model import Context, JsonSchema, Result
from openverify.serialization import decode
from openverify.standard.common import STRING, judge, object_schema, standard


async def parse_json(inputs: Context, config: Context) -> Context:
    return {"value": decode(inputs["text"])}


async def schema_check(inputs: Context, config: Context) -> Result:
    schema = cast(JsonSchema, config["schema"])
    check_schema(schema)
    try:
        validate_value(schema, inputs["value"])
    except ProtocolError as exc:
        return judge([{"code": "schema_mismatch", "message": exc.message}])
    return judge([])


def structured_providers():
    return [
        standard("json_parse", "DERIVE", {"text": STRING}, {"value": True}, parse_json),
        standard(
            "schema",
            "EVALUATE",
            {"value": True},
            {},
            schema_check,
            config=object_schema({"schema": {"type": ["object", "boolean"]}}),
        ),
    ]
