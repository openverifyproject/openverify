# OpenVerify Golden V4: Independent, Counted, Traceable Conformance Blueprint

**Status:** Design and normative-extraction baseline for implementation, **not** executed test results.  
**Input authority:** Current VCP and Provider Contract *normative prose and schemas*, followed by the explicitly supported Relay runtime profile and public port signatures.  
**Independence:** Start from the current normative specification. **Do not read, import, consult, compare with, or inherit any earlier Golden suite**, its frozen results, inventories, fixtures, case names, coverage claims, or tests.  
**External actor assumption:** Providers and external implementations are contract-compliant. During real Relay execution, simulate **only outcomes and events allowed by their contracts** (including valid error/cancellation/deadline outcomes). Invalid *locally authored inputs*, definitions, records and state combinations must still be rejected by inexpensive conformance tests. Malicious, malformed external-provider or replacement-port behavior is **outside this V4 profile** unless a normative Relay responsibility explicitly requires it; document such exclusions rather than quietly counting them as covered.

> **Central guarantee sought:** Every supported normative rule is inventoried. Every finite local state class is accounted for. Each required runtime transition and irreducible cross-module interaction has an independently checked witness or a sound composition proof. Every uncovered or unspecified behavior remains visible. A test count is never a completeness proof.

---

## 0. One mental picture

```text
                         CURRENT NORMATIVE CONTRACTS
                  VCP / Provider Contract / Relay profile
                                      |
                       CLAUSE-LEVEL REQUIREMENT INDEX
                         (nothing from older Golden)
                                      |
                   INDEPENDENT DOMAIN & CONSTRAINT MODEL
             finite values, missing/null, types, legal transitions
                                      |
          +---------------------------+---------------------------+
          |                           |                           |
     LOCAL CONTRACTS              COMPOSITION                 RUNTIME
  wire, schema, types,       bindings, DAG edges,         lifecycle, scheduler,
  Result, Decision,         policy precedence,         concurrency, cancellation,
  reducers, errors          fan-in/fan-out, guards      events, records, ports
          |                           |                           |
          +---------------------------+---------------------------+
                                      |
                      CANDIDATE COMBINATIONS INVENTORY
                 valid / invalid / impossible / unresolved
                                      |
                        TEST-REDUCTION JUSTIFICATIONS
          direct enumeration / equivalence proof / property law /
               compositional induction / bounded interaction
                                      |
                         INDEPENDENT FROZEN ORACLES
                                      |
          +---------------------------+---------------------------+
          |                           |                           |
       PURE/CHEAP                 REAL RELAY               ENTRYPOINT I/O
     exact isolated ID          exact isolated ID          exact isolated ID
          |                           |                           |
          +---------------------------+---------------------------+
                                      |
                PER-CASE ASSERTIONS + PER-CASE FAILURE REPORT
                                      |
                      RECONCILED CERTIFICATION REPORT
```

**Test selection is downstream of the contract inventory, never its source.** A valid external `ERROR`, `CANCELLED`, or `DEADLINE_EXCEEDED` outcome is a *valid runtime scenario*. Invalid definitions do not require executing Relay unless Relay itself owns that boundary.

## 1. Definitions and counting discipline

- **Candidate**: one member of a precisely specified finite projection, e.g. four Result state axes with their declared missing/null representations. Each projection states what other dimensions are held valid. Candidate counts from overlapping projections **must never be summed into one global state count**.
- **Valid (V)**: allowed under the current contract and all explicitly stated assumptions.
- **Invalid (I)**: malformed or forbidden by an explicit constraint. Assert rejection via the layer that owns the constraint.
- **Inapplicable (N)**: a combination that cannot arise in the stated typed model. It requires a precise impossibility derivation. Do not use N for a malformed input, an unsupported feature, or a simply untested case.
- **Unsupported (U)**: defined but excluded by the explicitly declared supported runtime/profile. Test a normative rejection if one is required.
- **Ambiguous (A)**: no determinate normative expected behavior. Name missing clause; do not invent an oracle.
- **Unbounded (∞)**: a domain containing arbitrary JSON, strings, graph lengths, numeric values, event histories or custom logic. Derive finite semantic partitions and general invariants; report proof/test bounds and residual unknowns.
- **Obligation**: one independently checkable expected behavior, rejection rule, transition or invariant linked to an authoritative normative clause.
- **Witness**: one actual executed assertion or valid proof establishing a specific obligation. Passing a test that never asserts the claimed effect is **not** a witness.
- **Cheap**: pure data/schema/parser/reducer/model checking in memory without running Relay or outside processes. Valid states may be checked cheaply if that is where their requirement is defined.
- **Real Relay**: actual public Relay invocation with correct scripted providers; checks data consumption, ordering, terminal statuses, control, events, persistent/returned records, and isolation.
- **Integration**: actual SDK/CLI/MCP/HTTP or standardized stdio boundary when genuinely supported. Contract-advertised operation differences must be respected.

For a closed, normatively decidable finite projection: `C = V + I + N`. If the contract does not determine classification for a candidate, track it as `Q = unresolved` and report `C = V + I + N + Q` until specification decisions settle it. **Supported/unsupported is a second, independent axis on contract-valid candidates**, not a way to relabel them invalid or inapplicable. For distinct supported requirements: `O = O_pass + O_fail + O_missing + O_proved`; tests and requirements are separate counts. A proof must be recorded with assumptions and a checker/test of those assumptions. If an asserted witness fails, count **failed**, not passed or missing. No fake global total for overlapping or infinite universes.

### Scope of compliance

A provider is correct if its invocation, streaming events, outcome, versions, capability schemas and advertised features obey the Provider Contract. We **do** test legal provider `ERROR`, `CANCELLED`, deadlines, streamed events (if advertised), zero events, and resource usages because these are normal contract behavior. We **do not** create malformed external streams or forged identities solely to attack Relay, unless normative Relay checks of such conditions are expressly in scope. We **do** independently test cheap schema/semantic rejection of invalid data objects generated locally.

---

## 2. Normative source inventory and freeze rule

Read **current checkout** source files, not old Golden tests:

