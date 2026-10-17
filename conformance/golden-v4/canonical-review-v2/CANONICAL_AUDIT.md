# Canonical v2 final-blocker investigation

CURRENT NORMATIVE UPDATE: both supported blockers are resolved by explicit approved prose. All four canonical gates PASS for the declared supported semantic domain. This is not implementation certification. Existing scope exclusions (undefined schema evaluation, future versions, portable float bits) remain. Counts:582 semantic IDs,33 whole-root predicates,86 finite/150 symbolic/1 dependent conditional domains; no new IDs.


Continues commit 0723fa8a8766bcfdd3c2c5e5a8559a70befca3b7. This is an in-place, targeted source investigation, not another inventory or a newly claimed full source traversal.

## Mandatory preflight

Main checkout remains on test/openverify-golden-fast-v0.3.1 at the specified canonical commit. Its existing untracked work was preserved. The clean existing .worktrees/golden-v4 branch diverged and could not fast-forward; it was left unchanged. The isolated active worktree is .worktrees/canonical-v2-blockers, branch review/canonical-v2-blockers, created directly at0723fa8a. All six review files existed before edits. The parallel language-sdks worktree was not entered or modified. No main checkout reset/overwrite, production/specification/test/expectation edit, push or merge was performed. The attempted fast-forward refused without changing the Golden worktree.

## Current counts and justified correction

All 581 existing semantic requirement IDs and all 33 whole-schema predicates are preserved. One overbroad Provider proposition was narrowed to its actual object-target authority: CM.PROVIDER.SCHEMA.REFERENCES.SCHEMA_TARGET. One previously unowned referenced-standard MUST was added: CM.SHARED.SCHEMA.EVALUATION.NONLOOPING (Core2020-12 section9.4.1). Recording undefined Boolean behavior only as a limitation must not erase that independent nonlooping obligation.

There are now 582 semantic requirements and 33 whole-schema predicates. Of the semantic records, 577 have no flagged blocked subspace and 5 carry a precisely scoped flag for the two remaining normative questions. This is not a test-coverage or universal correctness count. The 724 local schema components remain parts of whole-root predicates, not extra semantic requirements.

| Layer | Semantic requirements | Whole-root predicates |
| --- | --- | --- |
| VCP | 242 | 24 |
| PROVIDER | 106 | 9 |
| RELAY | 161 | 0 |
| SHARED | 73 | 0 |

Mathematics: 86 named finite domains, 150 symbolic domains, 1 conditional domain.44 additional leaf quotients and54 standard-capability declared-name projections are scoped separately. No overlapping candidate sum is reported. The InputPort full joint domain is now12=5 valid+7 invalid+0 inapplicable, with zero unresolved presence coordinates. The SDK's additional iff predicate has3 valid/9 invalid; these are different authority predicates.

## Gate status

| Gate | Status | Evidence and limit |
| --- | --- | --- |
| 1 Semantic source closure | PASS WITH TWO EXPLICIT QUESTIONS | Prior314 prose/366 declaration backlog closure retained; targeted source interpretation reconciled here. Custom-empty scope and availability priority remain explicitly unresolved, not unreviewed. |
| 2 Whole-schema semantics | PASS FOR DECLARED INTEROPERABLE DOMAIN | All33 normalized shipped roots retained. Standard-defined undefined evaluation results excluded explicitly; they are not converted to invalid-schema classifications. Nonlooping invariant retained. No production validator correctness claim. |
| 3 Behavioral mathematics | PASS FOR DECLARED SEMANTIC SCOPE | Typed cause-to-status priority and custom zero-member semantics remain unresolved. Other investigated domains/limits are classified; unused-default coordinates closed. |
| 4 Independent source audit | BASELINE PASS RETAINED; TARGETED CORRECTIONS RECONCILED | The complete source-first audit at0723fa8a is retained. This continuation is not advertised as a fresh complete traversal. Current primary IDs have comparison owners, including the newly identified Core MUST. Full-profile semantic closure remains incomplete. |

## Final-blocker disposition

| Issue | Current classification | Exact decision needed |
| --- | --- | --- |
| Q.CUSTOM_AGG_EMPTY | GENUINE_NORMATIVE_AMBIGUITY | State whether the nonempty rule applies to every custom Aggregate or only standard reducers. If universal, specify declaration-time rejection versus invocation failure and the error category; if custom-owned, explicitly allow [] structurally. |
| Q.RELAY_TIMING_KEY | RESOLVED_AUTHORITY_AND_OPTIONAL_NAMING | No normative naming decision is needed. A future production fix must preserve arbitrary preexisting dimensions, including both timing keys. Choosing a new collision-free local representation/name policy is implementation work outside this task. |
| Q.AVAILABILITY_OVERLAP | GENUINE_NORMATIVE_AMBIGUITY | Define one normative cause-to-status classifier/priority for unavailable declared outputs, including interrupted CANCELLED producers, and specify whether raw observed candidate validity is consulted before or after producer terminal cause. Preserve schema-rejected Result-port INVALID and valid bookkeeping Result AVAILABLE rules. |
| Q.ROUNDING | UNBOUNDED_PRECISION_LIMIT_NO_BITWISE_REQUIREMENT | Only if a cross-language numerical fidelity guarantee is wanted: choose numeric representation and rounding/error contract normatively. No such new guarantee is needed to preserve the current local reference arithmetic contract. |
| Q.DEFAULT_UNUSED | RESOLVED_BY_STRUCTURAL_AND_PROSE_CONJUNCTION | No normative decision is needed to classify the current written contract. To make the SDK iff portable, explicitly amend the normative conditional rule in a separately authorized task; do not silently add it to this model. |
| Q.VERSION_FUTURE_INTERSECTION | UNSUPPORTED_FUTURE_PROFILE_LIMIT | None for current0.1. A future multi-version protocol/profile is separate work; do not add fallback here. |
| Q.NONPROGRESSING_SCHEMA_REFERENCE | EXTERNAL_UNDEFINED_SCOPE_EXCLUSION | No decision is required to stop claiming a portable Boolean oracle for externally undefined behavior. If OpenVerify wants its own policy, explicitly choose a reject-at-load subset, cycle-aware runtime error, or defined fixed-point semantics plus codes in a future normative change. |
| Q.BOOLEAN_ANNOTATION_REFERENCE | EXTERNAL_UNDEFINED_SCOPE_EXCLUSION | No decision needed for portable scope exclusion or the corrected object-only source rule. If universal OpenVerify rejection of Boolean annotation targets is desired, add an explicit Provider subset rule and align both local validators in a separately authorized task. |

## Six blocker investigations

### Q.CUSTOM_AGG_EMPTY

**Verdict:** STANDARD_EMPTY_REJECTION_ESTABLISHED; CUSTOM_ZERO_MEMBER_SCOPE_UNRESOLVED.

Affected canonical IDs: `CM.VCP.AGG.MEMBERS.COMPLETE`, `CM.VCP.AGG.NONEMPTY`.

Blocked subspace owners: CM.VCP.AGG.MEMBERS.COMPLETE.

Sources: spec/draft/dataflow.md:127-140; spec/draft/aggregation.md:10-18; schemas/draft/graph.schema.json:50-56; src/openverify/dataflow.py:169-204; profiles/standard-draft/README.md:11-17.

Established: Standard reducer empty input and empty retained input are invalid (AGGREGATE_INPUT). Custom ordered structural membership, identity and subject/criterion/members snapshots are fully established. The graph root has no aggregate_inputs minItems.

Scope/remaining uncertainty: Aggregation prose introduces the standard reducers before its unqualified empty-input sentence; dataflow shares structural membership with custom Aggregate without explicitly specifying custom nonemptiness. Result* alone does not resolve the scope of that prohibition or definition-time versus invocation-time rejection.

Concrete example 1:

```json
{
  "alternative_A": "Definition valid; invoke custom capability with members=[] and no member Result inputs. Capability specification owns empty-list result.",
  "alternative_B": "Reject custom definition as empty membership; no invocation.",
  "alternative_C": "Accept declaration but reject an empty reduction when invoked. No universal custom error category is assigned.",
  "context": "Otherwise valid single custom AGGREGATE node; fixed valid subject/criterion Constant bindings and exactly one result port.",
  "delta": {
    "aggregate_inputs": [],
    "members_binding": {
      "kind": "CONSTANT",
      "value": []
    }
  }
}
```

