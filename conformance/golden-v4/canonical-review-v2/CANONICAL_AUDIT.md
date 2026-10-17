# Canonical audit v2 — NOT COMPLETE

This is an honest partial review. None of the four requested gates passes. The deliverables do not establish a complete canonical semantic contract model. Missing semantic requirement counts remain unknown because source-unit disposition and a complete independent proposition traversal are unfinished.

## Baseline and allowed inputs

Repository HEAD: cc8814898f2f1005e2edcbaf2f67c7d7f410755f.
Working branch at review: test/openverify-golden-fast-v0.3.1. No production checkout was imported or executed; this review uses the current repository bytes. Only canonical-review-v2 artifacts are intended for the commit.

Explicitly authorized provisional inputs:

| Original file | SHA-256 preserved |
| --- | --- |
| CANONICAL_AUDIT.md | 48f93a9ef8fe03f32136c90af3b0432b4efa9d0b27b70e6b32bd51c76ae90690 |
| CANONICAL_MATH.md | ff2abc24380358651da13b2e274216ae0cd8ea97fd6da7c469423c0767ae4450 |
| CANONICAL_MODEL.md | 0d1cf0a141ae751d841597c583a30bd4820aed52f4d1b39342202d1ef4ab3b1e |
| CANONICAL_REQUIREMENTS.jsonl | 750076be2d2cbde9bee35d8346aa476e3a7ecd458d9e0954a22e374012de16c4 |


Prior canonical inputs were read, preserved and used only as provisional records. No prior Golden test/fixture/blueprint/coverage inventory/frozen expectation was read to decide requirements. Historical Golden prose embedded in source documents is not an authority and does not contribute requirements. No test suite, Relay invocation, provider execution, expectation freeze or test mapping ran.

## Four gates

| Gate | Verdict | Evidence |
| --- | --- | --- |
| Gate One: semantic source closure | FAIL | 314 prose units lack full clause-by-clause disposition; 246 inherited semantic records remain provisional. Candidate overlap is not closure. |
| Gate Two: whole-schema semantic closure | FAIL | 33 root predicates reconstructed with references resolved; 724 retained local components require independent context review, and schema/prose interaction reconciliation is incomplete. |
| Gate Three: behavioral mathematics | FAIL | 84 independently derived finite projections; 156 noncomponent records lack a domain; typed availability remains partial and public operation atomic closure is incomplete. |
| Gate Four: independent source completeness | FAIL | 37 selected source-first propositions compared, not a complete second traversal; publicness/closure of 366 discovered declarations is pending. |


Gate One is not accepted. The other sections record partial independent work, not advancement through or acceptance of later gates.

## Different quantities

| Quantity | Count | Meaning |
| --- | --- | --- |
| Discovered source files | 161 | Bytes hashed/indexed; not fully semantically reviewed files |
| Fully source-closed files | 0 | No complete clause-disposition certificate is asserted |
| Source positions | 2617 | Sections/prose blocks/JSON positions/declarations/reexports, not obligations |
| Atomic propositions defined | 104 | Concrete split/additional propositions; whole-source audit still pending |
| Whole-root structural predicates | 33 | One predicate per current wire root |
| Local overlapping schema components | 724 | IDs retained, not independent requirement total |
| Operation/capability summaries | 64 | Useful contracts pending atomic decomposition |
| Inherited provisional semantic records | 246 | Retained concrete content pending semantic/domain review |
| New finite projections | 84 | Each C=V+I+N checked independently of production |
| New symbolic domain descriptions | 109 | Not all are a completeness proof |
| Conditional dependent domains | 1 | Typed reachability remains partial |
| Old component domain descriptions | 724 | Provisional; not newly reverified |
| Selected second-pass propositions | 37 | Not a complete independent traversal |


## Reconciliation against provisional records

Local schema components retain their IDs. Whole-root structural predicates own them; they are not additive behavior requirements. Compound Result prohibitions, BLOCK effects, event sequence/correlation, output atomicity, semantic bindings, source ancestry, membership, cancellation, provenance and initialization were split where concrete children were authored. Every retirement/replacement is recorded below and in SOURCE_CROSSWALK.jsonl. Dependency references are expanded to replacement children.

```json
[
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.RESULT.NONEXECUTION",
    "replacement_ids": [
      "CM.VCP.RESULT.NONEXECUTION.EXECUTION_OUTCOME",
      "CM.VCP.RESULT.NONEXECUTION.APPLICABILITY",
      "CM.VCP.RESULT.NONEXECUTION.DETERMINATION",
      "CM.VCP.RESULT.NONEXECUTION.JUDGMENT",
      "CM.VCP.RESULT.NONEXECUTION.VERDICT",
      "CM.VCP.RESULT.NONEXECUTION.SCORE",
      "CM.VCP.RESULT.NONEXECUTION.SEVERITY"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.RESULT.ERROR",
    "replacement_ids": [
      "CM.VCP.RESULT.ERROR.APPLICABILITY",
      "CM.VCP.RESULT.ERROR.DETERMINATION",
      "CM.VCP.RESULT.ERROR.JUDGMENT",
      "CM.VCP.RESULT.ERROR.VERDICT",
      "CM.VCP.RESULT.ERROR.SCORE",
      "CM.VCP.RESULT.ERROR.SEVERITY"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.RESULT.NOT_APPLICABLE",
    "replacement_ids": [
      "CM.VCP.RESULT.NOT_APPLICABLE.DETERMINATION",
      "CM.VCP.RESULT.NOT_APPLICABLE.JUDGMENT",
      "CM.VCP.RESULT.NOT_APPLICABLE.VERDICT",
      "CM.VCP.RESULT.NOT_APPLICABLE.SCORE",
      "CM.VCP.RESULT.NOT_APPLICABLE.SEVERITY"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.RESULT.UNKNOWN",
    "replacement_ids": [
      "CM.VCP.RESULT.UNKNOWN.JUDGMENT",
      "CM.VCP.RESULT.UNKNOWN.VERDICT",
      "CM.VCP.RESULT.UNKNOWN.SCORE",
      "CM.VCP.RESULT.UNKNOWN.SEVERITY"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.PROVIDER.LIFE.SEQUENCE",
    "replacement_ids": [
      "CM.PROVIDER.LIFE.SEQUENCE.FIRST",
      "CM.PROVIDER.LIFE.SEQUENCE.INCREASE",
      "CM.PROVIDER.LIFE.SEQUENCE.GAPS",
      "CM.PROVIDER.LIFE.SEQUENCE.DUPLICATE",
      "CM.PROVIDER.LIFE.SEQUENCE.REORDER"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.PROVIDER.LIFE.CORRELATION",
    "replacement_ids": [
      "CM.PROVIDER.LIFE.CORRELATION.UNKNOWN",
      "CM.PROVIDER.LIFE.CORRELATION.AFTER_TERMINAL",
      "CM.PROVIDER.LIFE.CORRELATION.DUPLICATE_OUTCOME"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.DATA.RESOLVE_BLOCK",
    "replacement_ids": [
      "CM.VCP.DATA.RESOLVE_BLOCK.NONINVOCATION",
      "CM.VCP.DATA.RESOLVE_BLOCK.STATE",
      "CM.VCP.DATA.RESOLVE_BLOCK.RESULT",
      "CM.VCP.DATA.RESOLVE_BLOCK.REASON",
      "CM.VCP.DATA.RESOLVE_BLOCK.RESOLUTION",
      "CM.VCP.DATA.RESOLVE_BLOCK.DOWNSTREAM",
      "CM.VCP.DATA.RESOLVE_BLOCK.PROVENANCE"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.DATA.RUN_ACCEPT",
    "replacement_ids": [
      "CM.VCP.DATA.RUN_ACCEPT.UNKNOWN_NAME",
      "CM.VCP.DATA.RUN_ACCEPT.MISSING_REQUIRED",
      "CM.VCP.DATA.RUN_ACCEPT.VALUE_SCHEMA"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.DATA.ATOMIC_OUTPUT",
    "replacement_ids": [
      "CM.VCP.DATA.ATOMIC_OUTPUT.MISSING",
      "CM.VCP.DATA.ATOMIC_OUTPUT.EXTRA",
      "CM.VCP.DATA.ATOMIC_OUTPUT.ATOMIC"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.DATA.SEMANTIC_SUBJECT",
    "replacement_ids": [
      "CM.VCP.DATA.SEMANTIC_SUBJECT.SUBJECT",
      "CM.VCP.DATA.SEMANTIC_SUBJECT.CRITERION"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.DATA.ANCESTOR",
    "replacement_ids": [
      "CM.VCP.DATA.ANCESTOR.PRODUCER_EXISTS",
      "CM.VCP.DATA.ANCESTOR.OUTPUT_EXISTS",
      "CM.VCP.DATA.ANCESTOR.STRICT_ANCESTRY"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.GRAPH.IDENTITY",
    "replacement_ids": [
      "CM.VCP.GRAPH.IDENTITY.NODE_ID",
      "CM.VCP.GRAPH.IDENTITY.EDGE_ID",
      "CM.VCP.GRAPH.IDENTITY.ENDPOINT"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.POLICY.DECLARATION",
    "replacement_ids": [
      "CM.VCP.POLICY.DECLARATION.DISCRIMINATOR",
      "CM.VCP.POLICY.DECLARATION.BUILTIN_INPUTS",
      "CM.VCP.POLICY.DECLARATION.PROBABILITY_FIELD"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.AGG.MEMBERS",
    "replacement_ids": [
      "CM.VCP.AGG.MEMBERS.ORDER",
      "CM.VCP.AGG.MEMBERS.UNIQUE",
      "CM.VCP.AGG.MEMBERS.SOURCE_ROLE",
      "CM.VCP.AGG.MEMBERS.COMPLETE",
      "CM.VCP.AGG.MEMBERS.REQUIREDNESS"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.AGG.MEMBERS_INPUT",
    "replacement_ids": [
      "CM.VCP.AGG.MEMBERS_INPUT.CONSTANT",
      "CM.VCP.AGG.MEMBERS_INPUT.RESERVED"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.LIFECYCLE.CANCEL_RUNNING",
    "replacement_ids": [
      "CM.VCP.LIFECYCLE.CANCEL_RUNNING.STATE",
      "CM.VCP.LIFECYCLE.CANCEL_RUNNING.RESULT",
      "CM.VCP.LIFECYCLE.CANCEL_RUNNING.LATER",
      "CM.VCP.LIFECYCLE.CANCEL_RUNNING.OBSERVATION"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.AGG.MAJORITY",
    "replacement_ids": [
      "CM.VCP.AGG.MAJORITY.PASS",
      "CM.VCP.AGG.MAJORITY.FAIL",
      "CM.VCP.AGG.MAJORITY.TIE"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.PROV.NODE_SET",
    "replacement_ids": [
      "CM.VCP.PROV.NODE_SET.EXACT",
      "CM.VCP.PROV.NODE_SET.ORDER"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.PROV.TIMING",
    "replacement_ids": [
      "CM.VCP.PROV.TIMING.INTERVAL",
      "CM.VCP.PROV.TIMING.DEPENDENCY"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.PROV.UNSTARTED",
    "replacement_ids": [
      "CM.VCP.PROV.UNSTARTED.EXECUTOR",
      "CM.VCP.PROV.UNSTARTED.OBSERVATION",
      "CM.VCP.PROV.UNSTARTED.INFORMATION",
      "CM.VCP.PROV.UNSTARTED.USAGE"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.VCP.OBS.AUTHORITY",
    "replacement_ids": [
      "CM.VCP.OBS.AUTHORITY.OVERLAP",
      "CM.VCP.OBS.AUTHORITY.NO_SUM"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "SPLIT_COMPOUND",
    "prior_id": "CM.PROVIDER.INIT.ONCE",
    "replacement_ids": [
      "CM.PROVIDER.INIT.ONCE.PREWORK",
      "CM.PROVIDER.INIT.ONCE.ONCE",
      "CM.PROVIDER.INIT.ONCE.FAIL_CLOSE"
    ],
    "reason": "Separately observable propositions; preserve the original source references."
  },
  {
    "kind": "EQUIVALENT_FORMULATIONS",
    "ids": [
      "CM.VCP.GRAPH.NO_DATA",
      "CM.VCP.DATA.CONTEXT"
    ],
    "reason": "Execution edges carry no values and absence of injected predecessor Context are related but different observable prohibitions; retained separately, not merged."
  }
]
```

## Independent second traversal — selected scope only

The source-first propositions below start from actual source clauses. Ownership comparison happens afterward. This list is not complete and cannot certify source completeness. A related broad owner still requires atomic review.

| Proposition ID | Source | Semantic proposition | Owner | Comparison |
| --- | --- | --- | --- | --- |
| SP.b569ae1a8db31113beb7 | spec/draft/computation.md:11-13 | Only declared resolved inputs, separate config; no ambient predecessor argument. | CM.VCP.DATA.CONTEXT | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.d9458f3a7f5fafd1578e | spec/draft/composition.md:5-9 | All predecessors must settle; edges carry neither data nor implicit failure. | CM.VCP.GRAPH.READINESS | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.4ffc08ee499e8d500bbe | spec/draft/dataflow.md:107-118 | Required BLOCK prevents invocation and yields SKIPPED/INPUT_UNAVAILABLE. | CM.VCP.DATA.RESOLVE_BLOCK.NONINVOCATION | OWNER_EXISTS_MEANING_COMPARISON_RECORDED |
| SP.491aafff2c4a1beb40e9 | spec/draft/dataflow.md:107-118 | Disabled nodes retain all input resolution snapshots. | CM.VCP.DATA.RESOLVE_ALL | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.d817c0a5f4ea8a924ffb | spec/draft/dataflow.md:74-85 | Bookkeeping Result is usable only if producer port admits it. | CM.VCP.DATA.BOOKKEEPING | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.05e3c9dc48999f5b8822 | spec/draft/dataflow.md:87-94 | Emitted null judgment requires schema validation; absence does not. | CM.VCP.DATA.JUDGMENT | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.fe0e370b338d56568f34 | spec/draft/dataflow.md:127-140 | Custom reducer receives members constant equal to ordered structural membership. | CM.VCP.AGG.MEMBERS_INPUT.CONSTANT | OWNER_EXISTS_MEANING_COMPARISON_RECORDED |
| SP.96d431c6a32d9d589530 | spec/draft/aggregation.md:20-38 | Filtering preserves original weight identities. | CM.VCP.AGG.WEIGHTED | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.74bb75c5f676efa91446 | spec/draft/aggregation.md:20-38 | Evidence order follows retained member order. | CM.VCP.AGG.EVIDENCE_ORDER | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.6b2f2d8cff67a1a5dddd | spec/draft/lifecycle.md:46-52 | Route exclusions accumulate, preserving shared joins. | CM.VCP.LIFECYCLE.ROUTE_EXCLUSION | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.74022253cf5672051ae9 | spec/draft/lifecycle.md:46-52 | Guarded join is all-incoming conjunction. | CM.VCP.LIFECYCLE.GUARD_JOIN | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.2e90de3d0956479a4923 | spec/draft/lifecycle.md:54-57 | Later cancellation/control never revises prior terminal records. | CM.VCP.LIFECYCLE.TERMINAL | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.5151b7cd5bea500e7167 | spec/draft/execution-policy.md:55-58 | Inactive/unselected opportunities create no occurrence records. | CM.VCP.POLICY.INACTIVE | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.96840f81b1fad21e042a | spec/draft/provenance.md:11-20 | Reconstruct recorded lineage without provider rerun. | CM.VCP.PROV.RECONSTRUCT | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.267ca5edf4ea9d41ae8c | spec/draft/provenance.md:29-32 | Consistency validation does not authenticate coherent rewrites. | CM.VCP.PROV.TRUST_LIMIT | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.6a8b83afb104a2abf14b | spec/draft/knowledge.md:11-14 | Empty structured data is meaningful Evidence; annotations alone are not. | CM.VCP.KNOWLEDGE.EVIDENCE | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.e99599a609a53058b1f2 | spec/draft/extensions.md:5-13 | Preserve unknown optional extension data without interpretation. | CM.VCP.EXT.PRESERVE | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.0e54456e7a4c4824a3ed | provider-contract/spec/draft/lifecycle.md:10-18 | First event is sequence one. | CM.PROVIDER.LIFE.SEQUENCE.FIRST | OWNER_EXISTS_MEANING_COMPARISON_RECORDED |
| SP.8ecd597bb0c21a4d67c6 | provider-contract/spec/draft/lifecycle.md:10-18 | Increasing sequence gaps are legal without replay promise. | CM.PROVIDER.LIFE.SEQUENCE.GAPS | OWNER_EXISTS_MEANING_COMPARISON_RECORDED |
| SP.9f215076e1b84e2f5e7d | provider-contract/spec/draft/lifecycle.md:10-18 | Distinct attempts may interleave while preserving local order. | CM.PROVIDER.LIFE.INTERLEAVING | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.12e0ea563f4c2acfb9a5 | provider-contract/spec/draft/lifecycle.md:20-27 | Terminal cancellation is acknowledged no-op. | CM.PROVIDER.CANCEL.TERMINAL | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.e1a8dd2cd84ad26b7b8f | provider-contract/spec/draft/lifecycle.md:29-39 | Expired valid request performs no work and ends deadline-exceeded. | CM.PROVIDER.DEADLINE.ACCEPT | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.4e2dfa5443e7734a6626 | provider-contract/spec/draft/lifecycle.md:41-45 | Expiry is irreversible even after clock rollback. | CM.PROVIDER.DEADLINE.IRREVERSIBLE | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.9ab0431b129f21e2b155 | provider-contract/spec/draft/lifecycle.md:56-59 | Final usage supersedes snapshots without addition. | CM.PROVIDER.USAGE.FINAL | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.53f43ce0b35490f977ce | provider-contract/spec/draft/transports.md:8-20 | Both partial and coalesced framed reads work. | CM.PROVIDER.STDIO.RECEIVE | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.9c31632d1703549f7d24 | provider-contract/spec/draft/transports.md:43-46 | Cancellation acknowledgement proves processing, not cancelled termination. | CM.PROVIDER.RPC.CANCEL_ACK | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.df980259fb217f4a597c | provider-contract/spec/draft/errors.md:23-27 | Independent error precedence is recommended, not universally mandatory. | CM.PROVIDER.ERROR.PRECEDENCE | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.e6a11cab46596265394f | provider-contract/spec/draft/capabilities.md:24-35 | Namespace syntax does not authenticate ownership. | CM.PROVIDER.NAMESPACE.OWNERSHIP | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.72d1b660c756d7bb2e8c | provider-contract/spec/draft/versioning.md:6-14 | Version selection respects runner preference among supported exact identifiers. | CM.PROVIDER.INIT.SELECT | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.b1dafc845078067e3e08 | docs/relay/architecture.md:64-70 | All wave members settle before successors. | CM.RELAY.SCHED.WAVE | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.81385d38da0a32545639 | docs/relay/architecture.md:64-70 | Control executes as a serial barrier. | CM.RELAY.SCHED.CONTROL | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.922cc6a807683590d890 | docs/relay/architecture.md:85-89 | Observer failure is diagnostic; store failure propagates. | CM.RELAY.OBSERVER.ERROR | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.c644a040d34227c26486 | docs/relay/integration.md:86-91 | Valid FAIL is an HTTP 200 RunRecord. | CM.RELAY.HTTP.SHAPE | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.8c49de9094c86fb20469 | docs/relay/security.md:9-16 | Default catalog has command checking without command launching. | CM.RELAY.CATALOG.TRUST | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.8b088b1a7f8adf969747 | docs/relay/providers.md:112-118 | Zero-length ranges intersect nothing. | CM.RELAY.SCOPE.RANGES | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |
| SP.7c70c01f6aae90cca793 | docs/relay/providers.md:120-127 | Allowed directory itself is not an allowed action target. | CM.RELAY.STANDARD.ACTION.PREFIX_SELF | OWNER_EXISTS_MEANING_COMPARISON_RECORDED |
| SP.d3f56f256e9d0d02e6b8 | docs/relay/limitations.md:7-40 | Task cancellation cleans up and returns no fabricated completed record. | CM.RELAY.CANCEL.TASK | RELATED_OWNER_EXISTS_ATOMIC_CLOSURE_PENDING |


