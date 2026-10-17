# OpenVerify Golden v4 implementation and audit

## 1. Source and integrity

Branch: `test/openverify-golden-v4`. Pinned production: `5f17f402a270882f244a54dde25eda92a085eb39`. Independent byte-preserving freeze commit: `147baf1`. Final implementation/evidence commit is the branch HEAD; no push/merge/tag/release was performed.

Imported source: `C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\golden-v4\src\openverify\__init__.py`; SHA-256 `4be5cfedb030a728985d7da72a9cc5da7035deac2df00eb90e5d8ab0bddec675`.

Source inventory SHA-256: `6f1bc6bb1533516b1f6f1325bbb2632148f00136e572038329bf41c0e0900ccc`. Freeze manifest SHA-256: `73ddbdb4df7a48e51f159cfc5bbce8d9d5dfaf6276ebb9def4db4bc224ba4fb3`. Frozen cases SHA-256: `63339eed66c39fd6e4cbd44a9c7eba881592737d7e3593d7cc6ebd83b51476de`. Blueprint SHA-256: `3c73fee1826a65d7101c375d21421988a798ae6ee336824546b055ca92d5a6d2`.

All original frozen bytes and production/spec/profile files verified unchanged. The isolated worktree is committed separately from the user's original checkout.

## 2. Every blueprint family

Obligation totals are not established: canonical deduplication and reviewed clause-level assertion links are incomplete. Pytest pass/fail counts remain separate in COVERAGE.json; they are never substituted for obligation totals. The 78 overlapping projections have no grand candidate total. See COUNT_PROOFS.md for the projection assumptions.

