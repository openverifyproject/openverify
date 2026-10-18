# Portable draft conformance

`manifest.json` enumerates deterministic UTF-8 JSON fixtures and expected outcomes.
Paths are relative to this directory; spec references are relative to the root.
`stage` identifies structural versus semantic invalidity. Unsupported required
extensions and unsupported graph features test this implementation's declared subset.

Implementations first check the normative Draft 2020-12 schema, then the prose
invariants. Schema-invalid fixtures use PROTOCOL_STRUCTURE except for an
unsupported protocol marker, which uses PROTOCOL_VERSION. No external resolution
is needed. Expected files are portable outcomes, not Python exception snapshots.

`binding-*` cases cover concrete ProviderBinding identity syntax, exact operation
compatibility, occurrence/node/executor identity consistency, identity mutations,
and host output rejection with retained usage. They require no provider rerun or
manifest discovery. Provider Contract schema validation itself remains covered by
its own portable suite; ordinary engine regressions exercise its enforcement.