## Exact unfinished review locations

These are pending review positions, not mechanically invented missing requirements. The number of actual missing semantic propositions cannot be inferred from either table. Semantic overlap does not discharge a whole paragraph.

| Source-unit ID | Source | Section | Selected second-pass propositions |
| --- | --- | --- | --- |
| SU.1316ca8f71bfbf4618a8 | conformance/README.md:3-6 | Portable draft conformance |  |
| SU.73a3499276fa13861ce5 | conformance/README.md:8-11 | Portable draft conformance |  |
| SU.39155945a955c4aa2a66 | conformance/README.md:13-17 | Portable draft conformance |  |
| SU.8fd452e5f173df8c2385 | docs/relay/architecture.md:3-6 | Relay architecture and contracts |  |
| SU.ae48e7803c656ff2f154 | docs/relay/architecture.md:24-29 | Relay architecture and contracts |  |
| SU.8155e863fd38725cd73e | docs/relay/architecture.md:31-38 | Relay architecture and contracts |  |
| SU.5c51ab9bbb98bdf52a00 | docs/relay/architecture.md:40-47 | Relay architecture and contracts |  |
| SU.e7e768ef1bca23379447 | docs/relay/architecture.md:49-53 | Relay architecture and contracts |  |
| SU.03ef9eab3c97cceedf01 | docs/relay/architecture.md:55-62 | Relay architecture and contracts |  |
| SU.7207a3c8d7fbd8c7e6b9 | docs/relay/architecture.md:64-70 | Relay architecture and contracts | SP.b1dafc845078067e3e08,SP.81385d38da0a32545639 |
| SU.339f8b6aafc151773a06 | docs/relay/architecture.md:72-76 | Relay architecture and contracts |  |
| SU.c5d91e5590603d465418 | docs/relay/architecture.md:78-83 | Relay architecture and contracts |  |
| SU.6ac158c03b6a7a60ebff | docs/relay/architecture.md:85-89 | Relay architecture and contracts | SP.922cc6a807683590d890 |
| SU.1849f0baf2678c48b9bb | docs/relay/architecture.md:91-94 | Relay architecture and contracts |  |
| SU.93a870bfdd7abd1f9592 | docs/relay/error-contract-hardening.md:3-5 | Error-contract hardening after the Golden 0.2.0 freeze |  |
| SU.6f5d9ad56406f1a3ad17 | docs/relay/error-contract-hardening.md:7-13 | Error-contract hardening after the Golden 0.2.0 freeze |  |
| SU.dc1f3c3723efc58ca636 | docs/relay/error-contract-hardening.md:15-19 | Error-contract hardening after the Golden 0.2.0 freeze |  |
| SU.477429bcf62b0747b75c | docs/relay/error-contract-hardening.md:21-23 | Error-contract hardening after the Golden 0.2.0 freeze |  |
| SU.3a61362acf27f3187e43 | docs/relay/error-contract-hardening.md:25-25 | Error-contract hardening after the Golden 0.2.0 freeze |  |
| SU.676c55f124d4c2cf5af5 | docs/relay/error-contract-hardening.md:27-35 | Error-contract hardening after the Golden 0.2.0 freeze |  |
| SU.ef865493d116c818598b | docs/relay/error-contract-hardening.md:37-40 | Error-contract hardening after the Golden 0.2.0 freeze |  |
| SU.1815111a470b1d2dd942 | docs/relay/error-contract-hardening.md:42-44 | Error-contract hardening after the Golden 0.2.0 freeze |  |
| SU.901f53bfb5d89dc25051 | docs/relay/error-contract-hardening.md:46-60 | Error-contract hardening after the Golden 0.2.0 freeze |  |
| SU.90e5f42a45ef069d85c1 | docs/relay/graph-authoring.md:3-4 | Author portable graphs |  |
| SU.340e784949aff9b94d94 | docs/relay/graph-authoring.md:12-17 | Author portable graphs |  |
| SU.efc84df4a40ce0d4fbd4 | docs/relay/graph-authoring.md:19-23 | Author portable graphs |  |
| SU.14535b8011db5e9deee9 | docs/relay/graph-authoring.md:25-30 | Author portable graphs |  |
| SU.68fa5aa752b1590ca328 | docs/relay/graph-authoring.md:32-35 | Author portable graphs |  |
| SU.c3a957e588ea2dd865b2 | docs/relay/graph-authoring.md:37-42 | Author portable graphs |  |
| SU.fbe30eb0437004598978 | docs/relay/graph-authoring.md:44-49 | Author portable graphs |  |
| SU.cd6665c4a30d08a0491e | docs/relay/graph-authoring.md:51-57 | Author portable graphs |  |
| SU.086bdb7ace6a79bb5406 | docs/relay/graph-authoring.md:59-63 | Author portable graphs |  |
| SU.88c32c1b252c0fed9627 | docs/relay/graph-authoring.md:65-70 | Author portable graphs |  |
| SU.d9b02e9d598d67241142 | docs/relay/graph-authoring.md:72-75 | Author portable graphs |  |
| SU.0bfb5ba1a15f0e0f03d2 | docs/relay/graph-authoring.md:84-87 | Author portable graphs |  |
| SU.6922ebe914ce0f226520 | docs/relay/integration.md:3-7 | Hosts, agents, services, and infrastructure |  |
| SU.ddf371532143b9f384f7 | docs/relay/integration.md:16-25 | Hosts, agents, services, and infrastructure |  |
| SU.ce0fd53b849de2d1fc80 | docs/relay/integration.md:27-30 | Hosts, agents, services, and infrastructure |  |
| SU.e5b192244d6ba6426047 | docs/relay/integration.md:32-32 | Hosts, agents, services, and infrastructure |  |
| SU.043795ecd52473d8270e | docs/relay/integration.md:39-45 | Hosts, agents, services, and infrastructure |  |
| SU.d581c4bde9e9f7a7d144 | docs/relay/integration.md:47-47 | Hosts, agents, services, and infrastructure |  |
| SU.a73fc13859f7101d4c35 | docs/relay/integration.md:59-63 | Hosts, agents, services, and infrastructure |  |
| SU.f5ea39f86a95ace2cd82 | docs/relay/integration.md:65-65 | Hosts, agents, services, and infrastructure |  |
| SU.4ec9a56421c8fb2c5958 | docs/relay/integration.md:72-74 | Hosts, agents, services, and infrastructure |  |
| SU.f8f1508725ea6d344544 | docs/relay/integration.md:80-80 | Hosts, agents, services, and infrastructure |  |
| SU.48539790df8d75f80481 | docs/relay/integration.md:86-91 | Hosts, agents, services, and infrastructure | SP.c644a040d34227c26486 |
| SU.d124a0eaa023d95a10f2 | docs/relay/integration.md:93-93 | Hosts, agents, services, and infrastructure |  |
| SU.dccc20156b096838973e | docs/relay/integration.md:113-119 | Hosts, agents, services, and infrastructure |  |
| SU.e14ea2ca1a171f1a5f6f | docs/relay/integration.md:121-121 | Hosts, agents, services, and infrastructure |  |
| SU.a3aaebba35a9d6e33c44 | docs/relay/integration.md:128-129 | Hosts, agents, services, and infrastructure |  |
| SU.fb4d386abc0a3ae7a80c | docs/relay/limitations.md:3-5 | Implemented boundary and limitations |  |
| SU.ed4c219abbd2282d2b7f | docs/relay/limitations.md:7-40 | Implemented boundary and limitations | SP.d3f56f256e9d0d02e6b8 |
| SU.9852959e6d1630c6031f | docs/relay/limitations.md:42-43 | Implemented boundary and limitations |  |
| SU.a659ca700e987d7c43e0 | docs/relay/production-fixes-report.md:3-4 | Targeted Relay production fixes |  |
| SU.7be99aee1cb7933ce03a | docs/relay/production-fixes-report.md:8-16 | Targeted Relay production fixes / Revisions and preservation |  |
| SU.017f3299042667e3d5cf | docs/relay/production-fixes-report.md:20-25 | Targeted Relay production fixes / Already present at 5064efb |  |
| SU.8ae866bbb5dee730fd28 | docs/relay/production-fixes-report.md:27-31 | Targeted Relay production fixes / Already present at 5064efb |  |
| SU.4391c25fee55f9ceb39b | docs/relay/production-fixes-report.md:35-63 | Targeted Relay production fixes / New repairs |  |
| SU.21c0e81347921491c960 | docs/relay/production-fixes-report.md:80-82 | Targeted Relay production fixes / Exact production files changed |  |
| SU.de70cafd16eb0e3fe67d | docs/relay/production-fixes-report.md:86-94 | Targeted Relay production fixes / Public Python compatibility |  |
| SU.eac933dee0c4c195c530 | docs/relay/production-fixes-report.md:98-100 | Targeted Relay production fixes / Validation |  |
| SU.4711dac6bb359c3f8a61 | docs/relay/production-fixes-report.md:102-115 | Targeted Relay production fixes / Validation |  |
| SU.54d9671be42d53cdbf7a | docs/relay/production-fixes-report.md:117-120 | Targeted Relay production fixes / Validation |  |
| SU.8255955341c662a69d16 | docs/relay/production-fixes-report.md:124-131 | Targeted Relay production fixes / Validation / Frozen Golden execution evidence |  |
| SU.32c42432cb9bb1314281 | docs/relay/production-fixes-report.md:133-138 | Targeted Relay production fixes / Validation / Frozen Golden execution evidence |  |
| SU.1f798ef113643192e4b8 | docs/relay/production-fixes-report.md:140-143 | Targeted Relay production fixes / Validation / Frozen Golden execution evidence |  |
| SU.a66494cdfce1c72230bc | docs/relay/production-fixes-report.md:147-150 | Targeted Relay production fixes / Remaining decisions and Golden-only work |  |
| SU.e2815eae4c06570cf022 | docs/relay/production-fixes-report.md:152-156 | Targeted Relay production fixes / Remaining decisions and Golden-only work |  |
| SU.0c987d8dd73c43ed0895 | docs/relay/production-fixes-report.md:160-169 | Targeted Relay production fixes / Verdicts |  |
| SU.6b80cd92b9dad661a533 | docs/relay/providers.md:3-5 | Providers and standard capabilities |  |
| SU.2e8e13a4a8b4be146afc | docs/relay/providers.md:12-23 | Providers and standard capabilities |  |
| SU.7536cb1f638ebbc7b4f3 | docs/relay/providers.md:25-29 | Providers and standard capabilities |  |
| SU.c4823ed15e25f16bf758 | docs/relay/providers.md:31-37 | Providers and standard capabilities |  |
| SU.db9b459f2b89d39c976b | docs/relay/providers.md:39-41 | Providers and standard capabilities |  |
| SU.4c56816d720d1440d647 | docs/relay/providers.md:43-50 | Providers and standard capabilities |  |
| SU.c298f5589376e9348035 | docs/relay/providers.md:52-53 | Providers and standard capabilities |  |
| SU.a2ab1ef85c1b92f18836 | docs/relay/providers.md:60-65 | Providers and standard capabilities |  |
| SU.3b8454eb4aa62260a9c4 | docs/relay/providers.md:67-70 | Providers and standard capabilities |  |
| SU.107a32b36508514ff681 | docs/relay/providers.md:72-91 | Providers and standard capabilities |  |
| SU.f066dff41e2095fee237 | docs/relay/providers.md:93-98 | Providers and standard capabilities |  |
| SU.938bbf7c4e1d464e0341 | docs/relay/providers.md:102-110 | Providers and standard capabilities / Local path comparisons |  |
| SU.bf944b2602a79db844fc | docs/relay/providers.md:112-118 | Providers and standard capabilities / Local path comparisons | SP.8b088b1a7f8adf969747 |
| SU.7ce305d419589a02b810 | docs/relay/providers.md:120-127 | Providers and standard capabilities / Local path comparisons | SP.7c70c01f6aae90cca793 |
| SU.a7a5036bc9eec2a13dce | docs/relay/providers.md:129-136 | Providers and standard capabilities / Local path comparisons |  |
| SU.67c2fdf8beb22aa0ad27 | docs/relay/providers.md:138-144 | Providers and standard capabilities / Local path comparisons |  |
| SU.a84e43e93a3e56bc5835 | docs/relay/providers.md:146-147 | Providers and standard capabilities / Local path comparisons |  |
| SU.c7858952a90b567f742a | docs/relay/quickstart.md:3-6 | OpenVerify Relay v0.1 |  |
| SU.524278c5e66a1761e024 | docs/relay/quickstart.md:14-16 | OpenVerify Relay v0.1 |  |
| SU.56f29c148f6a3855d312 | docs/relay/quickstart.md:18-18 | OpenVerify Relay v0.1 |  |
| SU.6d7faadc65afc639091b | docs/relay/quickstart.md:25-25 | OpenVerify Relay v0.1 |  |
| SU.8f5d3050ba377d5fbce1 | docs/relay/quickstart.md:31-31 | OpenVerify Relay v0.1 |  |
| SU.d0485ce282ac0a22aff8 | docs/relay/quickstart.md:43-46 | OpenVerify Relay v0.1 |  |
| SU.ba12201cdec85b317831 | docs/relay/quickstart.md:48-53 | OpenVerify Relay v0.1 |  |
| SU.12c2bd697c0bd79292d4 | docs/relay/quickstart.md:55-58 | OpenVerify Relay v0.1 |  |
| SU.a90275d19ba1e7cf1c40 | docs/relay/quickstart.md:60-60 | OpenVerify Relay v0.1 |  |
| SU.c67192ad37c65f97894a | docs/relay/quickstart.md:67-70 | OpenVerify Relay v0.1 |  |
| SU.d34c0bddba9e227d2752 | docs/relay/quickstart.md:77-80 | OpenVerify Relay v0.1 |  |
| SU.0d75ce87d7415cf46b37 | docs/relay/quickstart.md:82-82 | OpenVerify Relay v0.1 |  |
| SU.57a695351545afb2c595 | docs/relay/quickstart.md:100-105 | OpenVerify Relay v0.1 |  |
| SU.c62f7d4ac63d46d459ac | docs/relay/quickstart.md:107-109 | OpenVerify Relay v0.1 |  |
| SU.23a3c54739801b3b4a7d | docs/relay/security.md:3-7 | Execution and trust boundary |  |
| SU.5ee6ed887a4bde65a395 | docs/relay/security.md:9-16 | Execution and trust boundary | SP.8c49de9094c86fb20469 |
| SU.9a4aa01a7bd211b73ccb | docs/relay/security.md:18-25 | Execution and trust boundary |  |
| SU.b5d7e0d55f0b9916176f | docs/relay/security.md:27-33 | Execution and trust boundary |  |
| SU.aaba433073a930b70218 | docs/relay/security.md:35-42 | Execution and trust boundary |  |
| SU.5af4b95d013cd9d3ae3f | docs/relay/security.md:44-50 | Execution and trust boundary |  |
| SU.a8830db664098c58bad1 | docs/relay/security.md:52-58 | Execution and trust boundary |  |
| SU.2a27659f745ceb185c4d | docs/relay/security.md:60-66 | Execution and trust boundary |  |
| SU.555f1258eec4766e3d30 | docs/relay/security.md:68-73 | Execution and trust boundary |  |
| SU.a185bde3ad339e4bda22 | docs/relay/verification.md:3-7 | Relay v0.1 completion evidence |  |
| SU.716fa46703af8979980a | docs/relay/verification.md:9-21 | Relay v0.1 completion evidence |  |
| SU.e8f8a38762db0cf56bd3 | docs/relay/verification.md:23-23 | Relay v0.1 completion evidence |  |
| SU.d54aa53f06c5a13db1d1 | docs/relay/verification.md:25-35 | Relay v0.1 completion evidence |  |
| SU.a5b82c21292f3a8d22b9 | docs/relay/verification.md:37-42 | Relay v0.1 completion evidence |  |
| SU.f45bf0ecdb6e81c02341 | docs/relay/verification.md:44-44 | Relay v0.1 completion evidence |  |
| SU.91cd961c1787ed2305e6 | docs/relay/verification.md:46-75 | Relay v0.1 completion evidence |  |
| SU.e01197717a1f32ec47e6 | docs/relay/verification.md:77-81 | Relay v0.1 completion evidence |  |
| SU.f4696f710cfd158dac15 | docs/relay/verification.md:83-83 | Relay v0.1 completion evidence |  |
| SU.d5150a35c7a04fbfe7bd | docs/relay/verification.md:94-97 | Relay v0.1 completion evidence |  |
| SU.92cdc17696007d416d56 | docs/relay/verification.md:99-102 | Relay v0.1 completion evidence |  |
| SU.c86543f32cb0bfee53ce | profiles/standard-draft/README.md:3-7 | Standard draft profile |  |
| SU.5ee6d74214a06c572e86 | profiles/standard-draft/README.md:9-17 | Standard draft profile |  |
| SU.9a9f330a329b6292a8b3 | provider-contract/conformance/README.md:3-7 | Portable conformance suite |  |
| SU.2952fa177c2902f652ab | provider-contract/conformance/README.md:9-11 | Portable conformance suite |  |
| SU.3b43772ec245b9f448bb | provider-contract/conformance/README.md:13-18 | Portable conformance suite |  |
| SU.4373b804b697dff2f082 | provider-contract/conformance/README.md:20-23 | Portable conformance suite |  |
| SU.a5b709041ef9ee47473f | provider-contract/conformance/README.md:25-27 | Portable conformance suite |  |
| SU.bdc52225d128e9ff1eae | provider-contract/README.md:3-3 | OpenVerify Provider Contract |  |
| SU.60d417063a1afeba8928 | provider-contract/README.md:5-8 | OpenVerify Provider Contract |  |
| SU.2405869157df82ac59d3 | provider-contract/README.md:24-27 | OpenVerify Provider Contract |  |
| SU.67e8e1d58575987b4687 | provider-contract/README.md:33-39 | OpenVerify Provider Contract |  |
| SU.c9d868b00367c9061829 | provider-contract/README.md:41-44 | OpenVerify Provider Contract |  |
| SU.e563d0c6866565104a47 | provider-contract/README.md:46-52 | OpenVerify Provider Contract |  |
| SU.0921d28ba85db796a8b0 | provider-contract/README.md:54-56 | OpenVerify Provider Contract |  |
| SU.c25489a3f01c6e54686f | provider-contract/README.md:58-68 | OpenVerify Provider Contract |  |
| SU.dd50fe4823d02e419fea | provider-contract/README.md:70-70 | OpenVerify Provider Contract |  |
| SU.c72426cba850fd3202ef | provider-contract/spec/draft/capabilities.md:3-7 | Manifest and capabilities |  |
| SU.efe6e921f8d49cfadea4 | provider-contract/spec/draft/capabilities.md:9-22 | Manifest and capabilities |  |
| SU.fe8458cddebac363b8ce | provider-contract/spec/draft/capabilities.md:24-35 | Manifest and capabilities | SP.e6a11cab46596265394f |
| SU.8ded9e961eaa6ae0c4b7 | provider-contract/spec/draft/capabilities.md:37-45 | Manifest and capabilities |  |
| SU.a937f63ba49099d1a716 | provider-contract/spec/draft/capabilities.md:47-51 | Manifest and capabilities |  |
| SU.161b7861bc9abe471e50 | provider-contract/spec/draft/errors.md:3-4 | Errors |  |
| SU.609b3fbed16c00e0be0d | provider-contract/spec/draft/errors.md:6-15 | Errors |  |
| SU.d9bfe85de8e53e3612d8 | provider-contract/spec/draft/errors.md:17-21 | Errors |  |
| SU.04b5d81b88b88f11cac9 | provider-contract/spec/draft/errors.md:23-27 | Errors | SP.df980259fb217f4a597c |
| SU.b2dc968690180a3b7b90 | provider-contract/spec/draft/errors.md:29-33 | Errors |  |
| SU.8f480efac62237c3cdab | provider-contract/spec/draft/lifecycle.md:3-8 | Lifecycle |  |
| SU.6e1af19b317feb3c20b0 | provider-contract/spec/draft/lifecycle.md:10-18 | Lifecycle | SP.0e54456e7a4c4824a3ed,SP.8ecd597bb0c21a4d67c6,SP.9f215076e1b84e2f5e7d |
| SU.a29111d10a3790648f70 | provider-contract/spec/draft/lifecycle.md:20-27 | Lifecycle | SP.12e0ea563f4c2acfb9a5 |
| SU.49303d1c41be8ae403e4 | provider-contract/spec/draft/lifecycle.md:29-39 | Lifecycle | SP.e1a8dd2cd84ad26b7b8f |
| SU.4ef4b4e8689d89cad9f1 | provider-contract/spec/draft/lifecycle.md:41-45 | Lifecycle | SP.4e2dfa5443e7734a6626 |
| SU.349d9f7df4fd68780a8c | provider-contract/spec/draft/lifecycle.md:47-47 | Lifecycle |  |
| SU.d0c7c92401db2b6c675f | provider-contract/spec/draft/lifecycle.md:49-54 | Lifecycle |  |
| SU.945347d36a164704305d | provider-contract/spec/draft/lifecycle.md:56-59 | Lifecycle | SP.9ab0431b129f21e2b155 |
| SU.1cb6a75c6ed0ea2b3bcf | provider-contract/spec/draft/lifecycle.md:61-64 | Lifecycle |  |
| SU.79133c872d6e4755b1b8 | provider-contract/spec/draft/lifecycle.md:66-72 | Lifecycle |  |
| SU.2265e0c38dbf8be17bb2 | provider-contract/spec/draft/overview.md:3-5 | Overview |  |
| SU.302fb48f1a969569cb8f | provider-contract/spec/draft/overview.md:7-9 | Overview |  |
| SU.5b88dc40ceb6f08cd363 | provider-contract/spec/draft/overview.md:11-15 | Overview |  |
| SU.8a4a021fcef21466823a | provider-contract/spec/draft/overview.md:17-20 | Overview |  |
| SU.b1a82537f08d7e2fc01c | provider-contract/spec/draft/overview.md:22-25 | Overview |  |
| SU.515dea6424a6ab033a2a | provider-contract/spec/draft/transports.md:3-6 | Transport-neutral semantics; baseline stdio binding |  |
| SU.8c8fa33e57ab85dd65e2 | provider-contract/spec/draft/transports.md:8-20 | Transport-neutral semantics; baseline stdio binding | SP.53f43ce0b35490f977ce |
| SU.01840420f146a3836b59 | provider-contract/spec/draft/transports.md:22-24 | Transport-neutral semantics; baseline stdio binding |  |
| SU.0575631d13fcadf5e9d2 | provider-contract/spec/draft/transports.md:26-31 | Transport-neutral semantics; baseline stdio binding |  |
| SU.ea37d0b9f58556738ea9 | provider-contract/spec/draft/transports.md:33-41 | Transport-neutral semantics; baseline stdio binding |  |
| SU.69829fce7bd0194be09f | provider-contract/spec/draft/transports.md:43-46 | Transport-neutral semantics; baseline stdio binding | SP.9c31632d1703549f7d24 |
| SU.dd81fc0043b3542ed200 | provider-contract/spec/draft/transports.md:48-55 | Transport-neutral semantics; baseline stdio binding |  |
| SU.9b875752bfe0cf75da2b | provider-contract/spec/draft/transports.md:57-57 | Transport-neutral semantics; baseline stdio binding |  |
| SU.54a2ead93090cb043e10 | provider-contract/spec/draft/transports.md:63-64 | Transport-neutral semantics; baseline stdio binding |  |
| SU.06d541170320d315a93e | provider-contract/spec/draft/transports.md:71-75 | Transport-neutral semantics; baseline stdio binding |  |
| SU.edfec0130705427b3f06 | provider-contract/spec/draft/versioning.md:3-4 | Compatibility and initialization |  |
| SU.48008af6d67b0e06a4a0 | provider-contract/spec/draft/versioning.md:6-14 | Compatibility and initialization | SP.72d1b660c756d7bb2e8c |
| SU.7db91a88ad41afc0ae0f | provider-contract/spec/draft/versioning.md:16-20 | Compatibility and initialization |  |
| SU.c90e1976f14dad11a482 | provider-contract/spec/draft/versioning.md:22-28 | Compatibility and initialization |  |
| SU.505f6cb04ce49b5a1b49 | provider-contract/spec/draft/versioning.md:30-34 | Compatibility and initialization |  |
| SU.4c21f1ddcdfeb6fa966c | provider-contract/spec/draft/wire-format.md:3-10 | Wire objects |  |
| SU.f38cd5c413d67bba58b9 | provider-contract/spec/draft/wire-format.md:12-17 | Wire objects |  |
| SU.c4f4b244150cc8cba8c6 | provider-contract/spec/draft/wire-format.md:19-22 | Wire objects |  |
| SU.e28c3049e09b6d74eeb8 | provider-contract/spec/draft/wire-format.md:24-33 | Wire objects |  |
| SU.797b2b8ef156128da9f4 | provider-contract/spec/draft/wire-format.md:35-35 | Wire objects |  |
| SU.7e15d516475c4653f2cc | provider-contract/spec/draft/wire-format.md:37-44 | Wire objects |  |
| SU.80328ebd27f73ae0c5a6 | provider-contract/spec/draft/wire-format.md:46-48 | Wire objects |  |
| SU.455d7a055f1cb2f5c85b | provider-contract/spec/draft/wire-format.md:50-55 | Wire objects |  |
| SU.ebca9df6e40363e74715 | provider-contract/spec/draft/wire-format.md:57-65 | Wire objects |  |
| SU.c16f09412245ded0c6b5 | README.md:3-5 | Openverify |  |
| SU.d427af0b07eb5d1e4fc4 | README.md:7-8 | Openverify |  |
| SU.70a1ac89e76048379675 | README.md:12-14 | Openverify / Run verification with Relay |  |
| SU.9b3c19f3665419f9cd86 | README.md:25-31 | Openverify / Run verification with Relay |  |
| SU.b1f888966f2b9ed39c40 | README.md:35-39 | Openverify / Why it exists |  |
| SU.c7952c11a998807c0500 | README.md:65-67 | Openverify / Why it exists |  |
| SU.31969b0dcd35c42be665 | README.md:71-73 | Openverify / Project boundary |  |
| SU.c84b6ff96bc3ac0f7036 | README.md:75-79 | Openverify / Project boundary |  |
| SU.c186ae040fcb505f5c5f | README.md:131-133 | Openverify / The complete mental model |  |
| SU.3dea7c82d581909571d9 | README.md:135-139 | Openverify / The complete mental model |  |
| SU.7fc61eadd3a56365afef | README.md:141-144 | Openverify / The complete mental model |  |
| SU.34d2286e8b82fea71273 | README.md:146-151 | Openverify / The complete mental model |  |
| SU.48725243fad0578fbe2a | README.md:153-156 | Openverify / The complete mental model |  |
| SU.cee6c44c7914ba6eeae2 | README.md:158-161 | Openverify / The complete mental model |  |
| SU.993bce53c377feb27a2f | README.md:163-168 | Openverify / The complete mental model |  |
| SU.865ec881f7652faae985 | README.md:170-174 | Openverify / The complete mental model |  |
| SU.1909e3eb2a12cb5ed108 | README.md:176-183 | Openverify / The complete mental model |  |
| SU.98f9ec41dd9a73649cda | README.md:185-193 | Openverify / The complete mental model |  |
| SU.d8ef06d1ff11cc77c1d4 | README.md:197-197 | Openverify / Logical exhaustiveness within the boundary |  |
| SU.1bab4e4065848b052d07 | README.md:199-210 | Openverify / Logical exhaustiveness within the boundary |  |
| SU.8d3fc037c7afcd1d74b2 | README.md:212-216 | Openverify / Logical exhaustiveness within the boundary |  |
| SU.86c38a46ff96386c6618 | README.md:218-219 | Openverify / Logical exhaustiveness within the boundary |  |
| SU.64fced03d9d1c9960263 | README.md:230-231 | Openverify / Logical exhaustiveness within the boundary |  |
| SU.e09922db0357e303b663 | README.md:243-252 | Openverify / Protocol, SDK, and reference engine |  |
| SU.3b70b6f48f7d66611a24 | README.md:264-267 | Openverify / Protocol, SDK, and reference engine |  |
| SU.9cbeb38604fa3a61141b | README.md:269-272 | Openverify / Protocol, SDK, and reference engine |  |
| SU.8d99fb551b800391079b | README.md:274-276 | Openverify / Protocol, SDK, and reference engine |  |
| SU.19c2a9194196b1b891a1 | README.md:278-282 | Openverify / Protocol, SDK, and reference engine |  |
| SU.ca7cbe67ea102ab7f99e | README.md:286-291 | Openverify / What is implemented today |  |
| SU.4348c2c81c960586fec1 | README.md:293-298 | Openverify / What is implemented today |  |
| SU.ceb8eb873f84833f56b5 | README.md:300-304 | Openverify / What is implemented today |  |
| SU.d31c3290209875e00f74 | README.md:306-318 | Openverify / What is implemented today |  |
| SU.b0451edbd7baaeaac3de | README.md:320-324 | Openverify / What is implemented today |  |
| SU.e185b58345384555ae26 | README.md:326-329 | Openverify / What is implemented today |  |
| SU.27923bc8a259eb6c6267 | README.md:331-336 | Openverify / What is implemented today |  |
| SU.2e341df99b469e04751c | README.md:340-340 | Openverify / Quickstart |  |
| SU.d3d310863d239cab13e9 | README.md:349-351 | Openverify / Quickstart |  |
| SU.2cfe946d61b204f3466f | README.md:373-377 | Openverify / Quickstart |  |
| SU.eac4d6f41467fb17445f | README.md:381-381 | Openverify / Development |  |
| SU.e786f2bd158dce023b51 | README.md:391-394 | Openverify / Development |  |
| SU.85a65ad31d1481e23a41 | README.md:407-413 | Openverify / Development |  |
| SU.ea1878cad116ab1dba8d | README.md:418-435 | Openverify / Breaking DRAFT dataflow revision |  |
| SU.471ac8b64a9644fa37d1 | spec/draft/aggregation.md:5-8 | Aggregation / NORMATIVE SEMANTICS |  |
| SU.bc4b0afd8bf9c7ca71a0 | spec/draft/aggregation.md:10-18 | Aggregation / NORMATIVE SEMANTICS |  |
| SU.5b5e53a461d3887485f3 | spec/draft/aggregation.md:20-38 | Aggregation / NORMATIVE SEMANTICS | SP.96d431c6a32d9d589530,SP.74bb75c5f676efa91446 |
| SU.e885ed64c1275c9fec20 | spec/draft/boundary.md:5-10 | Verification boundary / NORMATIVE SEMANTICS |  |
| SU.64d014a3edf92e7549d9 | spec/draft/boundary.md:12-20 | Verification boundary / NORMATIVE SEMANTICS |  |
| SU.0d9f7290c99502403fc7 | spec/draft/composition.md:5-9 | Composition / NORMATIVE SEMANTICS | SP.d9458f3a7f5fafd1578e |
| SU.a874c9a895151f469872 | spec/draft/composition.md:11-13 | Composition / NORMATIVE SEMANTICS |  |
| SU.37e4e4b4000a7711699f | spec/draft/composition.md:15-22 | Composition / NORMATIVE SEMANTICS |  |
| SU.29cfc82bf0f61d91cfe1 | spec/draft/composition.md:24-24 | Composition / NORMATIVE SEMANTICS |  |
| SU.399dd19186bd6de85483 | spec/draft/computation.md:5-9 | Computation / NORMATIVE SEMANTICS |  |
| SU.6df4c08cfb0b81387d71 | spec/draft/computation.md:11-13 | Computation / NORMATIVE SEMANTICS | SP.b569ae1a8db31113beb7 |
| SU.fb8341bfde6f2baf716b | spec/draft/conceptual-audit.md:5-7 | Conceptual exhaustiveness audit / NORMATIVE SEMANTICS |  |
| SU.2e4390cb7939c6c846eb | spec/draft/conformance.md:5-8 | Conformance / NORMATIVE SEMANTICS |  |
| SU.a7bb4b08354598e497f9 | spec/draft/conformance.md:10-14 | Conformance / NORMATIVE SEMANTICS |  |
| SU.488d01ef720faf4d9ed7 | spec/draft/conformance.md:16-33 | Conformance / NORMATIVE SEMANTICS |  |
| SU.74caff23d30b3eb1867f | spec/draft/dataflow.md:5-5 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.fa8d081363f3af0565a7 | spec/draft/dataflow.md:20-25 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.7a723c5abc7ce5f398c0 | spec/draft/dataflow.md:27-33 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.937c9ecf9503322b0e9f | spec/draft/dataflow.md:35-35 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.90caa7c70744bd7f8f10 | spec/draft/dataflow.md:37-40 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.3de8868a3e0a5e18f5e4 | spec/draft/dataflow.md:42-47 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.19c06e693916199c5386 | spec/draft/dataflow.md:49-55 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.2167dd7fcd91f2b761fd | spec/draft/dataflow.md:57-72 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.d97bcbcebc7ccd47f3d0 | spec/draft/dataflow.md:74-85 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS | SP.d817c0a5f4ea8a924ffb |
| SU.5ae58e5750262d66ac6b | spec/draft/dataflow.md:87-94 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS | SP.05e3c9dc48999f5b8822 |
| SU.ad1069f659f9a0a9b259 | spec/draft/dataflow.md:96-105 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.71afd00d8e2c1179fbc8 | spec/draft/dataflow.md:107-118 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS | SP.4ffc08ee499e8d500bbe,SP.491aafff2c4a1beb40e9 |
| SU.a9f648f55f1ea64177e8 | spec/draft/dataflow.md:120-125 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.dc5359d439475c8c298b | spec/draft/dataflow.md:127-140 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS | SP.fe0e370b338d56568f34 |
| SU.9dce1cf5495278da6e23 | spec/draft/dataflow.md:142-147 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.5e3d216171d558fb79c0 | spec/draft/dataflow.md:149-153 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.b2a1ea6611457e79ceb9 | spec/draft/dataflow.md:155-169 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.03b6165483abf7a0f775 | spec/draft/dataflow.md:171-182 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.96ef13b4209bb4b7b2cf | spec/draft/dataflow.md:184-188 | Typed executable dataflow (breaking DRAFT revision) / NORMATIVE SEMANTICS |  |
| SU.283bb849261616241764 | spec/draft/dataflow.md:192-195 | Typed executable dataflow (breaking DRAFT revision) / Breaking changes |  |
| SU.7ff28621808b03e707d9 | spec/draft/execution-policy.md:5-7 | Execution policy / NORMATIVE SEMANTICS |  |
| SU.6049b03d8c71571eea34 | spec/draft/execution-policy.md:9-17 | Execution policy / NORMATIVE SEMANTICS |  |
| SU.6d6dbd7c9b71446440a2 | spec/draft/execution-policy.md:19-21 | Execution policy / NORMATIVE SEMANTICS |  |
| SU.e9eb6988f805bbd75b1e | spec/draft/execution-policy.md:23-26 | Execution policy / NORMATIVE SEMANTICS |  |
| SU.f8b0502ecdfdc695e323 | spec/draft/execution-policy.md:28-34 | Execution policy / NORMATIVE SEMANTICS |  |
| SU.7eb62dc5b90610add965 | spec/draft/execution-policy.md:36-43 | Execution policy / NORMATIVE SEMANTICS |  |
| SU.7f331c69415add47ed73 | spec/draft/execution-policy.md:45-51 | Execution policy / NORMATIVE SEMANTICS |  |
| SU.870549bafdd74e493155 | spec/draft/execution-policy.md:55-58 | Execution policy / Exact occurrence boundary | SP.5151b7cd5bea500e7167 |
| SU.9d4066bed4532c529079 | spec/draft/execution-policy.md:60-65 | Execution policy / Exact occurrence boundary |  |
| SU.df44bb6d836b1a6eba3a | spec/draft/execution-policy.md:67-71 | Execution policy / Exact occurrence boundary |  |
| SU.482fdbb62e954864bc4e | spec/draft/extensions.md:5-13 | Extensions / NORMATIVE SEMANTICS | SP.e99599a609a53058b1f2 |
| SU.bfdb4d50c2d72781f0da | spec/draft/knowledge.md:5-9 | Knowledge / NORMATIVE SEMANTICS |  |
| SU.758e0e06d77b598307aa | spec/draft/knowledge.md:11-14 | Knowledge / NORMATIVE SEMANTICS | SP.6a8b83afb104a2abf14b |
| SU.e35226fb0bd5f322523c | spec/draft/knowledge.md:16-17 | Knowledge / NORMATIVE SEMANTICS |  |
| SU.a49434f08df708a4aaef | spec/draft/lifecycle.md:5-7 | Occurrence and node lifecycle / NORMATIVE SEMANTICS |  |
| SU.a60d2ac3cd313c9de355 | spec/draft/lifecycle.md:9-13 | Occurrence and node lifecycle / NORMATIVE SEMANTICS |  |
| SU.5b191be126a2ddc4f7bd | spec/draft/lifecycle.md:15-24 | Occurrence and node lifecycle / NORMATIVE SEMANTICS |  |
| SU.1a4b346cf3c6a6d6dc79 | spec/draft/lifecycle.md:26-27 | Occurrence and node lifecycle / NORMATIVE SEMANTICS |  |
| SU.2768242729aff1345c73 | spec/draft/lifecycle.md:29-39 | Occurrence and node lifecycle / NORMATIVE SEMANTICS |  |
| SU.913321d4a8f1db2548b4 | spec/draft/lifecycle.md:41-44 | Occurrence and node lifecycle / NORMATIVE SEMANTICS |  |
| SU.058e74237491e8a6fb03 | spec/draft/lifecycle.md:46-52 | Occurrence and node lifecycle / NORMATIVE SEMANTICS | SP.6b2f2d8cff67a1a5dddd,SP.74022253cf5672051ae9 |
| SU.3d54c03182e2d7e3b2b0 | spec/draft/lifecycle.md:54-57 | Occurrence and node lifecycle / NORMATIVE SEMANTICS | SP.2e90de3d0956479a4923 |
| SU.17e8f1da7940e34d0c1f | spec/draft/lifecycle.md:61-67 | Occurrence and node lifecycle / Cancellation |  |
| SU.959e069e3a8a3699772c | spec/draft/lifecycle.md:69-74 | Occurrence and node lifecycle / Cancellation |  |
| SU.e4f973868d638a41a402 | spec/draft/meaning.md:5-7 | Meaning / NORMATIVE SEMANTICS |  |
| SU.cc7304f89c8e1b28b222 | spec/draft/meaning.md:9-14 | Meaning / NORMATIVE SEMANTICS |  |
| SU.2bce4fac048140305383 | spec/draft/meaning.md:16-19 | Meaning / NORMATIVE SEMANTICS |  |
| SU.fe4d1eb3d17da35db02c | spec/draft/provenance.md:5-9 | Provenance and history / NORMATIVE SEMANTICS |  |
| SU.461c2928fa4cc9a55a76 | spec/draft/provenance.md:11-20 | Provenance and history / NORMATIVE SEMANTICS | SP.96840f81b1fad21e042a |
| SU.3eb00843e031d842eaab | spec/draft/provenance.md:22-27 | Provenance and history / NORMATIVE SEMANTICS |  |
| SU.d6ecef0ea297673cf5cb | spec/draft/provenance.md:29-32 | Provenance and history / NORMATIVE SEMANTICS | SP.267ca5edf4ea9d41ae8c |
| SU.40fe8ea1d32d4b8d1f08 | spec/draft/provider-binding.md:5-10 | Concrete provider binding (DRAFT) / NORMATIVE SEMANTICS |  |
| SU.647f2f457609bd9b7dd4 | spec/draft/provider-binding.md:12-18 | Concrete provider binding (DRAFT) / NORMATIVE SEMANTICS |  |
| SU.30dda233b794292da249 | spec/draft/provider-binding.md:20-28 | Concrete provider binding (DRAFT) / NORMATIVE SEMANTICS |  |
| SU.3308975fa657100606de | spec/draft/provider-binding.md:30-39 | Concrete provider binding (DRAFT) / NORMATIVE SEMANTICS |  |
| SU.033d1bcae04e194e3218 | spec/draft/provider-binding.md:41-49 | Concrete provider binding (DRAFT) / NORMATIVE SEMANTICS |  |
| SU.23e660963524e34073de | spec/draft/provider-binding.md:51-57 | Concrete provider binding (DRAFT) / NORMATIVE SEMANTICS |  |
| SU.abace4e49716a137d569 | spec/draft/provider-binding.md:61-69 | Concrete provider binding (DRAFT) / REFERENCE ENGINE SUPPORT |  |
| SU.c728ecc906b9fa40646d | spec/draft/provider-binding.md:71-76 | Concrete provider binding (DRAFT) / REFERENCE ENGINE SUPPORT |  |
| SU.21a2475d08312f3d7879 | spec/draft/README.md:3-5 | Draft specification |  |
| SU.0adcb7ed46ce11122009 | spec/draft/README.md:9-12 | Draft specification / NORMATIVE SEMANTICS |  |
| SU.ebf7dc7546b8889292e6 | spec/draft/README.md:14-18 | Draft specification / NORMATIVE SEMANTICS |  |
| SU.ad1de0c9f4d045469168 | spec/draft/README.md:20-26 | Draft specification / NORMATIVE SEMANTICS |  |
| SU.71118c3b9b69a643f9ce | spec/draft/resources.md:5-12 | Resources / NORMATIVE SEMANTICS |  |
| SU.9b8c205e7a0dfbd417ae | spec/draft/resources.md:14-18 | Resources / NORMATIVE SEMANTICS |  |
| SU.e919e48fb4a4ee4fe9a1 | spec/draft/resources.md:20-22 | Resources / NORMATIVE SEMANTICS |  |
| SU.6c5b0651e05f6b1fe62e | spec/draft/result.md:5-16 | Result and Decision / NORMATIVE SEMANTICS |  |
| SU.fba3bf6d3f022789fa79 | spec/draft/result.md:18-22 | Result and Decision / NORMATIVE SEMANTICS |  |
| SU.f61e29073f5402fbf989 | spec/draft/result.md:24-28 | Result and Decision / NORMATIVE SEMANTICS |  |
| SU.7fafb5230521dd6149ce | spec/draft/result.md:30-33 | Result and Decision / NORMATIVE SEMANTICS |  |
| SU.570b04a09a43882783b2 | spec/draft/wire-format.md:5-14 | JSON wire format / NORMATIVE SEMANTICS |  |
| SU.34f8c94378e713b73cd5 | spec/draft/wire-format.md:16-20 | JSON wire format / NORMATIVE SEMANTICS |  |


