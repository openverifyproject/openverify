# Canonical review v2 source audit

Base commit: cdad9bad6ca6e5201fbda48dd5b85d58736e3731. Current repository source aggregate SHA-256: f976a456e361b9ac21fc62a8457598625479ba3178f4bd12f725e09f7852260c. The digest is SHA256 of sorted compact JSON path->SHA256 over the 162 reviewed repository source files; it is integrity metadata, not an expectation freeze.

## Gate verdicts

| Gate | Verdict | Evidence |
| --- | --- | --- |
| 1 Semantic source closure | PASS WITH EXPLICIT QUESTIONS | All original 314 unfinished prose units and 366 declaration candidates semantically dispositioned ; 55 exports/12 type aliases/special output lookup reviewed. Every discovered supported proposition has canonical ownership. Questions are separate from invented requirements. |
| 2 Whole-schema semantics | FAIL FOR FULL SUBSET; SHIPPED ROOTS PASS | 24 VCP+9 Provider roots reconstructed; 724 components reconciled in root context ; 34 packaged copies byte-identical. Nonprogressing recursion and Provider boolean annotation targets remain explicit portable-subset questions. |
| 3 Behavioral mathematics | FAIL FOR FULL PROFILE; KNOWN RULE DOMAINS DERIVED | All 581 semantic records have explicit domains ; 85 named finite projections and 44 own leaf quotients reconcile. Typed availability overlap and 2 unused-default coordinates remain blocked; no arbitrary finite count substitutes for them. |
| 4 Independent source-first traversal | PASS AS SOURCE COMPARISON, NOT CERTIFICATION | 162 source files independently revisited through semantic propositions; all614 primary records compared. Additional omissions/applicability errors were repaired. No identified supported semantic clause remains unowned; explicit questions prevent full-profile closure. |

## What was reviewed

The selected source set includes current VCP prose/schemas, Provider prose/schemas, standard profile, Relay profile documents, public SDK/type/authoring/Provider/Engine interfaces, all Relay sources and standard capability implementations, entrypoints, project script declarations and contributing guidance. Source indexing, semantic interpretation and second-pass comparison remain separate records in SOURCE_CROSSWALK.jsonl.

| Index/review category | Count | Meaning |
| --- | --- | --- |
| Repository source files | 162 | Includes informative/alias/process files; not all are normative. |
| Original source sections | 122 | Locations, not requirements. |
| Prose units | 409 | All dispositioned; original unfinished backlog 314 is closed. |
| Schema source positions | 1588 | Root/member/annotation/container positions, not independent requirements. |
| Public declaration candidates | 366 | All publicness/semantics or justified non-obligation reviewed. |
| Reexports | 55 | Resolved aliases to actual declarations. |
| Additional type aliases | 12 | Individually classified, not extra behavior by syntax. |
| Special-method review | 1 | NodeRef output lookup, included despite underscore extraction. |
| Standard-profile JSON positions | 77 | Selected data, not global core enums. |
| Semantic propositions | 581 | Concrete source-derived behaviors; counts independent of source formatting. |
| Whole-root structural predicates | 33 | Complete Boolean roots. |
| Local schema components | 724 | Parts of roots, excluded from semantic denominator. |
| Preserved split groups / aliases | 74 / 12 | IDs retained without counting their old compounds again. |

## Independence and reconciliation

No Golden test, fixture corpus, frozen expectation, blueprint or old Golden inventory was used to derive a requirement or expected value. This continuation read the existing canonical-review-v2 files as provisional inputs, as authorized, and the current repository authorities. Historical Relay completion/validation summaries in mixed docs were displayed during source discovery and classified as informative; their test counts/results were not used. Portable conformance helper code and documented data formats were reviewed, but their fixture manifests/corpus were not opened or run.

The second traversal starts with source propositions and then records canonical matches. It identified omitted score orientation, declarative Criterion/mapping meaning, opaque invocation context, advisory event timestamp ordering, direct upstream provenance, local required-extension support, optional Python Provider operations, SDK timestamp format behavior and local aggregate-key restrictions. It repaired conflation of CLI terminal-result exit selection with all-record action gating; generic string-subclass normalization with actual StrEnum/value versus mapping-key behavior; Provider features with Relay generated constraints; and false-schema validity with static binding contradiction. Split/alias decisions and corrected source ranges are individually retained in JSONL. A match ledger demonstrates reconciliation, not infallibility of human semantic judgment.


## Mathematical audit

All 85 named finite projections were independently checked with source-derived predicates or worked arithmetic: Result wire/quotient/observation assumptions, policy/Provider categorical products, all 34 required-key projections, graph source-set inclusion-exclusion and 53 declared codes. 44 rule-specific quotients avoid assigning joint Result-family validity counts to each leaf. Exact source schemas for 18 standard capabilities and 50 typed model constructor shapes are retained. Standard declared-key projections are presence-only, not whole-capability validity. Raw typed-availability products are not classified as reachable without source/role/schema/trace context.

The original 156 absent behavioral domains have been addressed through explicit argument classes, applicability, allowed/forbidden effects, dependent relations and semantic partitions. A domain reference alone was not accepted as derivation: incorrect old links (for example numeric reducers to membership-only mathematics) were repaired. Some semantic obligations, such as honesty/purpose of evidence, are intentionally intensional and cannot be decided from arbitrary natural-language wire payloads. This is explicitly separated from structural Evidence validity and graph-generated evidence absence.


