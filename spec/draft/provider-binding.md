# Concrete provider binding (DRAFT)

## NORMATIVE SEMANTICS

OperationRequirement remains the required capability ID and exact opaque version.
It contains no provider identity, discovery, ranking, fallback or selection policy.
After a host chooses a provider, ProviderBinding identifies the actual binding:
`provider_id`, `provider_version`, `capability_id`, `capability_version`. Identifier
syntax and exact version meaning are those of Provider Contract 0.1. No manifest
or capability schema is embedded in the VCP definition or binding object.

Before invocation with a concrete binding, a runtime MUST validate the binding's
structure, exact equality to the node's capability requirement, equality to the
bound manifest's provider identity/version, and the manifest's structural and
semantic validity, including all declared capability schemas. The exact capability
pair MUST be advertised. Contract/VCP interchange compatibility MUST follow Provider
Contract. Missing or incompatible bindings MUST fail before invocation; the runtime
MUST NOT choose or fall back to another provider.

The exact invocation input is the resolved port-name object, including explicit
defaults and excluding omitted ports. Configuration is the exact node config object.
The runtime MUST validate these against the advertised capability input_schema and
config_schema before invocation. Provider Contract requires config_schema; `true`
expresses unrestricted configuration. After successful invocation, the exact
output-port-name object MUST validate against output_schema before VCP port,
Result/Decision, judgment and other semantic acceptance. These are independent
boundaries. No implicit primitive wrapping, schema defaults or config overrides
are permitted. Execution-error observations do not represent successful outputs.

For each node that actually invokes a bound provider, RunRecord.provider_bindings
maps node_id to the exact concrete binding used for that invocation. NodeRecord
provider_binding repeats this identity as node provenance. Its executor_ref and
executor_version MUST equal provider_id and provider_version. Both binding copies
MUST agree, refer to an existing occurrence node, and satisfy its OperationRequirement.
An invocation that raises or is interrupted still retains its binding. A node
rejected before invocation or disabled by lifecycle has no invocation binding.
The binding map is occurrence data, never an instruction for future provider selection.
Local implementations without a Provider Contract manifest retain local executor
provenance; they MUST NOT fabricate a provider identity or manifest.

The runtime retains raw ExecutionObservation output and valid incurred usage even
when the provider output schema rejects it. NodeRecord.provider_output_error records
the host validation rejection separately (`code: INVALID_PROVIDER_OUTPUT`, message).
It requires a provider binding and an observation without an execution error.
Validation MUST reject accepted information/Decision/Result inconsistent with this
rejection: the terminal node is ERROR with the corresponding bookkeeping Result,
or CANCELLED under existing interrupted-cancellation semantics. Invalid raw output
MUST NOT become available downstream. Bookkeeping ERROR Results remain available
through declared Result ports according to existing dataflow semantics.

RunRecord validation MUST reject mismatches between occurrence invocation binding,
node provider provenance, executor identity/version and operation requirement with
PROVENANCE_LINEAGE. This is structural/semantic consistency, not authentication of
a binary, remote endpoint, signature, trust root or supply chain. Consistent rewriting
of an entire occurrence and dishonest provider/host claims are outside this guarantee.
Validation without the manifest checks the recorded host rejection's consistency;
it does not independently reproduce Provider Contract schema checks.

## REFERENCE ENGINE SUPPORT

`Engine(registry, provider_bindings={node_id: BoundProvider(binding, manifest, adapter)})`
accepts explicit host choices for graph nodes. Supplying even an empty mapping opts
into required provider binding for every eligible node; missing entries produce
PROVIDER_BINDING_REQUIRED, without consulting the local registry or built-in reducer.
An explicit binding overrides the built-in reducer path. The manifest and identity
are snapshotted before execution; the adapter uses the existing trusted local
`execute(inputs, config)` interface. No transport runner or Provider lifecycle server
is introduced. Policies continue using the explicitly registered local policy API.
Without this argument the existing local demonstration mode remains available.

Execution errors expose stable codes: PROVIDER_BINDING_MISMATCH for identity/pair
conflicts, PROVIDER_MANIFEST_INVALID for invalid manifests/contracts,
CAPABILITY_UNAVAILABLE or CAPABILITY_VERSION_UNSUPPORTED for missing advertisements,
CONTRACT_VERSION_UNSUPPORTED or INVALID_INVOCATION for incompatible interchange,
INVALID_INPUT / INVALID_CONFIG for contract violations before invocation, and
INVALID_PROVIDER_OUTPUT for declared output-schema rejection. Messages are diagnostic.

## OPEN QUESTIONS

Portable provider attestation, independently verifying host schema-rejection claims
without a manifest, and provenance for future transport/session invocations remain
open. No discovery, provider selection or Relay is implemented.