| FAMILY | FORMULA | C | VALID | INVALID | IMPOSSIBLE | UNRESOLVED | SUPPORTED OBLIGATIONS | DIRECT PASSED | PROVED | FAILED | MISSING | PYTEST CASES | RELAY API CALLS | DURATION |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V4.WIRE.ROOTS | 24 VCP + 9 Provider | 33 | 33 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 33 | 0 | 0.14063960005296394 |
| V4.WIRE.JSON | UTF-8, duplicate keys, nonfinite, unknown props, version marker, nested JSON | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 9 | 0 | 0.0017929000896401703 |
| V4.VCP.DEF.PRESENCE | 2^(9+3); V=2^3 | 4096 | 8 | 4088 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4096 | 0 | 1.5243135993368924 |
| V4.VCP.CRITERION.PRESENCE | 2^(2+2); V=2^2 | 16 | 4 | 12 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 16 | 0 | 0.00529530004132539 |
| V4.VCP.ARTIFACT.PRESENCE | 2^(3+3); V=2^3 | 64 | 8 | 56 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 64 | 0 | 0.017279400024563074 |
| V4.VCP.EVIDENCE.MEANING | (2^4-1)*2^3; invalid=2^3 | 128 | 120 | 8 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 128 | 0 | 0.03807310009142384 |
| V4.VCP.RESULT.WIRE_AXIS | 4*4^4; V=3*2^4+2^3+2^2+2+4 | 1024 | 66 | 958 | 0 | 0 | not established | not established | 1 proof(s); obligation count unreviewed | not established | unreconciled | 1024 | 0 | 0.316599199839402 |
| V4.VCP.RESULT.SEMANTIC_AXIS | 4*3^4; V=3+1+1+1+3 | 324 | 9 | 315 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 324 | 0 | 0.09050940026645549 |
| V4.VCP.RESULT.OBS_MASK | 9*2^8; V=3*2^8+6*2^5 | 2304 | 960 | 1344 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 2304 | 0 | 0.8274456000945065 |
| V4.VCP.RESULT.VALUES | observed judgment,score,severity,evidence,output,usage,metadata,extensions | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 12 | 0 | 0.004002300061983988 |
| V4.VCP.RESULT.PROJECTION | 9 semantic states; 2 binary+UNKNOWN+ERROR+SKIP | 9 | 5 | 4 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 9 | 0 | 0.0034339000121690333 |
| V4.VCP.DECISION.DEST | 6*4; V=1+5*2 | 24 | 11 | 13 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 24 | 0 | 0.006116999982623383 |
| V4.VCP.DECISION.ROUTE | destination Ã— reachable direct successors/guards/control | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 4 | 0.17932200003997423 |
| V4.VCP.NODE.ROLE | 4*3; V=4 INFORMATION+2 RESULT+1 DECISION | 12 | 7 | 5 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 12 | 0 | 0.026331799948820844 |
| V4.VCP.NODE.PRIMARY | required `result` or `decision`, auxiliary INFORMATION, duplicate/wrong role | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 15 | 0 | 0.030566199973691255 |
| V4.VCP.NODE.INVOKED_RESULT | 2*9; 2*(ERROR+NOT_APPLICABLE+UNKNOWN+3 KNOWN) | 18 | 12 | 6 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 18 | 12 | 0.5739331999793649 |
| V4.VCP.BIND.IDENTITY | 2^4; conjunction of four equalities | 16 | 1 | 15 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 16 | 0 | 0.07071270007872954 |
| V4.VCP.PORT.HANDLING | 2*3; required BLOCK, optional OMIT/DEFAULT | 6 | 3 | 3 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 6 | 0 | 0.008964099979493767 |
| V4.VCP.PORT.DEFAULT | 2 presence states | 2 | 1 | 1 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 2 | 0 | 0.0037586999824270606 |
| V4.VCP.SOURCE.KIND | 4 disjoint source constructors | 4 | 4 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 0 | 0.006889200012665242 |
| V4.VCP.SOURCE.POLICY | 4*3; only 3 pregraph source kinds | 12 | 9 | 3 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 12 | 0 | 0.021991200075717643 |
| V4.VCP.RESOLVE.HANDLER | 6*3 | 18 | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 18 | 18 | 0.6794628000352532 |
| V4.VCP.RESOLVE.CONSUMER | 4*6*3 | 72 | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 72 | 72 | 3.9625474003260024 |
| V4.VCP.RESOLVE.RAW | 4*4*6*3 | 288 | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 288 | 0 | 0.061517499678302556 |
| V4.VCP.RESOLVE.UNBOUND | 4*1*6*3 | 72 | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 72 | 0 | 0.015590299939503893 |
| V4.VCP.RESOLVE.RECORD_BITS | 6*3*2*2; V=3 AVAILABLE+5*3 unavailable | 72 | 18 | 54 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 72 | 0 | 0.02259899998898618 |
| V4.VCP.SCHEMA.PRIMITIVE | 7*7; seven diagonal + integer/number both ways | 49 | 9 | 40 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 49 | 0 | 0.10464579990366474 |
| V4.VCP.SCHEMA.FULL | boolean/object JSON Schema supported subset and references | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 10 | 0 | 0.008884399983799085 |
| V4.VCP.GUARD.OPERATOR | equality only | 1 | 1 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 1 | 0 | 0.0005074000218883157 |
| V4.VCP.GUARD.SOURCE | 4 source constructors; reachability conditional | 4 | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 4 | 0.10308069997699931 |
| V4.VCP.GUARD.BOOL | 2*2; equality diagonal | 4 | 2 | 2 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 4 | 0.08975699997972697 |
| V4.VCP.GUARD.POINTER | pointer existence, JSON type, unavailable source, incoming-edge conjunction | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 4 | 0.11195050002424978 |
| V4.VCP.GRAPH.DAG_0_4 | sum(n=0..4) 2^(n(n-1)); source-set inclusion/exclusion recurrence | 4166 | 573 | 3593 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4166 | 0 | 5.019414099311689 |
| V4.VCP.GRAPH.FEATURES | 2^2 feature subsets | 4 | 4 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 0 | 0.0028371000371407717 |
| V4.VCP.GRAPH.DEFINITION | IDs, edge endpoints, duplication, ports, binding, guards, cycles | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 7 | 0 | 0.011477000021841377 |
| V4.VCP.AGG.MEMBER_ROLE | 4*3; EVALUATE/AGGREGATE RESULT only | 12 | 2 | 10 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 12 | 0 | 0.05442230001790449 |
| V4.VCP.AGG.SEMANTIC | 2 kinds*2 semantic snapshots + aggregate members | 5 | 5 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 10 | 0 | 0.030739999987417832 |
| V4.VCP.AGG.HANDLING_MAP | 8*2^7 | 1024 | 1024 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 1024 | 0 | 0.5068207006261218 |
| V4.VCP.AGG.EXCEPTION | 8*7*2 behavior laws | 112 | 112 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 112 | 0 | 0.07156880007823929 |
| V4.VCP.AGG.LOGICAL | n retained PASS/FAIL members | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 186 | 0 | 0.11920059996191412 |
| V4.VCP.AGG.SCORE | numeric scores, min/max/average | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 20 | 0 | 0.010190199973294511 |
| V4.VCP.AGG.WEIGHT_SIGN_2 | 3^2; V=2^2-1 | 9 | 3 | 6 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 9 | 0 | 0.003489700029604137 |
| V4.VCP.AGG.WEIGHT_GENERAL | C=3^n; V=2^n-1; I=3^n-2^n+1 | unbounded | None | None | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 8 | 0 | 0.004999799974029884 |
| V4.VCP.AGG.WEIGHT_IDENTITY | permutations, missing/misassigned weights, filtered retention | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 2 | 0 | 0.0011241999745834619 |
| V4.VCP.AGG.SEVERITY | k-level domain and n retained members | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 30 | 0 | 0.025736100011272356 |
| V4.VCP.POLICY.DECLARATIONS | 2*2*3 | 12 | 12 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 12 | 0 | 0.010203300073044375 |
| V4.VCP.POLICY.PATH | 1 inactive+1 unselected+3 admitted | 5 | 5 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 5 | 5 | 0.13629619998391718 |
| V4.VCP.POLICY.ROLE_RESULT | 3*3; role/type diagonal | 9 | 3 | 6 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 9 | 0 | 0.003936799970688298 |
| V4.VCP.POLICY.EVAL_ORDER | 3!; exactly one required order | 6 | 1 | 5 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 6 | 6 | 0.11199030003626831 |
| V4.VCP.RESOURCE.PRESENCE_BINARY | 4*2^3; one nonnull pattern per kind | 32 | 4 | 28 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 32 | 0 | 0.00854269994306378 |
| V4.VCP.RESOURCE.PRESENCE_TRINARY | 4*3^3; V=2*2^2+2+2^3 | 108 | 18 | 90 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 108 | 0 | 0.03068359979079105 |
| V4.VCP.RESOURCE.RANGE_ORDER | <,=,>; <= admits first two | 3 | 2 | 1 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 3 | 0 | 0.0007651000050827861 |
| V4.VCP.EXEC_OBS.PRESENCE | 2^(3+1); V=2^1 | 16 | 2 | 14 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 16 | 0 | 0.009602800011634827 |
| V4.VCP.RUN_RECORD.PRESENCE | 2^(14+4); V=2^4 | 262144 | 16 | 262128 | 0 | 0 | not established | not established | 1 proof(s); obligation count unreviewed | not established | unreconciled | 30 | 0 | 0.020328399987192824 |
| V4.VCP.NODE_RECORD.PRESENCE | 2^(12+8); V=2^8 | 1048576 | 256 | 1048320 | 0 | 0 | not established | not established | 1 proof(s); obligation count unreviewed | not established | unreconciled | 268 | 0 | 0.14395640007569455 |
| V4.VCP.RECORD.LINEAGE | source, binding, upstream snapshot, errors, resource usage, timing | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 7 | 7 | 0.35644760000286624 |
| V4.VCP.LIFECYCLE.PHASES | 4*4; five progression + four stutter + seven other | 16 | conditional | conditional | 0 | phase pair versus explicit transition call; see 5/4/7 partition | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 16 | 0 | 0.002971700072521344 |
| V4.VCP.LIFECYCLE.RESULT | 4*4 per kind; SUCCESS1+ERROR1+NONEXECUTED3+CANCELLED1 | 16 | 6 | 10 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 72 | 0 | 0.8800062999362126 |
| V4.VCP.LIFECYCLE.REASON | nine distinct cause mappings | 9 | 9 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 9 | 9 | 0.21844589998363517 |
| V4.VCP.CANCEL.ELIGIBILITY | 2*3; admission RUN only | 6 | 2 | 4 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 6 | 6 | 0.17491619996144436 |
| V4.VCP.EXT.REQUIRED | 2*2; required AND unsupported excluded | 4 | 3 | 1 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 0 | 0.006273399980273098 |
| V4.PROVIDER.FEATURE_FLAGS | 2^4 independent booleans | 16 | 16 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 16 | 0 | 0.01572710002074018 |
| V4.PROVIDER.VCP_COMPAT | 2*2; declaration implies manifest support | 4 | 3 | 1 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 0 | 0.0038294999685604125 |
| V4.PROVIDER.INIT | success / reject-and-close; version list space unbounded | 2 | 2 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 3 | 0 | 0.005320600030245259 |
| V4.PROVIDER.INVOKE.DEADLINE | 2*2; presence implies feature | 4 | 3 | 1 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 0 | 0.007639999967068434 |
| V4.PROVIDER.INVOKE.BUDGET | 2*2; presence implies VCP | 4 | 3 | 1 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 4 | 0 | 0.0080257999652531 |
| V4.PROVIDER.OUTCOME.SHAPE | 4*2*2; one shape per terminal kind | 16 | 4 | 12 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 16 | 0 | 0.005737700004829094 |
| V4.PROVIDER.OUTCOME.USAGE | 2*4*2*2; absent16 + present with both flags4 | 32 | 20 | 12 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 32 | 0 | 0.07283309995546006 |
| V4.PROVIDER.EVENT.ELIGIBILITY | 6*2^3; 3 advisory*4 + 2 VCP*2 + 1 usage | 48 | 17 | 31 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 65 | 0 | 0.19691150015569292 |
| V4.PROVIDER.EVENT.SEQUENCE | valid strictly increasing positive sequence, gaps allowed | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 9 | 0 | 0.0027342999819666147 |
| V4.PROVIDER.ATTEMPT.TRANSITION | 4*4; unseen accept1+running3+terminal cancel1 | 16 | 5 | 11 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 16 | 0 | 0.031239199975971133 |
| V4.PROVIDER.CANCEL.ELIGIBILITY | 4*2; terminal2+supported running1 | 8 | 3 | 5 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 8 | 0 | 0.015352599963080138 |
| V4.PROVIDER.DEADLINE.RACE | 4*2*3; absent5+unexpired5+expired2 | 24 | 12 | 12 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 24 | 0 | 0.04975509995711036 |
| V4.PROVIDER.TRANSPORT.METHOD | 3 request methods + 1 notification | 4 | 4 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 10 | 0 | 4.61161429999629 |
| V4.ERROR.NAMES | 33 normative VCP + 8 Provider + 2 SDK + 10 Relay | 53 | 53 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 55 | 0 | 0.03224089989089407 |
| V4.RELAY.PORTS | 6 Protocols, seven direct methods; plus EventSink.emit | 7 | 7 | 0 | 0 | 0 | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 9 | 2 | 0.07857000007061288 |
| V4.RELAY.SCHEDULER | four logical VCP phases and Relay wave/barrier rules | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 18 | 18 | 1.2418900999473408 |
| V4.RELAY.ENTRYPOINT | every *actually shipped* Python/CLI/MCP/HTTP interface | conditional | None | None | 0 | conditional | not established | not established | 0 proof(s); obligation count unreviewed | not established | unreconciled | 11 | 6 | 6.487061400024686 |


