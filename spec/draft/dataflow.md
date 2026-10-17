# Typed executable dataflow (breaking DRAFT revision)

## NORMATIVE SEMANTICS

Every consumed value has TYPE + SOURCE + BINDING + PROVENANCE.

```text
RUN INPUT ───────────────┐
                        │
CONSTANT ────────────────┤
                        v
                  ┌──────────┐
EXTERNAL REF ────> │  NODE A  │── output.x ─────┐
                  └──────────┘                v
                                        ┌──────────┐
                                        │  NODE B  │
                                        └──────────┘
```

A definition declares `run_inputs` (InputPort sequence). Names are unique.
Occurrence creation MUST reject undeclared supplied names, missing required
values, and values violating their schemas, before invoking any implementation.
Run declarations use BLOCK for required inputs and OMIT or DEFAULT for optional
ones. DEFAULT contains an explicit Constant, including a possible JSON null.
JSON Schema `default` annotations never insert values.

A node declares `operation`, `inputs`, `outputs`, `bindings`, `config`, and
optionally `config_schema`. InputPort contains name, schema, required, and
on_unavailable: BLOCK (required), OMIT (optional), or DEFAULT (optional, with
explicit default Constant). OutputPort contains name, schema, and role:
INFORMATION, RESULT, or DECISION. Names are unique within each port sequence.
Bindings are a mapping from input name to exactly one ValueSource. Required
inputs MUST be bound. Unknown target names are invalid.

ValueSource is exactly one of these disjoint strict objects:

* CONSTANT: `{kind: "CONSTANT", value: <JSON>}`.
* RUN_INPUT: `{kind: "RUN_INPUT", name: <declared run input>}`.
* EXTERNAL_REFERENCE: `{kind: "EXTERNAL_REFERENCE", reference: <ArtifactRef>}`.
* UPSTREAM_OUTPUT: `{kind: "UPSTREAM_OUTPUT", node_id, output}`.

External bindings pass the exact ArtifactRef value, never fetched bytes. Fetching,
secrets, environment, clocks, randomness, network and databases belong to explicit
run/external inputs when they affect meaning. VCP does not supply a resolver.
Configuration is definition-authored implementation behavior; semantic information
consumed by an operation belongs in ports. Config MUST NOT override bound inputs.
If declared, config_schema MUST validate config before execution.

Execution dependency != data binding. Edges constrain ordering/eligibility and
transfer no data. Each upstream binding MUST name an existing output of a strict
ancestor through execution edges. A missing ordering path, self/forward dependency
or cycle is invalid. Array position is not execution order: later-listed producers
are legal if graph dependencies put them first. Cycles/iteration and dynamic
expansion remain unsupported. Future scoped occurrences can instantiate this same
node model; no iteration scope or expansion source is defined now.

operation is `{capability_id, capability_version}`. IDs follow the Provider
Contract namespace syntax; version is an exact nonempty opaque string, with no
range/fallback semantics. This is a requirement, never provider identity. A later
runner matches the pair to a manifest and validates assembled input/config/output
against capability schemas. No discovery, selection policy, or Relay is introduced.
The local registry binds that exact pair to trusted host code. The standard reducer
capability is `openverify.aggregate`, version `1`.
An explicit concrete provider binding supplied by the host is occurrence information;
see [provider binding](provider-binding.md). The reference engine enforces that
binding and its Provider Contract schemas when the host supplies provider bindings.
For direct Provider Contract binding, capability input is the exact port-name
object, config is the exact declared node config, and COMPLETED output is the
output-port-name object. A capability specification MUST declare these shapes and
VCP interchange when applicable. Contract usage/evidence observations populate the
separate VCP execution observation channel; COMPLETED alone does not imply a valid
VCP output or a verification PASS. No implicit primitive-to-port mapping exists.