Mathematics:

```json
{
  "derivation": "For n distinct eligible member identities, n! orders. n=0 gives 0!=1 structural list, whose custom semantic classification is unresolved. Standard reducer retained cardinality k=0 is invalid; k>=1 is eligible subject to the reducer rules. No count of arbitrary custom capabilities exists.",
  "domain": "D.AGG.MEMBERSHIP"
}
```

Decision needed: State whether the nonempty rule applies to every custom Aggregate or only standard reducers. If universal, specify declaration-time rejection versus invocation failure and the error category; if custom-owned, explicitly allow [] structurally.

Existing assertion evidence (static inspection only):

- tests/unit/test_aggregation.py:91-91 `test_empty_rejected`: Asserts standard direct reducers reject []; cannot distinguish custom zero-member semantics or its rejection phase.
- tests/relay/test_semantics.py:121-121 `test_custom_aggregate_receives_exact_ordered_members`: Asserts a two-member custom invocation receives [second,first]; cannot distinguish empty alternatives.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

### Q.RELAY_TIMING_KEY

**Verdict:** NO_NORMATIVE_SAME_UNIT_BLOCKER; CURRENT_LOCAL_KEY_RULE_ESTABLISHED.

Affected canonical IDs: `CM.RELAY.API.VIEWS.USAGE`, `CM.VCP.RES.WALL_TIME.SEPARATE`.

Blocked subspace owners: none.

Sources: docs/relay/architecture.md:78-83; src/openverify/relay/application/execution.py:141-194; spec/draft/resources.md:5-18.

Established: VCP requires retaining executor usage and own EXACT-second monotonic duration separately; no implicit sum. Relay docs require the alternate key for a different-unit wall_time but do not say if-and-only-if. The local implementation selects relay_wall_time whenever wall_time exists, including same-unit usage. That local naming rule is inspectable but is not portable VCP semantics.

Scope/remaining uncertainty: None for the two canonical propositions: usage views preserve per-node units; executor usage and runner duration remain distinct. Exact same-unit spelling is not uniquely prescribed by normative VCP. A simultaneous two-key collision is a separate static implementation defect, not a semantic naming ambiguity.

Concrete example 1:

```json
{
  "local_source_rule": "node.usage.wall_time remains provider 2; relay_wall_time is own duration in s.",
  "provider_usage": {
    "wall_time": {
      "kind": "EXACT",
      "unit": "s",
      "value": 2
    }
  },
  "required": "Keep provider 2 s and a separate runner duration; do not add/overwrite it."
}
```

Concrete example 2:

```json
{
  "provider_usage": {
    "wall_time": {
      "kind": "EXACT",
      "unit": "ms",
      "value": 2
    }
  },
  "required": "Provider ms retained; separate own s; documented alternate key relay_wall_time."
}
```

Concrete example 3:

```json
{
  "provider_usage": {
    "relay_wall_time": {
      "kind": "EXACT",
      "unit": "J",
      "value": 7
    },
    "wall_time": {
      "kind": "EXACT",
      "unit": "s",
      "value": 2
    }
  },
  "required": "Retain both authored measurements and own duration separately.",
  "static_observed": "usage[timing_key] overwrites the provider relay_wall_time=7 J. The original observation still contains it, but NodeRecord.usage no longer does."
}
```

Mathematics:

```json
{
  "domain": "D.RESOURCES.SEMANTICS",
  "local_key_projection": "wall_time absent/present -> wall_time/relay_wall_time, two deterministic local branches. Across arbitrary resource maps: if chosen own-duration key is already occupied, assignment loses that entry. Finite support and unit/value domains remain unbounded. No portable total or specific collision-free spelling is invented."
}
```

Decision needed: No normative naming decision is needed. A future production fix must preserve arbitrary preexisting dimensions, including both timing keys. Choosing a new collision-free local representation/name policy is implementation work outside this task.

Existing assertion evidence (static inspection only):

- tests/relay/test_semantics.py:58-58 `test_invalid_semantic_output_retains_measured_usage`: Checks tokens, provider wall_time in ms and runner relay_wall_time in s. It does not exercise same-unit wall_time or both keys already present.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

### Q.AVAILABILITY_OVERLAP

**Verdict:** HANDLER_EFFECTS_ESTABLISHED; COMPLETE_CAUSE_TO_STATUS_PRIORITY_UNRESOLVED.

Affected canonical IDs: `CM.VCP.DATA.BOOKKEEPING`, `CM.VCP.DATA.RESOLVE_ALL`, `CM.VCP.DATA.RESOLVE_BLOCK.RESOLUTION`, `CM.VCP.DATA.RESOLVE_DEFAULT.PROVENANCE`, `CM.VCP.DATA.RESOLVE_OMIT.PROVENANCE`.

Blocked subspace owners: CM.VCP.DATA.RESOLVE_ALL, CM.VCP.DATA.RESOLVE_BLOCK.RESOLUTION, CM.VCP.DATA.RESOLVE_DEFAULT.PROVENANCE, CM.VCP.DATA.RESOLVE_OMIT.PROVENANCE.

Sources: spec/draft/dataflow.md:107-118; spec/draft/lifecycle.md:22-24; spec/draft/lifecycle.md:53-55; src/openverify/dataflow.py:336-383.

Established: All six status labels, usable versus unusable publication, exact handler effects and per-input provenance are established. Valid ERROR/nonexecuted EVALUATE/AGGREGATE Result ports remain AVAILABLE when both schemas admit them. Guard/admission/cancellation precedence does not erase the obligation to record every input resolution.

Scope/remaining uncertainty: No normative total priority maps simultaneous producer ERROR, output absence and rejected value to exactly one original availability label. Interrupted CANCELLED INFORMATION/DECISION publication is forbidden, but its unavailable status label is not assigned.

Concrete example 1:

```json
{
  "context": "P declares INFORMATION x:integer. A local authored output attempt omits x, so the attempt becomes ERROR and no information publishes.",
  "question": "For C bound to P.x, must original status be OUTPUT_MISSING or PRODUCER_ERROR? This is a cheap local acceptance/record example, not a demand for malformed external Provider events."
}
```

Concrete example 2:

```json
{
  "context": "P declares INFORMATION x:integer. Local attempted x=\"bad\" is rejected, so P becomes ERROR with raw observation retained.",
  "question": "For C bound to P.x, INVALID versus PRODUCER_ERROR is not explicitly prioritized. Raw x cannot be consumed under either alternative."
}
```

Concrete example 3:

```json
{
  "context": "A compliant cancelled/interrupted producer has no accepted INFORMATION x. Descendant C is also cancelled by lifecycle precedence.",
  "question": "Every C input still has a resolution; is original status PRODUCER_NOT_EXECUTED, PRODUCER_ERROR, OUTPUT_MISSING or another explicit mapping within the existing six-label domain? Node cancellation reason is already determined."
}
```

Mathematics:

```json
{
  "candidate_count": "Dependent sum of Reach(definition,trace,port); unbounded across schemas/values/graphs. Never a source*status*handler flat total.",
  "determined_law": "For each specified unavailable status and each legal handler: BLOCK preserves status/no value/no invocation; OMIT preserves status/omits key; DEFAULT preserves status/substitutes validated exact default with used_default=true. The policy/lifecycle precedence separately chooses node reason.",
  "domain": "D.TYPED_AVAILABILITY",
  "unresolved": "Cause-to-status mapping on the three illustrated classes, and their overlapping-cause extensions. No fabricated numeric classification total."
}
```

Decision needed: Define one normative cause-to-status classifier/priority for unavailable declared outputs, including interrupted CANCELLED producers, and specify whether raw observed candidate validity is consulted before or after producer terminal cause. Preserve schema-rejected Result-port INVALID and valid bookkeeping Result AVAILABLE rules.

Existing assertion evidence (static inspection only):