- VCP: `spec/draft/README.md`, `meaning.md`, `wire-format.md`, `knowledge.md`, `result.md`, `computation.md` where present, `dataflow.md`, `aggregation.md`, `execution-policy.md`, `lifecycle.md`, `composition.md`, `resources.md`, `provenance.md`, `provider-binding.md`, `extensions.md`, `conformance.md`, `open-questions.md`.
- All `schemas/draft/*.schema.json` roots and transitive references. Current inspection suggests **24** VCP schema roots; independently verify.
- Provider Contract: `provider-contract/spec/draft/` normative prose (`wire-format.md`, `capabilities.md`, `lifecycle.md`, `versioning.md`, `transports.md`, `errors.md`, `open-questions.md`) and all `provider-contract/schemas/draft/*.schema.json`. Current inspection suggests **9** roots; independently verify.
- Relay: `src/openverify/relay/ports/__init__.py`, `src/openverify/relay/error_codes.py`, `docs/relay/architecture.md`, `integration.md`, `providers.md`, `limitations.md`, plus the actual shipped public entrypoint contracts. Relay is a **supported local implementation profile**, not automatically portable normative VCP.

**Gate 1:** For *every* normative MUST, MUST NOT, required condition, closed enum, distinct outcome, schema constraint, method contract and supported runtime limitation, record `clause_id`, `path`, line range, text digest, requirement ID, owner layer, obligation family, classification and expected evidence. Independently reconcile the normative clause index against schema properties and code-declared public methods. Zero untriaged clauses allowed. `open-questions` are scope constraints, not implied behaviors.

**Important:** The specific counts below come from a separate from-scratch read of current prose/schema definitions supplied for the design. They are **candidate targets for independent re-derivation**, not permission to copy a result into the oracle. When source text and this document disagree, halt and report the discrepancy; authoritative normative current text controls. Never silently change formulas or “make tests pass” by changing expected results.

---

## 3. Full named inventory with count formulas

**Reading the table:** `V/I` is the validity of exactly the indicated projection, with other values fixed valid unless stated. `Conditional` means there is no honest V/I/N division from the dimensions shown alone. `∞` means full concrete values are unbounded. `P` = cheap, `R` = real Relay, `X` = integration. Each row is a **distinct test family** with its own exact IDs and output counts; do not collapse all tests into one catch-all function.

