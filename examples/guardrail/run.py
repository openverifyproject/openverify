"""The host owns the operation. verify_before actually blocks calling it."""

import asyncio

from openverify import Relay
from openverify.errors import ProtocolError
from openverify.relay.templates import guardrail_graph


async def main() -> None:
    called: list[str] = []

    async def action() -> str:
        called.append("action ran")
        return "permitted"

    relay = Relay()
    inputs = {"action": "delete", "target": "src/auth.py", "allowed_prefixes": ["tmp/"]}
    try:
        await relay.verify_before(action, guardrail_graph(), inputs=inputs)
    except ProtocolError as exc:
        print(exc.code)
    assert not called
    inputs["target"] = "tmp/disposable.txt"
    print(await relay.verify_before(action, guardrail_graph(), inputs=inputs))
    assert called == ["action ran"]


if __name__ == "__main__":
    asyncio.run(main())
