# Focused adversarial review

A read-only review inspected the SDK lifecycle, schema resolution, and stdio
session validators before the final conformance/SDK commits. It checked ordering,
both correlation identities, exact version matching, event sequence boundaries,
terminal uniqueness, boolean/number identity, extension preservation, invalid
output, unsupported capabilities, and capability input/config/output schemas.

Read-only probes found two defects: fractional timestamps finer than a microsecond
lost ordering, and unresolved local schema pointers were accepted in manifests.
Inspection also found that a failed initialization could be retried. These were
fixed with exact fractional instant comparisons, local pointer target validation,
and an initialization-attempt guard. Targeted portable fixtures and reusable
regression tests cover those failures. Deadline precision requirements and the
supported self-contained schema subset are explicit in the specification.

Further checks exercise cancellation/completion races, expired attempts, split
UTF-8/coalesced frames, error responses after events, both RPC/invocation IDs,
enum/const/uniqueItems boolean distinctions, mutable caller data snapshots, and
missing/duplicate terminal Outcomes. Six focused property tests supplement the
portable cases. These checks cannot prove actual provider clock accuracy, budget
enforcement, side-effect isolation, or internal acceptance before any observable
response/event; those limitations are documented, not inferred from Python.
