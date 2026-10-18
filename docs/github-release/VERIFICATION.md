# Local release preparation evidence

Source-upload readiness and package-release approval are separate. The source
branch is prepared; package publication is blocked by the owner steps in
[GITHUB_HANDOFF.md](../../GITHUB_HANDOFF.md). The root Python semantic release
gate remains blocked. This document does not certify universal conformance.

## Executed profiles

| Profile | Actual outcome | Pytest console seconds |
|---|---|---:|
| Golden V4 | 15,236 passed | 84.59 |
| Revision regressions | 388 passed | 10.11 |
| Existing production suites | 1,037 passed, 1 skipped | 179.60 |
| Final Python SDK plus maintenance guards | 234 passed (197 SDK/compatibility + 37 guards) | 2.87 |

The one production skip is `tests/relay/test_local_paths.py:66`: POSIX path
semantics on Windows. There were no xfails in the final Python compatibility
run. Nine Golden and three revision mutation probes detected their targeted
corruptions. This demonstrates those probes, not general mutation completeness.

[VERIFICATION.json](VERIFICATION.json) records commands, JUnit timings and
package hashes. Console timings, JUnit suite timings and reporter wall timings
measure different intervals; they are retained separately. Compressed JUnit,
stdout and per-case JSONL are in [evidence/](evidence/).
[EVIDENCE_HASHES.json](EVIDENCE_HASHES.json) seals their exact compressed bytes.

The full Python suites ran at `479e59ee580f5578c14846a5bd8c8c1dfe15536b`.
Later changes fix the Node dependency and add handoff evidence; Python
production, normative files, schemas and Golden assertions did not change.
The freeze check was repeated on the final code descendant and passed.
Original frozen expectation files were preserved; the existing versioned
expectation corrections and the explicit documentation source overlay were
selected during execution.

## SDK native/package/consumer runs

Every language consumed the same 52 VCP and 45 Provider fixtures. These are
shared wire cases, not 97 independent semantic contracts or full Relay tests.
Each verifier ran native tests, built its main package twice, compared canonical
package contents and installed/used it from a disposable external consumer.

| SDK | Native test reporting | Verifier elapsed seconds |
|---|---|---:|
| Node | 105 tests | 21.13 |
| Python | 197 tests including original Python compatibility | 161.58 |
| Rust | 2 integration functions including the shared case loop | 202.95 |
| Go | 3 top-level test functions including shared subcases | 62.36 |
| JVM | 98 tests | 49.41 |
| .NET | 98 tests | 57.21 |
| Ruby | 99 runs, 154 assertions | 157.17 |
| PHP | 3 tests, 194 assertions | 65.95 |

[SDK_VERIFICATION.json](SDK_VERIFICATION.json) records each actual tested commit,
artifact hash and repeat-content digest. Seven SDKs ran at
`b992b926c24fc7eef88a9d69c6613c6a79c913be`; their language sources and shared
fixtures remained identical afterward, checked with `git diff --name-only`.
Node ran again at `4d8f128f7085e2dc4cb60a0465c3b5b9c61b8026` after pinning Ajv
8.20.0. The final npm audit reported zero advisories. That result does not audit
all ecosystems. Exact native stdout is retained, rather than adding test
function counts across incomparable native frameworks.

The former standalone Python compatibility discrepancy now passes as an actual
assertion: unknown `vcp_version` is rejected. The stale xfail fallback was
removed. Definition/dataflow unused-default semantics remain outside the wire
SDK implementation scope and are documented explicitly; structural acceptance
is not a promise of full semantic validation.

Initial JVM Javadoc and Ruby executions were denied by the sandbox. Authorized
reruns passed; the failed sandbox logs are retained. An optional final combined
Python invocation initially omitted `sdk/python/src` from `PYTHONPATH`, causing
collection failure; correcting the invocation yielded 234 passes. The original
failed collection log/XML is retained. These resolved execution failures are
not omitted from the record or presented as package defects.

## Core packaging and workflow checks

`uv build` produced wheel and source distribution. A disposable Python 3.13
environment installed the wheel, passed `pip check`, then ran the existing
consumer under isolated mode (`python -I`). It imported from site-packages,
executed an authored standard-text graph, checked CLI help and verified 24 VCP
and 9 Provider packaged schema roots. Optional extras and every public host
operation were not all consumer-tested. Root package installation success does
not discharge the existing 615-record semantic gate.

All 11 workflows pass actionlint 1.7.7, with shellcheck and pyflakes disabled.
Maintenance tests check full action SHA pins, PR triggering, publication
isolation, package boundaries and PHP mirror safety. GitHub-hosted Actions,
protected environments, registry credentials and release-tag execution cannot
be verified before the owner's authorized remote setup. No source branch push
triggers package publication; each SDK publisher needs its matching tag.

## Reproduce locally in PowerShell

Use the prepared worktree and a Python environment containing the root test
dependencies. SDK verification additionally requires the language tools listed
in `sdk/README.md`; it downloads dependencies and creates disposable consumers.

```powershell
Set-Location 'C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\openverify-release-v0.1'
uv sync --frozen
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
$env:OPENVERIFY_GOLDEN_SOURCE_REVISION = 'docs/github-release/SOURCE_REVISION.json'
$env:OPENVERIFY_GOLDEN_EXPECTATION_REVISION = 'conformance/golden-v4/verification-final/EXPECTATION_CORRECTIONS.json'
uv run python -m pytest -q -c tests/golden_v4/pytest.ini tests/golden_v4
$env:OPENVERIFY_RECONCILIATION_OUTPUT = '.pytest_cache/github-prep/reproduce-regressions'
uv run python -m pytest -q tests/golden_v4_reconciliation
uv run python -m pytest -q tests/unit tests/integration tests/property tests/conformance tests/relay tests/test_error_contract_hardening.py
uv run python -m tools.golden_v4.report --verify-freeze
uv run python -m pytest -q sdk/tests/test_tooling.py
# Run each separately; check $LASTEXITCODE after each invocation.
uv run --with build python tools/sdk_verify.py node
uv run --with build python tools/sdk_verify.py python
uv run --with build python tools/sdk_verify.py rust
uv run --with build python tools/sdk_verify.py go
uv run --with build python tools/sdk_verify.py jvm
uv run --with build python tools/sdk_verify.py dotnet
uv run --with build python tools/sdk_verify.py ruby
uv run --with build python tools/sdk_verify.py php
uv build --out-dir .pytest_cache/github-prep/reproduce-dist
```

Use the recorded JSON commands and supplied workflow environments for exact
CI/profile variants. The preparation used a Python 3.13 interpreter and local
language caches; CI selects supported Ubuntu/Windows and pinned runtime major
versions. Local .NET used net8.0 with an installed .NET 10 roll-forward runtime;
Java compiled target 17 on the available newer JDK. Those runs do not prove all
platform/runtime combinations. The owner must wait for the first remote CI.

## Remaining release limits

The preserved semantic gate has 615 dispositions: one verified projection,
396 partial records and 218 records without reviewed assertion links. Full
Golden certification is unproved, and the root distribution is not approved for
release. The SDK scope is bounded wire functionality. Registry names are not
reserved by the unauthenticated observations in
[REGISTRY_OBSERVATIONS.json](REGISTRY_OBSERVATIONS.json). See
[SECURITY_REVIEW.md](SECURITY_REVIEW.md) for scanner scope, reviewed false
positives, metadata exposure and large historical artifacts.