The final consistency pass checked 672 finite count identities: 85 named projections, 543 local component quotients and 44 leaf quotients. It found zero dangling canonical/domain references, unmatched primary comparison records, or stale source hash/line references. These integrity checks do not establish semantic completeness by themselves.

Only error categories or precedence actually assigned by current authoritative prose are fixed expectations. Unassigned category choices remain unspecified; the 53 enum identifiers do not imply a complete exact-error dispatch table. Historical Golden discussion in an open-questions page supplies no additional portable rule.

## Remaining questions and scope limits

### Q.CUSTOM_AGG_EMPTY

Status: EXPLICIT_SEMANTIC_BLOCKER.

Known: Standard reducers reject empty input and empty retained input. Custom Aggregate uses same ordered structural declaration.

Unresolved/limited: The standard reducer section rejects empty input; the universal structural membership paragraph does not explicitly require nonempty custom membership. No custom reducer output or definition-rejection stage is invented.

Impact: Custom empty-membership expectation cannot be closed without an explicit authority/scope decision; other membership and standard reducer rules continue.

Owners/interactions: CM.VCP.AGG.MEMBERS.COMPLETE, CM.VCP.AGG.NONEMPTY. Sources: spec/draft/dataflow.md:127-140; spec/draft/aggregation.md:10-18.

### Q.RELAY_TIMING_KEY

Status: DOCUMENTED_PROFILE_KEY_UNDERSPECIFICATION.

Known: Provider usage and runner timing are separate, no unit merging.

Unresolved/limited: Docs specifically describe relay_wall_time when provider wall_time uses another unit; code chooses it whenever that key exists. Exact same-unit key naming is not resolved into a portable requirement.

Impact: Exact local same-unit timing-key expectation requires clarification of the documented profile; retain both source statements.

Owners/interactions: CM.RELAY.API.VIEWS.USAGE, CM.VCP.RES.WALL_TIME.SEPARATE. Sources: docs/relay/architecture.md:78-83; src/openverify/relay/application/execution.py:141-194.

### Q.AVAILABILITY_OVERLAP

Status: EXPLICIT_SEMANTIC_BLOCKER.

Known: Six status names and all handler effects are specified; valid error/nonexecution Result ports remain inspectable when schemas admit them.

Unresolved/limited: Normative prose names six statuses without complete priority among output missing/invalid/error causes, and does not assign an unavailable status to interrupted CANCELLED information/Decision producer. Disjoint available/error/unstarted contexts and all handler effects are specified.

Impact: Only exact ambiguous status coordinates remain blocked; rejection/nonpublication/default/omit/block effects remain derived. No raw source/status Cartesian total claimed.

Owners/interactions: CM.VCP.DATA.RESOLVE_ALL, CM.VCP.DATA.BOOKKEEPING. Sources: spec/draft/dataflow.md:107-118.

### Q.ROUNDING

Status: UNBOUNDED_PRECISION_LIMIT_NO_BITWISE_REQUIREMENT.

Known: Arithmetic reducer equations and finite score bounds apply.

Unresolved/limited: No portable cross-language float-bit/rounding oracle. Exact rational intermediate behavior is implementation descriptive.

Impact: Use algebraic semantics and declared number fidelity; no bit-identical portable claim.

Owners/interactions: CM.VCP.AGG.MEAN, CM.VCP.AGG.WEIGHTED.SCORE. Sources: spec/draft/aggregation.md:42-46.

### Q.DEFAULT_UNUSED

Status: EXPLICIT_SEMANTIC_BLOCKER.

Known: DEFAULT requires explicit Constant; requiredness fixes BLOCK versus optional OMIT/DEFAULT.

Unresolved/limited: Prose does not expressly prohibit an unused default on BLOCK/OMIT; SDK rejects it. Portable rejection for that unused-field coordinate is not established.

Impact: Only this portable field-interaction expectation remains ambiguous; SDK rejection is a separate local behavior.

Owners/interactions: CM.VCP.DATA.PORT_HANDLING, CM.VCP.DATA.DEFAULT.CONSTANT. Sources: spec/draft/dataflow.md:20-33; src/openverify/dataflow.py:36-45.

### Q.VERSION_FUTURE_INTERSECTION

Status: UNSUPPORTED_FUTURE_PROFILE_LIMIT.

Known: Contract0.1 exact versions, runner-first shared selection, draft implementations select only0.1.

Unresolved/limited: For lists advertising an earlier shared future version before0.1, generic preference text and local supported-version restriction do not define a portable multi-version implementation profile.

Impact: 0.1-only declared profile is decidable; hypothetical future support not silently inferred. SDK helper first-common-then0.1 behavior separately specified.

Owners/interactions: CM.PROVIDER.INIT.SELECT, CM.SDK.PROVIDER.NEGOTIATE. Sources: provider-contract/spec/draft/versioning.md:3-14; src/openverify/provider/lifecycle.py:25-30.

### Q.NONPROGRESSING_SCHEMA_REFERENCE

