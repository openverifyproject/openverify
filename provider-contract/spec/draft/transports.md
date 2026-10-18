# Transport-neutral semantics; baseline stdio binding

The lifecycle is transport-neutral. This standard binding uses
[JSON-RPC 2.0](https://www.jsonrpc.org/specification), with the established
[LSP byte-length framing](https://raw.githubusercontent.com/microsoft/language-server-protocol/gh-pages/_specifications/lsp/3.17/specification.md)
only; it does not implement LSP methods or LSP lifecycle semantics.

Runner writes to provider stdin; provider writes to stdout. stderr is for logs.
stdout MUST contain only frames. Each frame is ASCII
`Content-Length: N\r\n\r\n` followed by exactly N bytes of one UTF-8 JSON object.
N is positive decimal digits counting bytes, not characters. Senders use exactly
that header. Receivers accept ASCII case-insensitive Content-Length, a single
space after colon, CRLF terminators, and no other/duplicate headers. Optional
Content-Type is omitted in this binding; UTF-8 is fixed. Partial reads and multiple
frames in one read MUST work. No newline delimiter is appended to bodies.
Invalid/oversized/truncated framing closes the session as PROTOCOL_VIOLATION;
there is no speculative resynchronization. Implementations MAY set documented
message/header size limits (SDK defaults: 16 MiB / 8 KiB); limits are transport
limits, not contract resource costs. A complete frame with invalid JSON gets the
standard JSON-RPC parse error where possible.

Requests use nonempty string IDs unique for the entire session, separate from
invocation_id. This binding uses object params, single messages (no batches),
and exactly these methods:

| direction | method | params | response result |
| --- | --- | --- | --- |
| runner -> provider request | initialize | InitializeRequest | InitializeResult |
| runner -> provider request | invoke | Invocation | terminal Outcome |
| runner -> provider request | cancel | CancelRequest | null acknowledgement |
| provider -> runner notification | event | ProviderEvent | no response |

No work before initialize success. Only one initialize attempt per session;
failure closes it. Invocation contract_version MUST match the negotiated version.
Other messages inherit that version from the session; they do not repeat a marker.
Provider MUST validate and accept or reject invoke in receive order before handling
later cancel requests. It MUST continue reading controls while invokes are pending.
All accepted-invoke failures use Outcome in result, never JSON-RPC error.
Provider MUST write all events for an invocation before its terminal response.
Runner MUST correlate both RPC ID and invocation_id; unsolicited responses and
notifications for unknown/rejected attempts are violations.

Cancel null acknowledges processing, not successful termination. It may arrive
before or after the invoke Outcome. A pending cancel for an invocation that has
already terminated succeeds as a no-op. Running unsupported/unknown cancellation
uses JSON-RPC error. No pause/resume/migrate/checkpoint methods exist.

JSON-RPC's reserved errors retain their meanings: -32700 parse error, -32600
invalid request, -32601 unknown method, -32602 invalid params, -32603 internal
RPC failure. Contract rejections use application code -32000, message from the
ProviderError, and data containing the ProviderError. This numeric code is not
the contract string code. Invalid invoke params use -32602 with
INVALID_INVOCATION data when available. Invalid notifications receive no reply
as required by JSON-RPC; receiver records a violation and closes the session.
Unknown methods receive -32601. No other provider RPCs are standardized.

Example JSON bodies (each independently byte-length framed):

```json
{"jsonrpc":"2.0","id":"init-1","method":"initialize","params":{"supported_contract_versions":["0.1"],"supported_vcp_versions":[]}}
```

Initialize returns `{contract_version: "0.1", manifest: <ProviderManifest>}` in
result. Afterward an ordinary attempt can be:

```json
{"jsonrpc":"2.0","id":"rpc-1","method":"invoke","params":{"invocation_id":"attempt-1","contract_version":"0.1","capability_id":"com.example.execution.echo","capability_version":"1","input":"hello","config":{}}}
{"jsonrpc":"2.0","id":"rpc-1","result":{"invocation_id":"attempt-1","state":"COMPLETED","output":"hello"}}
```

EOF/process death before pending outcomes is transport loss, not CANCELLED or
verification FAIL. No remote discovery, restart, retry, or replay is specified.
The SDK implements frame codecs and read-only session/trace validation, not an
executable runner/server. A provider in Rust, Go, Java, C#, Node, or Python can
implement this published binding without importing OpenVerify code.