### Declaration discovery and closure

The discovery deliberately includes non-underscore names from internal modules as candidates. It has not proved that each is a supported public API. Class/model declarations and aliases are not behaviors by themselves. Every candidate below still needs a publicness/authority disposition and complete operation-level semantics; direct symbol links are useful evidence only.

| Declaration position ID | Source/symbol | Directly linked contract IDs |
| --- | --- | --- |
| SD.e0e9152ca94167491b50 | src/openverify/adapters/__init__.py:8-11 Adapter |  |
| SD.d0bd5ad0892ea884b7a6 | src/openverify/adapters/__init__.py:9-11 Adapter.execute |  |
| SD.831334e517fde313ad1b | src/openverify/adapters/__init__.py:14-28 Registry |  |
| SD.8c0f1e48c39f345c0de9 | src/openverify/adapters/__init__.py:18-19 Registry.register |  |
| SD.756a1fec0c2c21cd639e | src/openverify/adapters/__init__.py:21-22 Registry.register_derive |  |
| SD.f762d1b0e6afd4d26f1c | src/openverify/adapters/__init__.py:24-25 Registry.register_evaluate |  |
| SD.3e4ae9bb8e4c61cb0bfd | src/openverify/adapters/__init__.py:27-28 Registry.register_control |  |
| SD.e86720ceb009c9396420 | src/openverify/adapters/demo.py:12-23 known |  |
| SD.47b2668cc4e3a5958a0b | src/openverify/adapters/demo.py:26-30 ConstantEvaluator |  |
| SD.d4c57e35b371e472bb5b | src/openverify/adapters/demo.py:29-30 ConstantEvaluator.execute |  |
| SD.22c11fe30e705078226c | src/openverify/adapters/demo.py:33-52 RegexEvaluator |  |
| SD.70d2df640bf20221b52b | src/openverify/adapters/demo.py:36-52 RegexEvaluator.execute |  |
| SD.8828555ce95284238087 | src/openverify/adapters/demo.py:55-67 RangeEvaluator |  |
| SD.129b79d9aba86807371e | src/openverify/adapters/demo.py:58-67 RangeEvaluator.execute |  |
| SD.ab03ddde43d4c144fae0 | src/openverify/adapters/demo.py:70-77 LengthDeriver |  |
| SD.85e0503d99d607bc3943 | src/openverify/adapters/demo.py:73-77 LengthDeriver.execute |  |
| SD.06f39ff6cf4615575706 | src/openverify/adapters/demo.py:80-92 UnknownRouter |  |
| SD.54f9eda4b83bb57f7669 | src/openverify/adapters/demo.py:83-92 UnknownRouter.execute |  |
| SD.7274f8121de2df6e2ad5 | src/openverify/adapters/demo.py:95-102 demo_registry |  |
| SD.8b940ef825877c036658 | src/openverify/authoring/graph.py:41-54 NodeRef |  |
| SD.74aad65d73b406cf5349 | src/openverify/authoring/graph.py:49-50 NodeRef.result |  |
| SD.cc91cb54134a42974c34 | src/openverify/authoring/graph.py:53-54 NodeRef.decision |  |
| SD.89da51b8c1ffe41b797f | src/openverify/authoring/graph.py:57-66 NodeOptions |  |
| SD.6884bf779fd2b754183b | src/openverify/authoring/graph.py:69-262 Graph |  |
| SD.c085e6c96d5927ac2b27 | src/openverify/authoring/graph.py:94-111 Graph.input | CM.SDK.AUTHORING.GRAPH.INPUT |
| SD.5fddbdbec84e25dc8909 | src/openverify/authoring/graph.py:113-181 Graph.node | CM.SDK.AUTHORING.GRAPH.NODE |
| SD.bae0dde4e4038073bdb2 | src/openverify/authoring/graph.py:183-184 Graph.derive |  |
| SD.df6fac7da434149ca8af | src/openverify/authoring/graph.py:186-187 Graph.evaluate |  |
| SD.b2fcc22ae5502a978b94 | src/openverify/authoring/graph.py:189-190 Graph.control |  |
| SD.a0f4e9aa9a1a1099d0d3 | src/openverify/authoring/graph.py:192-224 Graph.aggregate | CM.SDK.AUTHORING.GRAPH.AGGREGATE |
| SD.b59d4a01a7233213413b | src/openverify/authoring/graph.py:226-230 Graph.edge | CM.SDK.AUTHORING.GRAPH.EDGE |
| SD.f2cb4debd7e47c3dd92f | src/openverify/authoring/graph.py:232-240 Graph.add_node | CM.SDK.AUTHORING.GRAPH.ADD_NODE |
| SD.2d008bf262b99596e32c | src/openverify/authoring/graph.py:242-253 Graph.build | CM.SDK.AUTHORING.GRAPH.BUILD |
| SD.3884a932ca10a0a5590e | src/openverify/authoring/graph.py:255-256 Graph.validate | CM.SDK.AUTHORING.GRAPH.VALIDATE |
| SD.df2b49cda0c1e0091cf6 | src/openverify/authoring/graph.py:258-259 Graph.inspect | CM.SDK.AUTHORING.GRAPH.INSPECT |
| SD.afc0aa302bcf4ed6ba74 | src/openverify/authoring/graph.py:261-262 Graph.to_json | CM.SDK.AUTHORING.GRAPH.TO_JSON |
| SD.c4ab5e1101a046d9dab3 | src/openverify/authoring/references.py:11-13 Ref |  |
| SD.04ae924a18ca3e15b448 | src/openverify/authoring/references.py:16-17 constant | CM.SDK.REFERENCE.CONSTANT |
| SD.2696b4676539b08abfd4 | src/openverify/authoring/references.py:20-21 external | CM.SDK.REFERENCE.EXTERNAL |
| SD.ac85a51e7b63c0e6922f | src/openverify/cli.py:17-58 main |  |
| SD.6a2532bf575310631f2a | src/openverify/conformance/__init__.py:10-21 check_manifest |  |
| SD.a92d089f1a71dd07f6be | src/openverify/dataflow.py:32-33 fail |  |
| SD.532361dea5f0d1f4c178 | src/openverify/dataflow.py:36-45 validate_port |  |
| SD.5d6300dd9132635856ca | src/openverify/dataflow.py:48-52 unique_ports |  |
| SD.62a96f4619e9e9d66aae | src/openverify/dataflow.py:55-61 ancestors |  |
| SD.9d4d1a0d6db2ebb53ac1 | src/openverify/dataflow.py:64-83 pointer |  |
| SD.a510de140a7758497e25 | src/openverify/dataflow.py:86-110 source_schema |  |
| SD.d20da2891469283f8d3a | src/openverify/dataflow.py:113-133 validate_bindings |  |
| SD.3d25a41c2eac2e5c9902 | src/openverify/dataflow.py:136-268 validate_graph |  |
| SD.72f58d1ddb2f385e7b24 | src/openverify/dataflow.py:271-281 json_type |  |
| SD.91d9a6194a256aa2dba8 | src/openverify/dataflow.py:284-319 validate_executable |  |
| SD.bfc59a681c2c1c9619a0 | src/openverify/dataflow.py:322-334 validate_run_inputs |  |
| SD.10d924fdc93ec25b60cb | src/openverify/dataflow.py:337-383 resolve_source |  |
| SD.4616e92d595173c0d732 | src/openverify/dataflow.py:386-415 resolve_inputs |  |
| SD.c5a023928a5f241c4c4d | src/openverify/dataflow.py:418-434 guards_enabled |  |
| SD.073b595afcf9598b386b | src/openverify/dataflow.py:437-476 accept_outputs |  |
| SD.2dcc38d8c7becf5ab3c2 | src/openverify/dataflow.py:479-485 error_result |  |
| SD.044a3c47d5029a6f5c62 | src/openverify/engine/__init__.py:44-45 now |  |
| SD.bb2c9893809059d1a9ad | src/openverify/engine/__init__.py:48-56 observation |  |
| SD.9d405c2c606171256d9f | src/openverify/engine/__init__.py:59-295 Engine |  |
| SD.973752d8cfb096ba475b | src/openverify/engine/__init__.py:66-84 Engine.run |  |
| SD.2dec94a15953659075a7 | src/openverify/engine/__init__.py:86-295 Engine.attempt |  |
| SD.655e48371a062ff57510 | src/openverify/engine/admission.py:12-30 admit |  |
| SD.a9540ead4441cf65e547 | src/openverify/engine/aggregation.py:13-98 aggregate |  |
| SD.d51ba2ea910927f894d7 | src/openverify/engine/binding.py:20-62 BoundProvider |  |
| SD.fe66bfeb276592f5da2d | src/openverify/engine/binding.py:25-26 BoundProvider.snapshot |  |
| SD.533cd6da9cfcd2bfc01c | src/openverify/engine/binding.py:28-62 BoundProvider.prepare |  |
| SD.c350ffd73bd24a5f1fb6 | src/openverify/engine/binding.py:65-69 check_payload |  |
| SD.a4eabd1e4c98f9550fd6 | src/openverify/engine/policy.py:24-34 builtin |  |
| SD.bf63f8fc24b0ab87482a | src/openverify/engine/policy.py:37-80 evaluate |  |
| SD.39fd9aa04b7cde0dfe56 | src/openverify/error_codes.py:6-41 VcpErrorCode |  |
| SD.481cd3b8d1e693270962 | src/openverify/errors.py:9-32 ProtocolError |  |
| SD.153153cdb0d2168d23f0 | src/openverify/errors.py:26-32 ProtocolError.as_dict | CM.SDK.ERROR.ASDICT |
| SD.d8adad0b7f03da9261a7 | src/openverify/fingerprint/__init__.py:9-11 fingerprint | CM.SDK.FINGERPRINT |
| SD.2af7aed264c8d1c9407c | src/openverify/inspection.py:13-53 inspect_definition | CM.SDK.INSPECT |
| SD.1b0ed9fb34954bb7140c | src/openverify/inspection.py:56-68 flattened_status | CM.SDK.FLATTEN |
| SD.a5dbb09087733159062c | src/openverify/json_schema.py:56-116 check_schema |  |
| SD.cee62b6cb23b6ca4b219 | src/openverify/json_schema.py:119-120 Validator |  |
| SD.b325e566f5f94a17fddb | src/openverify/json_schema.py:120-120 Validator.validate |  |
| SD.f072215417edec495967 | src/openverify/json_schema.py:123-127 validate_value |  |
| SD.2dce8639effb767c6cc1 | src/openverify/json_schema.py:130-156 obvious_incompatible |  |
| SD.a41d3c6ad6861b58cf9c | src/openverify/lifecycle.py:13-15 nonexecution |  |
| SD.09901fb47bf59e535495 | src/openverify/lifecycle.py:18-24 reachable |  |
| SD.5b5582841ddcd29f80d5 | src/openverify/lifecycle.py:28-71 Lifecycle |  |
| SD.51cc07a62126964949df | src/openverify/lifecycle.py:34-56 Lifecycle.cause |  |
| SD.667937075aa58baa359e | src/openverify/lifecycle.py:58-71 Lifecycle.control |  |
| SD.2e9043ede00e4ef6a0ed | src/openverify/lifecycle.py:74-84 Cancellation |  |
| SD.57d7289f5eb89ef36e9b | src/openverify/lifecycle.py:80-84 Cancellation.cancel |  |
| SD.04227557b3d66a24c251 | src/openverify/model/__init__.py:8-9 Value |  |
| SD.885bf69a2c042c2c7fa3 | src/openverify/model/__init__.py:12-16 Extension |  |
| SD.f2baef5d2ac0f60a0680 | src/openverify/model/__init__.py:19-21 AnnotatedValue |  |
| SD.d375a555bc8b0405de41 | src/openverify/model/__init__.py:24-28 ArtifactRef |  |
| SD.c29eb3f7edc1433ed885 | src/openverify/model/__init__.py:31-36 Evidence |  |
| SD.e015faa842f38440002d | src/openverify/model/__init__.py:39-44 Measurement |  |
| SD.58d6f20ac24d6103f48a | src/openverify/model/__init__.py:51-54 ResourceDimension |  |
| SD.c8cdb5e0f8e08ae02ad9 | src/openverify/model/__init__.py:57-59 Severity |  |
| SD.67ed15e4ca7c8c685e36 | src/openverify/model/__init__.py:62-72 SeverityLevel |  |
| SD.a750ae4d567b02007f15 | src/openverify/model/__init__.py:68-72 SeverityLevel.integral_rank |  |
| SD.d70f9ca0d41da884d7a3 | src/openverify/model/__init__.py:75-77 SeverityDomain |  |
| SD.468b312340793a0c7a60 | src/openverify/model/__init__.py:80-92 Result |  |
| SD.3786989560162de33d45 | src/openverify/model/__init__.py:95-99 Decision |  |
| SD.be70fb7ad51582fbdc5c | src/openverify/model/__init__.py:105-107 Constant |  |
| SD.2166106dd92fa478225c | src/openverify/model/__init__.py:110-112 RunInput |  |
| SD.d9ed57c4ae0cc33e45d4 | src/openverify/model/__init__.py:115-117 ExternalReference |  |
| SD.c2d36c5cce3e0015d54b | src/openverify/model/__init__.py:120-123 UpstreamOutput |  |
| SD.1ba70ddfb245376e343f | src/openverify/model/__init__.py:131-136 InputPort |  |
| SD.6b08f996f718f0c9caec | src/openverify/model/__init__.py:139-142 OutputPort |  |
| SD.967dcd97a808c77e60db | src/openverify/model/__init__.py:145-147 OperationRequirement |  |
| SD.de0768e91fb62aa6d650 | src/openverify/model/__init__.py:150-153 Guard |  |
| SD.e0b4e3b4bd507a2b9caf | src/openverify/model/__init__.py:156-159 Edge |  |
| SD.e0c7d5b49d443478896b | src/openverify/model/__init__.py:162-172 Node |  |
| SD.6afa944a07950b0279d7 | src/openverify/model/__init__.py:175-180 Graph |  |
| SD.fd7dacfee8b601bba7b1 | src/openverify/model/__init__.py:183-185 Criterion |  |
| SD.67dcd347df266923631d | src/openverify/model/__init__.py:188-193 PolicyOperation |  |
| SD.0f5ede44c3d6871ff5c1 | src/openverify/model/__init__.py:196-197 Capability |  |
| SD.d347c0ef031fb63718cd | src/openverify/model/__init__.py:200-202 AdmissionPolicy |  |
| SD.b6fcd3c97150f20e785b | src/openverify/model/__init__.py:205-208 ExecutionPolicy |  |
| SD.7379c0aab383910b766d | src/openverify/model/__init__.py:211-221 VerificationDefinition |  |
| SD.81a3674966bdeed09fab | src/openverify/model/__init__.py:224-226 Admission |  |
| SD.e6181220f2bbcaa620a6 | src/openverify/model/__init__.py:229-231 Activation |  |
| SD.ef9be144e7f46330185f | src/openverify/model/__init__.py:234-236 Selection |  |
| SD.e2f4ba889952241750ba | src/openverify/model/__init__.py:239-241 ExecutionError |  |
| SD.ea6b7f93059f39634997 | src/openverify/model/__init__.py:244-248 ExecutionObservation |  |
| SD.c1984724f4bb95e766a7 | src/openverify/model/__init__.py:251-262 InputResolution |  |
| SD.150b7dc9dff7b7dcc072 | src/openverify/model/__init__.py:265-271 PolicyEvaluation |  |
| SD.b2b9f0d578211203d025 | src/openverify/model/__init__.py:274-277 CancellationEvent |  |
| SD.fc6d6a5efcd3fd78cb59 | src/openverify/model/__init__.py:280-286 ProviderBinding |  |
| SD.3171e07940353f708b58 | src/openverify/model/__init__.py:289-309 NodeRecord |  |
| SD.73e78ab4213c5dd65c44 | src/openverify/model/__init__.py:312-328 RunRecord |  |
| SD.87205fee94f31c44e6cd | src/openverify/model/__init__.py:331-340 Profile |  |
| SD.8b172c307c8128b5e22b | src/openverify/policy.py:21-23 policies |  |
| SD.f07dd164c88cb384832f | src/openverify/policy.py:26-36 check_outcome |  |
| SD.7a5f989fc9171e27e6fd | src/openverify/policy.py:39-84 check_evaluations |  |
| SD.8a632e5e14c3935bddf4 | src/openverify/provenance/__init__.py:11-12 RunStore |  |
| SD.714d17121020e2b6158b | src/openverify/provenance/__init__.py:12-12 RunStore.append |  |
| SD.33101fb8faf7790e3078 | src/openverify/provenance/__init__.py:15-24 MemoryStore |  |
| SD.79fdca3a18c38fe201af | src/openverify/provenance/__init__.py:19-21 MemoryStore.append |  |
| SD.fe1224114ee9cdfb289b | src/openverify/provenance/__init__.py:23-24 MemoryStore.records |  |
| SD.5a4c6c59c8382dd5f879 | src/openverify/provenance/__init__.py:27-41 JsonlStore |  |
| SD.254caae8f3281eb9365c | src/openverify/provenance/__init__.py:31-34 JsonlStore.append |  |
| SD.3a297b86acdd23301d12 | src/openverify/provenance/__init__.py:36-41 JsonlStore.records |  |
| SD.257f2637893f2ead41db | src/openverify/provider/__init__.py:37-49 Provider |  |
| SD.febf58b78054b7388d9c | src/openverify/provider/__init__.py:45-45 Provider.manifest |  |
| SD.61019c1aea0bc1e96dcd | src/openverify/provider/__init__.py:47-47 Provider.invoke |  |
| SD.9ecf8331aac472658a70 | src/openverify/provider/__init__.py:49-49 Provider.cancel |  |
| SD.0d421d29fc36f7cbdef2 | src/openverify/provider/conformance.py:14-50 check_case |  |
| SD.31a71d19c9c83dd53d16 | src/openverify/provider/conformance.py:53-67 check_manifest |  |
| SD.032cb19937580b3517df | src/openverify/provider/lifecycle.py:25-30 negotiate_contract_version |  |
| SD.2c65ae9996d76c75d023 | src/openverify/provider/lifecycle.py:43-190 LifecycleValidator |  |
| SD.c470e76a6e6a4d808d76 | src/openverify/provider/lifecycle.py:51-60 LifecycleValidator.initialize |  |
| SD.7cd106892606568c9df8 | src/openverify/provider/lifecycle.py:62-98 LifecycleValidator.accept |  |
| SD.f79035400cf936cf8d41 | src/openverify/provider/lifecycle.py:110-133 LifecycleValidator.event |  |
| SD.14b4ad559a7b0fbaf14d | src/openverify/provider/lifecycle.py:135-142 LifecycleValidator.cancel |  |
| SD.aaedc557457725557376 | src/openverify/provider/lifecycle.py:150-179 LifecycleValidator.outcome |  |
| SD.8f54fc37229aca1b2685 | src/openverify/provider/lifecycle.py:181-186 LifecycleValidator.reject |  |
| SD.b8aa0b399cf758777924 | src/openverify/provider/lifecycle.py:188-190 LifecycleValidator.finish |  |
| SD.177de1aa1a7423986e74 | src/openverify/provider/lifecycle.py:193-229 validate_lifecycle |  |
| SD.3dbe45fefe4eba4a53b3 | src/openverify/provider/model.py:10-11 ProviderValue |  |
| SD.b5d98e8672dc2467b474 | src/openverify/provider/model.py:14-15 Extensible |  |
| SD.11234a793e09aea0e330 | src/openverify/provider/model.py:18-22 LifecycleFeatures |  |
| SD.ff056e13758b1c49e2f0 | src/openverify/provider/model.py:25-32 Capability |  |
| SD.874b25e8a9b371c770d7 | src/openverify/provider/model.py:35-40 ProviderManifest |  |
| SD.da67ee43b648e315a276 | src/openverify/provider/model.py:43-53 Invocation |  |
| SD.5f99a4190cde270f6aaf | src/openverify/provider/model.py:56-68 ProviderEvent |  |
| SD.c9756b9e5d7cfc46c84a | src/openverify/provider/model.py:65-68 ProviderEvent.integral_sequence |  |
| SD.b248c1b3afbe40f436ed | src/openverify/provider/model.py:71-73 CancelRequest |  |
| SD.d4d291be6e8e50f6db45 | src/openverify/provider/model.py:76-89 ProviderError |  |
| SD.77ecae41e6f10cf0f528 | src/openverify/provider/model.py:83-89 ProviderError.typed_reserved_code |  |
| SD.ae936b999e6c8656c8bf | src/openverify/provider/model.py:92-97 Outcome |  |
| SD.8b53c92b7e05e8b294b0 | src/openverify/provider/model.py:100-102 InitializeRequest |  |
| SD.404c9fe0cb666e8da201 | src/openverify/provider/model.py:105-107 InitializeResult |  |
| SD.1b21a5653a71c3c2230b | src/openverify/provider/stdio.py:24-34 encode_frame |  |
| SD.6354e9afb999f7b51650 | src/openverify/provider/stdio.py:37-99 FrameDecoder |  |
| SD.e947ccd980c2f0660f2e | src/openverify/provider/stdio.py:53-95 FrameDecoder.feed |  |
| SD.03fdd6bbe2b7b62a1cf4 | src/openverify/provider/stdio.py:97-99 FrameDecoder.finish |  |
| SD.ff4669bfee6f54867944 | src/openverify/provider/stdio.py:109-250 StdioSessionValidator |  |
| SD.6bbed317df2b0ced973f | src/openverify/provider/stdio.py:125-165 StdioSessionValidator.runner_message |  |
| SD.3c9c2057a4da5c5f5daa | src/openverify/provider/stdio.py:167-242 StdioSessionValidator.provider_message |  |
| SD.cb52a74a36b9ecfd9e93 | src/openverify/provider/stdio.py:244-250 StdioSessionValidator.finish |  |
| SD.090834a3379c0ccb44a5 | src/openverify/provider/validation.py:52-64 ProviderContractError |  |
| SD.f4a2cfa1f598415e589a | src/openverify/provider/validation.py:63-64 ProviderContractError.as_dict | CM.SDK.PROVIDER.ERROR.ASDICT |
| SD.35473cad4a7e20cb50d8 | src/openverify/provider/validation.py:67-68 fail |  |
| SD.7cdefa25e13af2a5d7aa | src/openverify/provider/validation.py:71-73 wire_data | CM.SDK.PROVIDER.WIRE_DATA |
| SD.d6b7ba34870befd27b4a | src/openverify/provider/validation.py:76-77 serialize | CM.SDK.PROVIDER.SERIALIZE |
| SD.64ea8bbc0ff949276370 | src/openverify/provider/validation.py:80-90 load_provider_schema | CM.SDK.PROVIDER.SCHEMA.LOAD |
| SD.6eae048dab831da8a97d | src/openverify/provider/validation.py:93-95 Instant |  |
| SD.6068c8bf65fe7249b9d5 | src/openverify/provider/validation.py:98-112 timestamp |  |
| SD.65575852e3491d4310de | src/openverify/provider/validation.py:154-201 parse_provider_object |  |
| SD.c10b79bdaf17d90b6653 | src/openverify/provider/validation.py:322-328 validate_payload |  |
| SD.55908f66ee9c4f47a10c | src/openverify/provider/validation.py:331-332 parse_provider_manifest | CM.SDK.PROVIDER.PARSE_PROVIDER_MANIFEST |
| SD.b68784876b5e152cdbef | src/openverify/provider/validation.py:335-336 parse_invocation | CM.SDK.PROVIDER.PARSE_INVOCATION |
| SD.e074aed1df7b4625f323 | src/openverify/provider/validation.py:339-340 parse_provider_event | CM.SDK.PROVIDER.PARSE_PROVIDER_EVENT |
| SD.ab7d407694b07040672b | src/openverify/provider/validation.py:343-344 parse_outcome | CM.SDK.PROVIDER.PARSE_OUTCOME |
| SD.4de8377b130c97c10c41 | src/openverify/provider/validation.py:347-348 parse_cancel_request | CM.SDK.PROVIDER.PARSE_CANCEL_REQUEST |
| SD.0ae00f265cea19af0261 | src/openverify/provider/validation.py:351-352 validate_provider_manifest | CM.SDK.PROVIDER.VALIDATE_PROVIDER_MANIFEST |
| SD.7f2514fa71078a6f46e9 | src/openverify/provider/validation.py:355-356 validate_invocation | CM.SDK.PROVIDER.VALIDATE_INVOCATION |
| SD.0f4ceb6b1a7ce4d3e02a | src/openverify/provider/validation.py:359-360 validate_provider_event | CM.SDK.PROVIDER.VALIDATE_PROVIDER_EVENT |
| SD.1ea292a3deec77e51cfb | src/openverify/provider/validation.py:363-364 validate_outcome | CM.SDK.PROVIDER.VALIDATE_OUTCOME |
| SD.ae920c2cbd1daaa047f2 | src/openverify/provider_codes.py:6-14 ProviderErrorCode |  |
| SD.06473ead4ed14c5fe58f | src/openverify/relay/adapters/binder.py:11-31 DeterministicBinder |  |
| SD.4d0d8c89e1712a73ad88 | src/openverify/relay/adapters/binder.py:12-31 DeterministicBinder.bind |  |
| SD.a328a75b6a0fd0b5cc36 | src/openverify/relay/adapters/catalog.py:19-80 Catalog |  |
| SD.4b56c9862093ee5f6a03 | src/openverify/relay/adapters/catalog.py:23-43 Catalog.register_transport |  |
| SD.d8b99a6a2d7dd12c52b6 | src/openverify/relay/adapters/catalog.py:45-58 Catalog.register |  |
| SD.1868c9852f713c96a598 | src/openverify/relay/adapters/catalog.py:60-74 Catalog.load_entry_points |  |
| SD.fd98d701c461090816d4 | src/openverify/relay/adapters/catalog.py:76-80 Catalog.providers |  |
| SD.baaad3aa4e84a1445ef0 | src/openverify/relay/adapters/inprocess.py:11-55 InProcessTransport |  |
| SD.14f2becd014a4c4661de | src/openverify/relay/adapters/inprocess.py:16-20 InProcessTransport.invoke |  |
| SD.337a44649edf54b9e6f8 | src/openverify/relay/adapters/jsonl.py:11-28 JsonlStore |  |
| SD.ebbc6922beb21dcef1a7 | src/openverify/relay/adapters/jsonl.py:19-25 JsonlStore.put |  |
| SD.f5a38eca883d1f60c271 | src/openverify/relay/adapters/jsonl.py:27-28 JsonlStore.get |  |
| SD.8c4e5efb9629bec6e890 | src/openverify/relay/adapters/local.py:25-28 InvalidProviderOutput |  |
| SD.4641067b8db111e1aa0a | src/openverify/relay/adapters/local.py:31-36 ObservedTransportFailure |  |
| SD.2286231c70117d613d42 | src/openverify/relay/adapters/local.py:39-110 LocalDriver |  |
| SD.462f0a8b8a297c021624 | src/openverify/relay/adapters/local.py:46-110 LocalDriver.execute |  |
| SD.f5ecdc65f1a81175389c | src/openverify/relay/adapters/logging.py:9-17 LoggingObserver |  |
| SD.62f500e8a8cb4fbb544a | src/openverify/relay/adapters/logging.py:10-17 LoggingObserver.observe |  |
| SD.88db1a52d08804d4cedd | src/openverify/relay/adapters/logging.py:20-25 CallbackObserver |  |
| SD.08cb9ca11a62e6f74856 | src/openverify/relay/adapters/logging.py:24-25 CallbackObserver.observe |  |
| SD.b0f6241d94693a608777 | src/openverify/relay/adapters/memory.py:8-21 MemoryStore |  |
| SD.66a0f45f4d86e9f91cd2 | src/openverify/relay/adapters/memory.py:12-17 MemoryStore.put |  |
| SD.30a93e7dc746de08e35c | src/openverify/relay/adapters/memory.py:19-21 MemoryStore.get |  |
| SD.77759c3c20369afcf45e | src/openverify/relay/adapters/process.py:15-20 Captured |  |
| SD.5858f82e164277c2141a | src/openverify/relay/adapters/process.py:23-55 spawn |  |
| SD.07d8571d4ce58fb10576 | src/openverify/relay/adapters/process.py:58-77 terminate |  |
| SD.7b508f76cc584445145d | src/openverify/relay/adapters/process.py:80-86 read_bounded |  |
| SD.5ebf02183bb227004689 | src/openverify/relay/adapters/process.py:89-123 capture |  |
| SD.e42d8f51a41340edf1d9 | src/openverify/relay/adapters/server.py:25-125 serve_stdio |  |
| SD.42ff3b38089e2e9ca6b4 | src/openverify/relay/adapters/stdio.py:25-154 StdioTransport |  |
| SD.ed1a753f6889c5199c4f | src/openverify/relay/adapters/stdio.py:32-154 StdioTransport.invoke |  |
| SD.cb413b4415cae247e644 | src/openverify/relay/adapters/windows_job.py:15-26 BasicLimits |  |
| SD.f15c83a93cf7f128949d | src/openverify/relay/adapters/windows_job.py:29-40 IoCounters |  |
| SD.27ca5fb3055b7610f2c2 | src/openverify/relay/adapters/windows_job.py:43-51 ExtendedLimits |  |
| SD.8b6525d306f008444ef8 | src/openverify/relay/adapters/windows_job.py:54-77 main |  |
| SD.1425e44969c77c97f380 | src/openverify/relay/api.py:41-67 Run |  |
| SD.7c690b8dba0c55119ee3 | src/openverify/relay/api.py:45-46 Run.results |  |
| SD.4765efb2ae9c71e22e00 | src/openverify/relay/api.py:49-50 Run.decisions |  |
| SD.461e216d0588ccd0eae2 | src/openverify/relay/api.py:53-60 Run.evidence |  |
| SD.0d988db843a85aeed738 | src/openverify/relay/api.py:63-64 Run.usage |  |
| SD.c2f4e9ed858829a35c8f | src/openverify/relay/api.py:66-67 Run.to_json |  |
| SD.5374e00dffb5ff9de86c | src/openverify/relay/api.py:70-79 passing_gate |  |
| SD.312af6203c36b24e35f1 | src/openverify/relay/api.py:85-165 Relay |  |
| SD.2a70eb5a469df3316342 | src/openverify/relay/api.py:116-141 Relay.run |  |
| SD.0a614da31832cabcddaf | src/openverify/relay/api.py:143-150 Relay.run_sync | CM.SDK.RELAY.RUN_SYNC |
| SD.b781839ddf70d494c385 | src/openverify/relay/api.py:152-165 Relay.verify_before | CM.SDK.RELAY.VERIFY_BEFORE |
| SD.b35d9de84ebd3ae4ea39 | src/openverify/relay/application/binding.py:21-28 validate_choice |  |
| SD.9b2808a4377c97029015 | src/openverify/relay/application/binding.py:31-58 bind |  |
| SD.ec3a15ffbda14fb38125 | src/openverify/relay/application/contract.py:8-37 validate_report |  |
| SD.8eb65bd9161adddb9dab | src/openverify/relay/application/execution.py:40-41 now |  |
| SD.af74afa755758162fc45 | src/openverify/relay/application/execution.py:44-65 invocation |  |
| SD.7fb253eb290b405660f7 | src/openverify/relay/application/execution.py:68-98 observation |  |
| SD.614c273fd51606699e3e | src/openverify/relay/application/execution.py:101-194 execute_node |  |
| SD.e5a2524e75e7c40851c3 | src/openverify/relay/application/policies.py:32-123 evaluate_policies |  |
| SD.7036d814af07206831ad | src/openverify/relay/application/preparation.py:15-18 PreparedRun |  |
| SD.f8d088f24c8ff3c70078 | src/openverify/relay/application/preparation.py:21-39 prepare |  |
| SD.f358125f6f7cadb6ee33 | src/openverify/relay/application/run.py:48-71 validate_catalog |  |
| SD.fce6ed68f825507cae53 | src/openverify/relay/application/run.py:74-310 coordinate |  |
| SD.6a9402eea0c42ac80d53 | src/openverify/relay/config.py:10-21 RuntimeConfig |  |
| SD.e4110b6bd5ec3b9c00e6 | src/openverify/relay/core/aggregation.py:14-99 reduce_results |  |
| SD.16e822cbfc000887ef7a | src/openverify/relay/core/readiness.py:6-20 ready_wave |  |
| SD.5e13c5b176c1624a46d1 | src/openverify/relay/core/state.py:12-25 RunState |  |
| SD.1628130fa3e291c40301 | src/openverify/relay/core/state.py:16-25 RunState.transition |  |
| SD.d274c18ad93bbf1ad7d1 | src/openverify/relay/entrypoints/cli.py:25-26 read_json |  |
| SD.0965a46d895fa48a60fb | src/openverify/relay/entrypoints/cli.py:29-66 configured_catalog |  |
| SD.d3bb70c1118eab6bd5ab | src/openverify/relay/entrypoints/cli.py:69-75 load_bindings |  |
| SD.fee18e2c94153639aa97 | src/openverify/relay/entrypoints/cli.py:78-92 exit_code |  |
| SD.e728c60a6d8eb7fc7396 | src/openverify/relay/entrypoints/cli.py:95-204 main |  |
| SD.c3d91872487440cee844 | src/openverify/relay/entrypoints/http.py:13-48 create_app |  |
| SD.1b498caab11602fb2584 | src/openverify/relay/entrypoints/http.py:51-54 serve |  |
| SD.5ec646bc78cbda1c86f7 | src/openverify/relay/entrypoints/mcp.py:9-33 create_server |  |
| SD.64aca9c5c484fea4e605 | src/openverify/relay/entrypoints/mcp.py:36-38 main |  |
| SD.12afc5e2203581b0688a | src/openverify/relay/entrypoints/service.py:16-59 GraphService |  |
| SD.c678d645990f4a6aca0b | src/openverify/relay/entrypoints/service.py:35-38 GraphService.definition | CM.SDK.SERVICE.GRAPHSERVICE.DEFINITION |
| SD.61a75b3503106a5316aa | src/openverify/relay/entrypoints/service.py:40-41 GraphService.list_graphs | CM.SDK.SERVICE.GRAPHSERVICE.LIST_GRAPHS |
| SD.ffa7ccd2b52e73846ce3 | src/openverify/relay/entrypoints/service.py:43-44 GraphService.describe_graph | CM.SDK.SERVICE.GRAPHSERVICE.DESCRIBE_GRAPH |
| SD.c3154d758802a51dea5d | src/openverify/relay/entrypoints/service.py:46-51 GraphService.run_graph | CM.SDK.SERVICE.GRAPHSERVICE.RUN_GRAPH |
| SD.0feff7d5331619e110ca | src/openverify/relay/entrypoints/service.py:53-59 GraphService.inspect_result | CM.SDK.SERVICE.GRAPHSERVICE.INSPECT_RESULT |
| SD.a1f6323d207b9ed39171 | src/openverify/relay/error_codes.py:6-16 RelayErrorCode |  |
| SD.134886f4b948cd644270 | src/openverify/relay/errors.py:9-17 RelayError |  |
| SD.f153a68d3a1765de880a | src/openverify/relay/ports/__init__.py:14-16 InvocationRequest |  |
| SD.1def275ed2c1e8a950a3 | src/openverify/relay/ports/__init__.py:19-20 ProviderTransport |  |
| SD.cd98e442db3547c15bf6 | src/openverify/relay/ports/__init__.py:20-20 ProviderTransport.invoke |  |
| SD.813774de3e35509ad048 | src/openverify/relay/ports/__init__.py:24-26 AvailableProvider |  |
| SD.1608b8f70ed86eeec6cb | src/openverify/relay/ports/__init__.py:30-34 InvocationReport |  |
| SD.7f512f393d4823208c4b | src/openverify/relay/ports/__init__.py:38-43 RelayEvent |  |
| SD.445e6ad7c5f2ba1a5ad3 | src/openverify/relay/ports/__init__.py:46-47 ProviderCatalog |  |
| SD.50197fe556f6ccb0734b | src/openverify/relay/ports/__init__.py:47-47 ProviderCatalog.providers |  |
| SD.c69186ba7adef1868f3f | src/openverify/relay/ports/__init__.py:50-56 ProviderBinder |  |
| SD.4e7966ffa80c2601cda2 | src/openverify/relay/ports/__init__.py:51-56 ProviderBinder.bind |  |
| SD.6b9395032b7ea58b81f4 | src/openverify/relay/ports/__init__.py:59-66 ExecutionDriver |  |
| SD.1815a78323a71585b82a | src/openverify/relay/ports/__init__.py:60-66 ExecutionDriver.execute |  |
| SD.7b04b6fa0607f711c578 | src/openverify/relay/ports/__init__.py:69-71 RecordStore |  |
| SD.c9d5b599542389114240 | src/openverify/relay/ports/__init__.py:70-70 RecordStore.put |  |
| SD.35ed88edc884f5416fc2 | src/openverify/relay/ports/__init__.py:71-71 RecordStore.get |  |
| SD.0ccd881e6341bda09428 | src/openverify/relay/ports/__init__.py:74-75 EventObserver |  |
| SD.8113fd85ab3d959b4b74 | src/openverify/relay/ports/__init__.py:75-75 EventObserver.observe |  |
| SD.a37644e6fc0df305d2f3 | src/openverify/relay/ports/binding.py:8-19 compatible |  |
| SD.269514c27c70e54cac23 | src/openverify/relay/ports/binding.py:22-28 identity |  |
| SD.dcf4d15c370c8a85959a | src/openverify/relay/providers.py:44-124 FunctionProvider |  |
| SD.b813ef534b7f521c2179 | src/openverify/relay/providers.py:49-50 FunctionProvider.manifest |  |
| SD.310a991b196301014ef1 | src/openverify/relay/providers.py:52-54 FunctionProvider.cancel |  |
| SD.d5ba25eed352c70d7592 | src/openverify/relay/providers.py:56-124 FunctionProvider.invoke | CM.SDK.FUNCTION_PROVIDER.RESULT,CM.SDK.FUNCTION_PROVIDER.DECISION,CM.SDK.FUNCTION_PROVIDER.POLICY,CM.SDK.FUNCTION_PROVIDER.OBSERVATION,CM.SDK.FUNCTION_PROVIDER.EXCEPTION,CM.SDK.FUNCTION_PROVIDER.TASK_CANCEL,CM.SDK.FUNCTION_PROVIDER.BUDGET |
| SD.f8c217f39a8251f7a8b6 | src/openverify/relay/providers.py:127-166 provider | CM.SDK.FUNCTION_PROVIDER.ASYNC,CM.SDK.FUNCTION_PROVIDER.MANIFEST |
| SD.3457dd9b785cda8cd3ff | src/openverify/relay/templates.py:7-33 text_graph |  |
| SD.ac4d80e996ec7e0456db | src/openverify/relay/templates.py:36-45 guardrail_graph |  |
| SD.59c47ad61196405a9c45 | src/openverify/relay/templates.py:48-119 code_graph |  |
| SD.23385b0a90d89e128adb | src/openverify/relay/templates.py:122-129 templates |  |
| SD.1fecb7fd4af7fa64edb3 | src/openverify/serialization/__init__.py:13-33 json_equal | CM.SDK.JSON.EQUALITY |
| SD.9f3a10df196f28745c8e | src/openverify/serialization/__init__.py:36-55 to_data | CM.SDK.SERIALIZE.DATA |
| SD.d57e4a0b80dbe30225fe | src/openverify/serialization/__init__.py:68-71 serialize | CM.SDK.SERIALIZE.BYTES |
| SD.7e52130f33d125aa7a5a | src/openverify/serialization/__init__.py:87-100 decode |  |
| SD.a6d450b8ce0e553585e9 | src/openverify/standard/__init__.py:21-65 standard_catalog |  |
| SD.46c45589d28c809b7542 | src/openverify/standard/astgrep.py:15-75 astgrep_provider | CM.RELAY.STANDARD.ASTGREP |
| SD.e7c64179637c6b1357e6 | src/openverify/standard/command.py:15-22 Command |  |
| SD.b860d4b98e0d55358484 | src/openverify/standard/command.py:25-44 command_provider | CM.RELAY.STANDARD.COMMAND |
| SD.4ee3d030ab6924b3c7b0 | src/openverify/standard/command.py:47-58 verify_observation |  |
| SD.147d8cbd856ad11decfe | src/openverify/standard/command.py:61-86 command_observation_provider |  |
| SD.3ca850623a87bd792d8b | src/openverify/standard/common.py:17-25 object_schema |  |
| SD.56f8cdcad0eedf658f88 | src/openverify/standard/common.py:28-37 judge |  |
| SD.0f5bb1a30aabc0a67cd8 | src/openverify/standard/common.py:40-62 standard |  |
| SD.71ba4071c946abf68d17 | src/openverify/standard/control.py:11-28 action_policy |  |
| SD.651e0a7528e9f56e019c | src/openverify/standard/control.py:31-40 gate_decision |  |
| SD.1c186690fc9bf1351eca | src/openverify/standard/control.py:43-53 control_providers |  |
| SD.65fe2044eb5a5b9b8edc | src/openverify/standard/filesystem.py:17-55 FileAccess |  |
| SD.d1d2687c252f7317a134 | src/openverify/standard/filesystem.py:32-43 FileAccess.path |  |
| SD.af863b4a14d562ee618f | src/openverify/standard/filesystem.py:45-55 FileAccess.read |  |
| SD.950922e8c5037b53a316 | src/openverify/standard/filesystem.py:58-124 filesystem_providers |  |
| SD.648554aa4ddc9fa29bac | src/openverify/standard/git.py:16-20 git |  |
| SD.07f4a1971c86db9c76cf | src/openverify/standard/git.py:23-32 fingerprints |  |
| SD.fb633bdfa2091de5ff28 | src/openverify/standard/git.py:35-210 git_providers |  |
| SD.749373ce81e1af73440a | src/openverify/standard/paths.py:7-17 local_path |  |
| SD.3d143f36ffbc3431efd8 | src/openverify/standard/paths.py:20-22 path_key |  |
| SD.27970361bc7faef86101 | src/openverify/standard/paths.py:25-26 in_directory |  |
| SD.24b0a789e2a2b0ec6a25 | src/openverify/standard/pattern_worker.py:8-12 main |  |
| SD.3be9e231228155148d96 | src/openverify/standard/pytest.py:11-44 pytest_provider | CM.RELAY.STANDARD.PYTEST |
| SD.87aafe3455198f163a7e | src/openverify/standard/ruff.py:15-86 ruff_provider | CM.RELAY.STANDARD.RUFF |
| SD.9c91a3512c8bc185cadc | src/openverify/standard/scope.py:12-30 intersects |  |
| SD.c9e56814ab1878b43c22 | src/openverify/standard/scope.py:33-53 span_intersects |  |
| SD.0d1d00af1d4de88ee3cd | src/openverify/standard/scope.py:56-72 filter_findings |  |
| SD.c559232c904f2a956f8c | src/openverify/standard/scope.py:75-76 no_findings |  |
| SD.825c13a8fedc9c635b41 | src/openverify/standard/scope.py:79-105 scope_providers |  |
| SD.79a0f0256a66ef874223 | src/openverify/standard/structured.py:12-13 parse_json |  |
| SD.a072c7240210ecb825b6 | src/openverify/standard/structured.py:16-23 schema_check |  |
| SD.7ca2d45e107bdc665ae2 | src/openverify/standard/structured.py:26-37 structured_providers |  |
| SD.a042b9b3ca2a8d843f5f | src/openverify/standard/text.py:17-69 check_text |  |
| SD.38c26091dc72bc557d0e | src/openverify/standard/text.py:72-84 text_provider | CM.RELAY.STANDARD.TEXT |
| SD.6afc807bc689462a3482 | src/openverify/standard/tools.py:13-41 Tools |  |
| SD.a2f203fe57879480e8cd | src/openverify/standard/tools.py:19-30 Tools.executable |  |
| SD.138b58b233dc1256db38 | src/openverify/standard/tools.py:32-41 Tools.files |  |
| SD.b8271a7f65018a6c903d | src/openverify/standard/tools.py:44-52 installed_tools |  |
| SD.e798c3c78d52336a361b | src/openverify/validation/__init__.py:81-91 load_schema | CM.SDK.SCHEMA.LOAD |
| SD.8148909c43ccbd4924c3 | src/openverify/validation/__init__.py:94-95 ValidatorPort |  |
| SD.da78b692493e294318ad | src/openverify/validation/__init__.py:95-95 ValidatorPort.validate |  |
| SD.1502a976940556e9683d | src/openverify/validation/__init__.py:116-124 schema_validator |  |
| SD.1c4f6ccce3ea8dfade84 | src/openverify/validation/__init__.py:127-139 validate_wire |  |
| SD.c1c7e76963536b323d30 | src/openverify/validation/__init__.py:142-165 parse_object |  |
| SD.6d9e0ff38d0bbec0a118 | src/openverify/validation/__init__.py:168-169 parse_definition | CM.SDK.PARSE.DEFINITION |
| SD.c7c11c680ef1c0dd85ab | src/openverify/validation/__init__.py:172-173 parse_result | CM.SDK.PARSE.RESULT |
| SD.d993384cca1c13e4c91d | src/openverify/validation/__init__.py:176-177 parse_run_record | CM.SDK.PARSE.RECORD |
| SD.9a45d81252d88e0c4290 | src/openverify/validation/__init__.py:180-181 validate_definition | CM.SDK.VALIDATE.DEFINITION |
| SD.264430c851e8181c72a8 | src/openverify/validation/__init__.py:184-185 validate_result | CM.SDK.VALIDATE.RESULT |
| SD.fd596c4cdc6e9dc87ad9 | src/openverify/validation/__init__.py:188-189 fail |  |
| SD.7427aab56b7d1e20b37f | src/openverify/validation/__init__.py:192-304 semantic |  |
| SD.2f097b69bc7eb7b4eba0 | src/openverify/validation/__init__.py:368-400 aggregate_config |  |
| SD.ca92dad6a8a6c57c8d51 | src/openverify/validation/__init__.py:422-438 ordered_nodes |  |
| SD.1e0ea30dfe078904a7fa | src/openverify/validation/__init__.py:449-451 validate_executable_definition |  |


