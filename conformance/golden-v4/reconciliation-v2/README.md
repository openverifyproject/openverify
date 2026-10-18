# Golden V4 canonical reconciliation, revision v2

This begins assertion reconciliation against the approved canonical model. It is
not another contract inventory and is not certification. Active worktree:
.worktrees/vcp-final-semantics, branch integration/vcp-final-semantics.
Existing Golden worktree remains unchanged at15bb1ce; SDK remains atbd251eb.

## Normative and canonical changes

Approved prose changes: spec/draft/dataflow.md, aggregation.md, open-questions.md.
Custom [] is structurally legal; exact members=[] is capability input, its schema
controls eligibility, and custom implementation owns Result. Standard reducers
reject empty original/retained input; unavailable declared members never disappear.
The six-status classifier uses persisted snapshots alone. Invoked CANCELLED
without accepted non-Result output yields OUTPUT_MISSING. Declared bookkeeping
Result is checked first against producer/consumer schemas. Raw observations never
publish accepted information. No new state, event-order log, scheduler barrier
or error code. Handler/provenance/lifecycle effects are retained.

582 semantic IDs and 33 whole-root predicates are preserved. The independent
availability proof has80 supported equivalence contexts and239 supported handler relations plus1 required-unbound preflight rejection,
not a finite count of arbitrary JSON/schema/graph traces. Two impossible
SUCCESS/producer-rejection coordinates are excluded explicitly. All four canonical
model gates PASS for the declared supported semantic domain, not implementation
or Golden coverage. Undefined schema Boolean-result cases, portable float bits/
rounding tolerances and future protocol profiles remain outside the guarantees.

Normative decision commit:67cad6f. Proof corrections:773fd62 andde33266.
Current canonical views/source-fragment reconciliation:40cb8a0 and9c10dbf. Final required-unbound applicability correction:2df7306.

## Actual execution

| Suite/profile | Passed | Failed | Executed |
| --- | ---: | ---: | ---: |
| Existing V4 cheap partition |14994|16|15010|
| Existing V4 runtime partition |205|0|205|
| Existing V4 integration partition |20|1|21|
| Existing V4 full suite |15219|17|15236|
| Revision regression/correction suite |204|49|253|
| Combined distinct cases |15423|66|15489|

Profile rows partition one full run; they are not independently timed processes.
Existing full run:56.2545301 seconds reporter wall (56.43 pytest display),
185 Relay API calls,9.2485952 Relay-awaited seconds.
Final revision run:4.6597233 seconds reporter wall (5.35 pytest display);
one actual live Relay call. Three intended custom-empty live witnesses reject
during definition validation before invocation. Exact process/case timing and
commands are retained in EXECUTION_REPORT.json, REGRESSION_EXECUTION.json and
compressed JUnit/JSONL/stdout. No maxfail truncation or silent skip was used.

## Failure adjudication

FAILURES.jsonl contains all66 exact failed IDs, expected/actual, source rationale
and single-case repro. Counts are failing cases, not66 distinct production bugs.

- 57 production-defect cases:45 local cancellation/status projections,1 live
  cancellation witness,3 custom-empty witnesses,7 existing custom-empty acceptance
  cases, and1 unknown-method transport case.
- 9 incorrect historical expectations:6 original-weight configuration categories,
  1 invalid description-object annotation fixture,2 unfounded certification/
  proved-success assertions.
- 0 remaining harness failures, unsupported-scope failures or unresolved normative
  failures in the final66 cases. Earlier24 fixture failures were repaired by
  authoring explicit empty Result evidence/usage. Initial evidence remains;
  HARNESS_CORRECTIONS.json distinguishes it from production failures. A collection
  relative-import error was also repaired before the final run.

No production repair was made. The nine new versioned correction cases pass.
Original negative/all-zero authored weight configuration is AGGREGATE_CONFIG;
AGGREGATE_INPUT is not a universal precedence for every invalid configuration.
description requires a string in the Draft metaschema; the old object is invalid,
while the separate default payload correctly demonstrates ignored annotation data.
Unknown method requires JSON-RPC -32601; the server session-validation path closes
before returning that response, producing EOF.

## Actual assertion links and limits

615 primary canonical records =582 semantic requirements+33 root predicates.
37 have reviewed partial assertion links;33 have some passing links;10 have some
failing links. These sets overlap.578 have no reviewed link. Zero whole
requirements are claimed fully reconciled or discharged.

