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
| Future provider transport/session provenance and policy provider bindings | Graph-node bindings use trusted local execute(inputs, config); policy operations remain local; no transport runner or Relay |

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
