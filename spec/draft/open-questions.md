# Open questions encountered in this implementation

Protocol status: DRAFT. These questions limit supported behavior; they are not
implicitly answered by reference Python behavior.

| Question | Current boundary |
| --- | --- |
| Cross-language canonical hashing of numbers, Unicode, defaults, nulls | Explicit id/version; local-sha256 is non-portable |
| Cross-engine numeric precision and reducer rounding | Mathematical reducers are defined; reference numeric measurements/scores use binary64, exact rational intermediate means, and one final rounding. No bit-identical numeric portability is claimed |
| General guard language and alternative join behavior | Equality guards, all prerequisites only |
| Cycles/iteration and dynamic expansion wire/execution | Recognized as GRAPH_UNSUPPORTED |
| Flattening deferred/cancelled/not-applicable and known without verdict | Partial projection raises RESULT_PROJECTION |
| Partial judgment/score on UNKNOWN | Supported subset excludes it |
| Portable criterion language and satisfaction mapping execution | Metadata identifies meaning; adapters evaluate |
| Majority tie and fail-closed/warning/escalation reducer policies | Tie rejected; explicit REJECT/IGNORE supported |
| Required extension capability/version negotiation | Preserve optional; reject unsupported required |
| Cross-engine sampling and opportunity identity | Host opportunity id; reference-only deterministic buckets |
| Maximum staleness + probability/history coverage | Conceptual only; no MAX_STALENESS built-in |
| Retry/defer scheduling and history/cache equivalence | Decisions serialize; engine does not schedule retries |
| External artifact integrity and schema resolution | No fetching; self-contained judgment schemas only |
| Provider authenticity and independent reproduction of host contract-rejection claims | Exact occurrence binding and structural consistency only; no binary/endpoint attestation or manifest snapshot in VCP records |
| Future provider transport/session provenance and policy provider bindings | Graph-node bindings are normative; Relay retains extra transport/policy correlation as optional unauthenticated annotations, not new portable fields |

No missing top-level category was established by the conceptual audit. Category
coverage does not imply portable syntax or runtime support for every example.


## Resolved in typed-dataflow DRAFT revision

Explicit ports and four ValueSource variants replace mutable Context lookup.
Execution edges transfer no values. Required unavailable inputs cause structural
SKIPPED/INPUT_UNAVAILABLE. All graph reducers have ordered explicit input membership
and name-keyed weights. Guards use explicit sources. Evaluate subject/criterion are
constant semantic input snapshots. RunRecord validates resolutions against sources.
Usage is an execution observation independent of semantic validity.

Schema implication is intentionally partial: primitive/finite checks are static,
all actual values validate at runtime. Unsupported external/nested/dynamic schema
resolution fails definitions up front. Severity references without domain snapshots
are opaque; no validation or registry resolution is claimed. These choices replace
previously open/engine-local behavior; see [dataflow](dataflow.md).

Still open: cycles/iteration scopes, expansion, provider selection, general subject-universe execution,
retry/defer scheduling, general guards, canonical signing, artifact integrity,
portable numeric precision and formal criterion/satisfaction languages. Adapters
remain responsible for honestly implementing bound semantic criteria.

## Resolved in policy-to-occurrence DRAFT revision

Activation now has ACTIVATE/DO_NOT_ACTIVATE outcomes; selection is a subject set
(empty or exact definition subject in the current single-subject subset).
Custom policy operations reuse typed ports, bindings and configuration. No hidden
Context or graph-output policy sources are allowed. Valid admission creates the
occurrence, including SKIP and DEFER; inactive/unselected opportunities do not.
See [execution policy](execution-policy.md).

