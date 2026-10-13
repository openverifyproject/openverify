# Open questions encountered in this implementation

Protocol status: DRAFT. These questions limit supported behavior; they are not
implicitly answered by reference Python behavior.

| Question | Current boundary |
| --- | --- |
| Cross-language canonical hashing of numbers, Unicode, defaults, nulls | Explicit id/version; local-sha256 is non-portable |
| General guard language and alternative join behavior | Equality guards, all prerequisites only |
| Cycles/iteration and dynamic expansion wire/execution | Recognized as GRAPH_UNSUPPORTED |
| Flattening deferred/cancelled/not-applicable and known without verdict | Partial projection raises RESULT_PROJECTION |
| Partial judgment/score on UNKNOWN | Supported subset excludes it |
| Portable criterion language and satisfaction mapping execution | Metadata identifies meaning; adapters evaluate |
| Majority tie and fail-closed/warning/escalation reducer policies | Tie rejected; explicit REJECT/IGNORE supported |
| Required extension capability/version negotiation | Preserve optional; reject unsupported required |
| Cross-engine sampling and opportunity identity | Host opportunity id; reference-only deterministic buckets |
| Maximum staleness + probability/history coverage | Conceptual only; no MAX_STALENESS built-in |
| Parallel derived-information conflicts | Sequential engine-local replacement only |
| Retry/defer scheduling and history/cache equivalence | Decisions serialize; engine does not schedule retries |
| External artifact integrity and schema resolution | No fetching; self-contained judgment schemas only |

No missing top-level category was established by the conceptual audit. Category
coverage does not imply portable syntax or runtime support for every example.

