# Relay Client v1 (local host interface)

Status: implementation draft. This interface is a host API; it does not add VCP
objects or change Provider Contract meaning.

The host reads UTF-8 JSON objects, one per LF-terminated line on standard input,
and writes one JSON object per line to standard output. A line is limited to
1,048,576 bytes. Every request has `client_version: "1"`, a nonempty string `id`
for response correlation, and an `op`. Responses contain the same `id`, `ok`, and
either `result` or `error: {code, message}`. Responses may be out of order.
The host continues to process requests while a run is active.

| Operation | Required fields | Result |
| --- | --- | --- |
| `register` | `definition` (complete VCP definition) | opaque `graph_id`, revision 1 |
| `replace` | `graph_id`, `definition` | new immutable numbered revision |
| `get` | `graph_id`; optional positive `revision` | complete definition and revision |
| `run` | `graph_id`, `inputs`; optional `revision`, `request_id` | pinned revision and validated RunRecord |
| `lookup` | `request_id` | state, revision, and record when completed |
| `cancel` | `request_id` | `CANCELLING` for active run, current state otherwise |

The host chooses providers from trusted configuration, never from the client
request. Each run pins the definition before execution. Completed records survive
restart in SQLite. An in-flight run found after restart is `INTERRUPTED` with no
fabricated VCP RunRecord. A cooperative cancellation may complete with a VCP
cancelled Result. The host does not promise an immediate terminal response to
`cancel`.

`openverify client --database relay.db` starts this interface. The database is a
local single-host adapter. It is not a distributed queue or provider registry.

## Example

```json
{"client_version":"1","id":"a","op":"get","graph_id":"opaque-id","revision":1}
```

## Open interoperability questions

Authentication, multihost coordination, reconnect/resume, cross-process cancel,
idempotency keys, and portable timing of cancellation are not specified in v1.
