# Wire objects

Normative encoding is UTF-8 JSON, with Draft 2020-12 schemas under
`urn:openverify:provider:0.1:`. Existing VCP references retain
`urn:verification:draft:` IDs and MUST resolve from supplied schemas offline.
Duplicate JSON keys, nonfinite numbers, invalid UTF-8, and non-JSON values are
invalid. Unknown core fields MUST be rejected. Optional core fields MUST be absent
instead of null, except arbitrary JSON values (input, config, output, context,
error details, event payloads, and extension data), where null is real data.
Schema defaults do not insert fields.

Booleans are never numbers. Integers allow integral numeric notation (1.0 equals
1) but not numeric strings. Event sequences are integers in [1, 9007199254740991]
so baseline peers can represent them exactly. Other JSON numbers have their JSON
mathematical value; implementations MUST reject values they cannot represent or
validate faithfully, rather than silently coerce types. No canonical number
format, signing bytes, or bit-identical resource arithmetic is defined.

Invocation IDs and RPC request IDs are case-sensitive nonempty opaque strings.
An invocation_id identifies one attempt, MUST NOT be reused in a session (including
rejected attempts), and SHOULD be globally unique, for example a UUID. Retries are
new attempts with new IDs; there is no idempotent replay guarantee.

Invocation requires invocation_id, contract_version, capability_id,
capability_version, input, config. input/config MUST validate against the matched
schemas. Optional context is arbitrary JSON reference/context data, never implicit
instructions to resolve content. Optional deadline is a UTC RFC3339 timestamp
(Z/z or +00:00, fractional seconds permitted). Optional resource_budget is a VCP
ResourceVector of EXACT measurements: each value is an upper consumption limit
in its explicit unit. A provider MUST reject a budget it cannot enforce, MUST NOT
silently drop dimensions or convert units, and MUST end with ERROR and a
provider-namespaced error if enforcement prevents completion. Limits are not cost
estimates. Reuse of the VCP mapping introduces no new resource ontology.

ProviderEvent requires invocation_id, sequence, kind, payload. Standard kinds:

| kind | payload |
| --- | --- |
| progress | arbitrary JSON advisory information |
| evidence | existing VCP Evidence, including its semantic invariants |
| artifact | existing VCP ArtifactRef |
| resource_usage | existing VCP ResourceVector observation |
| diagnostic | arbitrary JSON diagnostic information |
| extension | object with namespaced `namespace` and arbitrary JSON `data` |

Custom non-verification observations use progress/diagnostic/extension payloads
defined by their capability specification. They do not masquerade as VCP Evidence.
Optional timestamp follows the same UTC syntax and does not define ordering.

CancelRequest requires invocation_id and MAY contain a nonempty reason.
Outcome requires invocation_id and state. COMPLETED requires output, including
explicit null if admitted by output_schema, and forbids error. ERROR requires a
ProviderError and forbids output. CANCELLED/DEADLINE_EXCEEDED forbid output/error.
All states MAY contain resource_usage and extensions. No verdict core field exists.
ProviderError requires code/message and MAY include arbitrary JSON details.

Every contract object except ProviderError supports optional extensions: a JSON
object mapping collision-resistant identifier keys to arbitrary JSON values.
Unknown entries MUST survive parse/serialize roundtrip with JSON types and values
preserved (not whitespace/key order). They are optional annotations only and MUST
NOT alter core meaning. Mandatory extension semantics cannot be expressed in 0.1;
an implementation requiring them MUST reject the operation as PROTOCOL_VIOLATION
rather than encode them as ignored optional data. Negotiation is OPEN. These are
Provider Contract extension containers; embedded VCP objects retain VCP's own
extension representation and unsupported-required-extension rules.
