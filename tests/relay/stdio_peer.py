"""An actual subprocess peer for transport failure injection and cancellation."""

import sys
from io import BufferedReader
from pathlib import Path
from typing import cast

from openverify.model import Context
from openverify.provider import wire_data
from openverify.provider.stdio import FrameDecoder, encode_frame
from tests.relay.helpers import echo_provider


def main() -> None:
    mode = sys.argv[1]
    decoder = FrameDecoder()
    invoke_id = ""
    rpc_id = ""
    for chunk in iter(lambda: cast(BufferedReader, sys.stdin.buffer).read1(65536), b""):
        for message in decoder.feed(chunk):
            params = cast(Context, message["params"])
            if message["method"] == "initialize":
                response: Context = {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "result": {
                        "contract_version": "0.1",
                        "manifest": wire_data(echo_provider().manifest()),
                    },
                }
            elif message["method"] == "cancel":
                if len(sys.argv) > 2:
                    Path(sys.argv[2]).write_text("cancel received")
                response = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {"invocation_id": invoke_id, "state": "CANCELLED"},
                }
            else:
                invoke_id = str(params["invocation_id"])
                rpc_id = str(message["id"])
                if mode == "exit":
                    return
                if mode == "malformed":
                    sys.stdout.buffer.write(b"not JSON-RPC\n")
                    sys.stdout.buffer.flush()
                    return
                if mode == "hang":
                    sys.stdout.buffer.write(
                        encode_frame(
                            {
                                "jsonrpc": "2.0",
                                "method": "event",
                                "params": {
                                    "invocation_id": invoke_id,
                                    "sequence": 1,
                                    "kind": "progress",
                                    "payload": "accepted",
                                },
                            }
                        )
                    )
                    sys.stdout.buffer.flush()
                    continue
                response = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "invocation_id": invoke_id if mode != "correlation" else "wrong",
                        "state": "COMPLETED",
                        "output": params["input"],
                    },
                }
            frame = encode_frame(response)
            sys.stdout.buffer.write(
                frame + (frame if mode == "duplicate" and message["method"] == "invoke" else b"")
            )
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
