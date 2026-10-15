"""A new phrase verifier: manifest, implementation, registration, graph and invocation."""

import asyncio
import json

from openverify import Graph, Relay
from openverify.model import Context, Evidence, Result
from openverify.provider import wire_data
from openverify.relay import provider
from openverify.standard import standard_catalog
from openverify.standard.common import OBJECT, STRING, object_schema


@provider(
    provider_id="com.example.phrase_provider",
    provider_version="1",
    capability_id="com.example.prohibited_phrase",
    capability_version="1",
    kind="EVALUATE",
    input_schema=object_schema({"text": STRING, "subject": OBJECT, "criterion": OBJECT}),
    config_schema=object_schema({"phrase": STRING}),
    output_schema=object_schema({"result": OBJECT}),
)
async def prohibited_phrase(inputs: Context, config: Context) -> Result:
    phrase = str(config["phrase"])
    text = str(inputs["text"])
    offset = text.find(phrase)
    finding: Context = {
        "code": "prohibited_phrase",
        "phrase": phrase,
        "start": offset,
        "end": offset + len(phrase),
    }
    return Result(
        disposition="EXECUTED",
        execution_outcome="SUCCESS",
        applicability="APPLICABLE",
        determination="KNOWN",
        verdict="FAIL" if offset >= 0 else "PASS",
        output={"findings": [finding] if offset >= 0 else []},
        evidence=[Evidence(structured_data=finding)] if offset >= 0 else [],
    )


def graph() -> Graph:
    graph = Graph("custom-phrase")
    text = graph.input("text", STRING)
    graph.evaluate(
        "phrase", "com.example.prohibited_phrase", inputs={"text": text}, config={"phrase": "TBD"}
    )
    return graph


async def main() -> None:
    print(json.dumps(wire_data(prohibited_phrase.manifest())))
    catalog = standard_catalog()
    catalog.register(prohibited_phrase, concurrency_safe=True)
    result = await Relay(catalog=catalog).run(graph(), inputs={"text": "Release TBD"})
    print(result.to_json())
    assert result.results["phrase"].verdict == "FAIL"


if __name__ == "__main__":
    asyncio.run(main())