Status: EXTERNAL_UNDEFINED_SEMANTICS.

Known: Local root references are permitted. Finite JSON instances and progressing recursive schema evaluation have ordinary recursive predicates; infinite nonprogressing reference evaluation must not loop.

Unresolved/limited: A same-instance local reference cycle has undefined Boolean validation behavior in JSON Schema Core9.4.1; OpenVerify does not specify a portable accept/reject/error-code rule for it.

Impact: Only exact expectation for nonprogressing cyclic embedded schemas remains blocked; shipped33 root reference closure is acyclic and unaffected.

Owners/interactions: CM.VCP.SCHEMA.SUBSET, CM.VCP.SCHEMA.RUNTIME, CM.PROVIDER.SCHEMA.VALIDITY. Sources: spec/draft/dataflow.md:97-105; https://json-schema.org/draft/2020-12/json-schema-core#section-9.4.1.

### Q.BOOLEAN_ANNOTATION_REFERENCE

Status: SCOPE_AMBIGUITY.

Known: Object reference targets must occupy actual schema positions; supported schema-position booleans are valid.

Unresolved/limited: Provider prose specifically constrains object targets, while SDK membership check also applies only to dictionaries and can admit a boolean under annotation data. Core9.4.2 defines non-schema target interpretation as nonportable. VCP says annotation payloads are not schemas. No portable expected Boolean result is invented for the Provider boolean-annotation corner.

Impact: Provider boolean targets outside recognized schema positions are not certified as either valid supported evaluation or a particular rejection code.

Owners/interactions: CM.PROVIDER.SCHEMA.REFERENCES.SCHEMA_TARGET. Sources: provider-contract/spec/draft/capabilities.md:12-22; src/openverify/provider/validation.py:295-312; https://json-schema.org/draft/2020-12/json-schema-core#section-9.4.2.


## Static implementation/profile findings

These are source findings, not executed Golden failures and not an exhaustive production bug audit. They do not justify weakening source-derived expectations.

- `F.TEXT.PATTERN_LIMIT`: Documented deterministic finding bound is 10000, but pattern_missing appends have no post-pattern count check; config.patterns has no cardinality bound.
- `F.NO_FINDINGS.NULL_EVIDENCE`: Nonempty admitted findings array produces FAIL according to documented no_findings predicate. Capability input schema admits findings:[null]. no_findings passes list to judge; judge wraps every finding as Evidence(structured_data=f). f=null contributes no meaningful Evidence field, so emitted Result fails normative Evidence acceptance.

## Branch verdicts

| Branch | Semantic | Roots | Finite domain refs | Symbolic refs | Conditional refs | Blocking questions | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VCP/Aggregation | 33 | 0 | 1 | 5 | 0 | 1 | INCOMPLETE |
| VCP/Composition | 12 | 0 | 0 | 3 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Computation | 13 | 0 | 5 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Conformance | 2 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Dataflow | 37 | 0 | 5 | 8 | 2 | 2 | INCOMPLETE |
| VCP/Decisions | 1 | 0 | 1 | 0 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Extensions | 2 | 0 | 1 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Knowledge | 3 | 0 | 1 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Lifecycle | 22 | 0 | 3 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Meaning | 6 | 0 | 1 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Policies | 22 | 0 | 4 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Profiles | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Provenance | 28 | 0 | 0 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Provider binding | 12 | 0 | 0 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Resources | 5 | 0 | 0 | 1 | 0 | 1 | INCOMPLETE |
| VCP/Result | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Results | 30 | 0 | 3 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Schemas | 3 | 0 | 0 | 1 | 0 | 1 | INCOMPLETE |
| VCP/Wire roots | 0 | 24 | 0 | 24 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Wire semantics | 9 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Capabilities | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Compatibility | 10 | 0 | 0 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Control | 18 | 0 | 1 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Discovery | 4 | 0 | 0 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Errors | 12 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Events | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Extensions | 3 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Invocation | 6 | 0 | 1 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Lifecycle | 5 | 0 | 1 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Meaning | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Resources | 7 | 0 | 1 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Schemas | 4 | 0 | 0 | 1 | 0 | 2 | INCOMPLETE |
| PROVIDER/Streaming | 11 | 0 | 2 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Transport | 21 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Wire | 2 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| PROVIDER/Wire roots | 0 | 9 | 0 | 9 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Architecture | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Binding | 4 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Binding and execution | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Cancellation | 2 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Discovery | 3 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Entrypoints | 17 | 0 | 1 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Execution | 3 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Extension ports | 7 | 0 | 0 | 3 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Invocation callbacks | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Observability | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Policies | 2 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Preparation | 2 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Process execution | 2 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Providers | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Public API | 9 | 0 | 0 | 1 | 0 | 1 | INCOMPLETE |
| RELAY/Public SDK | 48 | 0 | 0 | 21 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Records | 6 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Scheduler | 5 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Standard providers | 42 | 0 | 0 | 19 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Transport | 4 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| SHARED/JSON value and schema semantics | 2 | 0 | 0 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| SHARED/Public SDK | 70 | 0 | 2 | 40 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |

## Source hashes

