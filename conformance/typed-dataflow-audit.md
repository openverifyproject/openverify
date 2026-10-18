# Typed executable graph audit

Protocol status: DRAFT. Scope: acyclic graphs without dynamic expansion, using
registered implementations of exact operation requirements. This audit concerns
dataflow consistency, not the truthfulness of an implementation's observations.

| Final question | Answer | Evidence |
| --- | --- | --- |
| Can every required node input be traced to exactly one explicit source? | YES | Required binding/target validation; duplicate JSON keys rejected; recorded per-port sources |
| Can every source be type-checked at least at runtime? | YES | Run validation, target validation, output validation, intrinsic Result/Decision checks |
| Can a failed producer leak a stale value? | NO | Producer-scoped resolution; failed-producer integration/property cases; ambient values excluded |
| Can independent reordering alter another node's input? | NO | Same-name unrelated producer regression; topological permutation property |
| Can aggregate membership change merely because predecessor state changes? | NO | Ordered aggregate_inputs, bound members, identity weights; Result-state property |
| Can a value change without detection across a declared edge with an unchanged consumer snapshot? | NO | Source/resolution reconstruction; producer/run-input tampering fixtures and properties |
| Can a generic harness know which capability is required? | YES | Exact operation.capability_id/capability_version; inspection API and registry |
| Does the harness need to guess domain semantics? | NO | Exact port-name objects, explicit subject/criterion, generic observation channel |

Adversarial probes are executable in `tests/integration/test_typed_dataflow.py`,
`tests/integration/test_weighted_graph_boundary.py`, and
`tests/property/test_typed_dataflow.py`:

* A: unrelated Derives produce the same port name; explicit producer identity
  preserves the chosen consumer value in either independent order.
* B: a producer reports ERROR while run/ambient input has the same name; the
  required consumer is NONEXECUTED with INPUT_UNAVAILABLE, without a stale value.
* C/D: changing a producer observation and accepted output together, or changing
  initial run inputs, invalidates unchanged dependent snapshots.
* E: node-array permutations respect topology and preserve bound values.
* F: invalid outputs from Derive, Evaluate, Control and custom Aggregate retain
  valid execution usage. Invalid/null judgments, invalid observed Evidence, and usage disagreement are checked.
* G: Derive success/failure and Evaluate exceptional/nonexecuted states cannot
  change aggregate member identities. Edge permutation cannot reassign weights;
  authored member order determines evidence order and reaches custom reducers.
* H: subject/criterion constants must match the definition. Provider configuration
  is separate and cannot replace those semantic inputs. Implementations are
  contractually required to honor them; VCP does not prove provider honesty.

Portable fixtures cover declarations, all four sources, every standard reducer,
custom Aggregate, default/absence, explicit null/false/zero/empty values, structural
errors, observed invalid output, stale-value consumption and contradictory lineage.
The Provider Contract suite remains independent and its files are unchanged.

Remaining limits are explicit: no cycles/iteration or expansion; no Relay,
discovery/selection, artifact fetching, external schema resolution, advanced policy
execution, retry scheduler, canonical signing or complete replay. Static schema
compatibility is deliberately partial; actual port values always validate.
Unresolved severity-domain identifiers are opaque unless a domain snapshot is given.
Consistent coordinated rewriting of an entire record requires external integrity
protection; contradictory declared edges are rejected without provider replay.