| Family ID | Contract slice (exact domain) | Mathematical candidates | Valid / invalid or rule | Method |
|---|---|---:|---|---|
| `V4.WIRE.ROOTS` | All VCP + Provider schema roots | 24 + 9 = **33 roots** (verify) | Schema contract list, not JSON object-count | P |
| `V4.WIRE.JSON` | UTF-8, duplicate keys, nonfinite, unknown props, version marker, nested JSON | ∞ | Normative semantic partitions | P/X |
| `V4.VCP.DEF.PRESENCE` | 9 required + 3 optional fields | 2^12 = **4,096** | **8 V / 4,088 I** | P |
| `V4.VCP.CRITERION.PRESENCE` | 2 required + 2 optional | 2^4 = **16** | **4 V / 12 I** | P |
| `V4.VCP.ARTIFACT.PRESENCE` | 3 required + 3 optional | 2^6 = **64** | **8 V / 56 I** | P |
| `V4.VCP.EVIDENCE.MEANING` | 4 meaning bits + 3 annotation-presence bits | 2^7 = **128** | **120 V / 8 I**, with valid contents | P |
| `V4.VCP.RESULT.WIRE_AXIS` | disposition:4 × four categorical fields each {absent,null,2 enum values} | 4×4^4 = **1,024** | **66 V / 958 I** | P |
| `V4.VCP.RESULT.SEMANTIC_AXIS` | same categories with absent/null identified | 4×3^4 = **324** | **9 V / 315 I** | P |
| `V4.VCP.RESULT.OBS_MASK` | 9 valid semantic Result states × 8 observation-presence bits | 9×2^8 = **2,304** | **960 V / 1,344 I**; judgment_schema=true for this projection | P |
| `V4.VCP.RESULT.VALUES` | observed judgment,score,severity,evidence,output,usage,metadata,extensions | ∞ | Type/boundary/null/cross-field partitions | P/R |
| `V4.VCP.RESULT.PROJECTION` | 9 valid semantic Results → flattened presentation | **9** | **5 defined / 4 undefined** | P |
| `V4.VCP.DECISION.DEST` | 6 kinds × {absent,null,empty,nonempty} destination | 6×4 = **24** | **11 V / 13 I** | P/R |
| `V4.VCP.DECISION.ROUTE` | destination × reachable direct successors/guards/control | ∞ | Explicit graph obligations, not another enum | P/R |
| `V4.VCP.NODE.ROLE` | 4 node kinds × 3 individual output roles | 4×3 = **12** | **7 permitted / 5 forbidden**, excludes port-name/cardinality obligations | P |
| `V4.VCP.NODE.PRIMARY` | required `result` or `decision`, auxiliary INFORMATION, duplicate/wrong role | finite rule matrix; derive | Required-role/name/cardinality invariants | P/R |
| `V4.VCP.NODE.INVOKED_RESULT` | EVALUATE,AGGREGATE × 9 semantic Result classes | 2×9 = **18** | **12 permitted executed / 6 forbidden nonexecution** if 6/3 per kind confirmed | P/R |
| `V4.VCP.BIND.IDENTITY` | 4 equality/mismatch bits against independent trusted anchors | 2^4 = **16** | **1 match / 15 mismatches**, in anchored projection | P/R |
| `V4.VCP.PORT.HANDLING` | input required? × {BLOCK,OMIT,DEFAULT} | 2×3 = **6** | **3 V / 3 I** | P |
| `V4.VCP.PORT.DEFAULT` | DEFAULT × value present/absent | **2** | **1 V / 1 I** | P |
| `V4.VCP.SOURCE.KIND` | CONSTANT,RUN_INPUT,EXTERNAL_REFERENCE,UPSTREAM_OUTPUT | **4** | all four defined kinds | P/R |
| `V4.VCP.SOURCE.POLICY` | four sources × three policy roles | 4×3 = **12** | **9 permitted / 3 forbidden**, assuming current policy source limits | P |
| `V4.VCP.RESOLVE.HANDLER` | six statuses × BLOCK/OMIT/DEFAULT | 6×3 = **18** | **Conditional on port/source/trace** | P/R |
| `V4.VCP.RESOLVE.CONSUMER` | 18 × four node kinds | 18×4 = **72** | Conditional; reused rules only with proof | P/R |
| `V4.VCP.RESOLVE.RAW` | 4 node kinds × 4 source kinds × 6 statuses × 3 handlers | 4×4×6×3 = **288** | **Not independently classifiable** without port, schema, producer role, trace | P/R |
| `V4.VCP.RESOLVE.UNBOUND` | 4 kinds × UNBOUND × 6 statuses × 3 handlers | **72** | Conditional | P/R |
| `V4.VCP.RESOLVE.RECORD_BITS` | 6 statuses × 3 handling × used_default bit × value-presence bit | 6×3×2×2 = **72** | **18 V / 54 inconsistent**, assuming reachable source/status | P |
| `V4.VCP.SCHEMA.PRIMITIVE` | seven JSON primitive type labels × seven | 7×7 = **49** | **9 overlapping / 40 disjoint** | P |
| `V4.VCP.SCHEMA.FULL` | boolean/object JSON Schema supported subset and references | ∞ | Refs, unsupported schema vocabularies, actual instance value | P |
| `V4.VCP.GUARD.OPERATOR` | equality operator only | **1** | exactly one normative operator | P/R |
| `V4.VCP.GUARD.SOURCE` | four possible source kinds × equality | **4 candidates** | typed/ancestor constraints apply | P/R |
| `V4.VCP.GUARD.BOOL` | two Boolean operands × two Boolean values | 2×2 = **4** | **2 true / 2 false** | P/R |
| `V4.VCP.GUARD.POINTER` | pointer existence, JSON type, unavailable source, incoming-edge conjunction | ∞ | Domain partition and interaction | P/R |
| `V4.VCP.GRAPH.DAG_0_4` | labeled loop-free directed graphs, n=0..4 | 1+1+4+64+4096 = **4,166** | **573 acyclic / 3,593 cyclic**; *topology only* | P |
| `V4.VCP.GRAPH.FEATURES` | {CYCLES,DYNAMIC_EXPANSION} presence bits | 2^2 = **4** | **1 executable / 3 unsupported** | P |
| `V4.VCP.GRAPH.DEFINITION` | IDs, edge endpoints, duplication, ports, binding, guards, cycles | ∞ | Test invariants and counterexamples | P |
| `V4.VCP.AGG.MEMBER_ROLE` | 4 producer node kinds × 3 output roles as aggregate input | 4×3 = **12** | **2 permitted / 10 forbidden** for upstream RESULT membership | P/R |
| `V4.VCP.AGG.SEMANTIC` | EVALUATE/AGGREGATE × subject+criterion plus Aggregate members | **5 required kind/name obligations** | Binding and snapshot equalities | P/R |
| `V4.VCP.AGG.HANDLING_MAP` | 8 reducers × 7 binary handling choices | 8×2^7 = **1,024** | All maps complete with valid prerequisites; distinguish reducer interactions | P |
| `V4.VCP.AGG.EXCEPTION` | 8 reducers × seven exceptional classes × two actions | 8×7×2 = **112** | Behavior obligations; actual admissibility depends on membership | P/R |
| `V4.VCP.AGG.LOGICAL` | n retained PASS/FAIL members | 2^n for each n≥1 | ALL/ANY/MAJORITY mathematical partitions | P |
| `V4.VCP.AGG.SCORE` | numeric scores, min/max/average | ∞ | Equations, boundaries, algebraic laws | P |
| `V4.VCP.AGG.WEIGHT_SIGN_2` | 2 members with negative/zero/positive weight class | 3² = **9** | **3 admissible / 6 rejected** before filtering | P |
| `V4.VCP.AGG.WEIGHT_GENERAL` | n members × 3 weight-sign classes | 3^n | **2^n−1 admissible / 3^n−2^n+1 invalid** pre-filtering | P |
| `V4.VCP.AGG.WEIGHT_IDENTITY` | permutations, missing/misassigned weights, filtered retention | ∞ | Identity/order interaction required | P/R |
| `V4.VCP.AGG.SEVERITY` | k-level domain and n retained members | k^n | Max rank j in j^n−(j−1)^n cases | P |
| `V4.VCP.POLICY.DECLARATIONS` | activation:2 × selection:2 × admission:3 supported declaration families | 2×2×3 = **12** | Other declaration/port cases separate | P |
| `V4.VCP.POLICY.PATH` | activation → selection → admission short circuit | **5 reachable paths** | All five need actual host/Relay disposition witness | R |
| `V4.VCP.POLICY.ROLE_RESULT` | 3 roles × 3 outcome-object types | 3×3 = **9** | **3 matched / 6 mismatched** | P |
| `V4.VCP.POLICY.EVAL_ORDER` | permutations of three role records | 3! = **6** | **1 valid / 5 invalid** where three records exist | P |
| `V4.VCP.RESOURCE.PRESENCE_BINARY` | 4 kinds × value/min/max presence bits | 4×2³ = **32** | **4 V / 28 I** | P |
| `V4.VCP.RESOURCE.PRESENCE_TRINARY` | 4 kinds × absent/null/present for value/min/max | 4×3³ = **108** | **18 V / 90 I** | P |
| `V4.VCP.RESOURCE.RANGE_ORDER` | min < max, =, > | **3** | **2 V / 1 I** | P |
| `V4.VCP.EXEC_OBS.PRESENCE` | 3 required + 1 optional (error) fields | 2^4 = **16** | **2 V / 14 I** | P |
| `V4.VCP.RUN_RECORD.PRESENCE` | 14 required + 4 optional | 2^18 = **262,144** | **16 V / 262,128 I**, presence-only | P, symbolic reduction |
| `V4.VCP.NODE_RECORD.PRESENCE` | 12 required + 8 optional | 2^20 = **1,048,576** | **256 V / 1,048,320 I**, presence-only | P, symbolic reduction |
| `V4.VCP.RECORD.LINEAGE` | source, binding, upstream snapshot, errors, resource usage, timing | ∞ | Independently anchored consistency laws | P/R |
| `V4.VCP.LIFECYCLE.PHASES` | PENDING,READY,RUNNING,TERMINAL × same next phase | 4×4 = **16** | **5 progression, 4 stutters, 7 non-progression pairs** | P/R |
| `V4.VCP.LIFECYCLE.RESULT` | four terminal record states × four Result dispositions for EVAL/AGG | 4×4 = **16 per kind** | **6 compatible / 10 incompatible per kind** | P/R |
| `V4.VCP.LIFECYCLE.REASON` | declared nonexecution reason enum | **9** | Each normatively reachable applicable reason | P/R |
| `V4.VCP.CANCEL.ELIGIBILITY` | 2 cancellation phases × 3 admission outcomes | 2×3 = **6** | **2 eligible / 4 forbidden** | P/R |
| `V4.VCP.EXT.REQUIRED` | required flag × consumer support flag | 2×2 = **4** | **3 consumable / 1 unsupported** | P |
| `V4.PROVIDER.FEATURE_FLAGS` | streaming,cancellation,deadlines,resource_reporting | 2^4 = **16** | **16 valid flag combinations** | P/R selective |
| `V4.PROVIDER.VCP_COMPAT` | capability declares VCP × manifest supports version | 2×2 = **4** | **3 permitted / 1 invalid** | P |
| `V4.PROVIDER.INIT` | valid session initialization / fail-and-close | **2 branches** | Version selection/preferences also unbounded | P/R |
| `V4.PROVIDER.INVOKE.DEADLINE` | deadline feature flag × deadline supplied | 2×2 = **4** | **3 permitted / 1 forbidden** | P |
| `V4.PROVIDER.INVOKE.BUDGET` | budget present × VCP enabled | 2×2 = **4** | **3 permitted / 1 forbidden** | P |
| `V4.PROVIDER.OUTCOME.SHAPE` | 4 terminal states × output presence × error presence | 4×2×2 = **16** | **4 V / 12 I** | P/R |
| `V4.PROVIDER.OUTCOME.USAGE` | usage present × 4 states × resource flag × VCP enabled | 2×4×2×2 = **32** | **20 permitted / 12 forbidden** | P |
| `V4.PROVIDER.EVENT.ELIGIBILITY` | 6 event kinds × stream flag × resource flag × VCP enabled | 6×2×2×2 = **48** | **17 permitted / 31 forbidden** | P/R valid only |
| `V4.PROVIDER.EVENT.SEQUENCE` | valid strictly increasing positive sequence, gaps allowed | 1…2^53−1 | Symbolic invariant, bound/overflow tests | P/R |
| `V4.PROVIDER.ATTEMPT.TRANSITION` | 4 correlation classes × 4 actions | 4×4 = **16** | **5 conditionally permitted / 11 forbidden** | P/R valid only |
| `V4.PROVIDER.CANCEL.ELIGIBILITY` | 4 correlation classes × cancellation feature bit | 4×2 = **8** | **3 permitted / 5 forbidden** | P/R |
| `V4.PROVIDER.DEADLINE.RACE` | 4 terminal outcomes × requested-cancel bit × deadline phase {absent,unexpired,expired} | 4×2×3 = **24** | **12 eligible / 12 forbidden**, given accepted constraints | P/R |
| `V4.PROVIDER.TRANSPORT.METHOD` | initialize,invoke,cancel,event | **4** | 3 RPC request methods, 1 notification | X |
| `V4.ERROR.NAMES` | VCP 33 + Provider 8 + Relay 10 declared named codes | **51 identifiers** | Error-source and layer-specific guards; do not cross product blindly | P/R |
| `V4.RELAY.PORTS` | Catalog,Binder,Driver,Transport,Store,Observer | **6 ports / 7 public methods** | Full legal signature/return behavior, unspecified custom-failure space separately noted | P/R |
| `V4.RELAY.SCHEDULER` | four logical VCP phases and Relay wave/barrier rules | **4 phases; event alphabet unspecified** | Derive a local model with explicit bounds; no invented normative total | P/R |
| `V4.RELAY.ENTRYPOINT` | every *actually shipped* Python/CLI/MCP/HTTP interface | up to **4 surface classes** | Discover supported operations; do not assume parity | X |

