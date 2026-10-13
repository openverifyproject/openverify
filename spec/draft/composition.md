# Composition

## NORMATIVE SEMANTICS

Conceptual foundation is a general directed execution graph: nodes, directed
edges, dependencies, guards, cycles, and dynamic expansion.
Sequence is dependency; parallelism is absence of ordering dependency;
conditional execution is a guarded edge; join is convergence; iteration is a
cycle; ForEach is expansion across a collection.

The wire subset contains nodes, edges {from_node, to_node, guard?}, and optional
features identifying CYCLES or DYNAMIC_EXPANSION as unsupported draft features.
Node IDs MUST be unique and all edge endpoints/guard node references MUST exist.
An edge's guard MUST reference its own source node. Parallel duplicate edges
with identical endpoints MUST be rejected in this subset.
A guard is equality only: {node_id, field, value}.
Fields are disposition, execution_outcome, applicability, determination, verdict,
decision_kind, decision_destination. Result-field values MUST be a value from
that axis; decision_kind uses the standard decision names. No scripting is allowed.
Absent compared field makes equality false.

For the supported acyclic subset, every incoming edge is a prerequisite.
A node is eligible only after every predecessor completed, and every incoming
guard is true. A disabled predecessor disables its successor. Independent nodes
have no semantic ordering; the reference engine executes them sequentially in
definition order when ready. Prior Results supplied to a node are direct
predecessor Results; Control decisions and Derive outputs are not Results.

Cycles and declared expansion features MUST yield GRAPH_UNSUPPORTED in the
current SDK/executor, not silently be treated as a DAG.
Simple routing uses decision_destination guards on a Control source. ROUTE
identifies a registered graph node, not a business action. Validation of a runtime
destination is the executing host's responsibility.

## NON-NORMATIVE REFERENCE ENGINE BEHAVIOR

The sequential engine snapshots Context before each invocation. Derive updates
replace matching keys for subsequent nodes. CONTINUE leaves execution active;
ROUTE validates its destination exists and uses explicit outgoing guards to enable
that branch. It does not force the destination to run outside graph dependencies.
STOP_SUCCESS/STOP_FAILURE stop remaining invocations; remaining nodes record
SKIPPED without synthesizing an overall verdict. RETRY/DEFER are recorded and
stop this local run; no retry or defer scheduler is provided. Stopping and inactive
guards propagate nonexecution; all graph nodes still have lineage records.
SKIPPED records for Derive/Control are bookkeeping, not judgments from those nodes.

## NON-NORMATIVE EXAMPLES

cheap evaluator -> Control -> strong evaluator -> Control -> human evaluator.
Decision guards can select strong/human destinations.

## OPEN QUESTIONS

General portable guard language, cycles/iteration, expansion wire semantics,
and alternative join/guard-combination semantics remain unresolved. The subset
makes no claim to implement all general graphs.