## 3. Every failing case

17 failing case IDs. Mutation probes: 9; all detected: True. Fourteen failures are frozen authoring defects, two are coverage gates, and one is the supported stdio boundary. They must not all be called production bugs.

- `V4.AUDIT.INVENTORY.INVENTORY`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/conformance.md:5-33`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.AUDIT.INVENTORY.INVENTORY"`
- `V4.AUDIT.INVENTORY.PROOFS`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/conformance.md:5-33`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.AUDIT.INVENTORY.PROOFS"`
- `V4.PROVIDER.TRANSPORT.METHOD.UNKNOWN_METHOD`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"exception": "0 bytes read on a total of undefined expected bytes"}`
  - SOURCE_CLAUSE: `provider-contract/spec/draft/transports.md:3-75`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.PROVIDER.TRANSPORT.METHOD.UNKNOWN_METHOD"`
- `V4.VCP.AGG.MEMBER_ROLE.AGGREGATE-RESULT`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/dataflow.md:5-195`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.MEMBER_ROLE.AGGREGATE-RESULT"`
- `V4.VCP.AGG.SEMANTIC.AGGREGATE-SUBJECT-MATCH1`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/dataflow.md:5-195`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.SEMANTIC.AGGREGATE-SUBJECT-MATCH1"`
- `V4.VCP.AGG.SEMANTIC.AGGREGATE-CRITERION-MATCH1`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/dataflow.md:5-195`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.SEMANTIC.AGGREGATE-CRITERION-MATCH1"`
- `V4.VCP.AGG.SEMANTIC.AGGREGATE-MEMBERS-MATCH1`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/dataflow.md:5-195`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.SEMANTIC.AGGREGATE-MEMBERS-MATCH1"`
- `V4.VCP.AGG.WEIGHT_SIGN_2.-1--1`
  - EXPECTED: `{"error": "AGGREGATE_INPUT"}`
  - ACTUAL: `{"error": "AGGREGATE_CONFIG"}`
  - SOURCE_CLAUSE: `spec/draft/aggregation.md:5-38`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.WEIGHT_SIGN_2.-1--1"`