**Do not compute an unqualified grand sum.** Most rows deliberately overlap. `V4.VCP.RESULT.SEMANTIC_AXIS` is a quotient of `WIRE_AXIS`. `RESOLVE.RAW` and `RESOLVE.UNBOUND` are candidates, not proven runtime reachability. `RUN_RECORD.PRESENCE` and `NODE_RECORD.PRESENCE` are combinatorial structural masks that must be reduced by proof before allocating pytest objects.

### Three mandatory source-sensitive corrections

1. **Graph edges are not generic data pipes.** Current VCP graph edges establish dependency/order and can carry guards. Data transfer occurs through explicit `UPSTREAM_OUTPUT` bindings; control arises from CONTROL Decisions and routing. Do **not** invent a normative `edge_type ∈ {VALUE,ORDER,CONTROL}` wire enum or declare 48 edge-type cases as normative. Instead separately test `16 producer-kind × consumer-kind candidate pairs`, typed binding rules, dependency ordering, guard/control combinations and their actual legal subset.
2. **Result counts use two distinct quotients.** 1,024 wire categorical forms yield 66 valid; after absent/null are semantically identified for the four categorical fields, there are nine valid semantic states. Eight observation-presence bits across those nine states yield 2,304 masks and 960 valid under stated fixture constraints. **This does not test arbitrary observation values or all judgment schemas.** Keep those separate.
3. **Availability cannot honestly be called 128/232 or any V/I/N split from only four kinds/four sources/six statuses/three handlers.** The full reachability tuple includes source, producer output role, port requiredness, target schema, prior trace and handling. The raw 360 candidate coordinates are an index, not a complete actual scenario domain. Enumerate the real typed subclasses and derive conditional status reachability; do not use prior-Golden figures.

---

## 4. Explicit categorical proofs for the largest finite classes

