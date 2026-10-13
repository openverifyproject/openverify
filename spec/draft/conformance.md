# Conformance

## NORMATIVE SEMANTICS

Conformance applies to the documented wire/semantic subset, not all conceivable
verification capabilities. A parser MUST structurally validate against the shipped
schema and then enforce semantic invariants. Unsupported engine features MUST
fail clearly rather than acquire invented behavior.

conformance/manifest.json enumerates deterministic fixtures with id, description,
object_type, input, valid, expected error_code when invalid, and spec reference.
Valid fixtures MUST pass both checks; invalid fixtures MUST fail the documented
stage/code. Semantic-invalid fixtures may be structurally valid.
Future implementations can run this suite without executing Python.

Errors have code, message, path, optional details. Structural failures use
PROTOCOL_STRUCTURE, unsupported marker PROTOCOL_VERSION, Result invariant
RESULT_STATE, Evidence EVIDENCE_EMPTY, graph reference/identity GRAPH_REFERENCE/
GRAPH_DUPLICATE, unsupported graph GRAPH_UNSUPPORTED, Resource RESOURCE_MEASUREMENT,
admission ADMISSION_POLICY, extension EXTENSION_UNSUPPORTED, aggregate config
AGGREGATE_CONFIG, profile PROFILE_DOMAIN, provenance PROVENANCE_LINEAGE.
Runtime failures use EXECUTOR_ERROR, EXECUTOR_UNSUPPORTED, AGGREGATE_INPUT,
POLICY_UNSUPPORTED; these do not redefine structural conformance.
Malformed JSON uses PROTOCOL_JSON.
Paths use JSON Pointer where known. Library errors are supplementary, not the
only public contract.

## NON-NORMATIVE EXAMPLES

Property tests search score, resource, and graph spaces. They supplement rather
than replace deterministic language-neutral fixtures.

## OPEN QUESTIONS

No stable protocol release is claimed; suite compatibility is revision-specific.

