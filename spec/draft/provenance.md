# Provenance and history

## NORMATIVE SEMANTICS

A RunRecord MUST contain protocol marker, run_id, definition snapshot,
definition_fingerprint, subject, initial_context, opportunity_id, admission
outcome/reason, started_at, finished_at, node records, and final_results.
definition snapshot establishes id/version/criterion/graph/input artifact identity.
The fingerprint MUST be identified as reference-only, not a portable digest.
Consumers retain that labeled identifier as opaque provenance. Recomputing a
reference-local digest is not a portable conformance requirement or integrity proof.
Timestamps are UTC RFC3339 strings. They establish recorded timing, not clock trust.

Each node record MUST identify node_id, executor_ref, upstream_node_ids,
input_context, upstream_results, started_at, finished_at, and actual usage.
executor_version MAY be present when known. Result, Decision, or derived update
records the operation output; skipped/error node records retain their Result.
Evidence and adapter resource usage remain in Result; engine duration remains
in node usage. Upstream Results are snapshots keyed by predecessor identity.
final_results is a mapping of emitted Result node IDs, including intermediates,
not an invented overall judgment. No overall verdict exists without aggregation.

Consumers MUST preserve definition snapshots and lineage if they claim
reconstructable run provenance. RunRecord validation MUST check duplicate/missing
node identities, graph relationships, output-kind consistency, and final Results.
Persistence mechanism is replaceable; no particular backend is required.

In the supported complete local-record subset, every graph node has exactly one
record, including nonexecuted nodes. Each record has exactly one Result, Decision,
or derived update. Nonexecuted/failure bookkeeping Results are allowed for every
node kind. Successful executed Results belong only to Evaluate/Aggregate nodes.
An admission SKIP records every node as SKIPPED; no adapter is invoked.
The reference implementation supplies an executor version when the registered
adapter exposes one. Adapter errors retain code/message in Result output; a failed
operation does not synthesize a Decision or derived update.

Continual learning is definition evolution, not a LEARN node:
mistake -> reusable knowledge -> changed definition -> new version/fingerprint ->
history identifies subjects not evaluated with that definition -> selection and
admission choose backfill -> ordinary execution. Core does not invent tests.
History permits coverage, auditing, incremental work, reproducibility, staleness,
backfill, resource accounting, and caching, but does not prescribe cache decisions.

## NON-NORMATIVE EXAMPLES

The reference engine returns a record and can write UTF-8 JSON. A JSONL store
appends snapshots; storage is local convenience with no durability guarantees.

## OPEN QUESTIONS

Portable digest identity, external artifact integrity, history coverage rules,
and cache reuse equivalence are unresolved. Full replay is not implemented.