### 4.1 Result 1,024 → 66

Each wire combination has disposition ∈ {EXECUTED,SKIPPED,DEFERRED,CANCELLED} and four other axes each represented as absent/null/option-1/option-2; hence `4 × 4^4 = 1,024`.

Independent, disjoint valid partitions:

1. Three nonexecution dispositions: other four axes absent/null: `3×2^4=48` valid.
2. EXECUTED + ERROR: applicability/determination/verdict absent/null: `2³=8` valid.
3. EXECUTED + SUCCESS + NOT_APPLICABLE: determination/verdict absent/null: `2²=4` valid.
4. EXECUTED + SUCCESS + APPLICABLE + UNKNOWN: verdict absent/null: `2` valid.
5. EXECUTED + SUCCESS + APPLICABLE + KNOWN: verdict absent/null/PASS/FAIL: `4` valid.

**Total valid = 48+8+4+2+4 = 66. Invalid = 1,024−66=958.** All 1,024 should be independent named cheap parameter cases, not one loop with a single shared assertion.

With absent/null identified: nonexecution 3; error 1; not applicable 1; unknown 1; known without verdict/PASS/FAIL 3 → **nine** valid semantic states.

### 4.2 Observations 2,304 → 960

Eight presence bits correspond exactly to: `judgment`, `score`, `severity`, `evidence`, `output`, `usage`, `metadata`, `extensions`. Among nine valid semantic Result states, three are successful/applicable/KNOWN and permit all eight bits: `3×2^8=768`. Six other states forbid first three observation fields, but permit five other presence bits: `6×2^5=192`. Thus **960 valid and 1,344 invalid out of 2,304**, under an independently valid judgment schema (`true`) and independently valid present-field payload values. Test explicit JSON `null` and value/type boundaries in separate tagged families; do not equate a present null with absent information indiscriminately.

### 4.3 Graph topology 4,166 → 573

Enumerate each labeled simple graph without self-loops, `n=0,1,2,3,4`. For each n, `n(n−1)` ordered potential directed edges. Hence totals: `1,1,4,64,4096`, summing to 4,166 candidates. Independently detect cycles; DAG counts: `1,1,3,25,543` = 573. Cyclic = 3,593. The graph's executable validity additionally requires allowed node count, unique IDs, typed ports/bindings, membership, and guards. **Do not multiply every DAG by 4^n and pretend that measures complete valid graphs.**

### 4.4 Massive record-presence universes: symbolic proof, not million test objects

For any object with r fields that are unconditionally required and o fields that are independently optional, there are `2^(r+o)` binary presence masks. Exactly `2^o` satisfy the **required-field presence subconstraint**, because each of the r required bits must be 1. Every other mask is rejected by the same conjunctive required-field rule. This is a valid reduction **only for the required-field-presence projection**, not for full semantic validity. Verify the schema actually expresses independent requiredness before applying this proof.

- RunRecord r=14,o=4: `262,144 = 16 present-required + 262,128 missing-required`.
- NodeRecord r=12,o=8: `1,048,576 = 256 present-required + 1,048,320 missing-required`.

**Execute:** all 16 and all 256 optional-field masks with required fields valid; for each required field, at least one single-field-deletion rejection with a stable ID; representative compound deletions and an independent schema-level monotonicity/metamorphic check. **Do not** generate 1.3 million pytest items. Document each mathematically proven unexecuted mask range and why the same required-field rule rejects it. Any non-monotone conditional constraints belong to a separate exhaustive or bounded family.

### 4.5 Reducer handling maps

Seven exceptional-member categories `UNKNOWN,ERROR,SKIP,DEFERRED,CANCELLED,NOT_APPLICABLE,MISSING`; each must explicitly map to REJECT or IGNORE. `2^7=128` handling configurations per standard reducer, eight reducers → **1,024** complete maps. Enumerate all maps cheaply with compliant data. For each of 8×7×2=112 specific exceptional-category/action laws, assert both expected filtering/rejection and changes in retained data, identity, usage/evidence when specified. Then test the smaller set of essential cross-member interactions: empty-after-filtering, mixed good/bad members, multiple retained unequal weights, tie/threshold, ordering. Higher member sequence lengths are mathematically unbounded; establish laws and residual limits.

### 4.6 Provider feature/event legality

Four independent advertised feature bits give **16** manifest combinations. Each of six event kinds must obey the specific feature gates for streaming, resource usage and VCP-aware event payloads. Six kinds × three feature flags gives **48 event-eligibility candidates**, separately **17 permitted / 31 forbidden** under current normative constraints. Execution with correct providers generates only 17 permitted classes; the forbidden 31 are cheap contract-rejection checks and are **not** fake bad-provider Relay scenarios. Test valid event sequencing, zero event, gap allowed, overflow rejected, and that all events precede final Outcome, with exact correlation/usage assertions.

---

## 5. Runtime and composition, without redundant Cartesian explosions

### 5.1 Actual OpenVerify connection semantics

A graph connection concept must be separated into:

- **Dependency edge:** producer must reach its prescribed terminal outcome before consumer becomes ready; edges alone **do not transfer data**.
- **Typed value binding:** consumer input explicitly references an upstream declared output, with role, schema and strict-ancestor constraints.
- **Guard:** equality comparison against declared source/pointer/value; all incoming guards constrain readiness; missing operands yield the prescribed false/ineligible behavior.
- **Control:** CONTROL emits a Decision; route/stop/defer/retry semantics affect eligibility, not an invented generic control-valued edge.
- **Aggregation:** an AGGREGATE's authored, ordered member identities point to upstream RESULT roles. Execution predecessors and aggregate membership are distinct.

**Coverage matrix:** 4×4=**16** producer/consumer kind candidates; classify which output roles and semantic bindings permit actual dataflow; test each permitted typed boundary, each structurally rejected boundary cheaply, and each **distinct** lifecycle propagation rule through real Relay. Treat no-data ORDER dependence separately from typed consumption. This avoids unnecessary products over all graph topologies.

### 5.2 Minimal irreducible graph witnesses

For each motif, assert exactly which new property it introduces:

