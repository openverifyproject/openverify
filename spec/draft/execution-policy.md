# Execution policy

## NORMATIVE SEMANTICS

The order is activation, selection, admission, then graph execution. Resources
are typed estimates, constraints or observations, not another decision stage.
Policy decisions MUST NOT inspect graph execution or undeclared ambient Context.

All three roles reuse InputPort, ValueSource bindings, OperationRequirement,
config and optional config_schema from [dataflow](dataflow.md). Required ports
MUST be bound. Only CONSTANT, RUN_INPUT and EXTERNAL_REFERENCE are legal before
graph execution. External references supply ArtifactRef, never fetched content.
Defaults, omissions and runtime schema validation follow ordinary port semantics.
All definition structure, schemas, constants and bindings MUST validate before
any implementation is invoked. Required unavailable/invalid policy inputs,
implementation exceptions and invalid outcomes abort policy evaluation; they MUST
NOT invent a decision or occurrence.

A custom policy declares operation: {capability_id, capability_version}. Its
implementation receives only the exact resolved input object and separate config,
and returns the role outcome object directly. The role fixes the output schema:

* Activation: {outcome: ACTIVATE | DO_NOT_ACTIVATE, reason: nonempty string}.
* Selection: {subjects: ArtifactRef[], reason: nonempty string}. Subjects form a
  set identified by id; duplicate identities are invalid.
* Admission: {outcome: RUN | SKIP | DEFER, reason: nonempty string}.

A Result, Decision, observation envelope or arbitrary boolean is not a policy
outcome. Candidate facts/identities needed by selection MUST be bound inputs.
This draft defines one subject per definition: selection MUST return either an
empty set or the exact definition subject snapshot. Other subjects require other
definitions/opportunities; selection does not expand or mutate graphs. General
subject-universe execution remains unsupported. A custom policy needing the
subject MUST explicitly bind it.

Legacy built-in shorthands remain: activation executor_ref MANUAL returns ACTIVATE
for a host-offered opportunity; selection executor_ref EXPLICIT returns the
structural definition subject; admission strategy ALWAYS returns RUN. PROBABILITY
requires finite p in [0,1]; p=0 SKIP, p=1 RUN, otherwise sampling returns RUN/SKIP.
A policy MUST choose exactly one of operation and its built-in discriminator
(executor_ref or strategy). Built-ins have no ports, bindings or config; only
PROBABILITY accepts probability. Other legacy names remain valid references but
unsupported locally. Custom policies cannot carry a built-in discriminator or p.

Hosts MUST provide a nonempty opportunity_id. The built-in sampler's complete
structural inputs are definition fingerprint, subject identity, opportunity_id
and explicit p. Its exact bucket identity is reference-only, not portable.
Custom policies needing opportunity identity MUST bind it as ordinary typed data.
There is no hidden budget, risk, history, clock or environment input. A budget-aware
policy simply declares the relevant typed values or external snapshots and returns
an ordinary admission outcome. Policy logic remains replaceable.

## Exact occurrence boundary

DO_NOT_ACTIVATE ends the opportunity before selection, with no occurrence.
Empty selection ends it before admission, with no occurrence for that subject.
Neither case creates a RunRecord or node records. Hosts MAY audit opportunities
outside RunRecord; no opportunity-audit object is defined here.

An occurrence is created exactly when valid admission returns RUN, SKIP or DEFER
for an activated, selected subject. RUN enables graph execution. SKIP creates one
terminal SKIPPED Result per node with ADMISSION_SKIP. DEFER creates one DEFERRED
Result per node with ADMISSION_DEFER. Neither invokes graph providers. These
states are never FAIL, ERROR or UNKNOWN. Policy failure before valid admission
creates no occurrence.

Each occurrence retains all three ordered policy evaluations: role, exact input
resolutions/values, constrained outcome and known executor identity/version.
RunRecord.admission repeats the admission outcome exactly. Validation reconstructs
policy inputs without rerunning policy logic; these are observations, not proof
of an honest implementation.

## Reference subset and open questions

Engine.attempt returns None when no occurrence exists. Engine.run is a convenience
requiring an occurrence and raises NO_OCCURRENCE for those opportunities. Neither
fabricates records. Required unavailable/invalid policy inputs raise POLICY_INPUT;
invalid outcomes raise POLICY_OUTPUT. Custom policies use the same explicit local
exact-pair registry as graph operations; no provider selection is defined.
No periodic scheduler, policy language, multi-subject expansion or retry scheduling
is implemented. Maximum staleness/history coverage and portable sampling remain OPEN.