### Noncomponent records without a reviewed domain

| ID | Hierarchy | Review status |
| --- | --- | --- |
| CM.PROVIDER.COMPAT.CAPABILITY | PROVIDER / Compatibility / Matching | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.COMPAT.CAPABILITY_VCP | PROVIDER / Compatibility / VCP | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.COMPAT.REVISION | PROVIDER / Compatibility / VCP | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.COMPAT.VCP_FIELDS | PROVIDER / Compatibility / VCP | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.COMPAT.VCP_INTERSECTION | PROVIDER / Compatibility / VCP | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.FEATURE.CANCEL | PROVIDER / Control / Eligibility | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.FEATURE.DEADLINE | PROVIDER / Control / Eligibility | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.NAMESPACE.OWNERSHIP | PROVIDER / Discovery / Identifiers | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.NAMESPACE.SYNTAX | PROVIDER / Discovery / Identifiers | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.MANIFEST.CAPABILITY_IDENTITY | PROVIDER / Discovery / Manifest | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.MANIFEST.SNAPSHOT | PROVIDER / Discovery / Manifest | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.CLASSIFY | PROVIDER / Errors / Codes | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.NO_REWRITE | PROVIDER / Errors / Peer validation | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.PRECEDENCE | PROVIDER / Errors / Precedence | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.CAPABILITY_UNAVAILABLE | PROVIDER / Errors / Reserved code / CAPABILITY_UNAVAILABLE | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.CAPABILITY_VERSION_UNSUPPORTED | PROVIDER / Errors / Reserved code / CAPABILITY_VERSION_UNSUPPORTED | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.CONTRACT_VERSION_UNSUPPORTED | PROVIDER / Errors / Reserved code / CONTRACT_VERSION_UNSUPPORTED | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.INVALID_CONFIG | PROVIDER / Errors / Reserved code / INVALID_CONFIG | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.INVALID_INPUT | PROVIDER / Errors / Reserved code / INVALID_INPUT | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.INVALID_INVOCATION | PROVIDER / Errors / Reserved code / INVALID_INVOCATION | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.INVALID_PROVIDER_OUTPUT | PROVIDER / Errors / Reserved code / INVALID_PROVIDER_OUTPUT | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.ERROR.PROTOCOL_VIOLATION | PROVIDER / Errors / Reserved code / PROTOCOL_VIOLATION | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.EXT.ROUNDTRIP | PROVIDER / Extensions / Optional maps | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.EXT.MANDATORY | PROVIDER / Extensions / Scope | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.INVOKE.VALIDATE | PROVIDER / Invocation / Acceptance | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.WIRE.ATTEMPT_ID | PROVIDER / Invocation / Identity | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.SEMANTIC_BOUNDARY | PROVIDER / Meaning / VCP separation | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.BUDGET.ENFORCE | PROVIDER / Resources / Budget | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.BUDGET.EXACT | PROVIDER / Resources / Budget | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.FEATURE.RESOURCE | PROVIDER / Resources / Eligibility | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.USAGE.FINAL | PROVIDER / Resources / Usage | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.SCHEMA.REFERENCES | PROVIDER / Schemas / Capability schemas | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.SCHEMA.VALIDITY | PROVIDER / Schemas / Capability schemas | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.FEATURE.STREAM | PROVIDER / Streaming / Eligibility | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.EVENT.PAYLOAD | PROVIDER / Streaming / Payloads | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.STDIO.CHANNELS | PROVIDER / Transport / Channels | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.RPC.ERROR_CHANNEL | PROVIDER / Transport / Errors | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.RPC.RESERVED_ERRORS | PROVIDER / Transport / Errors | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.STDIO.FRAME | PROVIDER / Transport / Framing | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.STDIO.RECEIVE | PROVIDER / Transport / Framing | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.LOSS.SEPARATE | PROVIDER / Transport / Loss | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.RPC.CANCEL_ACK | PROVIDER / Transport / Methods | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.RPC.METHODS | PROVIDER / Transport / Methods | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.RPC.ACCEPT_ORDER | PROVIDER / Transport / Ordering | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.RPC.EVENT_BEFORE_RESULT | PROVIDER / Transport / Ordering | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.WIRE.NUMBERS | PROVIDER / Wire / Numbers | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.PROVIDER.WIRE.NULL | PROVIDER / Wire / Optional fields | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.BUILDER.AGGREGATE | RELAY / Authoring / Graph | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.BUILDER.BUILD | RELAY / Authoring / Graph | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.BUILDER.OPTIONAL | RELAY / Authoring / Graph | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.BUILDER.SOURCES | RELAY / Authoring / Graph | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.BIND.SELECT | RELAY / Binding / DeterministicBinder | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.BIND.CHECK | RELAY / Binding / Injected binder | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.CANCEL.TOKEN | RELAY / Cancellation / Recorded token | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.CANCEL.TASK | RELAY / Cancellation / Task | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.CATALOG.ENTRYPOINTS | RELAY / Discovery / Catalog | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.CATALOG.TRUST | RELAY / Discovery / Catalog | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.CLI.EXIT | RELAY / Entrypoints / CLI | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.CLI.JSON | RELAY / Entrypoints / CLI | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.CLI.STDIN | RELAY / Entrypoints / CLI | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SERVICE.ALLOWLIST | RELAY / Entrypoints / GraphService | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SERVICE.CONCURRENCY | RELAY / Entrypoints / GraphService | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.HTTP.AUTH | RELAY / Entrypoints / HTTP | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.HTTP.BOUND | RELAY / Entrypoints / HTTP | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.HTTP.HEALTH | RELAY / Entrypoints / HTTP | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.HTTP.SHAPE | RELAY / Entrypoints / HTTP | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.MCP.TOOLS | RELAY / Entrypoints / MCP | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.DRIVER.CHECK | RELAY / Execution / Driver | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.DRIVER.BOUNDS | RELAY / Execution / Event capture | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.DRIVER.TIMEOUT | RELAY / Execution / Timeout | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PORT.EventObserver.observe | RELAY / Extension ports / EventObserver / observe | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PORT.EventSink.emit | RELAY / Extension ports / EventSink / emit | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PORT.ExecutionDriver.execute | RELAY / Extension ports / ExecutionDriver / execute | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PORT.ProviderBinder.bind | RELAY / Extension ports / ProviderBinder / bind | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PORT.ProviderCatalog.providers | RELAY / Extension ports / ProviderCatalog / providers | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PORT.ProviderTransport.invoke | RELAY / Extension ports / ProviderTransport / invoke | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PORT.RecordStore.get | RELAY / Extension ports / RecordStore / get | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PORT.RecordStore.put | RELAY / Extension ports / RecordStore / put | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.OBSERVER.ERROR | RELAY / Observability / Observer | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.POLICY.NO_RECORD | RELAY / Policies / Occurrence | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.POLICY.IDENTITY | RELAY / Policies / Opportunity | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PREP.SNAPSHOT | RELAY / Preparation / Inputs | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PROVIDER.SHARING | RELAY / Providers / Concurrency | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PROVIDER.ERROR | RELAY / Providers / Decorator | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PROVIDER.NORMALIZE | RELAY / Providers / Decorator | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.API.RUN | RELAY / Public API / Relay.run | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.API.VIEWS | RELAY / Public API / Run | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.API.GATE | RELAY / Public API / verify_before | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.STORE.VALIDATE | RELAY / Records / Acceptance | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.ANNOTATION.SCOPE | RELAY / Records / Annotations | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.STORE.COPY | RELAY / Records / Stores | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.STORE.ERROR | RELAY / Records / Stores | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.STORE.SCOPE | RELAY / Records / Stores | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SCHED.ORDER | RELAY / Scheduler / Acceptance | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SCHED.CONTROL | RELAY / Scheduler / Barriers | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SCHED.ISOLATION | RELAY / Scheduler / Concurrent runs | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SCHED.WAVE | RELAY / Scheduler / Waves | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.ACTION.PREFIX | RELAY / Standard providers / Action policy | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SCOPE.RANGES | RELAY / Standard providers / Coordinates | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SECURITY.FILES | RELAY / Standard providers / FileAccess | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SECURITY.FRESHNESS | RELAY / Standard providers / Git | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.GIT.CHANGES | RELAY / Standard providers / Git scope | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.GIT.MODES | RELAY / Standard providers / Git scope | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SCOPE.INVALID | RELAY / Standard providers / Scope paths | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SCOPE.PATH | RELAY / Standard providers / Scope paths | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.SECURITY.TEXT | RELAY / Standard providers / Text | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.TEXT.COORDINATES | RELAY / Standard providers / Text | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.TOOL.AST | RELAY / Standard providers / Tools | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.TOOL.PYTEST | RELAY / Standard providers / Tools | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.TOOL.RUFF | RELAY / Standard providers / Tools | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.PROCESS.CLEANUP | RELAY / Transport / Processes | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.RELAY.STDIO.SESSION | RELAY / Transport / Stdio | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.SHARED.JSON_EQUALITY | SHARED / JSON value and schema semantics / JSON_EQUALITY | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.SHARED.SCHEMA_APPLICATORS | SHARED / JSON value and schema semantics / SCHEMA_APPLICATORS | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.JUDGMENT | VCP / Computation / Acceptance | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.DERIVE_ROLE | VCP / Computation / Node outputs | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.PRIMARY_DECISION | VCP / Computation / Node outputs | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.PRIMARY_RESULT | VCP / Computation / Node outputs | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.PRIMARY_VALIDITY | VCP / Computation / Node outputs | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.CONFORMANCE.STAGES | VCP / Conformance / Consumer stages | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.CONFORMANCE.FIXTURE_PROTOCOL | VCP / Conformance / Portable harness | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.BOOKKEEPING | VCP / Dataflow / Availability | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.BIND_TARGET | VCP / Dataflow / Bindings | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.CONFIG | VCP / Dataflow / Configuration | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.CONTEXT | VCP / Dataflow / Isolation | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.OPERATION | VCP / Dataflow / Operation | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.PORT_NAMES | VCP / Dataflow / Ports | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.CAPABILITY_SHAPE | VCP / Dataflow / Provider boundary | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.RUN_NAMES | VCP / Dataflow / Run inputs | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.EXT_SOURCE | VCP / Dataflow / Sources | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.RUN_SOURCE | VCP / Dataflow / Sources | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.EXT.PRESERVE | VCP / Extensions / Optional | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.EXT.REQUIRED | VCP / Extensions / Required | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.KNOWLEDGE.REFERENCE | VCP / Knowledge / ArtifactRef | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.KNOWLEDGE.EVIDENCE | VCP / Knowledge / Evidence | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.KNOWLEDGE.NEUTRAL | VCP / Knowledge / Evidence | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.DATA.HONEST_EVALUATION | VCP / Meaning / Capability behavior | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.MEANING.JUDGMENT_SCHEMA | VCP / Meaning / Definition | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.MEANING.SELECTION_DISTINCT | VCP / Meaning / Selection versus criterion | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.BIND.INPUT | VCP / Provider binding / Contract boundaries | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.BIND.OUTPUT | VCP / Provider binding / Contract boundaries | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.BIND.PRECHECK | VCP / Provider binding / Identity | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.BIND.PROVENANCE | VCP / Provider binding / Provenance | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.BIND.OUTPUT_REJECTION | VCP / Provider binding / Rejected output | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.RES.UNITS | VCP / Resources / Accounting | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.RES.KINDS | VCP / Resources / Measurements | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.RES.ORDER | VCP / Resources / Measurements | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.RES.WALL_TIME | VCP / Resources / Reference profile | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.SEVERITY.VERSION | VCP / Results / Severity | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.SCHEMA.STATIC | VCP / Schemas / Compatibility | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.SCHEMA.SUBSET | VCP / Schemas / Embedded | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.SCHEMA.RUNTIME | VCP / Schemas / Instances | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.WIRE.JSON | VCP / Wire semantics / JSON | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.WIRE.NULL | VCP / Wire semantics / Null | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.WIRE.OFFLINE | VCP / Wire semantics / References | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |
| CM.VCP.WIRE.VERSION | VCP / Wire semantics / Version | V1_CONCRETE_PROPOSITION_RETAINED_PENDING_ATOMIC_AND_DOMAIN_REVIEW |