| Motif | Shape | Unique behavior that must be checked |
|---|---|---|
| `INDEPENDENT` | A, B | No implicit dataflow, isolation, no unwanted ordering obligation |
| `EDGE` | A→B | Dependency completion + explicitly bound vs unbound input distinction |
| `CHAIN` | A→B→C | Transitive readiness/lineage and no stale intermediate value |
| `FORK` | A→B and A→C | Two consumers receive correct snapshots; independence after fork |
| `JOIN` | A→C and B→C | Fan-in waits for prerequisites and combines declared inputs only |
| `DIAMOND` | A→B/C→D | Shared ancestor correctness, coherent join, deduped upstream lineage |
| `ROUTE` | CONTROL→branches | Exactly intended branch eligible, excluded branches recorded properly |
| `GUARDED_JOIN` | guarded inputs→join | False guard and precursor handling precedence |
| `AGG_FANIN` | multiple RESULT members→AGGREGATE | Authored ordered membership, filtering, typed reducer result |
| `PARALLEL_BARRIER` | independent wave + CONTROL barrier | Relay scheduling wave/barrier semantics and record order |
| `STOP_CANCEL` | running siblings/descendants | Termination/cancellation propagation, usage, no later commit |
| `MULTIRUN` | two or more concurrent runs | No input/event/record leakage; correct provider synchronization |

Motifs beyond EDGE are **not** a mandate to multiply all four node kinds at every node. Make only the combinations necessary to show each semantic operation and interactions. If a new motif is irreducible under the normative rules, add it as its own ID; do not bury it inside a miscellaneous stress test.

### 5.3 What can be reduced mathematically

1. **Required presence:** proven conjunction permits counting but not executing all invalid masks (Section 4.4).
2. **Independent nodes:** prove input/record/event disjointness and absence of shared mutable state; execute simple two-run/two-node witnesses plus isolate backend/provider where contract allows shared services. Independence is a **property to prove and test**, not assumed from lack of an edge.
3. **Composition:** induction over topological order when node-local behavior, exact typed input resolution and scheduler eligibility form a closed contract. Verify base cases; verify successor composition and noninterference; explicitly isolate shared state, cancellation and control barriers outside naive induction.
4. **Reducers:** commutative reducers permit multiset equivalence **only after** proving identities/evidence ordering/weights do not create observable differences. Do not apply such reduction to identity-weighted or ordered evidence output.
5. **Provider event traces:** validate finite automaton legality with cheap abstract checker, test normal legal terminal/event classes through actual Relay; do not simulate arbitrary external violations.
6. **Pairwise vs higher order:** calculate every cross-family pair candidate but execute only normative interacting pairs; use 3-way/higher tests for provable non-pairwise coupling (admission×cancellation×record; filtering×weights×membership; guard×route×join; completion×cancellation×usage; manifest features×event kind×VCP). Do **not** assert pairwise coverage implies higher-order correctness.

### 5.4 Production Relay's distinctive rules to witness

- Ready non-CONTROL nodes execute in bounded waves; entire wave settles before successor dispatch.
- Record acceptance within a wave follows definition order; independent provider completions may arrive in different orders.
- CONTROL nodes create serial barriers.
- Shared in-process providers serialize unless explicitly concurrency safe; separate runs isolate semantic state.
- Completed terminal occurrences never change after later cancellation.
- Host/task cancellation differs from protocol cancellation; determine which paths return a terminal record vs propagate a cancellation exception.
- Resource usage from accepted/failed/interrupted work is recorded as specified; authoritative final usage, if normative, supersedes intermediate resource events.
- Route exclusions, guards, nonexecution and aggregate handling are distinct causes; assert recorded reasons and non-invocation.

**Limits:** Relay has no fully normative closed event alphabet for every scheduler implementation detail. Define a transparent bounded abstract model with assumptions and test all *specified* legal transitions. Never invent a purported complete universal scheduler-state count. Mark unsupported retry/replay/recovery and uncontracted custom-port malicious behavior as explicit scope exclusions.

---

## 6. Exact test organization and tag vocabulary

Root: `tests/golden_v4/` only for new Golden V4. Each family gets a separately collected test module (or submodule), stable IDs and separate JSONL results:

```text
tests/golden_v4/
  conftest.py                     # fixtures, strict collection, native assertions
  oracle/                        # independent normative models; NO Relay imports
  generators/                    # deterministic domain enumerators, symbolic ranges
  reporters/                     # per-case tagged result recorder + coverage check
  test_vcp_wire.py
  test_vcp_definition.py
  test_vcp_artifact_evidence.py
  test_vcp_result_axes.py
  test_vcp_result_observations.py
  test_vcp_decision.py
  test_vcp_node_roles.py
  test_vcp_bindings_sources.py
  test_vcp_resolution.py
  test_vcp_schemas_guards.py
  test_vcp_graph_structure.py
  test_vcp_aggregation.py
  test_vcp_policies.py
  test_vcp_resources.py
  test_vcp_records.py
  test_vcp_lifecycle_cancel.py
  test_provider_manifest_capability.py
  test_provider_init_invoke.py
  test_provider_events_outcomes.py
  test_provider_lifecycle.py
  test_provider_transport.py
  test_errors_extensions.py
  test_relay_independent_node.py
  test_relay_typed_connections.py
  test_relay_composition_motifs.py
  test_relay_policies_control.py
  test_relay_aggregation.py
  test_relay_scheduler.py
  test_relay_cancellation_resources.py
  test_relay_ports_catalog_binder.py
  test_relay_ports_driver_transport.py
  test_relay_ports_store_observer.py
  test_relay_record_lineage.py
  test_entrypoints.py
  test_inventory_coverage_gate.py
  test_oracle_mutation_sensitivity.py
```

The inventory table's detailed family names are authoritative; test files may contain multiple **explicitly distinguishable** families, but not one opaque `test_everything` function.

### Tag format

`V4.<LAYER>.<OBJECT>.<RULE>.<COORDINATE>`

Examples:

```text
V4.VCP.RESULT.WIRE_AXIS.EXECUTED-SUCCESS-APPLICABLE-KNOWN-PASS
V4.VCP.RESULT.OBS_MASK.KNOWN_PASS.BITS_10110110
V4.VCP.DECISION.DEST.ROUTE-ABSENT
V4.VCP.GRAPH.DAG_0_4.N4.EDGEBITS_000000100101
V4.VCP.AGG.HANDLING_MAP.WEIGHTED_AVERAGE.MASK_0101001
V4.VCP.RESOLVE.RUNTIME.RUN_INPUT-ABSENT-OPTIONAL-OMIT
V4.PROVIDER.EVENT.ELIGIBILITY.EVIDENCE-STREAM1-VCP1-RESOURCE0
V4.RELAY.MOTIF.DIAMOND.UPSTREAM-LINEAGE
V4.RELAY.PORT.STORE.PUT.SNAPSHOT-ISOLATION
```

- Include a **short readable description**, **normative clause ID**, and **structural coordinate** alongside every ID.
- Case IDs must be deterministic across systems and independent of execution order/sharding. Numeric case indexes may assist but must not be the sole identity when semantic coordinates exist.
- Small and moderate enumerations use `pytest.mark.parametrize(..., ids=[...])`. Each candidate appears as its **own collected pytest test item** and retains its exact ID in junit/JSON output; avoid monolithic loops.
- For million-scale **logically invalid** presence masks, do not generate a million pytest items. Store the complete symbolic ranges, exact cardinalities, a mechanically checked reduction/proof and an independent test for each generating rule and boundary. Every executed case still has its own case ID; every unexecuted subspace has a stable **proof-subspace ID**, formula, representative checks, and explicit status `PROVED`, never `PASSED`.
- For an intentionally batched large domain (only if absolutely necessary), the reporter must emit **one JSONL outcome per case**, including every failed ID, independent expected/actual and a single-case rerun selector. `pytest` must also raise separate failures keyed by those IDs or materialize separate failure tests; a single `failed 57 of 10,000` summary is prohibited.
- No `except Exception: pass`, no broad exception-as-success assertions, no `xfail` or `skip` for a supported untested obligation, and no placeholder expectation.

### Pytest markers

```text
@golden_v4            all new Golden tests
@vcp / @provider / @relay / @entrypoint
@wire / @result / @decision / @binding / @availability / @guard
@aggregate / @policy / @record / @lifecycle / @port / @scheduler
@valid / @invalid / @unsupported / @ambiguous
@cheap / @runtime / @integration
@direct / @property / @composition / @proof_check
```

`@ambiguous` never asserts a fabricated normative result; ambiguity belongs in the explicit unresolved-inventory report, with bounded exploratory tests separate from certification. `@unsupported` checks supported rejection only when specified.

### Machine-readable per-case record

```json
{
  "case_id": "V4.VCP.RESULT.WIRE_AXIS.EXECUTED-SUCCESS-APPLICABLE-KNOWN-PASS",
  "obligation_ids": ["V4.O.VCP.RESULT.KNOWN_VERDICT"],
  "normative_sources": [{"path": "spec/draft/result.md", "clause_id": "...", "digest": "..."}],
  "family": "V4.VCP.RESULT.WIRE_AXIS",
  "projection_axes": {"disposition": "EXECUTED", "execution_outcome": "SUCCESS"},
  "classification": "VALID",
  "expected": {"accepted": true},
  "observed": null,
  "witness_type": "CHEAP",
  "status": "NOT_RUN",
  "proof_id": null,
  "duration_ms": null
}
```

No `case_id` may belong to two contradictory expectations. Cases may witness multiple obligations only when the exact assertions for **each obligation** are present.

---

## 7. Expected results: independence, freeze, and mutation detection

1. **Independent authoring:** Write the normative inventory, case generators, pure expected outputs and accepted/rejected partitions without importing production semantic helpers. Mathematical oracle functions must be independently derived, testable and small enough to inspect.
2. **Freeze** normative file hashes, inventory hashes, all case coordinates and expected outcomes **before** authoring adapters that call production interfaces. Commit or sign the frozen inventory; scripts must refuse updates to the frozen release without a new version.
3. **Test execution:** production may be imported only by execution adapters and tests, not by expected-output authoring.
4. **Exact observables:** state, consumed values, output values, errors where normative, invocation/non-invocation, ordering, route exclusions, terminal states, evidence, usage, lineage, and persistence. Time/floating tolerance only when explicitly allowed by normative rules.
5. **Mutation sensitivity:** deliberately perturb **actual evaluated oracles/tests**: valid→invalid enum, swapped input provenance, changed provider version, wrong result state, missing resource measurement, forbidden invoke after guard, changed reducer retained-weight identity, reordered branch membership, missing recorded cancellation. Each mutation must be detected, with a named case ID; do not count mutations that only compare constants within a stand-alone mock.
6. **Provider compliance:** real Relay scripted providers may emit `COMPLETED`, `ERROR`, `CANCELLED`, `DEADLINE_EXCEEDED` only when legal under their manifest and invocation lifecycle. Invalid-provider syntax/error tests remain cheap Provider Contract validator cases.
7. **Allowed nondeterminism:** event timing, legitimate scheduling order and numeric rounding where unspecified are encoded by **invariants**, not by freezing arbitrary production observations.

---

## 8. Coverage accounting and failure gate

Create `conformance/golden-v4/` with:

```text
README.md
BLUEPRINT.md
NORMATIVE_CLAUSES.jsonl
NORMATIVE_SOURCE_HASHES.json
CONTRACT_INVENTORY.md
COUNT_PROOFS.md
COMPOSITION_PROOFS.md
REDUCTION_LEDGER.jsonl
DOMAIN_LIMITS.md
CASES.jsonl
OBLIGATIONS.jsonl
WITNESSES.jsonl
FROZEN_EXPECTATIONS/
GOLDEN_FAILURES.jsonl
COVERAGE.json
COVERAGE_REPORT.md
EXECUTION_REPORT.json
MUTATION_REPORT.json
```

**Run-generated reports** must go outside tracked normative/frozen files or be committed in a separate evidence-only step; running the test suite must never silently rewrite expected results. Hash verification before every run. Run-specific environment and timing artifacts are not normative evidence by themselves.

For **every family**, report:

- precise projection definition, all axis labels and values, source clauses, source digests;
- `C,V,I,N,U,A` where mathematically meaningful; proof of classifications;
- actual collected **pytest case count**, **cheap run count**, **real Relay invocation count**;
- obligations directly tested / compositionally proved / failed / missing / unsupported / ambiguous;
- per-case case IDs and witness/proof IDs; duration and repro command;
- sample of each class, plus all failures and all unproved branches;
- proof that test selection did not silently remove distinct behavior;
- whether type/property domains are genuinely bounded or unbounded.

**Coverage gate fails certification when:**

- a normative clause or a public supported method is unindexed;
- a finite enumerated candidate has no classification or an arithmetic identity fails;
- a stated `INAPPLICABLE` classification lacks a contract-derived impossibility proof;
- an `INVALID` family lacks its cheap rejection test or a valid reduction proof;
- any `VALID` local behavior, permitted transition or contract-distinct interaction lacks an exact test or valid proof;
- a reduction relies on unverified independence, absent ordering or uncontracted provider behavior;
- a test claims a witness without its asserted observable trace;
- assertions and frozen expectations share production implementation logic;
- a failure is hidden behind a broader successful batch;
- an independent oracle mutation is not detected;
- a case fails, a freeze hash differs, or the actual tested production import source does not match the pinned revision.

Unsupported and ambiguous entries are **separate** and explicitly visible; a green supported-profile verdict must state their scope and cannot imply universal arbitrary-provider/graph proof.

### Summary table, one row per family

`Family | Formula | C | V | I | N | U | A | Required obligations | Direct passed | Proven | Failed | Missing | Cheap cases | Relay calls | Seconds | Source`.

**Never** report one global candidate sum over overlapping projections; a global unique obligation count may be reported only after canonical deduplication by clause and exact behavior (with auditable crosswalk).

---

## 9. Implementation order and gates

1. Create isolated worktree from pinned production checkout, new `test/openverify-golden-v4` branch. Verify `git status --short` clean and runtime import points to pinned source. No references to any prior Golden test/source, including historical folders.
2. Read and hash all **current** normative files, all 24+9 roots (actual numbers independently confirmed), profiles, Relay public interfaces. Generate the clause and field inventory. Gate: all source roots/methods accounted for.
3. Recompute every finite projection in Section 3 from named actual enum/field values; write pure counting scripts. Gate: every formula checked independently and semantic/domain mismatches surfaced; no silent reconciliation.
4. Classify all candidate local states and all documented transitions. Derive reachability for availability using typed producer role, requiredness, schema and trace (do not trust raw 360 split). Gate: each defined finite slice reconciles.
5. Define all cross-module composition proof obligations and reduction assumptions; choose minimum real-runtime witnesses. Gate: no unproved independence assumptions enter coverage.
6. Author independent expectation fixtures, reference math and exact outcome/oracle specifications, frozen hashes. Commit frozen artifacts separately before production adapters.
7. Implement cheap **per-case tagged** parametric tests; start with Results, Decisions, wire presence, graphs, schemas, reducers, policy, Provider Contract.
8. Implement small real Relay tests from typed connection and runtime obligation ledger; cover legal provider outcomes, route/guard, join, control wave, cancellation, concurrency, usage and records. Tag every scenario and its individual asserted obligations.
9. Implement all six port methods as legal-boundary tests and supported entrypoint flows. Do not invent malformed external-provider execution requirements.
10. Create independent mutation/counterexample checks. Verify test outcome sensitivity and failure identity.
11. Run targeted tests and inventory dry run, then complete Golden V4 once. Minutes are acceptable. Use deterministic sharding without changing expectations.
12. Generate full release report, source/expectation hashes, failing case list, exact per-family math, reduction proof ledger, timings and revision IDs; commit. No production/spec edits; no push/merge.

**Suggested stable commands**, adapt only to actual valid entrypoints after inspection:

```bash
python -m pytest -q tests/golden_v4/ --collect-only
python -m pytest -q tests/golden_v4/ -m 'golden_v4 and cheap'
python -m pytest -q tests/golden_v4/ -m 'golden_v4 and runtime'
python -m pytest -q tests/golden_v4/ -m 'golden_v4 and integration'
python -m pytest -q tests/golden_v4/
```

Reporter should additionally support: `python -m tools.golden_v4.report --verify-inventory`, `--verify-freeze`, `--case-id <EXACT_ID>`, `--summary`, and JSON/JUnit exports; the builder should implement these entrypoints rather than documenting nonexistent commands.

**Final release conditions:** normative inventory complete for declared current supported profile; mathematical partitions reconciled; every valid local requirement and distinct composition/runtime obligation directly witnessed or proved; all invalid requirements rejected cheaply or discharged by proof; all tests actually passing; failure-ID reports verified with deliberate mutation; all unsupported/ambiguous/unbounded limitations explicitly enumerated. Otherwise label **NOT CERTIFIED**, even if all executed tests pass.

---

## 10. Mandatory final human-readable answer from the implementer

Give one concise overview with:

1. Branch/commit, production SHA, tested import path, clean worktrees, source/spec/frozen expectation hashes.
2. The **full Section 3 table** updated with actual independently verified counts, and for each family: planned/collected/pass/fail/missing/allowed proof reductions, actual Relay calls and wall time.
3. The exact list of every failed `case_id`, its one-line expected vs observed and reproduction command; if none, `0 failed, reporter mutation check passed`.
4. Separate lists of all `UNSUPPORTED`, `AMBIGUOUS`, `UNBOUNDED`, `SAMPLED`, and `NOT YET PROVED` items.
5. The proof ledgers for major reductions (Result quotient, optional-record presence, DAG induction, weighted identity, Provider state machine), all indexed by normative clause.
6. Exact counts for total **unique supported obligations**, direct witness obligations, formally/inductively proved obligations, failed, missing; never use number of pytest items as requirement count.
7. A binary scoped verdict: `CERTIFIED FOR DECLARED SUPPORTED PROFILE` only when justified, otherwise `NOT CERTIFIED`, with precise blockers.

*Nothing in this blueprint grants completeness without the independently checked current normative contract inventory and executable evidence.*