DERIVE outputs have INFORMATION role. EVALUATE/AGGREGATE MUST declare exactly one
RESULT output named `result`; CONTROL exactly one DECISION output named `decision`.
These kinds MAY additionally declare INFORMATION outputs. Result and Decision
values MUST satisfy VCP semantics as well as the port schema. Bookkeeping Results
for failed/nonexecuted Derive/Control are not declared outputs. Evaluate/Aggregate
result ports expose recorded ERROR/nonexecuted Results too, for explicit inspection.
If a node refines its Result-port schema to exclude one of those states, the
bookkeeping Result remains recorded but that port is INVALID for downstream use.
Error bookkeeping MUST NOT bypass the producer's declared port schema.
Information outputs publish atomically only on semantic success. Missing declared
outputs or extra outputs invalidate the attempt; no partial information leaks.
Produced information is not forced into Result.output.

Every EVALUATE and AGGREGATE MUST bind required `subject` and `criterion` input
ports to CONSTANT snapshots equal to the definition's subject and criterion.
The provider receives these exact semantic values in its input object. Capability
implementations MUST evaluate that subject/criterion; configuration cannot choose
an unrelated criterion. This establishes auditable meaning, not proof that an
untrusted implementation tells the truth. Aggregate membership excludes these two
semantic inputs. Emitted judgments MUST validate against judgment_schema, including
an explicitly emitted null judgment. Absent judgment differs from null.

All port/config/judgment schemas MUST be valid self-contained Draft 2020-12 object
or boolean schemas. References use resolvable local JSON Pointer fragments only;
nested resource IDs, anchors/dynamic references and external schema references are
rejected up front as SCHEMA_UNSUPPORTED. Annotation payloads are not schemas.
`format` is annotation-only. Schema equality MUST distinguish booleans/numbers,
including const, enum, uniqueItems. Runtime validation is mandatory at every input
and output. Static validation MUST validate constants/defaults/references and reject
disjoint explicit primitive type sets (integer overlaps number), false schemas,
and incompatible finite const/enum sets. Other subsumption is deliberately deferred
to runtime; accepting structure does not claim general schema implication.

For each node the runtime resolves bindings without ambient state. Resolution
records AVAILABLE, ABSENT (optional unbound/omitted run input),
PRODUCER_NOT_EXECUTED, PRODUCER_ERROR, OUTPUT_MISSING, or INVALID. A valid
Evaluate ERROR Result itself is AVAILABLE; its absent information is not.
Invalid output snapshots remain observations, never usable information.
AVAILABLE values are validated against target schemas. Optional OMIT explicitly
omits unavailable/invalid inputs; DEFAULT explicitly substitutes its validated
constant. Required BLOCK inputs cause SKIPPED with reason INPUT_UNAVAILABLE;
they never produce FAIL or UNKNOWN. No stale value, null, name-based lookup, or
unrelated producer is a fallback. Every declared input has a resolution snapshot,
even when execution is disabled. Nonexecution because of guards/control/admission
is distinguished from blocked input by the node record's reason.

### Original availability from the resolution snapshot

Original availability MUST be a deterministic function of the persisted definition,
effective run inputs, and preceding finalized producer records at the exact input
resolution snapshot. It MUST NOT depend on unrecorded rejection/cancellation order.
These rules classify availability, not the producer's lifecycle or error code.

Invalid declarations, absent required bindings, unknown source identities,
nonancestor upstream bindings, and malformed/inconsistent records are rejected
by their existing validation rules; they are not extra availability states.
Unavailable source values do not become JSON null implicitly.

Apply the following disjoint, ordered branches:

1. For a non-upstream source, an optional unbound input or an omitted optional
   effective run input is ABSENT. Otherwise CONSTANT, RUN_INPUT and
   EXTERNAL_REFERENCE supply their exact authored/effective value. If that value
   fails the applicable target schema it is INVALID; otherwise it is AVAILABLE.
   Constant/reference/static failures and invalid occurrence run inputs still
   reject before invocation under the existing preflight rules.
