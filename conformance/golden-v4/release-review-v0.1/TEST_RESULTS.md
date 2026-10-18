# Executed release verification

Final runs use Python 3.13.5 on Windows, importing this isolated worktree's `src/openverify`. Exact interpreter, dependencies and commands are in GOLDEN_EXECUTION.json.gz and REGRESSION_EXECUTION.json. The installed consumer instead imports its own `Lib/site-packages/openverify` with `-I`.

| Final profile | Passed | Failed/errors | Skipped | JUnit suite seconds |
|---|---:|---:|---:|---:|
| Golden V4 | 15,236 | 0 | 0 | 232.889 |
| All revision regressions | 388 | 0 | 0 | 16.811 |
| Existing unit/integration/property/conformance/Relay suites | 1,037 | 0 | 1 | 338.222 |

Pytest stdout reports 232.77, 17.54 and 338.25 seconds respectively; JUnit and plugin measurements use different start/end boundaries. Golden plugin monotonic duration is 232.1572248999728 seconds, with 185 Relay API calls and 17.723293699731585 awaited seconds. Revision plugin wall duration is 16.993614699982572 seconds, with 15 Relay API calls and 1.9280781000852585 awaited seconds. Counts are test executions, not distinct semantic obligations.

Golden's executed modes are 15,010 cheap, 205 runtime and 21 integration cases. Some historical coordinate scaffolds are not assertions and receive no additional coverage credit. Nine Golden mutation probes and three revision probes pass by detecting the targeted corruption: Result state, optional observations, Decision, availability, weight identity, policy noninvocation, Provider ordering, lineage, cancellation, plus the reintroduced cancellation/custom-empty/usage-collision defects. They do not prove sensitivity to every possible bug.

The 366 existing revision cases are reused; 22 new parameter cases are in `tests/golden_v4_reconciliation/test_release_closure.py`. Current failures: **zero**. The new stdio checks initially failed twice with EOF, then passed after the production fix; INITIAL_RPC_RESULTS.jsonl and release-targeted-initial.xml.gz preserve the counterevidence. Assertions compare -32700/null id and -32600/known id independently of SUT output.

An earlier broader run produced **1,036 passed, 1 failed, 1 skipped** in 285.70 seconds: the standard regex child exceeded its two-second budget under concurrent verification/build load. Its isolated rerun passed (5.76 seconds including pytest overhead); the final sequential full run passed. The earlier failure is retained in release-existing.xml.gz and release-existing.log.gz, not erased by the rerun. The remaining skip is POSIX path behavior at `tests/relay/test_local_paths.py:66`.

## Package and consumer

- Current source archive and wheel build: PASS. Exact artifact SHA-256 values are in PACKAGE_RESULTS.json. Wheel SHA-256: `788cacc8b906466a3609280403c2c855473dc4c8aee7a5e210879d4e6cd519f2`.
- Disposable consumer environment, no system site packages; stdlib `venv --without-pip`, `ensurepip`, then force-reinstall wheel and dependencies: PASS. `pip check`: no broken requirements.
- `-I` consumer executes an authored standard-text graph and checks PASS, starts the installed `openverify --help` launcher with PYTHONPATH/PYTHONHOME removed, checks `py.typed`, profile and all 24+9 schema resources: PASS.
- Every packaged schema root and changed server source is byte-equal to the reviewed checkout: 34/34 checks PASS. Installed resource digests are in CONSUMER_RESULTS.json.
- `uv` initially failed to edit Windows PE launcher resources in sandbox temp. `ensurepip` also hit sandbox temp permissions. Workspace-local TMP/TEMP and the standard installer succeeded; these were environment failures. The first consumer harness incorrectly imported `constant` from the top-level module and then tried nonexistent `python -m openverify`; both were harness errors, corrected to `openverify.authoring.constant` and the documented installed console launcher. Initial harness logs are preserved. No production change was made for these errors.
- This is a core installed-consumer check. Optional HTTP/MCP/code extras are exercised in the existing development environment, not independently installed as every clean consumer configuration. No other platform or interpreter is certified.

## PowerShell reproduction

Run from the named worktree. `$py` is the existing shared development interpreter; `$consumer` is disposable and stays in this worktree.

```powershell
Set-Location 'C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\vcp-final-semantics'
$py = (Resolve-Path '..\..\.venv\Scripts\python.exe').Path
$review = Join-Path (Get-Location) 'conformance/golden-v4/release-review-v0.1'
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
$env:OPENVERIFY_GOLDEN_SOURCE_REVISION = Join-Path $review 'SOURCE_REVISION.json'
$env:OPENVERIFY_GOLDEN_EXPECTATION_REVISION = Join-Path (Get-Location) 'conformance/golden-v4/verification-final/EXPECTATION_CORRECTIONS.json'
& $py -B -m pytest -q -c tests/golden_v4/pytest.ini tests/golden_v4 --junitxml=.pytest_cache/release-golden-final.xml
$env:OPENVERIFY_RECONCILIATION_OUTPUT = $review
& $py -B -m pytest -q tests/golden_v4_reconciliation --basetemp=.pytest_cache/release-regression-final-tmp --junitxml=.pytest_cache/release-regression.xml
& $py -B -m pytest -q tests/unit tests/integration tests/property tests/conformance tests/relay tests/test_error_contract_hardening.py --basetemp=.pytest_cache/release-existing-final-tmp --junitxml=.pytest_cache/release-existing-final.xml
& $py -m tools.golden_v4.report --verify-freeze
& $py -m ruff check src/openverify/relay/adapters/server.py tests/golden_v4_reconciliation/test_release_closure.py
```

Exact single-case selectors and rerun commands are retained per case in GOLDEN_RESULTS.jsonl.gz and REGRESSION_RESULTS.jsonl. Example for the new parse response:

```powershell
& $py -m pytest -q 'tests/golden_v4_reconciliation/test_release_closure.py::test_stdio_reserved_errors_at_real_server[PARSE_ERROR]'
```

Package commands (the first venv directory must be new for a fresh check):

```powershell
& "$env:LOCALAPPDATA\hermes\bin\uv.exe" build --python $py --out-dir .pytest_cache/release-package/dist
& $py -m venv --without-pip .pytest_cache/release-package/consumer-python
$consumer = Join-Path (Get-Location) '.pytest_cache/release-package/consumer-python/Scripts/python.exe'
$installerTemp = Join-Path (Get-Location) '.pytest_cache/release-installer-temp'
New-Item -ItemType Directory -Force $installerTemp | Out-Null
$env:TEMP = $installerTemp
$env:TMP = $installerTemp
& $consumer -I -m ensurepip --default-pip
& $consumer -I -m pip install --no-cache-dir --force-reinstall .pytest_cache/release-package/dist/openverify-0.1.0-py3-none-any.whl
& $consumer -I -m pip check
& $consumer -I conformance/golden-v4/release-review-v0.1/consumer_check.py
& $py -B conformance/golden-v4/release-review-v0.1/review_evidence.py
```

The review script only emits conservative release dispositions and checks original frozen file hashes. It does not extract requirements, update frozen expectations, or certify residuals. Human-maintained domain/limitation/test reports remain separate from generated execution evidence.

JUnit XML, per-case JSONL, initial failures, stdout/build/installer logs, source hashes and package digests are retained beside this document. All 21 original frozen files remain byte-identical to their manifest. Earlier canonical/reconciliation/final-verification artifacts are unchanged. A passing test asserting a fail-closed historical inventory verdict is not a passing coverage gate; no universal certification is asserted.