Previously ambiguous DISABLED, control DEFER/RETRY, route exclusion and cancellation
now have deterministic lifecycle/disposition/reason mappings and provenance; see
[lifecycle](lifecycle.md). ROUTE is constrained to a direct successor and excludes
exclusive branch descendants while preserving shared joins. Ordinary false guards
retain the existing explicit-dataflow behavior, with no implicit edge propagation.
This is a breaking DRAFT clarification, not stable 1.0 compatibility. Provider
selection, asynchronous/distributed cancellation, scheduling retries/deferred work,
cycles/iteration and dynamic expansion remain unsupported.

## Relay v0.1 implementation boundaries (not new VCP semantics)

Relay implements trusted provider selection and asynchronous finite DAG execution.
The existing cancellation event represents one interrupted attempt followed by
unstarted nodes. Portable provenance for **multiple simultaneously interrupted
attempts** remains OPEN. Relay serializes occurrences that request a recorded
host Cancellation token. Task cancellation aborts the API call after process
cleanup; it does not fabricate a completed RunRecord. Other runs remain independent.

Independent non-Control nodes execute in deterministic ready waves. A Control
node is a scheduling barrier; no other wave member can be concurrently affected
by its stop/route decision. Parallel completion order never determines control
meaning or record ordering. This is a conservative scheduling choice permitted
by the existing acyclic semantics, not a new graph feature.

Portable transport/session and custom-policy provider provenance fields remain
OPEN. Relay retains additional invocation correlation and diagnostic traces in
an optional `urn:openverify:relay` extension. These annotations do not replace
the normative graph-node ProviderBinding or change SDK lineage validation. The
SDK does not authenticate or independently validate these optional annotations.
No cryptographic provider attestation or coherent-forgery detection is claimed.
# Golden v0.2 audit questions (non-normative; no rule changes)

The following questions record unresolved public categories. Golden v0.2 requires
the specified semantic rejection and reports exact-code uncertainty separately.
No category is selected from observed implementation behavior.

- **Aggregate membership category:** dataflow.md requires a required constant-bound
  `members` input equal to `aggregate_inputs`; conformance.md lists both
  DATAFLOW_BINDING and AGGREGATE_CONFIG but does not specifically assign an absent
  membership declaration or precedence between these categories. Affected Golden
  cases: invalid `dag.kinds.*` Aggregate assignments (22).
- **Forbidden resource events:** capabilities.md forbids resource_usage events
  when resource_reporting=false. errors.md covers invalid emitted events with
  INVALID_PROVIDER_OUTPUT and lifecycle violations with PROTOCOL_VIOLATION. Which
  category owns a structurally valid event forbidden by an advertised feature?
  Rejection remains mandatory. Affected: four `provider.flags.*.resource_usage`
  traces with streaming=true and resource_reporting=false.
- **Known guard operand mismatch:** dataflow.md requires definition-time rejection
  for invalid known operand types. Which precise category owns comparing constant
  null with boolean true: GRAPH_REFERENCE or DATAFLOW_SCHEMA? The definition must
  not execute and must not yield runtime GUARD_FALSE. Affected: guard.literal.None.
- **Local action-policy directory prefix spelling:** docs/relay/providers.md
  promises directory-prefix membership and rejects absolute/traversal paths but
  does not define equivalence of `tmp` and `tmp/`, whether the directory itself is
  eligible, or separator normalization. Keep the original `tmp` spelling case
  explicitly blocked; add unambiguous `tmp/` child, sibling and traversal examples.
- **Local finding/range wire profile:** published standard capability schemas
  declare arrays without complete finding/range object schemas. Golden uses
  independently constructed one-based half-open coordinates, Git-relative hunk
  paths and Python AST ranges. These experiments establish those explicit
  examples, not an exhaustive portable finding-object schema.
- **Standard computation error identity:** Provider Contract permits namespaced
  computation failures; it does not normatively reserve the local Python
  wrapper's `openverify.computation_error` or require embedding a caught VCP
  exception's code in ProviderError.details. Golden asserts that existing wrapper
  identity only as current local API compatibility. It keeps the mathematical VCP
  cause separately and never treats it as a Provider Contract reserved code.