- tests/integration/test_typed_dataflow.py:105-105 `test_required_information_availability_reasons`: Already asserts missing->OUTPUT_MISSING, invalid->INVALID, error->PRODUCER_ERROR, unstarted->PRODUCER_NOT_EXECUTED. These assertions distinguish those local implementation choices; their existence cannot settle portable priority.
- tests/relay/test_concurrency.py:124-124 `test_cancellation_observed_before_output_acceptance_wins_completion_race`: Asserts cancelled producer and empty information. Does not assert descendant input-resolution status for an interrupted producer.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

### Q.DEFAULT_UNUSED

**Verdict:** PORTABLE_UNUSED_VALID_CONSTANT_PERMITTED; SDK_IFF_RESTRICTION_IS_ADDITIONAL.

Affected canonical IDs: `CM.VCP.DATA.DEFAULT.CONSTANT`, `CM.VCP.DATA.PORT_HANDLING`.

Blocked subspace owners: none.

Sources: spec/draft/dataflow.md:20-33; src/openverify/dataflow.py:36-45; schemas/draft/input-port.schema.json:1-50; spec/draft/dataflow.md:97-105.

Established: InputPort explicitly declares optional Constant default with no conditional exclusion. Prose fixes requiredness/handler pairs and requires an explicit Constant for DEFAULT (a one-way implication), and statically validates defaults. No normative rule says default is present iff handler is DEFAULT. A supplied valid Constant on legal BLOCK/OMIT is therefore not invalid merely because unused; it never changes those handler effects.

Scope/remaining uncertainty: The old review imported an unexpressed converse as a possible portable restriction. The conjunction of current structural and semantic predicates classifies these two coordinates without that converse. SDK validate_port implements the stronger iff and rejects both as DATAFLOW_BINDING; keep that extra local behavior separate.

Concrete example 1:

```json
{
  "local_SDK": "validate_port raises DATAFLOW_BINDING due to the iff test.",
  "port": {
    "default": {
      "kind": "CONSTANT",
      "value": 7
    },
    "name": "x",
    "on_unavailable": "BLOCK",
    "required": true,
    "schema": {
      "type": "integer"
    }
  },
  "portable": "Valid declaration. An unavailable required value BLOCKs; do not insert 7.",
  "precondition": "Node x otherwise has a valid explicit source binding; or this is a valid run-input declaration."
}
```

Concrete example 2:

```json
{
  "local_SDK": "validate_port raises DATAFLOW_BINDING.",
  "port": {
    "default": {
      "kind": "CONSTANT",
      "value": 7
    },
    "name": "x",
    "on_unavailable": "OMIT",
    "required": false,
    "schema": {
      "type": "integer"
    }
  },
  "portable": "Valid declaration. Unavailable x is omitted with used_default=false; do not insert 7."
}
```

Concrete example 3:

```json
{
  "port": {
    "default": {
      "kind": "CONSTANT",
      "value": "bad"
    },
    "name": "x",
    "on_unavailable": "OMIT",
    "required": false,
    "schema": {
      "type": "integer"
    }
  },
  "portable": "Invalid authored default under its port schema, despite being unused. The resolved presence projection assumes valid Constant payloads."
}
```

Mathematics:

```json
{
  "axes": {
    "handler": [
      "BLOCK",
      "OMIT",
      "DEFAULT"
    ],
    "required": [
      false,
      true
    ],
    "valid_Constant_present": [
      false,
      true
    ]
  },
  "candidate_count": 12,
  "derivation": "Three illegal requiredness/handler pairs times two presence values =6 invalid; legal DEFAULT without Constant adds1. Legal BLOCK and OMIT each admit both presence values (4), legal DEFAULT with Constant adds1. SDK strengthens implication to iff: V3/I9.",
  "domain": "D.PORT.REQUIREDNESS_DEFAULT_JOINT",
  "inapplicable_count": 0,
  "invalid_count": 7,
  "predicate": "(required -> handler=BLOCK) and (not required -> handler in {OMIT,DEFAULT}) and (handler=DEFAULT -> default_present)",
  "unresolved_count": 0,
  "valid_count": 5
}
```

Decision needed: No normative decision is needed to classify the current written contract. To make the SDK iff portable, explicitly amend the normative conditional rule in a separately authorized task; do not silently add it to this model.

Existing assertion evidence (static inspection only):

- tests/integration/test_typed_dataflow.py:140-140 `test_optional_explicit_omit_and_default`: Exercises OMIT without default and DEFAULT with explicit null Constant, so cannot distinguish unused-default allowance from the SDK iff restriction.
- tests/relay/test_execution.py:279-279 `test_custom_policies_nonoccurrence_admission_and_defaults`: Uses legal DEFAULT behavior; it does not supply an unused Constant on BLOCK or OMIT.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

### Q.NONPROGRESSING_SCHEMA_REFERENCE

**Verdict:** PORTABLE_BOOLEAN_RESULT_OUT_OF_SCOPE; NO_INFINITE_LOOP_INVARIANT_ESTABLISHED.

Affected canonical IDs: `CM.PROVIDER.SCHEMA.VALIDITY`, `CM.SHARED.SCHEMA.EVALUATION.NONLOOPING`, `CM.VCP.SCHEMA.RUNTIME`, `CM.VCP.SCHEMA.SUBSET`.

Blocked subspace owners: none.

Sources: spec/draft/dataflow.md:97-105; https://json-schema.org/draft/2020-12/json-schema-core#section-9.4.1.

Established: Core 2020-12 section9.4.1 requires avoiding infinite validation loops and leaves nonprogressing recursion behavior undefined. OpenVerify supplies no additional Boolean/error/stage policy for that undefined subspace. Ordinary progressing recursive schema use and all 33 shipped roots remain in scope.

Scope/remaining uncertainty: Not a missing portable Boolean requirement: validation true/false for an actually nonterminating reference unfolding has no defined upstream answer. Do not infer that all syntactic cycles are invalid or all must be rejected at schema load.

Concrete example 1:

```json
{
  "instance": 0,
  "result": "No portable true/false or exact rejection stage/code; validator must not run indefinitely.",
  "schema": {
    "$ref": "#"
  }
}
```

Concrete example 2:

```json
{
  "instance": {
    "next": {}
  },
  "result": "Progressing finite instance recursion: both referenced objects are valid. Cyclic ref graph alone is not grounds for exclusion.",
  "schema": {
    "additionalProperties": false,
    "properties": {
      "next": {
        "$ref": "#"
      }
    },
    "type": "object"
  }
}
```

Concrete example 3:

```json
{
  "instance": 0,
  "result": "Inactive recursive branch imposes no condition; this example is valid and terminates. A blanket syntactic-cycle ban would exclude more than the undefined case.",
  "schema": {
    "if": false,
    "then": {
      "$ref": "#"
    }
  }
}
```

Mathematics:

```json
{
  "domain": "D.SCHEMA.EMBEDDED",
  "symbolic_partition": "Evaluate (schema location,instance location,selected applicator branch). Ordinary well-founded evaluations have Boolean semantics. Infinite same-instance unfolding is externally undefined. Finite instance descent supplies a sufficient well-founded measure for the progressing example; mere presence of a schema graph cycle is not the classification predicate. No finite total over arbitrary schema ASTs."
}
```

Canonical correction: Add one previously unowned atomic Core9.4.1 MUST: CM.SHARED.SCHEMA.EVALUATION.NONLOOPING. Existing581 preserved; total 582. Scope exclusion of Boolean outcomes must not erase the nonlooping invariant.

Decision needed: No decision is required to stop claiming a portable Boolean oracle for externally undefined behavior. If OpenVerify wants its own policy, explicitly choose a reject-at-load subset, cycle-aware runtime error, or defined fixed-point semantics plus codes in a future normative change.

Existing assertion evidence (static inspection only):

- tests/unit/test_provider_contract.py:155-155 `test_local_pointer_schemas_and_annotation_data`: Uses an acyclic local $defs reference with annotation data; does not assert termination/error behavior of a nonprogressing cycle.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

### Q.BOOLEAN_ANNOTATION_REFERENCE

**Verdict:** CORRECT_OVERBROAD_PROVIDER_RULE; KEEP_VCP_RESTRICTION_AND_PROVIDER_SCOPE_SEPARATE.