| Source path | SHA-256 |
| --- | --- |
| CONTRIBUTING.md | 463bd0bf73b693d1f5612da29cd951114d4173ff38751a507e40979b3b63e1db |
| README.md | 31d60f1ac0405e037ddf0685cc9649865808224b9d01bd7bef6d6ce45c3d2cb9 |
| conformance/README.md | 156d01519fd92322f064c8325822b464d9cb8fdafefeeacfeab67c8c3796a92c |
| docs/relay/architecture.md | 39dd8e1f1266998cef3b1c565398dd0945c991210f9ae83ab445ee9c617840b1 |
| docs/relay/error-contract-hardening.md | a6ad9882b47410f6039ab2940adbf69d8f63ab4be2523b43e294334790ed2d9d |
| docs/relay/graph-authoring.md | 32749238bf11169001e8388cccdcb48f84e2dceae04da27fa58f92c06660cdac |
| docs/relay/integration.md | 139ec04516206e4225fb460091ae2504c171a4d890d6523835797071b67b9c3a |
| docs/relay/limitations.md | d3e704cd8897804b095372b895df7de4a09c7d1c4997d1080e3abc700e4c2969 |
| docs/relay/production-fixes-report.md | 08d56ce3970f3d726b6eb8ae19c30a2267e42892d2921b68bf20d90424cb11f2 |
| docs/relay/providers.md | f066a4343ad905b727ab59b3a9dcb4d3940a0cca0258f615ee98c04f72bd86fa |
| docs/relay/quickstart.md | f373bf0fca3aaf7933de4fd0a924eddccd50cd481554fd5d3dfd15c1d707044f |
| docs/relay/security.md | 9ebb21e72e636235ca387dd017244c5ca16de315011ba99dafc65833e054877d |
| docs/relay/verification.md | 8410d000f3ad586d44df42a37f8883ddcc10dd2f735bc46919d64739906a0c22 |
| profiles/standard-draft/README.md | 19adacdd0c48c7cda6dc1fbcb2b0fe8ec26567ffc7dfc3afd3a28bb2387237c4 |
| profiles/standard-draft/profile.json | e67739ae4a45719b27f661f12a933a9b021fa6164c5bed19f3fc261034651ed4 |
| provider-contract/README.md | 8b4c352be5b8d1d66943fb94e69ba17f72e4dfdc5a6a27530983917c9167de72 |
| provider-contract/conformance/README.md | ce41e7a7fa1a50acc49e062778f05f4a4e4823f5d0083e55d3c02d1afb4f8470 |
| provider-contract/schemas/draft/cancel-request.schema.json | 7e5fe523a3533558a28049c73b927550460bc6f5cddf8b41c3e2de45121379fa |
| provider-contract/schemas/draft/capability.schema.json | 66242f836060a987d7dd7208872630a3ffc9f865b81565410950213d1f667dad |
| provider-contract/schemas/draft/initialize-request.schema.json | e23a6c9c372c72f39cc29443d24c37e70844a6c2d65eb68c2ae0a649137b63da |
| provider-contract/schemas/draft/initialize-result.schema.json | 71686e48b7b398b8efe786dc433c1a2e2f25d311e2ba89e402b22efae062ee62 |
| provider-contract/schemas/draft/invocation.schema.json | f10b9cda14d7f18e58289d981da5b8b8261bfa3d246d71c8cc7c2b473adf24e6 |
| provider-contract/schemas/draft/outcome.schema.json | 7df6c6622b35d483bb42589ff571b061be2cbdd97d85fe4030b6aef6719d85c8 |
| provider-contract/schemas/draft/provider-error.schema.json | eebf40e65a56ddeeda103cf2a18df73eeb65e8a5bdca2733caf84342e4dfe5d9 |
| provider-contract/schemas/draft/provider-event.schema.json | 0bf4bb10e54b99f7c9edd1bcb64d71b2146b164cf3397ceb0a948514263f885e |
| provider-contract/schemas/draft/provider-manifest.schema.json | e2c5c88d4e2c5e906a4218722a791154d847664f86af121d8f747480286cae49 |
| provider-contract/spec/draft/capabilities.md | 9ac03569a88e9982b5a75ceb705daa59cd0ff21aa3ab440d9ee0e3b2afcaa66a |
| provider-contract/spec/draft/errors.md | 421ba6acd25ce220f3cd986f14819bd07034873b4b23cef891149d9657d6d3e4 |
| provider-contract/spec/draft/lifecycle.md | 122e8e4aaa8deb60d0cf6397d9857294d096f063c5c7ecde59d3d0359596177d |
| provider-contract/spec/draft/open-questions.md | 0c0ddb9a1f51619d6b787ceeac452c659a5f4b1f7be71fa33894643d4000bb19 |
| provider-contract/spec/draft/overview.md | b2d0b56c135323accc4927db85b0af447b7f925c4bb8debc00443ec495487807 |
| provider-contract/spec/draft/transports.md | 3d5b5d158363059147706b232ecbc7112a911845b5f22fc3db40ed2d490f0fea |
| provider-contract/spec/draft/versioning.md | 2656dd1dbd2a872bd9d9912b8dba4c2ec61fc4dbaf145d091f7cda1203132921 |
| provider-contract/spec/draft/wire-format.md | 23d1e6bc4518225afa86f422d15eee22214d7a285b369c42c6843f45d06895a7 |
| pyproject.toml | f6cd9f3b0e62fb40631d9c3116d49de2783cd945acc679c02727171ab3bb802a |
| schemas/draft/activation.schema.json | 6e37ab4712eb1e96d5a5ff866f2b27bde808ec51a81dca8b47dfd9e2655b0dc9 |
| schemas/draft/admission.schema.json | bcbcee1094ba855888dc566a48004a0f1ee5d9625e5f94a7138ae293b676953f |
| schemas/draft/artifact-ref.schema.json | 7bf26b3364910fc080867c4cef15e4cb7fd3c416f4fee6b7f2650d01373e1f2d |
| schemas/draft/cancellation-event.schema.json | 9cbac956328c63c971092e1d07c1a9cc49d63b692893ffd4c1ce0fecccf4f641 |
| schemas/draft/decision.schema.json | 47ebf3ea5ab3fd1f4cd434ec2d18981d5593f7f66dd3cdeb9a2f6b15160723ee |
| schemas/draft/evidence.schema.json | e5fe25b8d81739697c6139d5d6e7b541ad6910f58c543a6a90b5f1e9e44a688f |
| schemas/draft/execution-observation.schema.json | 3925c1e9077ecfb9eaa47094325aa4c6c4a22871aadede4f977b06d0fd8115b4 |
| schemas/draft/extension.schema.json | d311028d33dc5062da712c553eb75d61a1f6d9038ec35b6e7a15b6fafaa12abc |
| schemas/draft/graph.schema.json | d363f055c63cf2692a566885b71030da8f8ac9ab2d024798f652c2c3f119d86c |
| schemas/draft/input-port.schema.json | 06bf28b97b7d3c4cb92d058ff2866cc334120c00c5279cba8fda8425c7f9d3c9 |
| schemas/draft/input-resolution.schema.json | b648c5a0866f5c56bbc62e20fa8a93b9ef9c389be522126bb322023a3e35349f |
| schemas/draft/operation-requirement.schema.json | 93f38eb5c2c21f7afcfebc46e05fe36143b7cdcede959ffae69a0e9eee919af0 |
| schemas/draft/output-port.schema.json | 6c4160672d752a4b12340290b6069f305eebaf9d2e7ea4fbb2d61ef1cc25f2bf |
| schemas/draft/policy-evaluation.schema.json | cd4cb6210e17891149edbe908dc1a1daab8abb8f8471e6c14fdaaed45e132806 |
| schemas/draft/profile.schema.json | 1c46b09ba4bb431f5781f8663b30774895fa719fe3ba08753960f3df8478aedd |
| schemas/draft/provider-binding.schema.json | b3230a926aac92122ba09889966dbcbce0985f2b6f37773874c9d5331af4933d |
| schemas/draft/resource-dimension.schema.json | fa4e4bcdc4d442c5db8e19c7e9cfeee041c1f843355454eccbfc0d0132f1bb29 |
| schemas/draft/resource.schema.json | da075a12e91b40d9110f7e5f07ef4aad6a3d4dfcf0edc499219098b7c4cb2145 |
| schemas/draft/result.schema.json | 41625c8616ebb6cbe5da97a88bb8d7e747b40d40db35b82eb0ea4a534a4c2173 |
| schemas/draft/run-record.schema.json | f0d812b54bd748d282e39016885d3776207a7865763969365002e052aca02773 |
| schemas/draft/selection.schema.json | d6c0f5e13bf50425e9b934254188a95a968465dc27774f61187caec77f5000b9 |
| schemas/draft/severity-domain.schema.json | 5451af1a9db01672b874f8d38811ea265f9635fb9f8b9892cfe0f07a693540fd |
| schemas/draft/value-source.schema.json | d2b60c21b86c717dfd76aa10573bd85750aebcf653f93d04b57535e1ae73e3d5 |
| schemas/draft/verification-definition.schema.json | 4830194f7bfc1c33ba1d6f9d977ac402231f9bcc59e2990ab076ba0e7b545294 |
| spec/draft/README.md | 5113269e6de739338601ef897ab253142ff648e8b25060a2d8d5c937ad2fa058 |
| spec/draft/aggregation.md | 9c5599e6c6553ed7da5da13ffe65294c97402be7b6c221c326c7efbf98b8da8d |
| spec/draft/boundary.md | f9b9393c9e16bec7b9cd7ff73997b6e656817486b1e3aaaee3b0d5406cb0dbab |
| spec/draft/composition.md | cd930f696dbfe7c5897930a848f999575241570fbdaa81fa51a167828f7299cc |
| spec/draft/computation.md | 52c89f5f0bd6e87dee5cce3cd3b548fbae49975cce6896df352660215a4b188c |
| spec/draft/conceptual-audit.md | f748fb8da7159456e29ad7750b499481172c957fca7b82f90e8f57a9a2f9cc2d |
| spec/draft/conformance.md | b48dec7685452f8ba47b1896747decf37d247d0e8eabee6e0289b22f87f0c074 |
| spec/draft/dataflow.md | 50c60efcd2701f35d93b05040bc0aef5a2f3dcf8252e026a3df956c4d4554c02 |
| spec/draft/execution-policy.md | 2bb545ce77cbf3790261a35a9955104fecb8c18be1f56e51c1ff0c2d251ce4cf |
| spec/draft/extensions.md | fc57202300c344967487f4d631e7b6bbc99281634a1f4391249ce2a7ec7040d7 |
| spec/draft/knowledge.md | 46dd1dbb4b8ca84d87ada6fa3790eac4891be4814267b764d39fafd0293b4dd3 |
| spec/draft/lifecycle.md | 7a64e510300c0a326985bab7435ed5dd65f3c0745bb003202df6d03c9b52af02 |
| spec/draft/meaning.md | 7dfc04cad4db77ed6eeda32a97f13460b8a271159260b7b3e89ef17e54dec55c |
| spec/draft/open-questions.md | d172d96b92104a6de8eabb1541cdd3bf598b30f076730cb2dbc095ee2f129546 |
| spec/draft/provenance.md | 3e02714727ab1b957df766739e37871362ae1ece47bd7623c7cfe90e5464818a |
| spec/draft/provider-binding.md | 0e0b75547db6e869aaa66d17ba43b5fe4cf2473f3ea7eb344844f332b0b61f8f |
| spec/draft/resources.md | 69fc4771421d8f1672488e7b2266397d0bba6b8a179a08834a9a0b981357ea72 |
| spec/draft/result.md | 14acc3ccf0b4bc26570687be3a9f9a78746deb29007756626c2c1677e9e695ba |
| spec/draft/wire-format.md | e2ff9695699de355d19490a67a27480dbb382c533f8fa408ef404900909e78ee |
| src/openverify/__init__.py | 427a28137cc93d02f536658976e79f838a1a71de11a37a14e653d70280bf6956 |
| src/openverify/adapters/__init__.py | 3f1ce9f105f56fd35e1337f8d7fe508a0078d174926ebd2a8a16734b49144497 |
| src/openverify/adapters/demo.py | b2ceecdf764c31ccf5e72d749ba75af28151a475dc4a193b19c9350839416a01 |
| src/openverify/authoring/__init__.py | 9aad27400ab7bcf602cf253e6c5788d87093f88c889f75e7541dfb8415fb6e06 |
| src/openverify/authoring/graph.py | 48b0dce02e1487ccc3ca51d6a40e5446de78ca4010e95fff81e6217281fb5fad |
| src/openverify/authoring/references.py | 97385c774624753bfde2a0802cefdb98259522ed630c8d98fd767f10e244dd67 |
| src/openverify/cli.py | e1d38334f878c2d825db591e7acb5fb7bfca0b52d3878ae0f8bccbb4dfb0e61b |
| src/openverify/conformance/__init__.py | f99b26c5f9884d0a87b6d024c55762129265edaef42f7879a07a715fe769b5d9 |
| src/openverify/dataflow.py | f61468ce1f934e4d677171f651eb5ccaf9fb1e8145e980cded7c75203e808d8c |
| src/openverify/engine/__init__.py | 10a333e85bc0cd3c779004a0877f53389cbc2e039930d00f6527d44bcecaffd8 |
| src/openverify/engine/admission.py | bdef93be2d243f82c20a887405718b3c8da81127f5ee965b67ee8f142c7acbcb |
| src/openverify/engine/aggregation.py | f2c0824988a07573eec033485969298bf4cf5790bf4627044b2343d62a92833f |
| src/openverify/engine/binding.py | 817805b3f60908e7d66af96953c941f9ac5d292de8ba4000f413dd5b846fd145 |
| src/openverify/engine/policy.py | c612e423b8d0908b775c2e032b26d99bc44dac2972357cf6cad431578f54306b |
| src/openverify/error_codes.py | 11b802c51c53b094e6aa694c5f0962270e399c6a3b356de788b20abac8373d8b |
| src/openverify/errors.py | 2dce7a2f896b8ced248c1b7be8f4ee9ff5bd2dedc96bbb118612c660ecde930a |
| src/openverify/fingerprint/__init__.py | f5ced653c2ba3ea6aa54dda046b3b6c8d1c13e290c0e97ab2fa4385dd6895d34 |
| src/openverify/inspection.py | 24da3a1930d931e2307906a12b8bb60ced0e2635023801365595215af4824c8d |
| src/openverify/json_schema.py | b5152f0faf46997b91fb312eca5cefc552c1dbad7dee8c1b0f17b8658eab1a24 |
| src/openverify/lifecycle.py | 4d32fcb3bb4cbad17ceae9e05f9a81ccdc1952a350112844808aeeef8430ffba |
| src/openverify/model/__init__.py | 9b71e732e4304d9ddf8fce98ea6f8dc941b1c44f3cf73f72d6959a2012aae805 |
| src/openverify/policy.py | 86f96763583dfc1d91e2f0169db51ff0a9ca793c556d041d098bdfd160a1c485 |
| src/openverify/provenance/__init__.py | d70976288aaa16e48ae0cc462c0d18b521148b2e6f8a90b5f73b1dab9dd720fa |
| src/openverify/provider/__init__.py | 65fb1f6e8f1ad95404077dc11a16b78d6392fa31298b361db4409558e8d27af9 |
| src/openverify/provider/conformance.py | 678bc1b2d1b4b4365d826dc12ac9d88616023b9d0c70f0298c3baaf36932db9f |
| src/openverify/provider/lifecycle.py | f8456c8f8988a9e9af16a6bf92b435ada182fdc3dc00799b3c119288d82ba4d4 |
| src/openverify/provider/model.py | 3ac0e970a0eb77358a7f1c775fe17f2c0442ad46fa68e4abcd74c5ef29dc5f36 |
| src/openverify/provider/stdio.py | 580faa7347627657f75e0bce7318fc5bfa4b72409c4e0dc1b707c43661243d79 |
| src/openverify/provider/validation.py | c087fa9fd79a68d4907322a5173acc9c31453570f679f1942d3066499d416be4 |
| src/openverify/provider_codes.py | 8c920dcfbb0c00e1eeb7d776be4719128ddeeb8021ca3e0c1b2e489d12dc23ec |
| src/openverify/relay/__init__.py | 4aa20cfa0974c516fd9f06622693c45bf518287b3e8be98d5085cb648c2a76bd |
| src/openverify/relay/adapters/__init__.py | a851473aac79e9bc3c846d4a06937e253ad7c08d01857043fb5b0a4904913b29 |
| src/openverify/relay/adapters/binder.py | 3e7b6726db45b2c1f0b0ba5ca041ce42de050c09e331f7ec8448cf408cef5590 |
| src/openverify/relay/adapters/catalog.py | 99b2b48d7b6abb55d1e9445817d0d51743b26fce2be1d89b8234106f8ef00476 |
| src/openverify/relay/adapters/inprocess.py | 5d5bbe5f9de841cb4ac3a152614164f45390858fd9119dd4839da4d8dafe456d |
| src/openverify/relay/adapters/jsonl.py | a1c424fac3cafc8067dfa6a2a1b29322f5f04eee849f932f7aa70d80ca5f8f58 |
| src/openverify/relay/adapters/local.py | 614ace847fd560405d3b89d44115ef90efc28b979935218f44079b98af3f6fbf |
| src/openverify/relay/adapters/logging.py | 962df25c768f6ac9c006e0b3006bb9c8e30b26064ffc7adaa0349b27a1eb75db |
| src/openverify/relay/adapters/memory.py | 61972d7f49bc9c0421a81a7259ffd16a71fcca4bacba46b5e23ddd8d441652ad |
| src/openverify/relay/adapters/process.py | 0f43102c2dd6c43fd12068a70bb8d789b75c55c6b8ac71fa3c7090f6a61c6214 |
| src/openverify/relay/adapters/server.py | 2809b840229320a8706c4266da06168408ae0ded3413a38706ec9caf2c051b18 |
| src/openverify/relay/adapters/stdio.py | a1bd23c4f597626cd3adf4d323f67e479345fa5ce740c505e0173ac3a3792968 |
| src/openverify/relay/adapters/windows_job.py | 8d19c67b06e7a4ec1bbe5b70523a3a61a66cbb723845dfd61856fefbafa811b7 |
| src/openverify/relay/api.py | 3b01df667b8272016b0bd177defce7b5cfa33dfad238a945021782c3cc3f6549 |
| src/openverify/relay/application/__init__.py | a39172ecc2173839ea51bfefe8f749e50d275d4118788541c60a8d67ae26e7e5 |
| src/openverify/relay/application/binding.py | 0be39eaa0aa1c4ca84ec64b75098d6d9b470b7158cbdc568ccd5d0b691f3cfb3 |
| src/openverify/relay/application/contract.py | 4385a847188853cf05010b9e588bc001ddbde8b3679ce3df02af080ec0af7f34 |
| src/openverify/relay/application/execution.py | 948c3be317f68e74be00426550807791eb3a3147b1b8c18fdeb0cc0773292183 |
| src/openverify/relay/application/policies.py | fee622397d05f8f3cc4630a86ea91262f11a9d6c1a13447f7946bfe0d81c68aa |
| src/openverify/relay/application/preparation.py | 6234f7c08f723a629fbdc8e345f12d5dbe2bef698dc9f7f47d6687dcbb042429 |
| src/openverify/relay/application/run.py | a958f472edd9ce6644ca3f2f2b08e082ef04e07b6c4c8d3baacb1652cf92f249 |
| src/openverify/relay/config.py | 0baac5f1e572475560f0e62b555540423cdb549038d206f5634adcbb93e1d551 |
| src/openverify/relay/core/__init__.py | c6130bc3323b8549815977495758720c28f27e7fc277558f4b5e26a49390e9a3 |
| src/openverify/relay/core/aggregation.py | 1cfa76d89c54d40d477a6be4b280cf23c18a01559bd6cc8036dc1ca6e1b27da6 |
| src/openverify/relay/core/readiness.py | 7975b54522437f833d43f0b33dc37346988459c9da9f4acd36c4b6e26d87c08b |
| src/openverify/relay/core/state.py | 8da362b801c62687041e9b27218c59b2a6b3fb2bbc6589d02ed57807b8102e57 |
| src/openverify/relay/entrypoints/__init__.py | f6df74eb909aaa95457f7b89ad94eefe57d6e9e3360d8144d8a710c9f771718e |
| src/openverify/relay/entrypoints/cli.py | ce61e293fb4f12bc2f9bed02bf89a81b9cb8084ac8085e8e41b48c5e375a6d47 |
| src/openverify/relay/entrypoints/http.py | abb2644b25d8bfefe10fdb0f1869e36103325217223af108f8bcb88415e669d2 |
| src/openverify/relay/entrypoints/mcp.py | 26dbd8c469550e5826b7d7dda2ad5f4e80e7f25e0db1c455b6678b67ee235b9d |
| src/openverify/relay/entrypoints/service.py | 0accc0770270fe8ea7c5229244da2cf9074218caf085f133d4b4b3527f04700d |
| src/openverify/relay/error_codes.py | d12a354eaa8cb5f769af97acba6e3cd46d06a76436de78e14bab4e12e15c98fc |
| src/openverify/relay/errors.py | a1564afe96238e3ba22dd89c17bbe22f8c14df80655c02e7ad185fc82ad82c2e |
| src/openverify/relay/ports/__init__.py | 5d8626535f199d406cdb6fe93457155defbe6f4666063cf7fd892642229dd778 |
| src/openverify/relay/ports/binding.py | 335d3c7ba4040fbc944d7e8a51ec33858fcb6033c47f6bd322abd83d2953e404 |
| src/openverify/relay/providers.py | c3b967ff59c7c3fbd6abb65da9b74292504f81ff04df0b24116a923704289d2c |
| src/openverify/relay/templates.py | b7f12cb3e289dd582ced7ee3aa7b9d319f9453b5c256c44641fab475af953c74 |
| src/openverify/serialization/__init__.py | 7a2f46c623f94a81925d12d8e92f446db440f2415508f0db4ae6e06e542a7110 |
| src/openverify/standard/__init__.py | 2ad7f0c2cf4ae6a03f1a7939f1df2b51947519485fc5248858705482fdd5e96f |
| src/openverify/standard/astgrep.py | ae28d7f38f65a96580fa41c86518321086ddc8be0d86fde4fcfcdd1321e7b2e6 |
| src/openverify/standard/command.py | 1532d1dfb2f3a6820bcb26458d589b422562dbbe34fc4ebff6df39a41eab1b52 |
| src/openverify/standard/common.py | bc55d0c0bb9c0e134b0564b6e72ad1fb6cd4a2d4a61c497fb5d6e58c3bfa6f0b |
| src/openverify/standard/control.py | 5ae8c4250ac674ffd11a81f5049633468b788b103a0749106b1d1eda4a67a8ab |
| src/openverify/standard/filesystem.py | 8e72d8e8a03c78677d1ff1582fbde88eeb072c3f2f3975b8fdcfca4b25f8f85e |
| src/openverify/standard/git.py | 9ff2cee66ebaccb377bd325a6ec879f18fa473e43f54274004c7017d8673b218 |
| src/openverify/standard/paths.py | 4f450710e1ff08464ca8e6e27a3f96926169a96111241071fa3e6c6b67d711d2 |
| src/openverify/standard/pattern_worker.py | 4b7085e919688799c00b894bd9ae22d981188abe9f4e7504bca84d27b66085d2 |
| src/openverify/standard/pytest.py | 4306df9f9a1f7aa274805bdf49f1013dd870fac71c5fc8e1719125fa2116d692 |
| src/openverify/standard/ruff.py | f1ba8ae9c316f96e0d56a4fe1a66a490db8e354617633af36f68bce7a27c4c52 |
| src/openverify/standard/scope.py | 935b8b2996a0f6416c4292f2155a5e4220295fe49728c944b51bf59699482ab6 |
| src/openverify/standard/structured.py | 8930b3d022eee59a86fe7d57f5bb29b04a1d54e83c795a25ad3c7b805c5d188a |
| src/openverify/standard/text.py | 98eab2a5ca35d2a79a3182e1c60c64073369f6a516b6c398f9661af2cc54d22e |
| src/openverify/standard/tools.py | 98b9b073b3776dd0e4119e98219fe7cd8968702b184f531cac19b266f51831c9 |
| src/openverify/validation/__init__.py | cef5aa3510c1657692209d8fb9c8bb06377ddafacb4c7f267e3b52868da6cfc8 |

## Verification limits

Integrity checks verify JSON parsing, unique IDs, real source hashes/line bounds/pointers, root normalization, enum/constant agreement, source/declaration classifications, reverse canonical links, arithmetic and schema-copy identity. They do not infer semantic closure from line accounting or test counts. External standards are versioned references used within the declared subset, not vendored bytes or a claim to audit every external standard clause. Relevant JSON Schema caveats: [Core9.4.1](https://json-schema.org/draft/2020-12/json-schema-core#section-9.4.1), [Core9.4.2](https://json-schema.org/draft/2020-12/json-schema-core#section-9.4.2); the transport delegates to [JSON-RPC2.0](https://www.jsonrpc.org/specification) under the repository binding restrictions.

No test suite, Relay integration, provider process or installed tool was run. No Golden tests/fixtures were generated or mapped. No frozen expectation, production, specification or earlier canonical-review file was changed. Full supported-profile semantic closure is NOT CERTIFIED while the explicit blocking questions remain.
