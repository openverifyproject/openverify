# Provenance and history

## NORMATIVE SEMANTICS

[Typed dataflow](dataflow.md) defines the complete node input/output lineage contract.
RunRecord contains definition snapshot, opaque reference-only definition_fingerprint,
subject, initial supplied run_inputs, ambient nonsemantic initial_context, admission,
opportunity identity, complete node records and all final Results. It does not invent
an overall verdict. Every node has exactly one terminal record in dependency order.

Node records retain operation requirements, kind, executor identity/version when known,
exact input resolutions and values, direct upstream Result snapshots, execution
observations, accepted information and Result/Decision, resource usage and timing.
A validator reconstructs each resolution from recorded source values and checks
semantic output acceptance, availability and guard/control/admission eligibility.
No provider is rerun. Contradictions are PROVENANCE_LINEAGE errors. Usage on executor
observations remains distinct from engine wall-time usage and semantic Results.

Input/output comparisons distinguish JSON booleans from numbers and preserve array
order. Admission SKIP requires all node Results SKIPPED. Disabled/blocked nodes
contain no executor observations. Every record is within its run interval and each
predecessor finishes before its consumer starts. Timestamps are UTC RFC3339 with
Z/z or +00:00. Timing establishes recorded ordering, not clock trust.

Memory and local JSONL stores are replaceable convenience implementations. The
local-sha256 fingerprint is nonportable and is not an integrity signature. Consistent
coordinated record rewriting and forged implementation behavior cannot be detected
without external trust. Edge contradictions can be detected without replay.

## OPEN QUESTIONS

Portable canonical identity/signing, clock trust, history coverage, cache equivalence,
external artifact integrity and complete replay remain open. No registry or backend
is required.
