# Specification blocks and trust limits

Authority is the pinned prose/schema revision, never observed Relay behavior.
The task prohibits modifying normative specifications, so new ambiguity notes
are recorded here instead of editing `spec/draft/open-questions.md`.

| ID | Exact boundary | Source |
| --- | --- | --- |
| numeric_portability | Mathematical mean is defined; no portable precision, rounding or tolerance specifies an exact JSON float for 1/3. Do not compare against an invented epsilon. Exactly representable 0.75 remains a mandatory golden. | `spec/draft/aggregation.md`, OPEN QUESTIONS; `spec/draft/open-questions.md` |
| sampling_identity | For 0<p<1, portable RUN/SKIP bucket identity is undefined. p=0 and p=1 are exact; determinism within one implementation can be tested separately. | `spec/draft/execution-policy.md` |
| parallel_cancellation_provenance | Portable RunRecord describes one interrupted attempt; multiple simultaneously interrupted attempts have no specified representation. Relay serializes token-cancelled occurrences. | `spec/draft/open-questions.md`, Relay boundaries |
| transport_policy_provenance | Optional Relay annotations are not normative transport/session or policy-provider provenance and have no independent SDK validation promise. | `spec/draft/provider-binding.md`, OPEN QUESTIONS |
| authenticity | Changing an opaque run identity without creating an internal contradiction, coherently rewriting a definition, and dishonest provider truth cannot be rejected through unauthenticated snapshots alone. | `spec/draft/provenance.md` |
| decision_error_category | ROUTE destination presence rules are explicit, but the normative stable-code list in `spec/draft/conformance.md` does not name a Decision-invariant error category. Rejection is required; its exact string category is BLOCKED_BY_SPEC. | `spec/draft/result.md`; `spec/draft/conformance.md` |
| weight_rewrite_validation | Weighted arithmetic and authored membership are required, but provenance validation does not promise re-execution of arbitrary custom Aggregate logic. Mutating only authored weights need not create a reconstructible source contradiction. Do not claim generic authenticated validation of such a rewrite. | `spec/draft/dataflow.md`; `spec/draft/provenance.md` |

Nonportable `local-sha256` identities are syntax-checked and retained, not treated
as portable signing bytes. Timing checks establish recorded bounds/order, not
clock authenticity. Metadata can vary without changing verdicts. Required unknown
extensions, cycles, iteration and dynamic expansion are unsupported and reject;
they are not silently implemented by the test model.
