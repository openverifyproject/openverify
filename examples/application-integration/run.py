"""Arbitrary typed application information and already-produced output."""

import asyncio

from openverify import Graph, Relay
from openverify.model import Context


async def main() -> None:
    graph = Graph("inventory-record")
    value = graph.input("inventory", {"type": "object"})
    graph.evaluate(
        "contract",
        "openverify.schema",
        inputs={"value": value},
        config={
            "schema": {
                "type": "object",
                "required": ["sku", "quantity"],
                "additionalProperties": False,
                "properties": {
                    "sku": {"type": "string", "minLength": 1},
                    "quantity": {"type": "integer", "minimum": 0},
                },
            }
        },
    )
    relay = Relay()
    inputs: Context = {"inventory": {"sku": "ITEM-42", "quantity": -1}}
    failure = await relay.run(graph, inputs=inputs)
    assert failure.results["contract"].verdict == "FAIL"
    inputs["inventory"] = {"sku": "ITEM-42", "quantity": 3}
    success = await relay.run(graph.to_json(), inputs=inputs)
    assert success.results["contract"].verdict == "PASS"
    print(success.to_json())


if __name__ == "__main__":
    asyncio.run(main())
