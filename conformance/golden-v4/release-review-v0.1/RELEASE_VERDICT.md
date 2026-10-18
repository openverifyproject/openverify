# OpenVerify v0.1 release closure — BLOCKED

Base: `4da463e489c9d9bdb26af9c47979269500ba141f`, branch `fix/golden-v4-verification`, worktree `.worktrees/vcp-final-semantics`.

All 615 canonical records receive a conservative release disposition: **1 VERIFIED**, **396 PARTIALLY VERIFIED**, **218 RELEASE BLOCKER**, **0 UNSUPPORTED**. The 582 semantic requirements and 33 schema predicates are preserved. These are disposition counts, not a claim of completed assertion-sufficiency review. No normative requirement was silently removed from scope.

The release gate fails B: requirement-wide assertion sufficiency is not established. Gate A passes only as disposition accounting; its stronger requirement to finish review of every behavior is not met. Gate C has no newly known unresolved deterministic production defect, but the retained regex timeout is a reliability limitation. Gate D depends on the exact results in TEST_RESULTS.md. Gate E is disclosed in KNOWN_LIMITATIONS.md. Gate F is bounded to the recorded clean consumer checks, not all optional packages or platforms.

Two confirmed stdio defects were fixed: complete invalid JSON now gets -32700 with null id; malformed request envelopes get -32600. Initially both exact response assertions failed with EOF; INITIAL_RPC_RESULTS.jsonl retains this evidence. The new tests also exercise gate classes, storage snapshots, cancellation reasons, file byte boundaries, provider failure/usage and service admission concurrency. Original frozen artifacts remain byte-identical; nine prior expectation corrections remain a separate opt-in overlay.

One isolated projection is discharged: RG.GATE.QUOTIENT. This is not full Result validation, full schema conformance, arbitrary DAG correctness, or universal Golden certification.

| Branch | Records | Verified | Partial | Blocker | Status |
|---|---:|---:|---:|---:|---|
| PROVIDER / Capabilities | 1 | 0 | 0 | 1 | BLOCKED |
| PROVIDER / Compatibility | 10 | 0 | 3 | 7 | BLOCKED |
| PROVIDER / Control | 18 | 0 | 10 | 8 | BLOCKED |
| PROVIDER / Discovery | 4 | 0 | 1 | 3 | BLOCKED |
| PROVIDER / Errors | 12 | 0 | 9 | 3 | BLOCKED |
| PROVIDER / Events | 1 | 0 | 0 | 1 | BLOCKED |
| PROVIDER / Extensions | 3 | 0 | 1 | 2 | BLOCKED |
| PROVIDER / Invocation | 6 | 0 | 3 | 3 | BLOCKED |
| PROVIDER / Lifecycle | 5 | 0 | 4 | 1 | BLOCKED |
| PROVIDER / Meaning | 1 | 0 | 0 | 1 | BLOCKED |
| PROVIDER / Resources | 7 | 0 | 3 | 4 | BLOCKED |
| PROVIDER / Schemas | 4 | 0 | 0 | 4 | BLOCKED |
| PROVIDER / Streaming | 11 | 0 | 11 | 0 | BLOCKED |
| PROVIDER / Transport | 21 | 0 | 10 | 11 | BLOCKED |
| PROVIDER / Wire | 2 | 0 | 0 | 2 | BLOCKED |
| PROVIDER / Wire roots | 9 | 0 | 9 | 0 | BLOCKED |
| RELAY / Architecture | 1 | 0 | 1 | 0 | BLOCKED |
| RELAY / Binding | 4 | 0 | 1 | 3 | BLOCKED |
| RELAY / Binding and execution | 1 | 0 | 0 | 1 | BLOCKED |
| RELAY / Cancellation | 2 | 0 | 1 | 1 | BLOCKED |
| RELAY / Discovery | 3 | 0 | 1 | 2 | BLOCKED |
| RELAY / Entrypoints | 17 | 0 | 12 | 5 | BLOCKED |
| RELAY / Execution | 3 | 0 | 1 | 2 | BLOCKED |
| RELAY / Extension ports | 7 | 0 | 7 | 0 | BLOCKED |
| RELAY / Invocation callbacks | 1 | 0 | 1 | 0 | BLOCKED |
| RELAY / Observability | 1 | 0 | 1 | 0 | BLOCKED |
| RELAY / Policies | 2 | 0 | 0 | 2 | BLOCKED |
| RELAY / Preparation | 2 | 0 | 0 | 2 | BLOCKED |
| RELAY / Process execution | 2 | 0 | 2 | 0 | BLOCKED |
| RELAY / Providers | 1 | 0 | 0 | 1 | BLOCKED |
| RELAY / Public API | 9 | 0 | 8 | 1 | BLOCKED |
| RELAY / Public SDK | 48 | 0 | 36 | 12 | BLOCKED |
| RELAY / Records | 6 | 0 | 3 | 3 | BLOCKED |
| RELAY / Scheduler | 5 | 0 | 4 | 1 | BLOCKED |
| RELAY / Standard providers | 42 | 1 | 28 | 13 | BLOCKED |
| RELAY / Transport | 4 | 0 | 1 | 3 | BLOCKED |
| SHARED / JSON value and schema semantics | 3 | 0 | 1 | 2 | BLOCKED |
| SHARED / Public SDK | 70 | 0 | 36 | 34 | BLOCKED |
| VCP / Aggregation | 33 | 0 | 26 | 7 | BLOCKED |
| VCP / Composition | 12 | 0 | 9 | 3 | BLOCKED |
| VCP / Computation | 13 | 0 | 11 | 2 | BLOCKED |
| VCP / Conformance | 2 | 0 | 0 | 2 | BLOCKED |
| VCP / Dataflow | 37 | 0 | 26 | 11 | BLOCKED |
| VCP / Decisions | 1 | 0 | 1 | 0 | BLOCKED |
| VCP / Extensions | 2 | 0 | 0 | 2 | BLOCKED |
| VCP / Knowledge | 3 | 0 | 2 | 1 | BLOCKED |
| VCP / Lifecycle | 22 | 0 | 14 | 8 | BLOCKED |
| VCP / Meaning | 6 | 0 | 2 | 4 | BLOCKED |
| VCP / Policies | 22 | 0 | 14 | 8 | BLOCKED |
| VCP / Profiles | 1 | 0 | 0 | 1 | BLOCKED |
| VCP / Provenance | 28 | 0 | 13 | 15 | BLOCKED |
| VCP / Provider binding | 12 | 0 | 8 | 4 | BLOCKED |
| VCP / Resources | 5 | 0 | 2 | 3 | BLOCKED |
| VCP / Result | 1 | 0 | 1 | 0 | BLOCKED |
| VCP / Results | 30 | 0 | 28 | 2 | BLOCKED |
| VCP / Schemas | 3 | 0 | 2 | 1 | BLOCKED |
| VCP / Wire roots | 24 | 0 | 24 | 0 | BLOCKED |
| VCP / Wire semantics | 9 | 0 | 4 | 5 | BLOCKED |

See [REQUIREMENT_COVERAGE.jsonl](REQUIREMENT_COVERAGE.jsonl) for exact IDs, source references, applicability, actual assertion expressions and requirement-specific residuals. [RELEASE_BLOCKERS.md](RELEASE_BLOCKERS.md) contains the finite decision list. No READY or publication claim is made.
