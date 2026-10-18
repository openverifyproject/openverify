# Portable conformance suite

`manifest.json` lists cases by id, object_type, input, valid, expected, and spec.
An invalid case has a stable error_code. Paths are relative to this directory;
expected files contain valid and, for invalid cases, error_code. Implementations
must check both schema structure and prose semantics. Do not compare library
exception messages. The suite requires no Python or provider executable.

Wire object types name the schemas. Valid objects must survive parse/serialize
with JSON types and values preserved. Integral event numbers may normalize notation.
Capability schema validation and compatibility need lifecycle context.

`lifecycle` fixtures follow the trace format in [lifecycle](../spec/draft/lifecycle.md).
`stdio-session` fixtures are arrays of `{direction, message, now?}`; direction is
runner/provider, message is a JSON-RPC object, and now is a provider-clock UTC
observation for deadline validation. End of the array requires no pending RPCs
and all accepted invocations terminal. Initialization rejection closes a session.
An invoke rejection before observable acceptance has no terminal Outcome.

`framing` fixtures have chunks (hexadecimal byte strings fed in order) and
message_count. Decode frames, then signal EOF. Invalid cases fail before or at
EOF. Valid cases require exactly message_count decoded messages. These test
UTF-8 byte lengths, split/coalesced reads, and unambiguous failure on bad framing.

Maintenance: `uv run python tools/build_provider_schemas.py`, then
`uv run python tools/build_provider_fixtures.py`. Schemas reference the existing
root VCP schemas; supply both directories to an offline schema resolver.