## Specific closure findings

- Typed availability: source/port/producer-role/terminal-state/schema/ancestor/trace context is modeled explicitly. The relation is partial; missing-output reachability and overlapping invalid causes are not silently assigned invented counts. Status-handler consistency is a separate 72-coordinate projection with 18 coherent/54 incoherent states under its stated assumptions.
- Whole-schema normalization: 24 VCP and 9 Provider roots reconstructed with offline references. All keywords used by current roots are recognized. The Boolean tree preserves applicator scope. Local predicate context, prose intersections, format-versus-semantic timestamp rules and a second independent reconstruction remain unfinished.
- Standard providers: 18 named capability contracts are described, including opt-in host command launching. Documented standard catalog does not register that launcher. Capability summaries still need exact schema/mode/invalid-input/side-effect decomposition; their existence is not closure.
- Public helpers: concrete serialization/parsing/authoring/inspection/error/service contracts were added under SDK authority. Export resolution and all operations/errors remain incomplete; the declaration candidate list is not a public method inventory certificate.
- Lifecycle: independent logical phase, attempt/action, cancellation, event feature, sequence/deadline and terminal-result projections are recorded. Full dependent state/event effect classification remains unfinished; SDK checks are not physical provider timer enforcement.
- Composition: independent/edge/chain/fork/join/diamond/route/guard/aggregate/wave/cancellation/isolation partitions are explicit. Topological induction states readiness, node correctness, typed lineage, state isolation and global-effect premises; there is no unconditional proof of implementation correctness.

