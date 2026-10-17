# Independent count derivations

Each row is a distinct projection. There is no grand candidate sum. Structural presence does not imply full semantic validity.

Result branch proof: nonexecution forces all four optional axes to bottom, giving 3*2^4. ERROR forces three bottoms, giving 2^3. NOT_APPLICABLE forces two, giving 2^2. UNKNOWN forces verdict bottom, giving 2. KNOWN admits bottom/PASS/FAIL at wire multiplicities 2/1/1, giving 4. These first-divergence branches are disjoint.

Absent/null are identified only for nullable categorical controls; explicit judgment/output null remains present data. The observation-mask derivation fixes true judgment_schema and valid payloads. Three KNOWN classes permit eight fields; six remaining classes permit five fields.

DAG recurrence: a nonempty source set of size k contributes choose(n,k)*2^(k(n-k))*DAG(n-k); inclusion/exclusion over source sets yields [1,1,3,25,543]. Enumeration tests independently use cycle detection. Topology is not full definition validity.

Record presence: all required bits must be 1; optional bits are free. Invalid masks missing a required bit remain invalid under all deletions/additions of other fields. Only the presence subconstraint is reduced. All optional masks and each single required deletion are executed.

| Family | Formula | C | V | I | N | Q |
| --- | --- | --- | --- | --- | --- | --- |
| V4.VCP.DEF.PRESENCE | 2^(9+3); V=2^3 | 4096 | 8 | 4088 | 0 | 0 |
| V4.VCP.CRITERION.PRESENCE | 2^(2+2); V=2^2 | 16 | 4 | 12 | 0 | 0 |
| V4.VCP.ARTIFACT.PRESENCE | 2^(3+3); V=2^3 | 64 | 8 | 56 | 0 | 0 |
| V4.VCP.EXEC_OBS.PRESENCE | 2^(3+1); V=2^1 | 16 | 2 | 14 | 0 | 0 |
| V4.VCP.RUN_RECORD.PRESENCE | 2^(14+4); V=2^4 | 262144 | 16 | 262128 | 0 | 0 |
| V4.VCP.NODE_RECORD.PRESENCE | 2^(12+8); V=2^8 | 1048576 | 256 | 1048320 | 0 | 0 |
| V4.VCP.EVIDENCE.MEANING | (2^4-1)*2^3; invalid=2^3 | 128 | 120 | 8 | 0 | 0 |
| V4.VCP.RESULT.WIRE_AXIS | 4*4^4; V=3*2^4+2^3+2^2+2+4 | 1024 | 66 | 958 | 0 | 0 |
| V4.VCP.RESULT.SEMANTIC_AXIS | 4*3^4; V=3+1+1+1+3 | 324 | 9 | 315 | 0 | 0 |
| V4.VCP.RESULT.OBS_MASK | 9*2^8; V=3*2^8+6*2^5 | 2304 | 960 | 1344 | 0 | 0 |
| V4.VCP.RESULT.PROJECTION | 9 semantic states; 2 binary+UNKNOWN+ERROR+SKIP | 9 | 5 | 4 | 0 | 0 |
| V4.VCP.DECISION.DEST | 6*4; V=1+5*2 | 24 | 11 | 13 | 0 | 0 |
| V4.VCP.NODE.ROLE | 4*3; V=4 INFORMATION+2 RESULT+1 DECISION | 12 | 7 | 5 | 0 | 0 |
| V4.VCP.NODE.INVOKED_RESULT | 2*9; 2*(ERROR+NOT_APPLICABLE+UNKNOWN+3 KNOWN) | 18 | 12 | 6 | 0 | 0 |
| V4.VCP.BIND.IDENTITY | 2^4; conjunction of four equalities | 16 | 1 | 15 | 0 | 0 |
| V4.VCP.PORT.HANDLING | 2*3; required BLOCK, optional OMIT/DEFAULT | 6 | 3 | 3 | 0 | 0 |
| V4.VCP.PORT.DEFAULT | 2 presence states | 2 | 1 | 1 | 0 | 0 |
| V4.VCP.SOURCE.KIND | 4 disjoint source constructors | 4 | 4 | 0 | 0 | 0 |
| V4.VCP.SOURCE.POLICY | 4*3; only 3 pregraph source kinds | 12 | 9 | 3 | 0 | 0 |
| V4.VCP.RESOLVE.HANDLER | 6*3 | 18 | None | None | 0 | conditional |
| V4.VCP.RESOLVE.CONSUMER | 4*6*3 | 72 | None | None | 0 | conditional |
| V4.VCP.RESOLVE.RAW | 4*4*6*3 | 288 | None | None | 0 | conditional |
| V4.VCP.RESOLVE.UNBOUND | 4*1*6*3 | 72 | None | None | 0 | conditional |
| V4.VCP.RESOLVE.RECORD_BITS | 6*3*2*2; V=3 AVAILABLE+5*3 unavailable | 72 | 18 | 54 | 0 | 0 |
| V4.VCP.SCHEMA.PRIMITIVE | 7*7; seven diagonal + integer/number both ways | 49 | 9 | 40 | 0 | 0 |
| V4.VCP.GUARD.OPERATOR | equality only | 1 | 1 | 0 | 0 | 0 |
| V4.VCP.GUARD.SOURCE | 4 source constructors; reachability conditional | 4 | None | None | 0 | conditional |
| V4.VCP.GUARD.BOOL | 2*2; equality diagonal | 4 | 2 | 2 | 0 | 0 |
| V4.VCP.GRAPH.DAG_0_4 | sum(n=0..4) 2^(n(n-1)); source-set inclusion/exclusion recurrence | 4166 | 573 | 3593 | 0 | 0 |
| V4.VCP.GRAPH.FEATURES | 2^2 feature subsets | 4 | 4 | 0 | 0 | 0 |
| V4.VCP.AGG.MEMBER_ROLE | 4*3; EVALUATE/AGGREGATE RESULT only | 12 | 2 | 10 | 0 | 0 |
| V4.VCP.AGG.SEMANTIC | 2 kinds*2 semantic snapshots + aggregate members | 5 | 5 | 0 | 0 | 0 |
| V4.VCP.AGG.HANDLING_MAP | 8*2^7 | 1024 | 1024 | 0 | 0 | 0 |
| V4.VCP.AGG.EXCEPTION | 8*7*2 behavior laws | 112 | 112 | 0 | 0 | 0 |
| V4.VCP.AGG.WEIGHT_SIGN_2 | 3^2; V=2^2-1 | 9 | 3 | 6 | 0 | 0 |
| V4.VCP.AGG.WEIGHT_GENERAL | C=3^n; V=2^n-1; I=3^n-2^n+1 | unbounded | None | None | 0 | 0 |
| V4.VCP.POLICY.DECLARATIONS | 2*2*3 | 12 | 12 | 0 | 0 | 0 |
| V4.VCP.POLICY.PATH | 1 inactive+1 unselected+3 admitted | 5 | 5 | 0 | 0 | 0 |
| V4.VCP.POLICY.ROLE_RESULT | 3*3; role/type diagonal | 9 | 3 | 6 | 0 | 0 |
| V4.VCP.POLICY.EVAL_ORDER | 3!; exactly one required order | 6 | 1 | 5 | 0 | 0 |
| V4.VCP.RESOURCE.PRESENCE_BINARY | 4*2^3; one nonnull pattern per kind | 32 | 4 | 28 | 0 | 0 |
| V4.VCP.RESOURCE.PRESENCE_TRINARY | 4*3^3; V=2*2^2+2+2^3 | 108 | 18 | 90 | 0 | 0 |
| V4.VCP.RESOURCE.RANGE_ORDER | <,=,>; <= admits first two | 3 | 2 | 1 | 0 | 0 |
| V4.VCP.LIFECYCLE.PHASES | 4*4; five progression + four stutter + seven other | 16 | 5 | 7 | 4 | 0 |
| V4.VCP.LIFECYCLE.RESULT | 4*4 per kind; SUCCESS1+ERROR1+NONEXECUTED3+CANCELLED1 | 16 | 6 | 10 | 0 | 0 |
| V4.VCP.LIFECYCLE.REASON | nine distinct cause mappings | 9 | 9 | 0 | 0 | 0 |
| V4.VCP.CANCEL.ELIGIBILITY | 2*3; admission RUN only | 6 | 2 | 4 | 0 | 0 |
| V4.VCP.EXT.REQUIRED | 2*2; required AND unsupported excluded | 4 | 3 | 1 | 0 | 0 |
| V4.PROVIDER.FEATURE_FLAGS | 2^4 independent booleans | 16 | 16 | 0 | 0 | 0 |
| V4.PROVIDER.VCP_COMPAT | 2*2; declaration implies manifest support | 4 | 3 | 1 | 0 | 0 |
| V4.PROVIDER.INIT | success / reject-and-close; version list space unbounded | 2 | 2 | 0 | 0 | 0 |
| V4.PROVIDER.INVOKE.DEADLINE | 2*2; presence implies feature | 4 | 3 | 1 | 0 | 0 |
| V4.PROVIDER.INVOKE.BUDGET | 2*2; presence implies VCP | 4 | 3 | 1 | 0 | 0 |
| V4.PROVIDER.OUTCOME.SHAPE | 4*2*2; one shape per terminal kind | 16 | 4 | 12 | 0 | 0 |
| V4.PROVIDER.OUTCOME.USAGE | 2*4*2*2; absent16 + present with both flags4 | 32 | 20 | 12 | 0 | 0 |
| V4.PROVIDER.EVENT.ELIGIBILITY | 6*2^3; 3 advisory*4 + 2 VCP*2 + 1 usage | 48 | 17 | 31 | 0 | 0 |
| V4.PROVIDER.ATTEMPT.TRANSITION | 4*4; unseen accept1+running3+terminal cancel1 | 16 | 5 | 11 | 0 | 0 |
| V4.PROVIDER.CANCEL.ELIGIBILITY | 4*2; terminal2+supported running1 | 8 | 3 | 5 | 0 | 0 |
| V4.PROVIDER.DEADLINE.RACE | 4*2*3; absent5+unexpired5+expired2 | 24 | 12 | 12 | 0 | 0 |
| V4.PROVIDER.TRANSPORT.METHOD | 3 request methods + 1 notification | 4 | 4 | 0 | 0 | 0 |
| V4.ERROR.NAMES | 33 normative VCP + 8 Provider + 2 SDK + 10 Relay | 53 | 53 | 0 | 0 | 0 |
| V4.WIRE.ROOTS | 24 VCP + 9 Provider | 33 | 33 | 0 | 0 | 0 |
| V4.RELAY.PORTS | 6 Protocols, seven direct methods; plus EventSink.emit | 7 | 7 | 0 | 0 | 0 |
| V4.WIRE.JSON | UTF-8, duplicate keys, nonfinite, unknown props, version marker, nested JSON | conditional | None | None | 0 | conditional |
| V4.VCP.RESULT.VALUES | observed judgment,score,severity,evidence,output,usage,metadata,extensions | conditional | None | None | 0 | conditional |
| V4.VCP.DECISION.ROUTE | destination Ã— reachable direct successors/guards/control | conditional | None | None | 0 | conditional |
| V4.VCP.NODE.PRIMARY | required `result` or `decision`, auxiliary INFORMATION, duplicate/wrong role | conditional | None | None | 0 | conditional |
| V4.VCP.SCHEMA.FULL | boolean/object JSON Schema supported subset and references | conditional | None | None | 0 | conditional |
| V4.VCP.GUARD.POINTER | pointer existence, JSON type, unavailable source, incoming-edge conjunction | conditional | None | None | 0 | conditional |
| V4.VCP.GRAPH.DEFINITION | IDs, edge endpoints, duplication, ports, binding, guards, cycles | conditional | None | None | 0 | conditional |
| V4.VCP.AGG.LOGICAL | n retained PASS/FAIL members | conditional | None | None | 0 | conditional |
| V4.VCP.AGG.SCORE | numeric scores, min/max/average | conditional | None | None | 0 | conditional |
| V4.VCP.AGG.WEIGHT_IDENTITY | permutations, missing/misassigned weights, filtered retention | conditional | None | None | 0 | conditional |
| V4.VCP.AGG.SEVERITY | k-level domain and n retained members | conditional | None | None | 0 | conditional |
| V4.VCP.RECORD.LINEAGE | source, binding, upstream snapshot, errors, resource usage, timing | conditional | None | None | 0 | conditional |
| V4.PROVIDER.EVENT.SEQUENCE | valid strictly increasing positive sequence, gaps allowed | conditional | None | None | 0 | conditional |
| V4.RELAY.SCHEDULER | four logical VCP phases and Relay wave/barrier rules | conditional | None | None | 0 | conditional |
| V4.RELAY.ENTRYPOINT | every *actually shipped* Python/CLI/MCP/HTTP interface | conditional | None | None | 0 | conditional |
