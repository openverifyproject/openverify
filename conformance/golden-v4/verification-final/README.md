# Golden V4 verification against canonical V2

**NOT CERTIFIED. The 615-record implementation coverage reconciliation is unfinished.**
All 66 baseline failures are resolved, but green executions do not close the
remaining assertion-review and domain-proof gaps. `COVERAGE_REPORT.json` gives
the exact current counts. An unlinked record is a review gap, not automatically
a missing test. No exact count of genuinely new tests still needed is established.

This work continues `ad7fad6986eb79e55094687022d15a7bc70ede30` in
`.worktrees/vcp-final-semantics` on `fix/golden-v4-verification`.
The integration, original Golden V4 and SDK branches/worktrees are preserved.
The canonical six files, their 582 semantic IDs and 33 whole-schema IDs are unchanged.

## Baseline failure identity and repairs

`ROOT_CAUSES.json` preserves all 66 baseline case IDs, original observations and
individual final expectations/results. Its original rationale/source fields
describe the baseline; the final result fields describe this revision.

| Root cause | Baseline failing cases | Repair |
| --- | ---: | --- |
| Invoked CANCELLED producer classified as never invoked | 46 | `dataflow.resolve_source`: no accepted output after CANCELLED is OUTPUT_MISSING; bookkeeping Result handling remains first |
| Universal nonempty aggregate membership restriction | 10 | `dataflow.validate_graph`: empty CUSTOM legal, standard reducers remain nonempty |
| Unknown JSON-RPC method closed instead of replying | 1 | Session validator and stdio server return -32601 and preserve correlation/session continuity |
| Original-weight error category expectation | 6 | Separately versioned AGGREGATE_CONFIG expectation; retained-input failures remain distinct |
| Object-valued description annotation expectation | 1 | Reject invalid Draft schema; independent positive default-annotation payload case retained |
| Certification demanded for an incomplete historical ledger | 2 | Fail-closed false expectations; the historical ledger was not declared complete |

These are three distinct baseline production bugs, not 57 distinct bugs.
The nine expectation corrections are in `EXPECTATION_CORRECTIONS.json`;
all original frozen files retain their exact bytes. The overlay checks that
each original expectation matches before replacing it. Its digest is sealed in
`SOURCE_REVISION.json`; unsealed overlays fail the integrity gate.

Additional source-supported defects repaired with focused assertions:

- Valid unused defaults under BLOCK/OMIT were rejected. They are now validated
  but never consumed unless DEFAULT applies.
- Standalone invocation parsing accepted unsupported VCP markers.
- A null finding generated empty, invalid Evidence. Its authored null is now
  retained inside structured data, with the original findings output unchanged.
- Regex pattern findings bypassed the documented 10,000 observation bound.
- Runner timing overwrote an existing provider `relay_wall_time` dimension when
  `wall_time` was also present. Runner time now chooses a fresh numbered suffix
  on further collisions; all provider dimensions and units remain intact.
- Invalid invoke parameters used -32000 instead of the specified -32602.

The V4 runtime adapter no longer silently inserts seed members into empty custom
aggregates. Frozen stimuli and expectations are preserved; the authored empty
membership now reaches the actual runtime. Separate witnesses verify that a
capability schema can reject it and that an unavailable declared member never
becomes an intentionally empty declaration.

## Evidence and limits

- `EXECUTION_REPORT.json`: exact run counts, monotonic durations, imported source
  path, dependency versions, source digests and profile partitions.
- `GOLDEN_RESULTS.jsonl.gz`, `REGRESSION_RESULTS.jsonl`: per-case outcomes and
  exact replay selectors. Existing tests' JUnit and stdout are also retained.
- `ROOT_CAUSES.json`: all baseline failure resolutions, individually identified.
- `MUTATION_REPORT.json`: nine original semantic probes plus cancellation,
  custom-empty and usage-collision probes; each real baseline passes before its
  corruption is detected. This is not exhaustive mutation coverage.
