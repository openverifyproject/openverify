# Composition

## NORMATIVE SEMANTICS

The supported executable graph is acyclic, with unique node IDs, unique directed
execution edges, and existing endpoints. Every incoming edge requires its predecessor
to reach a terminal occurrence state. Edges transfer no data and do not implicitly
propagate predecessor failure/nonexecution. Data unavailability propagates only
through explicit bindings; guards explicitly constrain eligibility.

Bindings to upstream ports require a strict execution ancestor. Node array order
is not data identity. Independent nodes may execute in any topologically valid order;
the reference executor uses definition order among ready nodes.

Equality guards, port identity, availability and aggregate membership follow
[typed dataflow](dataflow.md). Every node gets a record, including disabled/blocked
nodes. STOP_SUCCESS/STOP_FAILURE stop remaining invocations; RETRY/DEFER also stop
this local execution without scheduling. ROUTE requires an existing graph node and
selects through explicit guards; it does not bypass dependencies. No overall verdict
is synthesized without Aggregate. Control decisions are verification control, never
external business actions.

Cycles/iteration and DYNAMIC_EXPANSION features MUST yield GRAPH_UNSUPPORTED.

## OPEN QUESTIONS

General guard expressions, alternative joins, scoped iteration, dynamic expansion,
and portable retry/defer scheduling remain unsupported.