- `V4.VCP.AGG.WEIGHT_SIGN_2.-1-0`
  - EXPECTED: `{"error": "AGGREGATE_INPUT"}`
  - ACTUAL: `{"error": "AGGREGATE_CONFIG"}`
  - SOURCE_CLAUSE: `spec/draft/aggregation.md:5-38`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.WEIGHT_SIGN_2.-1-0"`
- `V4.VCP.AGG.WEIGHT_SIGN_2.-1-2`
  - EXPECTED: `{"error": "AGGREGATE_INPUT"}`
  - ACTUAL: `{"error": "AGGREGATE_CONFIG"}`
  - SOURCE_CLAUSE: `spec/draft/aggregation.md:5-38`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.WEIGHT_SIGN_2.-1-2"`
- `V4.VCP.AGG.WEIGHT_SIGN_2.0--1`
  - EXPECTED: `{"error": "AGGREGATE_INPUT"}`
  - ACTUAL: `{"error": "AGGREGATE_CONFIG"}`
  - SOURCE_CLAUSE: `spec/draft/aggregation.md:5-38`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.WEIGHT_SIGN_2.0--1"`
- `V4.VCP.AGG.WEIGHT_SIGN_2.0-0`
  - EXPECTED: `{"error": "AGGREGATE_INPUT"}`
  - ACTUAL: `{"error": "AGGREGATE_CONFIG"}`
  - SOURCE_CLAUSE: `spec/draft/aggregation.md:5-38`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.WEIGHT_SIGN_2.0-0"`