2. For the declared RESULT port of EVALUATE or AGGREGATE, use the recorded
   semantic/bookkeeping Result, including ERROR, nonexecution and cancellation.
   If its declared producer port schema or the consumer input schema rejects it,
   classify INVALID; otherwise AVAILABLE. This branch precedes lifecycle-based
   absence rules. Bookkeeping Results of DERIVE/CONTROL are not declared outputs.
3. For any other accepted declared output in the persisted information/Decision
   snapshot, classify AVAILABLE if the applicable producer/consumer schemas accept
   it, otherwise INVALID. Raw observations are never accepted output snapshots.
4. With no such output, a producer recorded as NONEXECUTED never started its
   computation: classify PRODUCER_NOT_EXECUTED. This is an unstarted lifecycle,
   not the CANCELLED state of an interrupted attempt.
5. With no such output, an invoked producer whose terminal state is CANCELLED is
   OUTPUT_MISSING, regardless of retained raw observations or apparent raw schema
   validity. Preserve CANCELLED and CANCELLATION in its lifecycle/diagnostics;
   losing output observations cannot change availability or publish information.
6. For an ERROR producer with a recorded completed output attempt (an observation
   without an execution error), reconstruct its failed output acceptance from the
   declared outputs, schemas/semantic invariants and any recorded host
   provider_output_error. If acceptance rejected that output attempt, a present
   candidate for the requested port is INVALID; an explicitly omitted declared
   port is OUTPUT_MISSING. Atomic rejection does not publish other raw candidates.
   A valid executed ERROR Result is an execution-error report, not an output
   acceptance rejection; its accompanying unpublished information falls through.
7. Any remaining producer terminated ERROR without the preceding recorded
   rejected/missing output cause is PRODUCER_ERROR. This includes raised or
   reported execution errors with no accepted requested output.
8. Any other finalized producer with no accepted declared output is OUTPUT_MISSING.

The first applicable branch is the original status. A failed producer schema
check does not additionally evaluate an absent/irrelevant consumer value.
Classification requires no new terminal state, acceptance-event log, scheduler
barrier, or seventh status. The CANCELLED branch deliberately ignores raw
observations even if their values would fail a schema.

Handlers apply only after classification and MUST preserve the original status
and source. AVAILABLE consumes the exact validated value with used_default=false.
For any other status, BLOCK does not invoke the node and retains no usable value;
OMIT omits the input key with used_default=false; DEFAULT consumes the exact
validated Constant (including null) with used_default=true. These effects do not
replace stronger lifecycle nonexecution causes or their diagnostic reasons.

Guards are equality over `{source: ValueSource, pointer: JSON Pointer, value: JSON}`.
Empty pointer compares the complete value. Upstream sources MUST be ancestors of
the consumer. Sources and statically known operands MUST be validated. Invalid
pointers/known operand types are rejected; unresolved runtime optional fields make
the guard false. No expressions or global Context lookup exist. Guards observe
declared result/decision ports, typed information, run inputs, constants or refs.

All Aggregate nodes declare `aggregate_inputs`, an ordered, unique list of input
port names. Each MUST bind an upstream RESULT-role output. The list is the complete
structural reducer membership, for standard and custom reducers, independent of
edge order and predecessor states/kinds. No undeclared RESULT binding may be omitted
from membership. Members are required BLOCK inputs. Nonexecution/ERROR Results stay
members and standard handling applies; unavailable values block the aggregate.
Weights in graph WEIGHTED_AVERAGE are an exact name-to-nonnegative-number mapping
over aggregate_inputs, with positive total. Filtering preserves identities. The
direct reducer SDK's ordered sequence API retains aligned positional weights.
Evidence concatenation follows aggregate_inputs order for all standard reducers.
Every Aggregate also MUST declare required `members` input bound to a CONSTANT
equal to aggregate_inputs. This supplies the authored ordering in the exact input
object received by custom implementations; JSON object member order is irrelevant.
The reserved semantic names subject, criterion and members cannot be member names.