## Ambiguities, unsupported and open-ended limits


### Q.CUSTOM_AGG_EMPTY

Authority: NORMATIVE_VCP. Sources: spec/draft/dataflow.md:127-140, spec/draft/aggregation.md:10-18.
Known: Standard reducers reject empty input and empty retained input. Custom Aggregate uses same ordered structural declaration.
Unresolved/limit: The standard reducer section rejects empty input; the universal structural membership paragraph does not explicitly require nonempty custom membership. No custom reducer output or definition-rejection stage is invented.
Effect: Custom empty-membership expectation cannot be closed without an explicit authority/scope decision; other membership and standard reducer rules continue.

### Q.RELAY_TIMING_KEY

Authority: RELAY_PROFILE_VS_IMPLEMENTATION. Sources: docs/relay/architecture.md:78-83, src/openverify/relay/application/execution.py:141-194.
Known: Provider usage and runner timing are separate, no unit merging.
Unresolved/limit: Docs specifically describe relay_wall_time when provider wall_time uses another unit; code chooses it whenever that key exists. Exact same-unit key naming is not resolved into a portable requirement.
Effect: Exact local same-unit timing-key expectation requires clarification of the documented profile; retain both source statements.

### Q.AVAILABILITY_OVERLAP

Authority: NORMATIVE_VCP_SCOPE_LIMIT. Sources: spec/draft/dataflow.md:107-118.
Known: Six status names and all handler effects are specified; valid error/nonexecution Result ports remain inspectable when schemas admit them.
Unresolved/limit: No universally specified precedence for multiple simultaneous invalid snapshot/source causes. OUTPUT_MISSING is a status but coherent successful outputs cannot omit declared ports.
Effect: Do not label arbitrary raw source/status coordinates reachable. This is not a blocker for disjoint valid-runtime contexts; the dependent relation still needs full closure.