- `V4.VCP.AGG.WEIGHT_SIGN_2.2--1`
  - EXPECTED: `{"error": "AGGREGATE_INPUT"}`
  - ACTUAL: `{"error": "AGGREGATE_CONFIG"}`
  - SOURCE_CLAUSE: `spec/draft/aggregation.md:5-38`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.AGG.WEIGHT_SIGN_2.2--1"`
- `V4.VCP.NODE.PRIMARY.AGGREGATE-VALID`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/dataflow.md:5-195`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.NODE.PRIMARY.AGGREGATE-VALID"`
- `V4.VCP.NODE.ROLE.AGGREGATE-INFORMATION`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/dataflow.md:5-195`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.NODE.ROLE.AGGREGATE-INFORMATION"`
- `V4.VCP.NODE.ROLE.AGGREGATE-RESULT`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/dataflow.md:5-195`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.NODE.ROLE.AGGREGATE-RESULT"`
- `V4.VCP.SCHEMA.FULL.ANNOTATION`
  - EXPECTED: `{"accepted": true}`
  - ACTUAL: `{"accepted": false}`
  - SOURCE_CLAUSE: `spec/draft/dataflow.md:5-195`
  - REPRO: `python -m tools.golden_v4.report --case-id "V4.VCP.SCHEMA.FULL.ANNOTATION"`

## 4. Reductions

RunRecord structural presence executes 16 valid optional masks plus 14 single required deletions; 262,114 other invalid masks are discharged by the unconditional required-field conjunction. NodeRecord executes 256 valid optional masks plus 12 single deletions; 1,048,308 other invalid masks are discharged. Total invalid presence cases avoided by these two disjoint object projections: 1,310,422. This is not a reduction of full semantic record validity.