For a custom Aggregate capability, an explicitly empty aggregate_inputs is
structurally legal. Its required Constant-bound members input is exactly [].
The capability receives that exact ordered empty list, with subject/criterion and
any other declared resolved inputs; its declared input schema controls invocation
eligibility and its implementation determines the Result. VCP invents no PASS,
FAIL, score or empty-input error for custom aggregation. Standard reducers still
reject empty original or retained input. A declared member that is unavailable
remains declared and follows BLOCK resolution; it MUST NOT silently disappear or
be reinterpreted as an intentionally empty membership declaration. All normal
binding, semantic input, output acceptance and provenance rules still apply.

Execution policies that consume information MUST use the same typed declarations
and ValueSource bindings (run/constants/external only, before graph execution).
The reference engine implements MANUAL/EXPLICIT and ALWAYS/PROBABILITY shorthands
and registered custom operations with role-constrained outcomes; see
[execution policy](execution-policy.md). It validates the complete definition
before invoking any policy or node.

Context now means optional ambient NONSEMANTIC host metadata. It is retained as
initial_context in provenance, never passed as computation input or mutated by
Derive. Engine.run's supplied values are run_inputs, not Context. Each invocation
receives a fresh exact input object and separate config. An implementation using
ambient information to change portable meaning violates the capability contract.

ExecutionObservation is the standard local/wire semantic observation channel:
`outputs`, `usage`, `evidence`, optional `error` {code,message}. It is not a Provider
Contract Outcome. All node kinds use this channel, including custom Aggregate.
Valid incurred usage/evidence MUST be retained separately from semantic output
acceptance, including invalid judgment/output and explicit execution errors.
Engine timing remains separate from executor usage; units are never merged.
An implementation that raises without reporting usage cannot have that unknown
usage reconstructed. It can report an error observation with incurred usage.
ExecutionObservation.usage is authoritative for the attempt. Result.usage, when
present, MUST agree on its dimensions with that observation and is a repeated
snapshot, never an additive charge. A mismatch invalidates semantic output without
erasing the valid execution observation.
Observation evidence is structurally typed but remains an observation until
semantic acceptance. Invalid Evidence meaning invalidates acceptance while its
observed snapshot and valid usage remain recorded, just like invalid port values.

RunRecord stores immutable occurrence run_inputs and ambient initial_context.
Each NodeRecord stores operation requirement, executor identity/version when known,
input resolutions (source, status, explicit value only when usable, used_default),
exact assembled input_values, observed outputs, accepted information outputs,
semantic Result/Decision, execution state/reason, usage/evidence and timing.
Source identity is (run_id, node_id, output); definitions identify run/constants.
Validators MUST reconstruct resolutions from definition, initial run inputs and
earlier node records; compare all snapshots with JSON type equality; validate
outputs and judgments; reject unbound input values and aggregate membership drift.
No provider rerun is required. This detects contradictions along declared edges,
not coordinated rewriting of an entire consistent record or forged provider truth.
Unadmitted/disabled/blocked nodes MUST NOT contain executor observations or usage.

Severity.domain remains an opaque profile/domain identifier unless an explicit
domain is supplied (e.g. WORST_SEVERITY config). No registry or implicit version
resolution exists; the identifier MUST identify a versioned semantic domain when
versions matter. Parsing Result does not claim its label belongs to an unresolved
domain. WORST_SEVERITY validates against its explicit domain snapshot.

## Breaking changes

Node executor_ref/global Context/prior-results injection and implicit graph reducer
membership are removed. Nodes require operation/ports/bindings; definitions require
run_inputs; RunRecord uses explicit resolutions and observations. Old records and
definitions must be reauthored. Protocol status remains DRAFT.