Affected canonical IDs: `CM.PROVIDER.SCHEMA.REFERENCES.SCHEMA_TARGET`.

Blocked subspace owners: none.

Sources: provider-contract/spec/draft/capabilities.md:12-22; src/openverify/provider/validation.py:295-312; https://json-schema.org/draft/2020-12/json-schema-core#section-9.4.2; spec/draft/dataflow.md:97-105; src/openverify/json_schema.py:91-106.

Established: Core 2020-12 section9.4.2 does not define interoperable behavior for references into non-schema locations. Provider prose explicitly constrains object targets to recognized schema positions; it does not explicitly impose that same extra position check on every Boolean target. VCP independently says annotation payloads are not schemas. Booleans in actual schema positions are valid.

Scope/remaining uncertainty: The previous Provider record overclaimed an object-or-Boolean universal restriction. Correct that record to the explicit object-target rule. Do not turn undefined Provider Boolean-annotation interpretation into a mandated accept, reject or error code.

Concrete example 1:

```json
{
  "instance": 0,
  "result": "Recognized Boolean schema target: true. Replacing b with false gives false. Both schemas are well-formed.",
  "schema": {
    "$defs": {
      "b": true
    },
    "$ref": "#/$defs/b"
  }
}
```

Concrete example 2:

```json
{
  "instance": 0,
  "result": "Provider: external standard undefined/nonportable result; no universal rejection code assigned. VCP: annotation data is not a schema target, so unsupported schema-resolution rejection before invocation. SDK membership check tests dict targets only.",
  "schema": {
    "$ref": "#/default",
    "default": true
  }
}
```

Concrete example 3:

```json
{
  "instance": 0,
  "result": "Provider explicitly forbids annotation object target; VCP also forbids it.",
  "schema": {
    "$ref": "#/default",
    "default": {}
  }
}
```

Concrete example 4:

```json
{
  "instance": 0,
  "result": "Annotation payload contains ref-like text but is not referenced/evaluated; it must not trigger schema traversal or external resolution.",
  "schema": {
    "$defs": {
      "b": true
    },
    "$ref": "#/$defs/b",
    "default": {
      "$ref": "annotation-only"
    }
  }
}
```

Mathematics:

```json
{
  "authority_partition": "Provider annotation-object targets: rejected by explicit subset restriction. Provider annotation-Boolean targets: externally undefined portability, no Boolean-result count. VCP annotation targets: unsupported by explicit prose. Ignored annotation-only data: not independently evaluated.",
  "candidate_count": "Unbounded schema/location/instance space; no one 2x2 position/type table can conflate schema validity, evaluation result and supported scope.",
  "domain": "D.SCHEMA.EMBEDDED",
  "supported_boolean_projection": "target truth value in {false,true} at a recognized schema position: two well-formed schema candidates; for fixed ordinary instance, validation false/true respectively. Validation false is not invalid schema."
}
```

Decision needed: No decision needed for portable scope exclusion or the corrected object-only source rule. If universal OpenVerify rejection of Boolean annotation targets is desired, add an explicit Provider subset rule and align both local validators in a separately authorized task.

Existing assertion evidence (static inspection only):

- tests/unit/test_provider_contract.py:155-155 `test_local_pointer_schemas_and_annotation_data`: Checks annotations are not traversed when a ref points into $defs. Does not point a ref at an annotation Boolean, so cannot distinguish alternatives.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

## Existing implementation/profile discrepancies

These are static source findings, not executed test failures. Expected behavior came from contract authority; code was used only to explain the implementation path. None justifies weakening the normative rule.

### F.TEXT.PATTERN_LIMIT

**Verdict:** DETERMINED_LOCAL_PROFILE_DISCREPANCY.

Affected canonical IDs: `CM.RELAY.SECURITY.TEXT`, `CM.RELAY.STANDARD.TEXT`.

Blocked subspace owners: none.

Sources: docs/relay/security.md:35-42; src/openverify/standard/text.py:67-77; src/openverify/standard/text.py:55-84.

Required: No accepted deterministic text output may exceed 10000 observations. Documentation does not mandate a particular truncation/error category.

Static source derivation: Worker can return10001 false search results in a small legal payload; the post-worker append loop adds10001 pattern_missing findings with no cap. This is a source path, not a successful timed process execution.

Concrete example 1:

```json
{
  "config": {
    "patterns": "10001 copies of literal pattern x"
  },
  "fixed_context": "Valid subject/criterion and standard capability invocation; no required/prohibited terms.",
  "inputs": {
    "text": ""
  }
}
```

Mathematics:

With m missing required terms, p prohibited matches and z missing regex entries, the attempted findings length is m+p+z. Required/prohibited stages enforce their bound, pattern appends can make it >10000. The three length representatives9999/10000/10001 give two cap-satisfying and one cap-violating output sizes; this is an output-bound quotient, not full capability input validity.

Decision needed: None to establish the documented bound. A production fix must enforce it on the pattern path; overflow ERROR versus another explicit bounded policy is not decided here.

Existing assertion evidence (static inspection only):

- tests/relay/test_standard.py:48-48 `test_json_parse_schema_boolean_number_and_pattern`: Checks one successful regex pattern; does not exercise10001 missing patterns or findings cap.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

### F.NO_FINDINGS.NULL_EVIDENCE

**Verdict:** DETERMINED_LOCAL_PROFILE_DISCREPANCY.

Affected canonical IDs: `CM.RELAY.STANDARD.NO_FINDINGS`.

Blocked subspace owners: none.

Sources: src/openverify/standard/scope.py:74-78; src/openverify/standard/common.py:27-38; docs/relay/providers.md:75-90; spec/draft/knowledge.md:11-14; schemas/draft/evidence.schema.json:1-53.

Required: Nonempty supplied findings require FAIL. Accepted Result evidence must also satisfy at least one non-null meaningful Evidence component.

Static source derivation: judge returns FAIL but wraps null as Evidence(structured_data=None); serialization/acceptance has no non-null meaningful field and violates EVIDENCE_EMPTY. The local Result/Evidence constructors do not themselves prove full semantic acceptance; Relay VCP acceptance should reject this output.

Concrete example 1:

```json
{
  "fixed_context": "Valid semantic subject/criterion supplied; capability ARRAY has no items restriction.",
  "inputs": {
    "findings": [
      null
    ]
  }
}
```

Mathematics:

For the finite list representatives[],[null],[{}], all3 inputs pass the declared array-type predicate. judge output Evidence semantics pass for[] and[{}] and fail for[null]: output acceptance2/1. In general every finding f must be non-null for this particular structured_data-only wrapping to be meaningful; false,0,empty-string,{},[] remain non-null data.

Decision needed: No normative ambiguity: current broad input schema, no_findings verdict rule and Evidence invariant are explicit. Future implementation must emit meaningful evidence for every admitted item, or explicitly narrow and document a changed capability input contract; no change made here.

Existing assertion evidence (static inspection only):

No discriminating existing assertion was established in the bounded non-Golden source reads. This is not a global absence claim.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

## Additional discrepancies exposed by resolving these blockers

### F.DEFAULT.UNUSED_IFF

Affected IDs: CM.VCP.DATA.PORT_HANDLING, CM.VCP.DATA.DEFAULT.CONSTANT.

Expected: Two legal BLOCK/OMIT unused-valid-Constant declarations satisfy current normative predicates.

Static source derivation: SDK validate_port adds iff, rejects both as DATAFLOW_BINDING; this extra rejection cannot be called a portable requirement.

Sources: spec/draft/dataflow.md:20-33; src/openverify/dataflow.py:36-45; schemas/draft/input-port.schema.json:1-50; spec/draft/dataflow.md:97-105.

Concrete examples, source-authority distinction and bounded existing-assertion review are in Q.DEFAULT_UNUSED above. No production edit or execution was performed.

### F.TIMING.DOUBLE_KEY_COLLISION

Affected IDs: CM.VCP.RES.WALL_TIME.SEPARATE, CM.RELAY.API.VIEWS.USAGE.

Expected: Retain both valid provider timing-named measurements and separate own duration in node usage.

Static source derivation: If both wall_time and relay_wall_time already exist, execution.py overwrites the latter with own seconds. Observation retains the original, but node.usage loses it.