- `PROOFS.json`: independent finite-product integrity checks and mandatory-field
  reductions, including exact saved execution counts and tested premises.
- `CANONICAL_ASSERTION_COVERAGE.jsonl.gz`: every existing canonical ID, its source,
  actual reviewed assertions, scope, outcome and remaining domain obligations.
- `TEST_ASSERTION_CROSSWALK.jsonl.gz`: reverse links, including uncredited executed
  cases. No coverage credit for the 360 raw-coordinate scaffold cases.
- `COVERAGE_REPORT.json`: fail-closed leaf/branch reconciliation counts. Every
  branch remains INCOMPLETE; no finite sample is promoted to a universal proof.
- `GOLDEN_FAILURES.jsonl`: exact current Golden/revision failures; empty when zero.
- `ARTIFACT_SHA256.json`: retained artifact integrity.

Record-presence reductions prove structural presence only. Result state and
observation counts apply to their stated axes and valid-payload assumptions.
Graph topology is exhaustive only for labelled loop-free graphs with at most four
nodes. Reducer map enumeration does not prove every member/handling interaction.
No arbitrary-size scheduler/shared-state induction, arbitrary schema/JSON/trace
exhaustiveness, cross-language floating-point identity or cryptographic record
authenticity is claimed. Existing Hypothesis runs are sampled, not exhaustive.
Undefined nonprogressing references and Boolean annotation-target cases retain
the canonical model's explicit scope limits. Provider deadlines/budgets are local
protocol checks where the Relay host API does not supply those constraints.

Normal pre-existing suites include defensive tests outside the compliant-provider
assumption. Running them does not make malicious provider/custom-port behavior a
required portable runtime scenario. New live providers emit permitted events and
outcomes. Invalid objects and state transitions are checked locally.

The one ordinary-suite skip is the POSIX case/separator check on Windows; it is
not a passing cross-platform witness. The original frozen ledger's unsupported,
unproved and missing entries remain historical evidence, not certification input.
Independent review of the remaining canonical records is still required; this
directory does not pretend that all 615 have a complete assertion/proof discharge.

## Reproduce in PowerShell

From the isolated worktree:

```powershell
$python = 'C:\Users\siddh\OneDrive\Desktop\openverify\.venv\Scripts\python.exe'
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
$env:OPENVERIFY_GOLDEN_SOURCE_REVISION = Join-Path (Get-Location) 'conformance/golden-v4/verification-final/SOURCE_REVISION.json'
$env:OPENVERIFY_GOLDEN_EXPECTATION_REVISION = Join-Path (Get-Location) 'conformance/golden-v4/verification-final/EXPECTATION_CORRECTIONS.json'
$env:OPENVERIFY_RECONCILIATION_OUTPUT = Join-Path (Get-Location) 'conformance/golden-v4/verification-final'

& $python -B -m tools.golden_v4.report --verify-freeze
& $python -B -m pytest -q -c tests/golden_v4/pytest.ini tests/golden_v4 --junitxml=.pytest_cache/verification-golden.xml
& $python -B -m pytest -q tests/golden_v4_reconciliation --basetemp=.pytest_cache/verification-revision-tmp --junitxml=.pytest_cache/verification-revision.xml
& $python -B -m pytest -q tests/unit tests/integration tests/property tests/conformance tests/relay tests/test_error_contract_hardening.py --basetemp=.pytest_cache/verification-existing-tmp --junitxml=.pytest_cache/verification-existing.xml
& $python -B -m tools.golden_v4.verify_final
# Exit 1 is intentional: coverage has not been certified.
& $python -B -m tools.golden_v4.final_evidence

# An exact frozen case, under the same versioned correction environment:
& $python -B -m tools.golden_v4.report --case-id 'V4.VCP.AGG.WEIGHT_SIGN_2.-1--1'
```

The source revision authorizes only exact old/new hashes for the named inherited
normative decisions and reviewed production changes. Default historical-freeze
verification without the opt-in revision continues to reject source drift.
No update mode modifies original frozen expectations. No push/merge/publication.
