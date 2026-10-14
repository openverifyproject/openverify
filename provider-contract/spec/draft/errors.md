# Errors

ProviderError is `{code, message, details?}`. Codes are stable; messages/details
are informative and MUST NOT be used for programmatic classification.

| code | meaning |
| --- | --- |
| CONTRACT_VERSION_UNSUPPORTED | no common or wrong session contract version |
| CAPABILITY_UNAVAILABLE | requested capability ID absent |
| CAPABILITY_VERSION_UNSUPPORTED | ID exists but exact version absent |
| INVALID_INVOCATION | malformed invocation, unsupported constraint or VCP version |
| INVALID_CONFIG | config violates declared schema |
| INVALID_INPUT | input violates declared schema |
| INVALID_PROVIDER_OUTPUT | malformed manifest/event/outcome, invalid declared output or embedded VCP data |
| PROTOCOL_VIOLATION | correlation, sequence, lifecycle, framing, or session rule violated |

Other failures MUST use provider-namespaced codes, e.g. com.example.tool_failed.
The eight uppercase codes are reserved; unknown unnamespaced codes are invalid.
Contract errors MUST NOT be converted automatically into VCP FAIL. A literal
state FAIL or a core verdict field in an Outcome is detectable and rejected;
arbitrary capability output cannot reveal an incorrect VCP interpretation.

Checks proceed in order: JSON/structure/version, manifest semantics, session
compatibility, capability matching, input, config, constraints, lifecycle,
provider output. Where independent errors coexist, implementations SHOULD report
the first in that order. Fixtures contain one targeted failure except correlation
tests, where correlation/lifecycle is checked before decoding the body.

Before acceptance invoke rejection is a JSON-RPC error with ProviderError in
error.data. After acceptance execution failure is a successful JSON-RPC response
whose result is an ERROR Outcome. Invalid emitted output is a peer validation
failure; a runner MUST NOT rewrite the received data into a fabricated Outcome.
Local SDK ProviderContractError exposes the same code/message/details structure.
