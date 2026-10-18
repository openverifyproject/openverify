# Golden v4 (DRAFT, not certified)

This is a new suite based on production commit
`5f17f402a270882f244a54dde25eda92a085eb39`, in branch
`test/openverify-golden-v4`. It does not import historical Golden suites.
Production, normative specifications, standard profiles and existing tests are
unchanged. No push, merge, tag or publication is part of this work.

The supplied BLUEPRINT.md is preserved byte-for-byte with SHA-256
`3c73fee1826a65d7101c375d21421988a798ae6ee336824546b055ca92d5a6d2`.
The user explicitly corrected its error inventory to **53 declarations**:
33 normative VCP, 8 normative Provider Contract, 2 SDK diagnostics and 10
Relay-specific declarations. CONTRACT_INVENTORY.md and ERROR_INVENTORY.json list
every identifier, authority, exact source reference and byte digest.

Independent expectation authoring is committed before execution adapters:
`ed28c21`, followed by byte-preserving Git normalization correction `147baf1`.
The latter commit restores the exact already-authored bytes to Git without
altering working-tree expectations. Directory-local `.gitattributes` disables
newline conversion so a later checkout can verify the same digests.

The original freeze is immutable. The execution audit identifies errors in that
freeze instead of silently updating expectations. This release is **NOT
CERTIFIED**. FINAL_REPORT.md contains all 78 blueprint family rows, every failed
case and its replay command, proof reductions, limits and exact timings.
AUDIT_FINDINGS.json separates frozen-authoring defects from production findings.

## PowerShell execution

Use the existing Python 3.13 environment; the system `python` may be 3.14.
From the isolated worktree:

```powershell
Set-Location 'C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\golden-v4'
$env:PATH = 'C:\Users\siddh\OneDrive\Desktop\openverify\.venv\Scripts;' + $env:PATH
python --version
python -m pytest -q tests/golden_v4/ --collect-only
python -m pytest -q tests/golden_v4/ -m 'golden_v4 and cheap'
python -m pytest -q tests/golden_v4/ -m 'golden_v4 and runtime'
python -m pytest -q tests/golden_v4/ -m 'golden_v4 and integration'
python -m pytest -q tests/golden_v4/
python -m tools.golden_v4.report --verify-inventory
python -m tools.golden_v4.report --verify-freeze
python -m tools.golden_v4.report --summary
python -m tools.golden_v4.report --summary --json
python -m tools.golden_v4.report --case-id 'V4.VCP.DECISION.DEST.ROUTE-ABSENT'
```

The directory-local pytest configuration sets the production import to this
worktree and excludes ancestor conftest files. No existing test suite is collected.
Every collected case has a frozen ID. Collection rejects duplicate, missing and
extra IDs; exact replay still reconciles the complete inventory before selecting
one item. The release run has no maxfail, skip or xfail setting.

`--verify-freeze` succeeds only if every frozen file and inventoried production
source byte is unchanged. `--verify-inventory` intentionally exits nonzero while
reviewed clause/method obligations or proof premises remain missing. It must not
be turned green by replacing its expected result with the observed failure.

Run reports go under `.pytest_cache/golden-v4/`, outside the freeze. Set
`GOLDEN_V4_ARTIFACTS` to choose a distinct run directory. Add
`--junitxml=.pytest_cache/golden-v4/<run>/junit.xml` to retain JUnit output.
Each JSONL result contains expected and actual values, classification, clause
IDs, source hashes/ranges, obligations, execution mode, duration and an exact
replay command. Failure stdout repeats those essentials. Mutants exercise real
frozen assertions with targeted semantic corruptions, after a passing baseline.

The original profile mode labels and corrected execution modes are both retained
in result records. Invalid policy outcome and invoked-nonexecution output checks
are local. Mutation probes and the SDK policy-error boundary run in the runtime
profile. No malformed external Provider event stream is manufactured for Relay.

## Evidence and limits

RUN_EVIDENCE/results.jsonl and junit.xml retain the complete release execution;
the compressed profile files preserve the actual earlier profile runs.
GOLDEN_FAILURES.jsonl contains every release failure, never only the first.
COVERAGE.json and COVERAGE_REPORT.md are the fail-closed inventory result.
EXECUTION_REPORT.json, PROFILE_EXECUTIONS.json and MUTATION_REPORT.json retain
timing, imported source identity, dependency versions, digests and mutation data.

Record-presence reductions apply only to structural requiredness. The full
semantic/provenance record domain remains separate. Mathematical candidate
projections overlap and must not be summed. DOMAIN_LIMITS.md and
SCOPE_LEDGERS.json distinguish unsupported, ambiguous, unbounded, sampled,
unproved and excluded behaviors. Finite tests do not prove universal JSON/schema,
graph, external-provider or scheduling correctness.

`tools.golden_v4.discover`, `freeze` and `seal` are one-time authoring commands
and refuse to overwrite a sealed expectation manifest. There is no execution-time
golden update mode. `tools.golden_v4.finalize` publishes reports and evidence only;
it never changes the independent freeze.