### Q.ROUNDING

Authority: NORMATIVE_VCP_OPEN_LIMIT. Sources: spec/draft/aggregation.md:42-46.
Known: Arithmetic reducer equations and finite score bounds apply.
Unresolved/limit: No portable cross-language float-bit/rounding oracle. Exact rational intermediate behavior is implementation descriptive.
Effect: Use algebraic semantics and declared number fidelity; no bit-identical portable claim.

Unsupported behavior remains separate from invalid wire/semantics: cycles/iteration/dynamic expansion, general guards/alternative joins, portable retry/defer scheduling, unsupported external schema resolution, unimplemented required extensions, bundled unshipped tools/providers, pooling/replay/recovery and public multi-tenant hosting are outside this declared local profile. Their exact section dispositions are not all closed.

Unbounded domains include JSON payloads, schemas, names/versions, numeric precision, text/filesystem state, trace lengths and arbitrary graph sizes. Finite categorical equations do not exhaust these. Physical scheduling races and honest external provider truth are not proved by this semantic model.

## Additional diagnostic discovery

| Identifier | Authority | Source | Meaning |
| --- | --- | --- | --- |
| PROVIDER_CONFIG | PUBLIC_SDK_CLI_DIAGNOSTIC | src/openverify/relay/entrypoints/cli.py:29-66 | Trusted CLI provider configuration violates its local schema; not a portable VCP identifier. |
| UNAUTHORIZED | HTTP_ADAPTER_RESPONSE | src/openverify/relay/entrypoints/http.py:13-48 | Configured Bearer token mismatch; HTTP 401. |
| BODY_TOO_LARGE | HTTP_ADAPTER_RESPONSE | src/openverify/relay/entrypoints/http.py:13-48 | Streaming body exceeded configured maximum; HTTP 413. |
| INVALID_REQUEST | HTTP_ADAPTER_RESPONSE | src/openverify/relay/entrypoints/http.py:13-48 | Wrong verify request object shape/types; HTTP 400. |


These four local boundary literals are not added to the 53 declared enum identifiers and are not portable normative errors. Their discovery also shows why enum counts alone cannot close all public error boundaries.

## Source hashes and scope

