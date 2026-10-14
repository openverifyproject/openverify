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
order. Admission SKIP requires all node Results SKIPPED/ADMISSION_SKIP; admission DEFER
requires DEFERRED/ADMISSION_DEFER. Disabled/blocked nodes
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

## Policy and lifecycle provenance

RunRecord.policy_evaluations contains exactly ACTIVATION, SELECTION, ADMISSION
in that order. Each PolicyEvaluation stores exact declared input values and
InputResolution snapshots, the role-constrained outcome, and optional actual
executor_ref/executor_version. Its operation requirement remains in the definition.
Activation MUST be ACTIVATE and selection MUST contain the exact definition subject;
otherwise no occurrence and no RunRecord exists. The admission outcome MUST equal
RunRecord.admission. Built-in outcomes are checked against their definition;
custom policy logic is not rerun. PROBABILITY records enforce p=0/p=1 boundaries
and RUN/SKIP outcomes, but do not enforce a reference-only bucket identity.
Invalid policy provenance is PROVENANCE_LINEAGE.

NodeRecord.reason is the stable machine-readable lifecycle cause for nonexecution;
its Result repeats it in diagnostic output. [Lifecycle](lifecycle.md) defines
precedence and exact mappings. Nonexecuted records have no executor identity,
observations, accepted information, Decision or executor usage. Engine wall time
is separate bookkeeping. Interrupted cancellation is state CANCELLED and may retain
unaccepted observations/usage; RunRecord.cancellation records the first affected
node, BEFORE_START/RUNNING phase and explicit host reason. Validators reconstruct
all eligibility effects, and reject contradictory lifecycle/Result combinations.