Every15489 executed ID is accounted for in TEST_RECONCILIATION.jsonl.gz;
REQUIREMENT_ASSERTION_LINKS.json provides the reverse direction. Reviewed links
include canonical IDs, hierarchy leaves, source, actual assertion/action locus,
expected/actual, status and replay.9034 cases remain UNREVIEWED and earn no
coverage credit.360 coordinate checks return a constant CONDITIONAL/missing-axis
result; they are scaffolding, not reachability or runtime witnesses. The two new
audit corrections are controls, not semantic coverage. Existing custom runtime
helpers inject a seed into empty membership; these cannot witness an intentionally
empty custom declaration. Names/fixtures/execution alone earned no coverage.

Verdict: NOT CERTIFIED. The remaining task is independent assertion/domain review,
not a large arbitrary test batch or production changes to force green.

## Frozen integrity and explicit source revision

All21 original frozen-manifest paths remain byte-identical (FROZEN_INTEGRITY.json).
Original cases, expectations, inventories and historical evidence are preserved.
SOURCE_REVISION.json separately records the three approved normative files'
exact old/new hashes and the original immutable manifest hash. Default
verify-freeze correctly detects source drift. Explicit revision execution permits
only those three hash pairs, never arbitrary production/schema drift or changed
frozen data. EXPECTATIONS.jsonl and EXPECTATION_CORRECTIONS.json are separately
versioned authored expectations. No update mode or observed-output oracle.

## PowerShell reproduction

Use Python3.13 and repository dev dependencies. This run reused the existing main
venv while importing this integration worktree's src:

    Set-Location C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\vcp-final-semantics
    $env:PYTHONPATH = Join-Path (Get-Location) 'src'
    $env:OPENVERIFY_GOLDEN_SOURCE_REVISION = Join-Path (Get-Location) 'conformance/golden-v4/reconciliation-v2/SOURCE_REVISION.json'
    $python = 'C:\Users\siddh\OneDrive\Desktop\openverify\.venv\Scripts\python.exe'
    & $python -B -m pytest -q -c tests/golden_v4/pytest.ini tests/golden_v4 --junitxml=.pytest_cache/golden-v4-existing-junit.xml
    & $python -B -m pytest -q tests/golden_v4_reconciliation --junitxml=.pytest_cache/golden-v4-revision-junit.xml
    & $python -B -m tools.golden_v4.reconcile_v2

Single old-case replay: python -m tools.golden_v4.report --case-id EXACT_ID
with the same revision environment. New pytest selectors are in FAILURES.jsonl.
Nonzero test exits are retained, not suppressed.

## Read-only SDK comparison

Inspected feat/language-sdks atbd251eb through Git objects. SDK worktree was not
entered or modified; no SDK tests/builds/packages/publication were performed.
All eight libraries explicitly exclude graph/definition/dataflow/provenance
semantics. All97 shared fixtures were read:52 VCP/45 Provider; none tests
aggregate_inputs, input_resolutions or on_unavailable. No existing fixture
expectation or schema change follows. Future graph/dataflow support must implement
these rules; supported normative revision documentation/digests need an explicit
future SDK update. Provider Contract semantics are unchanged.

Already reported original-Python failure remains: provider.vcp-version accepts
an unsupported standalone vcp_version instead of INVALID_INVOCATION; its earlier
audit xfails it. This task did not re-execute that SDK audit. Existing Python
validate_port also rejects unused defaults with an iff not present in current
normative schema/prose. The eight independent wire SDKs do not advertise InputPort
semantics. SDK_IMPACT.json records the comparison. Prior SDK package-test results
are not represented as executions of this task.

No production-code/schema/SDK modification, push, merge or publication.

One revision expectation was corrected by independent domain review before its final execution: required unbound is invalid preflight, not a runtime ABSENT path. EXPECTED_MODEL_CORRECTIONS.json preserves the previous revision expectation digest and precise correction. The original frozen artifacts were not changed. This correction does not add an availability status.

Local resolver tests are snapshot projections; they do not claim whole-RunRecord acceptance or all scheduler interactions. Full typed provenance is asserted only where a live RunRecord witness actually reaches those assertions. The live cancellation case fails on its original status; custom empty cases fail before invocation, so their intended output/provenance assertions remain unexecuted.

Final normative/canonical state is committed through2df7306. Reconciliation implementation/evidence is committed separately; its hash is the commit containing this report (not self-embedded).
