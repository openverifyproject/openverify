# Compatibility and initialization

The single version representation is an exact nonempty string. This contract's
version is "0.1". No SemVer comparison, ranges, coercion, or fallback is defined.

InitializeRequest contains ordered supported_contract_versions and
supported_vcp_versions arrays (unique strings), plus optional extensions.
The provider selects the FIRST version in the runner's contract list that the
provider supports. DRAFT 0.1 implementations select only "0.1". No common version
returns CONTRACT_VERSION_UNSUPPORTED and no work begins. InitializeResult contains
contract_version and manifest. The runner MUST verify the selection by the same
rule against the returned manifest. Initialization succeeds exactly once per
session; subsequent initialization is PROTOCOL_VIOLATION. On failure the session
is closed. Initialize doubles as DESCRIBE; no separate describe RPC is required.

The intersection of the two VCP lists is the session's available VCP versions.
VCP incompatibility does not forbid non-VCP capabilities. Every Invocation must
name the selected contract version and an exact advertised capability ID/version.
Missing ID is CAPABILITY_UNAVAILABLE; missing version of an existing ID is
CAPABILITY_VERSION_UNSUPPORTED. These rules establish compatibility, not selection.

Invocation vcp_version MUST equal the capability's declared vcp_version when
present, and MUST belong to the session intersection whenever present. A VCP
resource_budget also requires invocation vcp_version. VCP evidence, artifact, or
usage on responses requires invocation vcp_version. The only VCP representation
referenced by this draft is "draft". Other markers in these standard fields are
INVALID_INVOCATION (or INVALID_PROVIDER_OUTPUT for provider data). Non-VCP
capabilities MAY declare invocation vcp_version to allow those standard fields.

The existing VCP "draft" marker is revision-dependent and is not a stable VCP
release. Exact matching of that marker alone cannot establish revision equivalence.
For VCP interchange, deployments MUST use the same VCP specification/schema
revision and capability specification. Portable VCP revision identification is
OPEN. This contract does not silently introduce a new VCP version scheme.