Sources: docs/relay/architecture.md:78-83; src/openverify/relay/application/execution.py:141-194; spec/draft/resources.md:5-18.

Concrete examples, source-authority distinction and bounded existing-assertion review are in Q.RELAY_TIMING_KEY above. No production edit or execution was performed.

## Remaining rounding and version scope limits

### Q.ROUNDING

**Verdict:** ALGEBRAIC_SEMANTICS_ESTABLISHED; CROSS_LANGUAGE_BITS_AND_UNDECLARED_TOLERANCE_EXCLUDED.

Affected canonical IDs: `CM.VCP.AGG.MEAN`, `CM.VCP.AGG.WEIGHTED.SCORE`.

Blocked subspace owners: none.

Sources: spec/draft/aggregation.md:42-46.

Established: Mean and weighted-mean mathematical equations, retained weight identity, range and equal-score invariants are specified. The rational-intermediate/binary64 algorithm is expressly non-normative reference behavior. Portable numeric rounding/tolerance is not fixed.

Scope/remaining uncertainty: A finite JSON decimal cannot encode 1/3 exactly; the contract does not name a universal epsilon or one wire rounding bit pattern. Do not infer that any number in the input range is an adequate mean.

Concrete example 1:

```json
{
  "mathematical_mean": "1/3",
  "portable_limit": "No finite-decimal exact encoding or uniquely prescribed rounding tolerance.",
  "scores": [
    0,
    0,
    1
  ]
}
```

Concrete example 2:

```json
{
  "mathematical_mean": "1/2",
  "portable": "An exactly representable boundary witness can check the arithmetic relation without inventing global tolerance.",
  "scores": [
    0,
    1
  ]
}
```

Mathematics:

```json
{
  "domains": [
    "D.AGG.NUMERIC"
  ],
  "equation": "mean=sum(s_i)/n; weighted=sum(w_i*s_i,i in K)/sum(w_i,i in K), positive retained denominator.",
  "invariants": "min<=mean<=max; identical scores preserved; positive rescaling of all weights leaves mathematical weighted mean invariant; aligned member/weight permutation leaves mathematical value invariant. No bound on graph/member count or JSON precision is invented."
}
```

Decision needed: Only if a cross-language numerical fidelity guarantee is wanted: choose numeric representation and rounding/error contract normatively. No such new guarantee is needed to preserve the current local reference arithmetic contract.

Existing assertion evidence (static inspection only):

- tests/unit/test_aggregation.py:59-59 `test_identical_scores_remain_identical_after_mean_rounding`: Exact equality detects loss of the documented local identical-score invariant, not a portable rounding standard.
- tests/property/test_invariants.py:92-92 `test_weighted_bounds_and_aligned_permutation`: Checks bounds and exact reverse-permutation equality for reference arithmetic. Finite generated examples do not prove all values or specify cross-language bits.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

### Q.VERSION_FUTURE_INTERSECTION

**Verdict:** CURRENT_0_1_SELECTION_ESTABLISHED; MULTI_VERSION_FUTURE_PROFILE_OUT_OF_SCOPE.

Affected canonical IDs: `CM.PROVIDER.INIT.SELECT`, `CM.SDK.PROVIDER.NEGOTIATE`.

Blocked subspace owners: none.

Sources: provider-contract/spec/draft/versioning.md:3-14; src/openverify/provider/lifecycle.py:25-30.

Established: Contract versions are opaque exact strings; select first runner preference that provider supports. Current DRAFT implementations select only0.1. No intersection means CONTRACT_VERSION_UNSUPPORTED and no work. SDK helper takes first common then rejects unless0.1, without fallback.

Scope/remaining uncertainty: No missing current0.1 expectation. A peer whose first common supported version is0.2 needs a future-version profile to define a successful0.2 session; do not treat it as current0.1 fallback.

Concrete example 1:

```json
{
  "provider": [
    "0.1"
  ],
  "result": "Select0.1; runner entries unsupported by provider are skipped by intersection, not fallback after failed selection.",
  "runner": [
    "0.2",
    "0.1"
  ]
}
```

Concrete example 2:

```json
{
  "provider": [
    "0.2",
    "0.1"
  ],
  "result": "First common is0.2. SDK raises CONTRACT_VERSION_UNSUPPORTED and does not fall back to0.1; success under0.2 is outside this profile.",
  "runner": [
    "0.2",
    "0.1"
  ]
}
```

Concrete example 3:

```json
{
  "provider": [
    "0.2"
  ],
  "result": "No common version; reject current initialization, no work.",
  "runner": [
    "0.1"
  ]
}
```

Mathematics:

```json
{
  "domain": "D.PROVIDER.INITIALIZATION",
  "symbolic_partition": "First common0.1; empty intersection; first common other version (future successful-session semantics out of scope). Exact string comparison and runner order, no SemVer universe count."
}
```

Decision needed: None for current0.1. A future multi-version protocol/profile is separate work; do not add fallback here.

Existing assertion evidence (static inspection only):

- tests/unit/test_provider_contract.py:155-155 `test_local_pointer_schemas_and_annotation_data`: Initializes only mutually advertised0.1; cannot distinguish mixed future preference or fallback behavior.

No test was run. Golden test coverage is unassessed; source-defined semantics were established before inspecting the cited non-Golden assertions.

## Source completeness, provenance and scope

The prior source-first comparison covers162 repository source files,122 source sections,409 prose units,1588 schema source positions,366 declaration candidates,55 reexports,12 additional type aliases and77 profile positions. These are distinct source categories, not requirement totals. Whole-root normalization24 VCP/9 Provider,724 component reconciliation,34 packaged-copy checks and the original314/366 unfinished backlog closure are retained from the baseline; integrity checks alone do not independently prove semantic completeness.

This continuation reread the relevant normative aggregation/dataflow/lifecycle/resources/knowledge/schema/compatibility/error context, Relay documentation and the concrete implementation paths. JSON Schema Core2020-12 sections9.4.1/9.4.2 were checked at the official versioned source. It did not repeat the whole repository source traversal or claim comprehensive implementation/test coverage.

No Golden inventory, fixture, expected output or test result supplied semantic requirements. A first bounded keyword scan excluded Golden directories but also touched tests/relay/test_golden.py by filename without displaying a match; that file supplies no evidence. Subsequent assertion inspection explicitly excluded Golden paths. Cited non-Golden tests were read only after source-derived expectations, to answer distinguishability, and were not executed. No new test/fixture/freeze was created.

The main and isolated checkouts use different line-ending conversions.61 source files have different raw SHA-256 values with verified identical CRLF-normalized content and identical line numbering. SOURCE_CROSSWALK.jsonl retains both byte hashes in CHECKOUT_SOURCE_BYTE_RECONCILIATION; current references use active-checkout bytes. These are not source semantic edits. External standard URLs/sections/versions are recorded, but retrieved web bytes are not vendored/hashed. Source hashes do not constitute an expectation freeze.

Active-checkout source aggregate SHA-256: 160c9975ea69e7b407fe65f5c6080c6b15f4f405223ec9499c7ac9bbf440b150. It is SHA256 of sorted compact JSON path->SHA256 for the162 repository source files.

