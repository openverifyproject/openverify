"""Run as a real external Provider Contract process: python provider.py."""

import asyncio
import sys
from pathlib import Path

# This example reuses the adjacent example's provider, not any Relay execution logic.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom-provider"))
from check import prohibited_phrase  # noqa: E402

from openverify.relay.adapters.server import serve_stdio  # noqa: E402

if __name__ == "__main__":
    asyncio.run(serve_stdio(prohibited_phrase))