The Result disjoint branch partition is 48+8+4+2+4=66; all 1,024 wire cases are executed, so zero cases are omitted. Observation mask 960=3*256+6*32 is conditional on true judgment schema and valid payloads. All 4,166 topology candidates and all 1,024 reducer handling maps are executed, so zero are omitted. Graph DAG counts are independently checked by source-set inclusion/exclusion [1,1,3,25,543] against cycle-detection expectations.

Unbounded DAG induction and reducer reductions remain UNPROVED; they save no claimed covered obligations. Their precise premises are in COMPOSITION_PROOFS.md and REDUCTION_LEDGER.jsonl. No sample is upgraded to proof.

## 5. Scope ledgers

UNSUPPORTED: cycles and dynamic expansion; external/nested/dynamic schema resolution; automatic retries, durable replay/recovery; required unknown extension semantics; portable multi-attempt interrupted cancellation; network Provider bindings.

AMBIGUOUS: unmandated exact error precedence; portable numeric rounding/canonical identity/clock trust; raw availability coordinate reachability without mandatory extra axes.

UNBOUNDED: arbitrary JSON/schema/string/number values; DAGs of arbitrary size; arbitrary member lists, custom logic and event histories; unbounded concurrent scheduling histories.

SAMPLED: logical reducer sequences n=1..5; severity sequences n=1..4; authored score boundary vectors; twelve named Relay motifs and explicit resource/event paths.

UNPROVED: universal DAG induction noninterference/global-state premises; unbounded reducer order/identity reduction; complete normative clause-to-assertion review and canonical obligation deduplication; complete cross-module pair and required higher-order interaction matrix; all standard-provider behavioral contracts beyond text and aggregate; complete supported host/method clause indexing.

EXCLUDED: Byzantine Provider streams in real Relay; malicious arbitrary replacement ports; cryptographic attestation/coordinated coherent forgery.

EXECUTION_PLAN_CORRECTIONS: Mutation probes and the SDK policy-exception boundary execute in runtime mode, regardless of their frozen initial mode label.; Invalid invoked nonexecution Results and all policy role/outcome-object combinations execute locally in cheap mode. No deliberately malformed external provider is required.; The expired-deadline resource witness is a local Provider lifecycle check: the public Relay.run API has no deadline argument. It is not claimed as a live Relay deadline invocation.; The stdio helper's post-terminal EOF exit status is diagnostic: the binding does not mandate a numeric exit status after all responses settle. Its cancellation shutdown traceback is preserved separately in run artifacts..

## 6. Obligation accounting

2623 conservative clause units have explicit missing review obligations. 38 additional facade/host declarations lack clause-level method entries. A portable unique obligation total is NOT ESTABLISHED: canonical deduplication and assertion-level review are incomplete. Passing pytest item counts are not substituted for that total. Exact missing IDs and method declarations are in COVERAGE.json.

## 7. Execution evidence and commands

Full execution: 15236 individually reconciled cases; 15219 PASS, 17 FAIL; 48.650 seconds, 185 real Relay.run calls, 7.962 summed awaited seconds. Aggregate awaited seconds include concurrent calls and are not wall time.

cheap-release: 15010 executed; {'PASS': 14994, 'FAIL': 16}; 30.180 seconds; 0 Relay API calls; 0.000 awaited seconds.

runtime-release: 205 executed; {'PASS': 205}; 11.894 seconds; 179 Relay API calls; 7.120 awaited seconds.

integration-release: 21 executed; {'PASS': 20, 'FAIL': 1}; 14.728 seconds; 6 Relay API calls; 1.397 awaited seconds.

PowerShell commands and environment setup are in README.md. Stable raw per-case output, JUnit XML and stdout are in RUN_EVIDENCE/. PROFILE_EXECUTIONS.json records actual original profile runs. The frozen cases and original profile modes remain unchanged; execution mode corrections are explicit in SCOPE_LEDGERS.json and each result record.

## 8. Verdict

NOT CERTIFIED

The suite is executable and its audit is fail-closed. Complete supported normative obligation coverage has not been achieved. No stable 1.0, arbitrary JSON, arbitrary provider, universal DAG, or scheduler-race proof is claimed.