| Repository source | Active checkout SHA-256 |
| --- | --- |
| CONTRIBUTING.md | 463bd0bf73b693d1f5612da29cd951114d4173ff38751a507e40979b3b63e1db |
| README.md | ab5f94c4691230b88e0ecec0d35c82137e56770ad24aca1714eed146bb408eeb |
| conformance/README.md | 156d01519fd92322f064c8325822b464d9cb8fdafefeeacfeab67c8c3796a92c |
| docs/relay/architecture.md | 39dd8e1f1266998cef3b1c565398dd0945c991210f9ae83ab445ee9c617840b1 |
| docs/relay/error-contract-hardening.md | a6ad9882b47410f6039ab2940adbf69d8f63ab4be2523b43e294334790ed2d9d |
| docs/relay/graph-authoring.md | 32749238bf11169001e8388cccdcb48f84e2dceae04da27fa58f92c06660cdac |
| docs/relay/integration.md | 139ec04516206e4225fb460091ae2504c171a4d890d6523835797071b67b9c3a |
| docs/relay/limitations.md | c82e45d6d360b8e6bfd7c02016c064032d17bf488edf49e777f102cf82522c37 |
| docs/relay/production-fixes-report.md | 08d56ce3970f3d726b6eb8ae19c30a2267e42892d2921b68bf20d90424cb11f2 |
| docs/relay/providers.md | 72c3ccca55a889b1752118372b0177b557be1a0011c951d5b9b4eb4b7d3ae619 |
| docs/relay/quickstart.md | f373bf0fca3aaf7933de4fd0a924eddccd50cd481554fd5d3dfd15c1d707044f |
| docs/relay/security.md | 15bb938fd71fe9fd599e70c73533f7a799a9764f459450189b8e720c301a9d65 |
| docs/relay/verification.md | 8410d000f3ad586d44df42a37f8883ddcc10dd2f735bc46919d64739906a0c22 |
| profiles/standard-draft/README.md | 9345b2fc9885f12c12bf32b8b1678f2867027e39220d83cbc8715ade8f407899 |
| profiles/standard-draft/profile.json | e67739ae4a45719b27f661f12a933a9b021fa6164c5bed19f3fc261034651ed4 |
| provider-contract/README.md | ad230ab1920ecf6c2b71e903feb83e48a3b4f1212eb56ad25d8eb944cc99deed |
| provider-contract/conformance/README.md | ce41e7a7fa1a50acc49e062778f05f4a4e4823f5d0083e55d3c02d1afb4f8470 |
| provider-contract/schemas/draft/cancel-request.schema.json | b17be231743fe9044906e1c2aecf9b73da3dffeb5d4c39324608b3539532ad22 |
| provider-contract/schemas/draft/capability.schema.json | 67ad1c93bb83909e09bdcf3fb80fdef16e449937c72b3091e3d722490470d025 |
| provider-contract/schemas/draft/initialize-request.schema.json | 5c446cc8404f26a8dfc23a210e93f66b686c2f4d0e25f668119517e9af310f97 |
| provider-contract/schemas/draft/initialize-result.schema.json | b482448bc85f808515f3fbc023b9fb0aa5211aed14f9f8790869fe6c19cde4f9 |
| provider-contract/schemas/draft/invocation.schema.json | 14992170f80ea57a1171147a022af2a5bb83a38e5e8a49fbbaf32dbd801fc40f |
| provider-contract/schemas/draft/outcome.schema.json | 6c6a9b4bc62fe5a61096f7b50d1ceffce5edff0e6ffbaa797cd0cd685eccc0db |
| provider-contract/schemas/draft/provider-error.schema.json | 2c77abc25cd022473bc593457ba88f4a4b5e38a17b6262e0ee083726482bef62 |
| provider-contract/schemas/draft/provider-event.schema.json | 515f84003aa3c11a69bcd8ab3b6b4aa3a553f829277d31f413d4dcc1315e8d9a |
| provider-contract/schemas/draft/provider-manifest.schema.json | dd2509a8096a9290642d1d0b8e7870a4fa54ff9ace27840bfa5c57545360a783 |
| provider-contract/spec/draft/capabilities.md | 9ac03569a88e9982b5a75ceb705daa59cd0ff21aa3ab440d9ee0e3b2afcaa66a |
| provider-contract/spec/draft/errors.md | 421ba6acd25ce220f3cd986f14819bd07034873b4b23cef891149d9657d6d3e4 |
| provider-contract/spec/draft/lifecycle.md | 122e8e4aaa8deb60d0cf6397d9857294d096f063c5c7ecde59d3d0359596177d |
| provider-contract/spec/draft/open-questions.md | 0c0ddb9a1f51619d6b787ceeac452c659a5f4b1f7be71fa33894643d4000bb19 |
| provider-contract/spec/draft/overview.md | b2d0b56c135323accc4927db85b0af447b7f925c4bb8debc00443ec495487807 |
| provider-contract/spec/draft/transports.md | 3d5b5d158363059147706b232ecbc7112a911845b5f22fc3db40ed2d490f0fea |
| provider-contract/spec/draft/versioning.md | 2656dd1dbd2a872bd9d9912b8dba4c2ec61fc4dbaf145d091f7cda1203132921 |
| provider-contract/spec/draft/wire-format.md | 23d1e6bc4518225afa86f422d15eee22214d7a285b369c42c6843f45d06895a7 |
| pyproject.toml | 5c21eca3adc662919b4aa3e1edd0c8774ef42a8a9813cc0cc2cbf8a06a27d210 |
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
| spec/draft/README.md | b1c8dc3b0b3190997a1a6bbd1013d0f154e5a89ecbdda9d087953241c22d142c |
| spec/draft/aggregation.md | a627fc3bd6f8509d1f231caf3d919e16d88c33057b6f144e37e30d715165507e |
| spec/draft/boundary.md | f9b9393c9e16bec7b9cd7ff73997b6e656817486b1e3aaaee3b0d5406cb0dbab |
| spec/draft/composition.md | d5a1ae05299bc11d00d666f10912bef85320357cc5b890e5c6c3332f5cf872e6 |
| spec/draft/computation.md | 8c28297120854a138d194daaf169e1844b3cbe2c9d5658eb7b111d70175cca1d |
| spec/draft/conceptual-audit.md | c2ee7083ee271451a2b387625852371618c0e6b00bcac7064814685c14a87c71 |
| spec/draft/conformance.md | efd0e61e215a96d94ef3891c9f83bd821dbed045901f089cbf0c5bf3e0132f24 |
| spec/draft/dataflow.md | 10399b6c1ad0754d63b50404d060e8fcb6c362246d5d793d05c18e55f68074eb |
| spec/draft/execution-policy.md | d6c1d6c71da16609c67bcf77ad70723f47d4e53931301ba1e0eefbce2e46268c |
| spec/draft/extensions.md | fc57202300c344967487f4d631e7b6bbc99281634a1f4391249ce2a7ec7040d7 |
| spec/draft/knowledge.md | 37e238707b73b46eb3660c8716e252c506c5ffe7367f737e484808538c17ce76 |
| spec/draft/lifecycle.md | fd88c5ec2ce21f0172f0000f6662f81477f0a68e0e04d22dfbd9261f7b070e07 |
| spec/draft/meaning.md | 71e2a8f209fd91af1488f86c306a5aa73b4d30d2d524bb505af8229f4dcf6ad5 |
| spec/draft/open-questions.md | d172d96b92104a6de8eabb1541cdd3bf598b30f076730cb2dbc095ee2f129546 |
| spec/draft/provenance.md | f5e39f64216f88a8ba3b2e0d9dbcc2e1bdf61f6f747abf0c17af4b988624f713 |
| spec/draft/provider-binding.md | e9182644aa142b737291815f343c6eae5982f4e7b65195af035ccaf201bc4570 |
| spec/draft/resources.md | 0cd745defc13acf16c4cf74ee1045c010e470adf065a7fcf08c4ebd531135a48 |
| spec/draft/result.md | 899c305f508a87ae4bd648bfdc40aa856fc09a2877ef5c3774e2d0a6af6b2a33 |
| spec/draft/wire-format.md | b6935e2ebf193fffe59851efa5f69a00606652cf3f664bb78aaf12b020d28ef4 |
| src/openverify/__init__.py | 4be5cfedb030a728985d7da72a9cc5da7035deac2df00eb90e5d8ab0bddec675 |
| src/openverify/adapters/__init__.py | 94b9522b39696d4d23348044f15722d402ea74cff09be23ee76f3381c8ed7ccf |
| src/openverify/adapters/demo.py | 75cabbfdf562cdde28633830b7fdcb555ed15206ca713d9e017cb52f16a39593 |
| src/openverify/authoring/__init__.py | 8c0697f377d9856e7efcbaf67b6cb43e94ff173f9e31e06dcc22e40485c8f1ce |
| src/openverify/authoring/graph.py | 772423a33c75833b5d840898934e03d9c1d45cfb67bff7ef23427cfbb9d2f70e |
| src/openverify/authoring/references.py | 97385c774624753bfde2a0802cefdb98259522ed630c8d98fd767f10e244dd67 |
| src/openverify/cli.py | e1d38334f878c2d825db591e7acb5fb7bfca0b52d3878ae0f8bccbb4dfb0e61b |
| src/openverify/conformance/__init__.py | f99b26c5f9884d0a87b6d024c55762129265edaef42f7879a07a715fe769b5d9 |
| src/openverify/dataflow.py | ce993d3aa4ff878ff885cc9db32822a3a5ec8c9c81f6ebd9165c677bf0c611b1 |
| src/openverify/engine/__init__.py | 41a028ae475dafdcd992ef5c9f482117f9dc3b9fd542a3feca00e584ce9c19e8 |
| src/openverify/engine/admission.py | bdef93be2d243f82c20a887405718b3c8da81127f5ee965b67ee8f142c7acbcb |
| src/openverify/engine/aggregation.py | f2c0824988a07573eec033485969298bf4cf5790bf4627044b2343d62a92833f |
| src/openverify/engine/binding.py | 817805b3f60908e7d66af96953c941f9ac5d292de8ba4000f413dd5b846fd145 |
| src/openverify/engine/policy.py | e8c7a9226a71eef17a35b5049320a66303252a265a71ec50d4e11cd19785221f |
| src/openverify/error_codes.py | 11b802c51c53b094e6aa694c5f0962270e399c6a3b356de788b20abac8373d8b |
| src/openverify/errors.py | 2dce7a2f896b8ced248c1b7be8f4ee9ff5bd2dedc96bbb118612c660ecde930a |
| src/openverify/fingerprint/__init__.py | f5ced653c2ba3ea6aa54dda046b3b6c8d1c13e290c0e97ab2fa4385dd6895d34 |
| src/openverify/inspection.py | 24da3a1930d931e2307906a12b8bb60ced0e2635023801365595215af4824c8d |
| src/openverify/json_schema.py | 81a0fde00129168a7452ca09d5429246611602528b59d963045eb4895b44bab6 |
| src/openverify/lifecycle.py | 4d32fcb3bb4cbad17ceae9e05f9a81ccdc1952a350112844808aeeef8430ffba |
| src/openverify/model/__init__.py | 9b694cb0a131c2f5da2ca88be436f7f439bfb770fffa3fd331f0164fd8b6fef3 |
| src/openverify/policy.py | c0ba6941268eec65049b4728a771b84dcf558a4c998bab6a228b05d9413def79 |
| src/openverify/provenance/__init__.py | d70976288aaa16e48ae0cc462c0d18b521148b2e6f8a90b5f73b1dab9dd720fa |
| src/openverify/provider/__init__.py | 65fb1f6e8f1ad95404077dc11a16b78d6392fa31298b361db4409558e8d27af9 |
| src/openverify/provider/conformance.py | 678bc1b2d1b4b4365d826dc12ac9d88616023b9d0c70f0298c3baaf36932db9f |
| src/openverify/provider/lifecycle.py | f8456c8f8988a9e9af16a6bf92b435ada182fdc3dc00799b3c119288d82ba4d4 |
| src/openverify/provider/model.py | 3ac0e970a0eb77358a7f1c775fe17f2c0442ad46fa68e4abcd74c5ef29dc5f36 |
| src/openverify/provider/stdio.py | 580faa7347627657f75e0bce7318fc5bfa4b72409c4e0dc1b707c43661243d79 |
| src/openverify/provider/validation.py | c087fa9fd79a68d4907322a5173acc9c31453570f679f1942d3066499d416be4 |
| src/openverify/provider_codes.py | 8c920dcfbb0c00e1eeb7d776be4719128ddeeb8021ca3e0c1b2e489d12dc23ec |
| src/openverify/relay/__init__.py | 6398c2f15fe1dcf5d3faca87b488aadab374a95876deb7ee0f18893a17662d4a |
| src/openverify/relay/adapters/__init__.py | a851473aac79e9bc3c846d4a06937e253ad7c08d01857043fb5b0a4904913b29 |
| src/openverify/relay/adapters/binder.py | 3e7b6726db45b2c1f0b0ba5ca041ce42de050c09e331f7ec8448cf408cef5590 |
| src/openverify/relay/adapters/catalog.py | d97767e1d275b1930050f7462c0b5412b959059c4243fe89e5880eb8c8e42c58 |
| src/openverify/relay/adapters/inprocess.py | 5d5bbe5f9de841cb4ac3a152614164f45390858fd9119dd4839da4d8dafe456d |
| src/openverify/relay/adapters/jsonl.py | a1c424fac3cafc8067dfa6a2a1b29322f5f04eee849f932f7aa70d80ca5f8f58 |
| src/openverify/relay/adapters/local.py | 614ace847fd560405d3b89d44115ef90efc28b979935218f44079b98af3f6fbf |
| src/openverify/relay/adapters/logging.py | 962df25c768f6ac9c006e0b3006bb9c8e30b26064ffc7adaa0349b27a1eb75db |
| src/openverify/relay/adapters/memory.py | 61972d7f49bc9c0421a81a7259ffd16a71fcca4bacba46b5e23ddd8d441652ad |
| src/openverify/relay/adapters/process.py | 0f43102c2dd6c43fd12068a70bb8d789b75c55c6b8ac71fa3c7090f6a61c6214 |
| src/openverify/relay/adapters/server.py | 8c6263ab266a4184290696a5a2563e4728567794e79cbd7127dd2916fecfe642 |
| src/openverify/relay/adapters/stdio.py | a1bd23c4f597626cd3adf4d323f67e479345fa5ce740c505e0173ac3a3792968 |
| src/openverify/relay/adapters/windows_job.py | 8d19c67b06e7a4ec1bbe5b70523a3a61a66cbb723845dfd61856fefbafa811b7 |
| src/openverify/relay/api.py | 2fa41c0c270a762d2f2973470ec065279032b1f337fc283a5332d20ea77bb80d |
| src/openverify/relay/application/__init__.py | a39172ecc2173839ea51bfefe8f749e50d275d4118788541c60a8d67ae26e7e5 |
| src/openverify/relay/application/binding.py | 0be39eaa0aa1c4ca84ec64b75098d6d9b470b7158cbdc568ccd5d0b691f3cfb3 |
| src/openverify/relay/application/contract.py | 4385a847188853cf05010b9e588bc001ddbde8b3679ce3df02af080ec0af7f34 |
| src/openverify/relay/application/execution.py | 1763f6d7a703bbc460f7199783a80bc6c1a35c9d4d58cd9629bae5815a633bb8 |
| src/openverify/relay/application/policies.py | fee622397d05f8f3cc4630a86ea91262f11a9d6c1a13447f7946bfe0d81c68aa |
| src/openverify/relay/application/preparation.py | 6234f7c08f723a629fbdc8e345f12d5dbe2bef698dc9f7f47d6687dcbb042429 |
| src/openverify/relay/application/run.py | a958f472edd9ce6644ca3f2f2b08e082ef04e07b6c4c8d3baacb1652cf92f249 |
| src/openverify/relay/config.py | d67c30bf4f161ea6b946a9190012281cf308ac61d945280b44e9538155c3f215 |
| src/openverify/relay/core/__init__.py | c6130bc3323b8549815977495758720c28f27e7fc277558f4b5e26a49390e9a3 |
| src/openverify/relay/core/aggregation.py | 1cfa76d89c54d40d477a6be4b280cf23c18a01559bd6cc8036dc1ca6e1b27da6 |
| src/openverify/relay/core/readiness.py | 7975b54522437f833d43f0b33dc37346988459c9da9f4acd36c4b6e26d87c08b |
| src/openverify/relay/core/state.py | 72ad68ca5db6862b4c2abe9eb3a51ea7a72d03f1668fb9d0da4ad732d6c3df07 |
| src/openverify/relay/entrypoints/__init__.py | f6df74eb909aaa95457f7b89ad94eefe57d6e9e3360d8144d8a710c9f771718e |
| src/openverify/relay/entrypoints/cli.py | ce61e293fb4f12bc2f9bed02bf89a81b9cb8084ac8085e8e41b48c5e375a6d47 |
| src/openverify/relay/entrypoints/http.py | abb2644b25d8bfefe10fdb0f1869e36103325217223af108f8bcb88415e669d2 |
| src/openverify/relay/entrypoints/mcp.py | 8bdfc3736cad5bb0c8674a368c43e6eb6a9cd48326aa99e6ce56957385370ef8 |
| src/openverify/relay/entrypoints/service.py | 0accc0770270fe8ea7c5229244da2cf9074218caf085f133d4b4b3527f04700d |
| src/openverify/relay/error_codes.py | d12a354eaa8cb5f769af97acba6e3cd46d06a76436de78e14bab4e12e15c98fc |
| src/openverify/relay/errors.py | a1564afe96238e3ba22dd89c17bbe22f8c14df80655c02e7ad185fc82ad82c2e |
| src/openverify/relay/ports/__init__.py | b85ce606454f8b7ca006c0a4805536cf80810f34e886a3ce7ca90c29a84699e8 |
| src/openverify/relay/ports/binding.py | 335d3c7ba4040fbc944d7e8a51ec33858fcb6033c47f6bd322abd83d2953e404 |
| src/openverify/relay/providers.py | 3ece1fa3484f32ba79ec93f04baff83af270c953a74c113b74eafefc4ab99a50 |
| src/openverify/relay/templates.py | b7f12cb3e289dd582ced7ee3aa7b9d319f9453b5c256c44641fab475af953c74 |
| src/openverify/serialization/__init__.py | 7a2f46c623f94a81925d12d8e92f446db440f2415508f0db4ae6e06e542a7110 |
| src/openverify/standard/__init__.py | 7ce338ec6ba3e1faa8164b446fd29aadfcd69a6a4b9b23f18753c216b5c87331 |
| src/openverify/standard/astgrep.py | ae28d7f38f65a96580fa41c86518321086ddc8be0d86fde4fcfcdd1321e7b2e6 |
| src/openverify/standard/command.py | 0dba4c1ddd61543d46c9de30f7b5ebe4118c8ef1bfee968067cd98195b39a761 |
| src/openverify/standard/common.py | bc55d0c0bb9c0e134b0564b6e72ad1fb6cd4a2d4a61c497fb5d6e58c3bfa6f0b |
| src/openverify/standard/control.py | 5ae8c4250ac674ffd11a81f5049633468b788b103a0749106b1d1eda4a67a8ab |
| src/openverify/standard/filesystem.py | cb8a29d31cc960ed48f314a6e4600782aa4273532f79ce1a14c77d07589b3783 |
| src/openverify/standard/git.py | d80eca64f9bd7ee632653d079e15bba8b6ae51afd2e1f93b92f467d96c73f664 |
| src/openverify/standard/paths.py | 4f450710e1ff08464ca8e6e27a3f96926169a96111241071fa3e6c6b67d711d2 |
| src/openverify/standard/pattern_worker.py | 4b7085e919688799c00b894bd9ae22d981188abe9f4e7504bca84d27b66085d2 |
| src/openverify/standard/pytest.py | 02c72d766e52522d03298523e34587be44d0243d4c93002de8e5d96af6d1295a |
| src/openverify/standard/ruff.py | f1ba8ae9c316f96e0d56a4fe1a66a490db8e354617633af36f68bce7a27c4c52 |
| src/openverify/standard/scope.py | 935b8b2996a0f6416c4292f2155a5e4220295fe49728c944b51bf59699482ab6 |
| src/openverify/standard/structured.py | 17906027cb4181d6d28d7ce3bded74d05d2b265423ecfd5de87f44bd2f8d08c0 |
| src/openverify/standard/text.py | 98eab2a5ca35d2a79a3182e1c60c64073369f6a516b6c398f9661af2cc54d22e |
| src/openverify/standard/tools.py | 1bb17b2d63da52a43ae3d4ff51ec93d07b3414b4f69bacbf5c320cf65bbc46b5 |
| src/openverify/validation/__init__.py | 022d65bdc0b4c7553c4ca4c0b3bccdf37c16cdfa76f5d8bc714f63ceba87dec8 |

