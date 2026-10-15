"""Independent graph definitions and typed inputs sharing one Relay instance."""

import asyncio

from openverify import Graph, Relay


def graph(name: str, prohibited: str) -> Graph:
    graph = Graph(name)
    text = graph.input("text", {"type": "string"})
    graph.evaluate(
        "check", "openverify.text", inputs={"text": text}, config={"prohibited": [prohibited]}
    )
    return graph


async def main() -> None:
    relay = Relay()
    security, formatting = await asyncio.gather(
        relay.run(graph("agent-A-security", "secret"), inputs={"text": "contains secret"}),
        relay.run(graph("agent-B-formatting", "TODO"), inputs={"text": "finished"}),
    )
    assert security.results["check"].verdict == "FAIL"
    assert formatting.results["check"].verdict == "PASS"
    assert security.record.run_id != formatting.record.run_id
    print(security.record.definition.id, security.results["check"].verdict)
    print(formatting.record.definition.id, formatting.results["check"].verdict)


if __name__ == "__main__":
    asyncio.run(main())
