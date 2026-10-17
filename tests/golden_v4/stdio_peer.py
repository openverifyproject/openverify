"""Compliant test provider for actual subprocess transport integration."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"));sys.path.insert(0,str(ROOT/"tests"))
from golden_v4.oracle import model as m
from openverify.provider import Outcome,ProviderEvent,parse_provider_manifest
from openverify.relay.adapters.server import serve_stdio


class Peer:
    def __init__(self):self.cancel_events={}
    def manifest(self):return parse_provider_manifest(m.manifest(deadlines=False))
    async def cancel(self,invocation_id,reason=None):
        if invocation_id in self.cancel_events:self.cancel_events[invocation_id].set()
    async def invoke(self,invocation):
        barrier=asyncio.Event();self.cancel_events[invocation.invocation_id]=barrier
        yield ProviderEvent(invocation_id=invocation.invocation_id,sequence=1,kind="progress",payload={"accepted":True})
        if invocation.input.get("wait_for_cancel"):
            await barrier.wait()
            yield Outcome(invocation_id=invocation.invocation_id,state="CANCELLED")
        else:yield Outcome(invocation_id=invocation.invocation_id,state="COMPLETED",output={"echo":invocation.input})


if __name__=="__main__":asyncio.run(serve_stdio(Peer()))
