"""Build, inspect, serialize, parse and execute a complete custom VCP graph."""

import asyncio

from openverify import Graph, Relay, parse_definition
from openverify.model import Constant


async def main() -> None:
    graph = Graph("document-policy")
    text = graph.input("text", {"type": "string"})
    terms = graph.input(
        "required",
        {"type": "array", "items": {"type": "string"}},
        required=False,
        default=Constant(value=["Migration", "Rollback"]),
    )
    required = graph.evaluate(
        "required", "openverify.text", inputs={"text": text, "required_terms": terms}
    )
    forbidden = graph.evaluate(
        "forbidden", "openverify.text", inputs={"text": text}, config={"prohibited": ["TODO"]}
    )
    graph.aggregate("all", {"required": required.result, "forbidden": forbidden.result})
    graph.validate()
    print(graph.inspect()["node_order"])
    definition = parse_definition(graph.to_json())
    result = await Relay().run(
        definition, inputs={"text": "Migration and Rollback are documented."}
    )
    assert result.results["all"].verdict == "PASS"
    print(result.to_json())


if __name__ == "__main__":
    asyncio.run(main())