## Current branch verdicts

Canonical model closure only; known implementation discrepancies are reported separately. An explicit blocked subspace keeps its leaf and ancestor branch incomplete. Standard-defined unsupported/undefined-result scope is named and is not silently accepted or counted as invalid.

| Branch | Semantic | Roots | Finite refs | Symbolic refs | Conditional refs | Blocking questions | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VCP/Aggregation | 33 | 0 | 1 | 5 | 0 | 1 | CLOSED BY APPROVED SNAPSHOT/CUSTOM DECISION |
| VCP/Composition | 12 | 0 | 0 | 3 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Computation | 13 | 0 | 5 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Conformance | 2 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Dataflow | 37 | 0 | 6 | 8 | 1 | 1 | CLOSED BY APPROVED SNAPSHOT/CUSTOM DECISION |
| VCP/Decisions | 1 | 0 | 1 | 0 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Extensions | 2 | 0 | 1 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Knowledge | 3 | 0 | 1 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Lifecycle | 22 | 0 | 3 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Meaning | 6 | 0 | 1 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Policies | 22 | 0 | 4 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Profiles | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Provenance | 28 | 0 | 0 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Provider binding | 12 | 0 | 0 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Resources | 5 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Result | 1 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Results | 30 | 0 | 3 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| VCP/Schemas | 3 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
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
| PROVIDER/Schemas | 4 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
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
| RELAY/Public API | 9 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Public SDK | 48 | 0 | 0 | 21 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Records | 6 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Scheduler | 5 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Standard providers | 42 | 0 | 0 | 19 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| RELAY/Transport | 4 | 0 | 0 | 1 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| SHARED/JSON value and schema semantics | 3 | 0 | 0 | 2 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |
| SHARED/Public SDK | 70 | 0 | 2 | 40 | 0 | 0 | COMPLETE FOR DECLARED RULE SCOPE |