| Path | Bytes | SHA-256 | Authority |
| --- | --- | --- | --- |
| README.md | 23388 | 31d60f1ac0405e037ddf0685cc9649865808224b9d01bd7bef6d6ce45c3d2cb9 | PROJECT_OVERVIEW |
| conformance/README.md | 1080 | 156d01519fd92322f064c8325822b464d9cb8fdafefeeacfeab67c8c3796a92c | PORTABLE_HARNESS_DESCRIPTION |
| docs/relay/architecture.md | 6185 | 39dd8e1f1266998cef3b1c565398dd0945c991210f9ae83ab445ee9c617840b1 | RELAY_PROFILE_OR_INFORMATIVE |
| docs/relay/error-contract-hardening.md | 3823 | a6ad9882b47410f6039ab2940adbf69d8f63ab4be2523b43e294334790ed2d9d | RELAY_PROFILE_OR_INFORMATIVE |
| docs/relay/graph-authoring.md | 5080 | 32749238bf11169001e8388cccdcb48f84e2dceae04da27fa58f92c06660cdac | RELAY_PROFILE_OR_INFORMATIVE |
| docs/relay/integration.md | 5814 | 139ec04516206e4225fb460091ae2504c171a4d890d6523835797071b67b9c3a | RELAY_PROFILE_OR_INFORMATIVE |
| docs/relay/limitations.md | 3026 | d3e704cd8897804b095372b895df7de4a09c7d1c4997d1080e3abc700e4c2969 | RELAY_PROFILE_OR_INFORMATIVE |
| docs/relay/production-fixes-report.md | 9740 | 08d56ce3970f3d726b6eb8ae19c30a2267e42892d2921b68bf20d90424cb11f2 | RELAY_PROFILE_OR_INFORMATIVE |
| docs/relay/providers.md | 10205 | f066a4343ad905b727ab59b3a9dcb4d3940a0cca0258f615ee98c04f72bd86fa | RELAY_PROFILE_OR_INFORMATIVE |
| docs/relay/quickstart.md | 4235 | f373bf0fca3aaf7933de4fd0a924eddccd50cd481554fd5d3dfd15c1d707044f | RELAY_PROFILE_OR_INFORMATIVE |
| docs/relay/security.md | 5059 | 9ebb21e72e636235ca387dd017244c5ca16de315011ba99dafc65833e054877d | RELAY_PROFILE_OR_INFORMATIVE |
| docs/relay/verification.md | 5703 | 8410d000f3ad586d44df42a37f8883ddcc10dd2f735bc46919d64739906a0c22 | RELAY_PROFILE_OR_INFORMATIVE |
| profiles/standard-draft/README.md | 1084 | 19adacdd0c48c7cda6dc1fbcb2b0fe8ec26567ffc7dfc3afd3a28bb2387237c4 | STANDARD_VCP_PROFILE |
| profiles/standard-draft/profile.json | 1739 | e67739ae4a45719b27f661f12a933a9b021fa6164c5bed19f3fc261034651ed4 | STANDARD_VCP_PROFILE |
| provider-contract/README.md | 3951 | 8b4c352be5b8d1d66943fb94e69ba17f72e4dfdc5a6a27530983917c9167de72 | PROJECT_OVERVIEW |
| provider-contract/conformance/README.md | 1680 | ce41e7a7fa1a50acc49e062778f05f4a4e4823f5d0083e55d3c02d1afb4f8470 | PORTABLE_HARNESS_DESCRIPTION |
| provider-contract/schemas/draft/cancel-request.schema.json | 745 | 7e5fe523a3533558a28049c73b927550460bc6f5cddf8b41c3e2de45121379fa | PROVIDER_SCHEMA |
| provider-contract/schemas/draft/capability.schema.json | 1940 | 66242f836060a987d7dd7208872630a3ffc9f865b81565410950213d1f667dad | PROVIDER_SCHEMA |
| provider-contract/schemas/draft/initialize-request.schema.json | 1012 | e23a6c9c372c72f39cc29443d24c37e70844a6c2d65eb68c2ae0a649137b63da | PROVIDER_SCHEMA |
| provider-contract/schemas/draft/initialize-result.schema.json | 764 | 71686e48b7b398b8efe786dc433c1a2e2f25d311e2ba89e402b22efae062ee62 | PROVIDER_SCHEMA |
| provider-contract/schemas/draft/invocation.schema.json | 1650 | f10b9cda14d7f18e58289d981da5b8b8261bfa3d246d71c8cc7c2b473adf24e6 | PROVIDER_SCHEMA |
| provider-contract/schemas/draft/outcome.schema.json | 1859 | 7df6c6622b35d483bb42589ff571b061be2cbdd97d85fe4030b6aef6719d85c8 | PROVIDER_SCHEMA |
| provider-contract/schemas/draft/provider-error.schema.json | 1006 | eebf40e65a56ddeeda103cf2a18df73eeb65e8a5bdca2733caf84342e4dfe5d9 | PROVIDER_SCHEMA |
| provider-contract/schemas/draft/provider-event.schema.json | 3017 | 0bf4bb10e54b99f7c9edd1bcb64d71b2146b164cf3397ceb0a948514263f885e | PROVIDER_SCHEMA |
| provider-contract/schemas/draft/provider-manifest.schema.json | 1547 | e2c5c88d4e2c5e906a4218722a791154d847664f86af121d8f747480286cae49 | PROVIDER_SCHEMA |
| provider-contract/spec/draft/capabilities.md | 3456 | 9ac03569a88e9982b5a75ceb705daa59cd0ff21aa3ab440d9ee0e3b2afcaa66a | PROVIDER_PROSE |
| provider-contract/spec/draft/errors.md | 1974 | 421ba6acd25ce220f3cd986f14819bd07034873b4b23cef891149d9657d6d3e4 | PROVIDER_PROSE |
| provider-contract/spec/draft/lifecycle.md | 4586 | 122e8e4aaa8deb60d0cf6397d9857294d096f063c5c7ecde59d3d0359596177d | PROVIDER_PROSE |
| provider-contract/spec/draft/open-questions.md | 1638 | 0c0ddb9a1f51619d6b787ceeac452c659a5f4b1f7be71fa33894643d4000bb19 | PROVIDER_PROSE |
| provider-contract/spec/draft/overview.md | 1413 | b2d0b56c135323accc4927db85b0af447b7f925c4bb8debc00443ec495487807 | PROVIDER_PROSE |
| provider-contract/spec/draft/transports.md | 4625 | 3d5b5d158363059147706b232ecbc7112a911845b5f22fc3db40ed2d490f0fea | PROVIDER_PROSE |
| provider-contract/spec/draft/versioning.md | 2245 | 2656dd1dbd2a872bd9d9912b8dba4c2ec61fc4dbaf145d091f7cda1203132921 | PROVIDER_PROSE |
| provider-contract/spec/draft/wire-format.md | 4047 | 23d1e6bc4518225afa86f422d15eee22214d7a285b369c42c6843f45d06895a7 | PROVIDER_PROSE |
| pyproject.toml | 1697 | f6cd9f3b0e62fb40631d9c3116d49de2783cd945acc679c02727171ab3bb802a | PROJECT_OVERVIEW |
| schemas/draft/activation.schema.json | 504 | 6e37ab4712eb1e96d5a5ff866f2b27bde808ec51a81dca8b47dfd9e2655b0dc9 | VCP_SCHEMA |
| schemas/draft/admission.schema.json | 504 | bcbcee1094ba855888dc566a48004a0f1ee5d9625e5f94a7138ae293b676953f | VCP_SCHEMA |
| schemas/draft/artifact-ref.schema.json | 829 | 7bf26b3364910fc080867c4cef15e4cb7fd3c416f4fee6b7f2650d01373e1f2d | VCP_SCHEMA |
| schemas/draft/cancellation-event.schema.json | 588 | 9cbac956328c63c971092e1d07c1a9cc49d63b692893ffd4c1ce0fecccf4f641 | VCP_SCHEMA |
| schemas/draft/decision.schema.json | 1079 | 47ebf3ea5ab3fd1f4cd434ec2d18981d5593f7f66dd3cdeb9a2f6b15160723ee | VCP_SCHEMA |
| schemas/draft/evidence.schema.json | 1023 | e5fe25b8d81739697c6139d5d6e7b541ad6910f58c543a6a90b5f1e9e44a688f | VCP_SCHEMA |
| schemas/draft/execution-observation.schema.json | 1075 | 3925c1e9077ecfb9eaa47094325aa4c6c4a22871aadede4f977b06d0fd8115b4 | VCP_SCHEMA |
| schemas/draft/extension.schema.json | 584 | d311028d33dc5062da712c553eb75d61a1f6d9038ec35b6e7a15b6fafaa12abc | VCP_SCHEMA |
| schemas/draft/graph.schema.json | 3797 | d363f055c63cf2692a566885b71030da8f8ac9ab2d024798f652c2c3f119d86c | VCP_SCHEMA |
| schemas/draft/input-port.schema.json | 936 | 06bf28b97b7d3c4cb92d058ff2866cc334120c00c5279cba8fda8425c7f9d3c9 | VCP_SCHEMA |
| schemas/draft/input-resolution.schema.json | 687 | b648c5a0866f5c56bbc62e20fa8a93b9ef9c389be522126bb322023a3e35349f | VCP_SCHEMA |
| schemas/draft/operation-requirement.schema.json | 622 | 93f38eb5c2c21f7afcfebc46e05fe36143b7cdcede959ffae69a0e9eee919af0 | VCP_SCHEMA |
| schemas/draft/output-port.schema.json | 606 | 6c4160672d752a4b12340290b6069f305eebaf9d2e7ea4fbb2d61ef1cc25f2bf | VCP_SCHEMA |
| schemas/draft/policy-evaluation.schema.json | 1329 | cd4cb6210e17891149edbe908dc1a1daab8abb8f8471e6c14fdaaed45e132806 | VCP_SCHEMA |
| schemas/draft/profile.schema.json | 1573 | 1c46b09ba4bb431f5781f8663b30774895fa719fe3ba08753960f3df8478aedd | VCP_SCHEMA |
| schemas/draft/provider-binding.schema.json | 1064 | b3230a926aac92122ba09889966dbcbce0985f2b6f37773874c9d5331af4933d | VCP_SCHEMA |
| schemas/draft/resource-dimension.schema.json | 720 | fa4e4bcdc4d442c5db8e19c7e9cfeee041c1f843355454eccbfc0d0132f1bb29 | VCP_SCHEMA |
| schemas/draft/resource.schema.json | 1019 | da075a12e91b40d9110f7e5f07ef4aad6a3d4dfcf0edc499219098b7c4cb2145 | VCP_SCHEMA |
| schemas/draft/result.schema.json | 2681 | 41625c8616ebb6cbe5da97a88bb8d7e747b40d40db35b82eb0ea4a534a4c2173 | VCP_SCHEMA |
| schemas/draft/run-record.schema.json | 6454 | f0d812b54bd748d282e39016885d3776207a7865763969365002e052aca02773 | VCP_SCHEMA |
| schemas/draft/selection.schema.json | 513 | d6c0f5e13bf50425e9b934254188a95a968465dc27774f61187caec77f5000b9 | VCP_SCHEMA |
| schemas/draft/severity-domain.schema.json | 784 | 5451af1a9db01672b874f8d38811ea265f9635fb9f8b9892cfe0f07a693540fd | VCP_SCHEMA |
| schemas/draft/value-source.schema.json | 1508 | d2b60c21b86c717dfd76aa10573bd85750aebcf653f93d04b57535e1ae73e3d5 | VCP_SCHEMA |
| schemas/draft/verification-definition.schema.json | 5591 | 4830194f7bfc1c33ba1d6f9d977ac402231f9bcc59e2990ab076ba0e7b545294 | VCP_SCHEMA |
| spec/draft/README.md | 1768 | 5113269e6de739338601ef897ab253142ff648e8b25060a2d8d5c937ad2fa058 | VCP_PROSE |
| spec/draft/aggregation.md | 3453 | 9c5599e6c6553ed7da5da13ffe65294c97402be7b6c221c326c7efbf98b8da8d | VCP_PROSE |
| spec/draft/boundary.md | 1646 | f9b9393c9e16bec7b9cd7ff73997b6e656817486b1e3aaaee3b0d5406cb0dbab | VCP_PROSE |
| spec/draft/composition.md | 1533 | cd930f696dbfe7c5897930a848f999575241570fbdaa81fa51a167828f7299cc | VCP_PROSE |
| spec/draft/computation.md | 993 | 52c89f5f0bd6e87dee5cce3cd3b548fbae49975cce6896df352660215a4b188c | VCP_PROSE |
| spec/draft/conceptual-audit.md | 7409 | f748fb8da7159456e29ad7750b499481172c957fca7b82f90e8f57a9a2f9cc2d | VCP_PROSE |
| spec/draft/conformance.md | 2351 | b48dec7685452f8ba47b1896747decf37d247d0e8eabee6e0289b22f87f0c074 | VCP_PROSE |
| spec/draft/dataflow.md | 13136 | 50c60efcd2701f35d93b05040bc0aef5a2f3dcf8252e026a3df956c4d4554c02 | VCP_PROSE |
| spec/draft/execution-policy.md | 4976 | 2bb545ce77cbf3790261a35a9955104fecb8c18be1f56e51c1ff0c2d251ce4cf | VCP_PROSE |
| spec/draft/extensions.md | 1012 | fc57202300c344967487f4d631e7b6bbc99281634a1f4391249ce2a7ec7040d7 | VCP_PROSE |
| spec/draft/knowledge.md | 1459 | 46dd1dbb4b8ca84d87ada6fa3790eac4891be4814267b764d39fafd0293b4dd3 | VCP_PROSE |
| spec/draft/lifecycle.md | 4340 | 7a64e510300c0a326985bab7435ed5dd65f3c0745bb003202df6d03c9b52af02 | VCP_PROSE |
| spec/draft/meaning.md | 1628 | 7dfc04cad4db77ed6eeda32a97f13460b8a271159260b7b3e89ef17e54dec55c | VCP_PROSE |
| spec/draft/open-questions.md | 9322 | d172d96b92104a6de8eabb1541cdd3bf598b30f076730cb2dbc095ee2f129546 | VCP_PROSE |
| spec/draft/provenance.md | 3812 | 3e02714727ab1b957df766739e37871362ae1ece47bd7623c7cfe90e5464818a | VCP_PROSE |
| spec/draft/provider-binding.md | 5683 | 0e0b75547db6e869aaa66d17ba43b5fe4cf2473f3ea7eb344844f332b0b61f8f | VCP_PROSE |
| spec/draft/resources.md | 1713 | 69fc4771421d8f1672488e7b2266397d0bba6b8a179a08834a9a0b981357ea72 | VCP_PROSE |
| spec/draft/result.md | 3256 | 14acc3ccf0b4bc26570687be3a9f9a78746deb29007756626c2c1677e9e695ba | VCP_PROSE |
| spec/draft/wire-format.md | 2265 | e2ff9695699de355d19490a67a27480dbb382c533f8fa408ef404900909e78ee | VCP_PROSE |
| src/openverify/__init__.py | 1011 | 427a28137cc93d02f536658976e79f838a1a71de11a37a14e653d70280bf6956 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/adapters/__init__.py | 1076 | 3f1ce9f105f56fd35e1337f8d7fe508a0078d174926ebd2a8a16734b49144497 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/adapters/demo.py | 3618 | b2ceecdf764c31ccf5e72d749ba75af28151a475dc4a193b19c9350839416a01 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/authoring/__init__.py | 188 | 9aad27400ab7bcf602cf253e6c5788d87093f88c889f75e7541dfb8415fb6e06 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/authoring/graph.py | 9201 | 48b0dce02e1487ccc3ca51d6a40e5446de78ca4010e95fff81e6217281fb5fad | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/authoring/references.py | 553 | 97385c774624753bfde2a0802cefdb98259522ed630c8d98fd767f10e244dd67 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/cli.py | 2368 | e1d38334f878c2d825db591e7acb5fb7bfca0b52d3878ae0f8bccbb4dfb0e61b | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/conformance/__init__.py | 703 | f99b26c5f9884d0a87b6d024c55762129265edaef42f7879a07a715fe769b5d9 | PORTABLE_HARNESS_DESCRIPTION |
| src/openverify/dataflow.py | 21209 | f61468ce1f934e4d677171f651eb5ccaf9fb1e8145e980cded7c75203e808d8c | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/engine/__init__.py | 13746 | 10a333e85bc0cd3c779004a0877f53389cbc2e039930d00f6527d44bcecaffd8 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/engine/admission.py | 1446 | bdef93be2d243f82c20a887405718b3c8da81127f5ee965b67ee8f142c7acbcb | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/engine/aggregation.py | 4267 | f2c0824988a07573eec033485969298bf4cf5790bf4627044b2343d62a92833f | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/engine/binding.py | 3046 | 817805b3f60908e7d66af96953c941f9ac5d292de8ba4000f413dd5b846fd145 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/engine/policy.py | 3271 | c612e423b8d0908b775c2e032b26d99bc44dac2972357cf6cad431578f54306b | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/error_codes.py | 1627 | 11b802c51c53b094e6aa694c5f0962270e399c6a3b356de788b20abac8373d8b | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/errors.py | 1189 | 2dce7a2f896b8ced248c1b7be8f4ee9ff5bd2dedc96bbb118612c660ecde930a | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/fingerprint/__init__.py | 423 | f5ced653c2ba3ea6aa54dda046b3b6c8d1c13e290c0e97ab2fa4385dd6895d34 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/inspection.py | 2883 | 24da3a1930d931e2307906a12b8bb60ced0e2635023801365595215af4824c8d | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/json_schema.py | 6362 | b5152f0faf46997b91fb312eca5cefc552c1dbad7dee8c1b0f17b8658eab1a24 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/lifecycle.py | 2947 | 4d32fcb3bb4cbad17ceae9e05f9a81ccdc1952a350112844808aeeef8430ffba | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/model/__init__.py | 9357 | 9b71e732e4304d9ddf8fce98ea6f8dc941b1c44f3cf73f72d6959a2012aae805 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/policy.py | 3362 | 86f96763583dfc1d91e2f0169db51ff0a9ca793c556d041d098bdfd160a1c485 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/provenance/__init__.py | 1275 | d70976288aaa16e48ae0cc462c0d18b521148b2e6f8a90b5f73b1dab9dd720fa | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/provider/__init__.py | 2122 | 65fb1f6e8f1ad95404077dc11a16b78d6392fa31298b361db4409558e8d27af9 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/provider/conformance.py | 2699 | 678bc1b2d1b4b4365d826dc12ac9d88616023b9d0c70f0298c3baaf36932db9f | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/provider/lifecycle.py | 10334 | f8456c8f8988a9e9af16a6bf92b435ada182fdc3dc00799b3c119288d82ba4d4 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/provider/model.py | 2930 | 3ac0e970a0eb77358a7f1c775fe17f2c0442ad46fa68e4abcd74c5ef29dc5f36 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/provider/stdio.py | 11113 | 580faa7347627657f75e0bce7318fc5bfa4b72409c4e0dc1b707c43661243d79 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/provider/validation.py | 14088 | c087fa9fd79a68d4907322a5173acc9c31453570f679f1942d3066499d416be4 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/provider_codes.py | 572 | 8c920dcfbb0c00e1eeb7d776be4719128ddeeb8021ca3e0c1b2e489d12dc23ec | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/__init__.py | 316 | 4aa20cfa0974c516fd9f06622693c45bf518287b3e8be98d5085cb648c2a76bd | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/__init__.py | 46 | a851473aac79e9bc3c846d4a06937e253ad7c08d01857043fb5b0a4904913b29 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/binder.py | 1250 | 3e7b6726db45b2c1f0b0ba5ca041ce42de050c09e331f7ec8448cf408cef5590 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/catalog.py | 3432 | 99b2b48d7b6abb55d1e9445817d0d51743b26fce2be1d89b8234106f8ef00476 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/inprocess.py | 2412 | 5d5bbe5f9de841cb4ac3a152614164f45390858fd9119dd4839da4d8dafe456d | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/jsonl.py | 1051 | a1c424fac3cafc8067dfa6a2a1b29322f5f04eee849f932f7aa70d80ca5f8f58 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/local.py | 4046 | 614ace847fd560405d3b89d44115ef90efc28b979935218f44079b98af3f6fbf | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/logging.py | 688 | 962df25c768f6ac9c006e0b3006bb9c8e30b26064ffc7adaa0349b27a1eb75db | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/memory.py | 752 | 61972d7f49bc9c0421a81a7259ffd16a71fcca4bacba46b5e23ddd8d441652ad | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/process.py | 4156 | 0f43102c2dd6c43fd12068a70bb8d789b75c55c6b8ac71fa3c7090f6a61c6214 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/server.py | 5392 | 2809b840229320a8706c4266da06168408ae0ded3413a38706ec9caf2c051b18 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/stdio.py | 6713 | a1bd23c4f597626cd3adf4d323f67e479345fa5ce740c505e0173ac3a3792968 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/adapters/windows_job.py | 2491 | 8d19c67b06e7a4ec1bbe5b70523a3a61a66cbb723845dfd61856fefbafa811b7 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/api.py | 5409 | 3b01df667b8272016b0bd177defce7b5cfa33dfad238a945021782c3cc3f6549 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/application/__init__.py | 61 | a39172ecc2173839ea51bfefe8f749e50d275d4118788541c60a8d67ae26e7e5 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/application/binding.py | 2301 | 0be39eaa0aa1c4ca84ec64b75098d6d9b470b7158cbdc568ccd5d0b691f3cfb3 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/application/contract.py | 1560 | 4385a847188853cf05010b9e588bc001ddbde8b3679ce3df02af080ec0af7f34 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/application/execution.py | 7269 | 948c3be317f68e74be00426550807791eb3a3147b1b8c18fdeb0cc0773292183 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/application/policies.py | 4887 | fee622397d05f8f3cc4630a86ea91262f11a9d6c1a13447f7946bfe0d81c68aa | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/application/preparation.py | 1582 | 6234f7c08f723a629fbdc8e345f12d5dbe2bef698dc9f7f47d6687dcbb042429 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/application/run.py | 12453 | a958f472edd9ce6644ca3f2f2b08e082ef04e07b6c4c8d3baacb1652cf92f249 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/config.py | 746 | 0baac5f1e572475560f0e62b555540423cdb549038d206f5634adcbb93e1d551 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/core/__init__.py | 73 | c6130bc3323b8549815977495758720c28f27e7fc277558f4b5e26a49390e9a3 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/core/aggregation.py | 4212 | 1cfa76d89c54d40d477a6be4b280cf23c18a01559bd6cc8036dc1ca6e1b27da6 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/core/readiness.py | 557 | 7975b54522437f833d43f0b33dc37346988459c9da9f4acd36c4b6e26d87c08b | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/core/state.py | 876 | 8da362b801c62687041e9b27218c59b2a6b3fb2bbc6589d02ed57807b8102e57 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/entrypoints/__init__.py | 62 | f6df74eb909aaa95457f7b89ad94eefe57d6e9e3360d8144d8a710c9f771718e | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/entrypoints/cli.py | 8436 | ce61e293fb4f12bc2f9bed02bf89a81b9cb8084ac8085e8e41b48c5e375a6d47 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/entrypoints/http.py | 2055 | abb2644b25d8bfefe10fdb0f1869e36103325217223af108f8bcb88415e669d2 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/entrypoints/mcp.py | 1322 | 26dbd8c469550e5826b7d7dda2ad5f4e80e7f25e0db1c455b6678b67ee235b9d | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/entrypoints/service.py | 2261 | 0accc0770270fe8ea7c5229244da2cf9074218caf085f133d4b4b3527f04700d | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/error_codes.py | 558 | d12a354eaa8cb5f769af97acba6e3cd46d06a76436de78e14bab4e12e15c98fc | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/errors.py | 545 | a1564afe96238e3ba22dd89c17bbe22f8c14df80655c02e7ad185fc82ad82c2e | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/ports/__init__.py | 2023 | 5d8626535f199d406cdb6fe93457155defbe6f4666063cf7fd892642229dd778 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/ports/binding.py | 1139 | 335d3c7ba4040fbc944d7e8a51ec33858fcb6033c47f6bd322abd83d2953e404 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/providers.py | 6123 | c3b967ff59c7c3fbd6abb65da9b74292504f81ff04df0b24116a923704289d2c | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/relay/templates.py | 4231 | b7f12cb3e289dd582ced7ee3aa7b9d319f9453b5c256c44641fab475af953c74 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/serialization/__init__.py | 4999 | 7a2f46c623f94a81925d12d8e92f446db440f2415508f0db4ae6e06e542a7110 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/__init__.py | 2576 | 2ad7f0c2cf4ae6a03f1a7939f1df2b51947519485fc5248858705482fdd5e96f | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/astgrep.py | 2958 | ae28d7f38f65a96580fa41c86518321086ddc8be0d86fde4fcfcdd1321e7b2e6 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/command.py | 2790 | 1532d1dfb2f3a6820bcb26458d589b422562dbbe34fc4ebff6df39a41eab1b52 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/common.py | 2198 | bc55d0c0bb9c0e134b0564b6e72ad1fb6cd4a2d4a61c497fb5d6e58c3bfa6f0b | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/control.py | 1823 | 5ae8c4250ac674ffd11a81f5049633468b788b103a0749106b1d1eda4a67a8ab | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/filesystem.py | 4773 | 8e72d8e8a03c78677d1ff1582fbde88eeb072c3f2f3975b8fdcfca4b25f8f85e | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/git.py | 8630 | 9ff2cee66ebaccb377bd325a6ec879f18fa473e43f54274004c7017d8673b218 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/paths.py | 937 | 4f450710e1ff08464ca8e6e27a3f96926169a96111241071fa3e6c6b67d711d2 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/pattern_worker.py | 331 | 4b7085e919688799c00b894bd9ae22d981188abe9f4e7504bca84d27b66085d2 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/pytest.py | 1725 | 4306df9f9a1f7aa274805bdf49f1013dd870fac71c5fc8e1719125fa2116d692 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/ruff.py | 3085 | f1ba8ae9c316f96e0d56a4fe1a66a490db8e354617633af36f68bce7a27c4c52 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/scope.py | 3762 | 935b8b2996a0f6416c4292f2155a5e4220295fe49728c944b51bf59699482ab6 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/structured.py | 1219 | 8930b3d022eee59a86fe7d57f5bb29b04a1d54e83c795a25ad3c7b805c5d188a | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/text.py | 3126 | 98eab2a5ca35d2a79a3182e1c60c64073369f6a516b6c398f9661af2cc54d22e | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/standard/tools.py | 1791 | 98b9b073b3776dd0e4119e98219fe7cd8968702b184f531cac19b266f51831c9 | IMPLEMENTATION_OR_PUBLIC_SDK |
| src/openverify/validation/__init__.py | 26492 | cef5aa3510c1657692209d8fb9c8bb06377ddafacb4c7f267e3b52868da6cfc8 | IMPLEMENTATION_OR_PUBLIC_SDK |


Packaged SDK schema copies are discoverable implementation artifacts. This review indexes the authoritative schema roots; byte identity against every packaged copy is not yet independently certified. External dependencies reviewed as references include JSON Schema 2020-12 Core/Validation, JSON-RPC 2.0, RFC6901, RFC3339 and the framing reference. Their complete normative transitive scope, errata, exact-byte hashes and all applicability rules are not closed; no transitive external-standard completeness is claimed.

External primary references: [JSON Schema Core](https://json-schema.org/draft/2020-12/json-schema-core), [Validation](https://json-schema.org/draft/2020-12/json-schema-validation), [JSON-RPC](https://www.jsonrpc.org/specification), [RFC6901](https://www.rfc-editor.org/info/rfc6901/), [RFC3339](https://www.rfc-editor.org/info/rfc3339/), [LSP framing source](https://raw.githubusercontent.com/microsoft/language-server-protocol/gh-pages/_specifications/lsp/3.17/specification.md). Only project-selected semantics apply; LSP methods/lifecycle are not imported.

## Validation actually performed

Authoring-time metadata/arithmetic checks only: source hashes, resolvable nonrecursive published URN references, recognized schema keywords, finite count reconciliation, unique record IDs, domain link existence, dependency replacement and unchanged provisional files. These are not Golden tests and do not prove semantic completeness. No pytest or Relay suite ran.

## Verdict

**INCOMPLETE — ALL FOUR GATES FAIL.** Every hierarchy branch/leaf inherits that verdict. A complete canonical model has not yet been established. No approval for tests, frozen expectations or certification is requested or implied.

Inherited descriptive interaction branch labels were separated from requirement-ID dependencies for: CM.SHARED.JSON_EQUALITY. These branch labels still require cross-cutting semantic reconciliation.
