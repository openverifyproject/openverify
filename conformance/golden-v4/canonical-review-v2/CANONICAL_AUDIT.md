# Canonical v2 final semantic closure audit

The approved normative decisions supersede the two earlier blockers. Worktree .worktrees/vcp-final-semantics, branch integration/vcp-final-semantics; baseline d45dcffa56d8bf2eadc98bbe588c5c617af353eb. Existing Golden and SDK worktrees were preserved. Prior investigation remains in Git history and the JSONL reconciliation records.

| Layer | Semantic requirements | Whole-root predicates |
| --- | --- | --- |
| VCP | 242 | 24 |
| PROVIDER | 106 | 9 |
| RELAY | 161 | 0 |
| SHARED | 73 | 0 |

## Gate verdicts

| Gate | Verdict | Evidence and precise scope |
| --- | --- | --- |
| 1 Semantic source closure | PASS | Baseline162-file source-first audit retained. Targeted changed prose reviewed with complete dataflow/aggregation/lifecycle/provenance/wire context; new source units assigned existing canonical owners.582 IDs preserved. |
| 2 Whole-schema closure | PASS FOR DECLARED SUPPORTED DOMAIN | All33 existing whole-root predicates and724 schema components retained. No schema or wire field changed. Undefined nonprogressing/non-schema-target Boolean results remain outside the upstream defined domain; nonlooping MUST retained. |
| 3 Behavioral mathematics | PASS FOR DECLARED SUPPORTED DOMAIN | Custom ordered n=0 has0!=1 legal structural list; standard empty reduction rejects. Snapshot relation total/disjoint over80 supported equivalence contexts and240 legal handler combinations. No finite count of arbitrary JSON/schema/graph traces asserted. |
| 4 Independent audit reconciliation | PASS TARGETED CHANGES AGAINST BASELINE AUDIT | Source-first baseline comparison retained; independently authored partition predicates checked for exactly one match. Current fragments/hashes/owner links reconciled. This continuation is not another whole-repository traversal or a proof of implementation correctness. |

## Exact resolved rules

CM.VCP.AGG.MEMBERS.COMPLETE owns custom empty structural membership with exact Constant members=[]; CM.VCP.AGG.NONEMPTY applies to standard reducers. Required subject/criterion/member snapshot, capability eligibility, output/Result acceptance and provenance are unchanged. Unavailable declared members never vanish.

CM.VCP.DATA.RESOLVE_ALL owns the snapshot classifier. Branches: nonupstream absent/value; declared Result producer/consumer schema checks; other accepted outputs; unstarted NONEXECUTED; interrupted CANCELLED; rejected completed ERROR attempt with present/omitted requested port; other ERROR; other finalized absence. Checks occur on persisted snapshots/reconstructed acceptance, never historical rejection order. Handlers are subsequent functions retaining original source/status/value/default; node lifecycle reasons keep their existing precedence. CANCELLED is never reinterpreted as noninvocation. No new terminal state/barrier/event history.

The proof enumerates source-specific disjoint contexts, all seven permitted kind-role pairs, all terminal states where applicable, producer/consumer schema evaluation applicability and three legal handlers.16 AVAILABLE+25 INVALID+2 ABSENT+5 PRODUCER_NOT_EXECUTED+20 OUTPUT_MISSING+12 PRODUCER_ERROR=80 quotient contexts. An actual supported value is projected by its source/role/state and acceptance predicate, so unbounded payload choices do not introduce another branch. Malformed declarations/records are rejected separately.80*3=240 handler relations. The executable Python proof and exact context list are in CANONICAL_MATH.md. It does not assert the Python resolver implements them; new tests show mismatches.

## Preserved scope limits

| Question | Status | Effect |
| --- | --- | --- |
| Q.CUSTOM_AGG_EMPTY | RESOLVED_BY_EXPLICIT_NORMATIVE_DECISION | Resolved; no blocked supported semantic subspace. |
| Q.RELAY_TIMING_KEY | RESOLVED_AUTHORITY_AND_OPTIONAL_NAMING | Remove the ambiguity from CM.RELAY.API.VIEWS.USAGE and CM.VCP.RES.WALL_TIME.SEPARATE. Do not declare implementation correctness: the two-key overwrite counterexample remains. |
| Q.AVAILABILITY_OVERLAP | RESOLVED_BY_EXPLICIT_NORMATIVE_DECISION | Resolved; no blocked supported semantic subspace. |
| Q.ROUNDING | UNBOUNDED_PRECISION_LIMIT_NO_BITWISE_REQUIREMENT | Keep the algebraic oracle; exclude a universal portable float-bit/tolerance oracle. Local reference arithmetic may be checked as a local algorithm only. Domain still unbounded. |
| Q.DEFAULT_UNUSED | RESOLVED_BY_STRUCTURAL_AND_PROSE_CONJUNCTION | Close the two portable coordinates. Correct D.PORT.REQUIREDNESS_DEFAULT_JOINT from V3/I7/Q2 to V5/I7/Q0; preserve DEFAULT-only presence projection and schema-value obligations. This is a justified canonical interpretation correction, not a normative source edit. |
| Q.VERSION_FUTURE_INTERSECTION | UNSUPPORTED_FUTURE_PROFILE_LIMIT | Retain current supported behavior and exact local helper algorithm. Future protocol session semantics excluded; arbitrary string/list cardinality unbounded. |
| Q.NONPROGRESSING_SCHEMA_REFERENCE | EXTERNAL_UNDEFINED_SCOPE_EXCLUSION | Exclude only the upstream-undefined Boolean-result subspace from portable result classification; retain the no-infinite-loop safety requirement. This does not prove current validators terminate or that a recursion exception is an appropriate portable error. |
| Q.BOOLEAN_ANNOTATION_REFERENCE | EXTERNAL_UNDEFINED_SCOPE_EXCLUSION | Portable Provider evaluation result for annotation Boolean targets is excluded, not counted invalid by inference. VCP annotation-target rejection remains source-supported. SDK source admits those Boolean targets at the position-membership check; that is local behavior and does not define portable semantics. |

## Integrity and completeness limits

Current source aggregate SHA-256: 3c7694fc35900f93380bdf26ed345b54c51935c8f532a651c464d3144f3e9ad0. Per-file hashes and source-fragment hashes were updated after prose insertions, with previous changed fragment digest retained. Original33 root predicates unchanged. Existing source counts162 files,122 section positions,409 original prose units,1588 schema positions,366 declaration candidates/55 exports describe the baseline index; new decision clauses are additionally indexed without pretending those location counts are semantic requirements.

No production or SDK code changed. Canonical semantic closure is separate from complete Golden assertion mapping. The reconciliation report outside this directory explicitly reports unreviewed test links and failing regressions. No canonical gate PASS authorizes implementation certification. Prior four static implementation findings and rounding/future-version scope limits remain in SOURCE_CROSSWALK.jsonl; neither these two decisions nor the proof repairs production.