## Required normative decisions

1. Custom Aggregate empty membership: say whether [] is a legal structural declaration/custom invocation. If forbidden universally, assign definition-time versus invocation-time rejection and its category. If capability-owned, make that boundary explicit. Standard reducer empty-input rejection is already fixed.
2. Availability: specify an original-status classifier/priority for producer ERROR versus missing/invalid output, and for interrupted CANCELLED INFORMATION/DECISION producers. Preserve handler effects and lifecycle precedence; those do not need reinvention.

No other normative decision is needed to retain the current declared scope. Universal rejection policies for externally undefined schema cases, a new cross-language numeric error contract, or future-version success semantics would be new protocol/profile policy, not a reason to invent an expectation here.

FULL CANONICAL PROFILE CLOSURE: CLOSED BY APPROVED SNAPSHOT/CUSTOM DECISION. No certification, Golden coverage result, integration execution or proof of implementation termination is claimed.
## Current decision and source reconciliation

The preceding investigation narratives describe the earlier commit; this section supersedes their blocker/decision-needed verdicts. Custom [] is legal, capability schema controls input eligibility and custom implementation owns Result; standard reducers reject empty original/retained input. Snapshot availability is the ordered classifier in spec/draft/dataflow.md, with invoked CANCELLED/no accepted output -> OUTPUT_MISSING regardless of raw values. Declared bookkeeping Results precede lifecycle absence. No event-order provenance, extra state or scheduler barrier. Handlers retain original status/source/value/default and lifecycle reasons. Source hashes/citations and domain predicates are updated in JSONL and CANONICAL_MATH.md.

Gate1: PASS targeted normative context and ownership reconciled. Gate2: PASS33 whole-root predicates unchanged; no new wire fields. Gate3: PASS snapshot-dependent domain has a total/disjoint proof over80 equivalence contexts and240 handler checks, with unbounded input scope explicit. Gate4: PASS baseline independent source-first audit retained, targeted normative changes independently classified and checked; no new whole-repository traversal or implementation proof claimed. Unrelated limitations and four static implementation discrepancies remain.

Current normative-source aggregate SHA-256: 3c7694fc35900f93380bdf26ed345b54c51935c8f532a651c464d3144f3e9ad0. Earlier hash tables refer to the preserved pre-decision baseline; current exact per-source byte hashes are in SOURCE_CROSSWALK.jsonl.
