# Manifest and capabilities

ProviderManifest requires provider_id, provider_version,
supported_contract_versions, supported_vcp_versions, and capabilities. Arrays of
versions contain unique nonempty strings. Contract versions are exact identifiers,
not numbers or ranges. An empty VCP list means no VCP interchange. Capabilities
may be empty. The manifest is a snapshot fixed for one initialized session.

Each capability requires capability_id, capability_version, input_schema,
output_schema, config_schema, and lifecycle_features. Identity is the pair
(capability_id, capability_version), which MUST be unique within a manifest.
Multiple versions of one ID MAY be advertised. Schemas MUST be valid Draft 2020-12
objects or boolean schemas. They MUST be self-contained: references use only
local JSON Pointer fragments (`#` or `#/...`) that resolve to schema objects or
booleans within the root schema. Nested resource `$id` values, dynamic
references/anchors, and external resolution are unsupported. Root `$id` is allowed.
Object targets MUST occupy schema positions under standard Draft 2020-12 keywords
or `$defs`; arbitrary annotation objects are not schema targets in this subset.
Schema annotations are not executed.
Standard JSON Schema validation keywords apply; `format` is annotation-only in
capability schemas. In schema instance equality, boolean and number are distinct,
including enum/const/uniqueItems. No Python coercions are allowed.

Identifiers for providers, capabilities, extension keys, and provider-specific
error codes use lowercase dot-separated ASCII segments matching
`[a-z][a-z0-9_]*`, with at least three segments for third parties. A domain prefix
of at least two segments MUST be controlled by the publisher and written in reverse
label order, followed by at least one local identifier segment, such as
`com.example.verifier.smt` or `uk.co.example.execution`. `openverify.*` (at least
two segments) is reserved for OpenVerify-defined standards. Ownership cannot be proven by syntax validation;
there is no online registry. IDs such as verifier.smt, execution.container,
policy.evaluate, resource.estimate, and dependency.analyze describe conceptual
families, not registered or implicitly meaningful standard capabilities.
Capability schemas and the capability's published specification define meaning;
an ID alone does not. Providers MUST publish that specification with their adapter.

lifecycle_features requires explicit booleans streaming, cancellation, deadlines,
resource_reporting. streaming permits events; false forbids all events.
cancellation means a running operation can receive cooperative cancellation;
false rejects cancellation of a running operation. Every binding still supports
the CANCEL control surface. deadlines means the provider enforces deadline
semantics; false rejects invocations with deadlines. resource_reporting permits
resource_usage events and final usage; false forbids both. It does not imply
budget enforcement or estimation. Providers MUST reject constraints they cannot
honor before accepting work.

Optional capability vcp_version declares VCP interchange and MUST appear in the
manifest's supported_vcp_versions. Capability specifications MUST declare it
when input/config/output or events contain VCP objects. It is absent for ordinary
non-VCP capabilities. Evidence/artifact/resource fields in this contract always
use the existing VCP draft schemas and prose, not new models.
