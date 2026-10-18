# Targeted Relay production fixes

Protocol status remains DRAFT. No push, Golden merge, scheduler redesign, new
protocol object, wire schema revision, or Reference Engine change was made.

## Revisions and preservation

- Original checkout: `feat/openverify-relay` at `efe9abd` (initially clean).
- Implementation base: `fix/openverify-error-contract-v02` at `5064efb`.
- New implementation branch: `fix/relay-production-boundaries`.
- Frozen suite: existing `test/openverify-golden-v0.2` worktree at `bc41342`.
- Existing branches and worktrees were preserved. Implementation and final
  documentation commits are recorded in Git; final HEAD is reported on delivery.
- Implementation commits: `10a3055` (catalog/binder), `52335b7` (local paths),
  `bfa6906` (error identity/compatibility and policy regression coverage).
- The working tree is checked after the reporting commit; no push is performed.

## Already present at 5064efb

The malformed custom-policy parser boundary already returned POLICY_OUTPUT,
retaining its structured parsing cause, path, diagnostic details and exception
chain. Catalog entry checks and catalog/binder invocation exception wrappers
already existed. The three typed registries, typed known codes, wire-string
serialization, Provider namespaced extensibility and recursive StrEnum JSON
normalization were already implemented. These were verified rather than replaced.

The registry inventory is 35 VCP/SDK enum members (including the existing local
POLICY_ERROR and RESULT_PROJECTION diagnostics), eight normative reserved Provider
Contract codes, and ten Relay-only codes. The normative registry consistency
tests pass. Provider Contract CAPABILITY_UNAVAILABLE remains owned by its layer;
no merged vocabulary or new generic ERROR code was introduced.

## New repairs

1. Catalog discovery **and iteration** now share the exception boundary. Valid
   sequences are snapshotted with validated manifests; invalid members and duplicate
   identities reject before any invocation. Generators remain invalid because the
   existing port contract requires Sequence. Lazy sequence lookup/iteration failures
   become CATALOG_FAILURE with cause type/message and exception chaining.
2. Catalog initialization, provider manifest discovery, trusted entry-point loading,
   and invalid registration values now have structured boundaries. Existing
   ProtocolError and ProviderContractError objects retain their classifications.
3. Binder return validation, compatibility and trust checks are guarded too.
   Candidates receive independent manifest containers: a replacement binder cannot
   rewrite the trusted catalog's capability schemas and then approve that rewrite.
   Invalid/incompatible choices invoke no provider; explicit valid choices retain
   exact provider/version provenance.
4. Scope comparisons now use native local path components consistently for files,
   directories and ranges. Relative POSIX spellings work on both platforms. Windows
   native/mixed separators work; POSIX case/separator behavior is preserved.
   Traversal, empty/NUL paths and ambiguous/reserved Windows paths reject. Reported
   locations are unchanged. Matching is lexical and works for missing/deleted files.
5. Action-policy prefixes `tmp` and `tmp/` both denote descendants of a relative
   directory, excluding the directory itself and siblings. Invalid paths fail
   closed. This local choice is documented in providers.md and open-questions.md;
   it does not change VCP or Provider Contract semantics.
6. Empty coordinate ranges no longer intersect a nonempty range merely because
   their point lies inside it. Half-open endpoints and zero-count deletions remain
   exclusive/empty.
7. Unknown extensible exception codes normalize to their underlying plain strings,
   preventing overridden display/equality methods from impersonating reserved codes.
   Known codes retain their layer's enum identity. Nested JSON compatibility and
   caller-container preservation have direct regression coverage.

## Exact production files changed

```text
src/openverify/errors.py
src/openverify/provider/validation.py
src/openverify/relay/errors.py
src/openverify/relay/api.py
src/openverify/relay/adapters/catalog.py
src/openverify/relay/application/binding.py
src/openverify/relay/application/run.py
src/openverify/standard/paths.py
src/openverify/standard/scope.py
src/openverify/standard/control.py
```

Regression files: tests/relay/test_production_boundaries.py,
tests/relay/test_local_paths.py, tests/unit/test_error_code_compatibility.py, and
the expanded policy parametrization in tests/test_error_contract_hardening.py.

## Public Python compatibility

Existing signatures, wire strings, exception hierarchy and valid Sequence catalogs
remain supported. Known `.code` values remain StrEnums; unknown code strings stay
extensible, but custom string-subclass identity/equality is intentionally removed.
Binder candidate object identity is not preserved; manifests are independent
snapshots and transports retain identity. Mutating candidate schemas cannot change
the trusted catalog. Duplicate injected registrations now reject consistently
with Catalog.register. Newly guarded failures expose structured errors instead of
raw unexpected exceptions. Local path comparison and action-prefix behavior changes
are intentional corrections described above; invalid paths now reject explicitly.

## Validation

Run order began with focused production tests, followed by targeted frozen Golden,
then SDK/Relay, portable conformance, tooling, and smoke checks. Subsequent targeted
reruns checked follow-up changes; no full Golden run was performed.

| Check | Result |
| --- | --- |
| Final focused production/error compatibility regressions | 136 passed, one POSIX-only skip on Windows |
| Existing SDK/Relay/unit/property/integration run | 743 passed, one POSIX-only skip; later boundary additions verified in final focused run |
| Portable VCP + Provider Contract tests | 286 passed |
| Architecture direction/globals/cycle checks | Two passed |
| Ruff on production and SDK/Relay test directories | Pass |
| Formatting on the same scope | 128 files pass |
| Strict Pyright on src + relay/unit/property/integration/conformance tests | Zero errors/warnings |
| Whole-repository Ruff | 422 pre-existing errors, all in untouched Golden tests/tools |
| Whole-repository formatting | Nine untouched Golden tool files need formatting |
| Whole-repository Pyright | 1,992 errors: 1,957 in unchanged Golden adapters/tests and 35 in existing hardening tests |
| Text, real coding graph, guardrail, concurrent independent-run smoke | Four passed |
| Custom provider example | Exit 0; expected successful verification execution with FAIL judgment |

The broader run verifies capability/input/config/output schema enforcement,
provider errors distinct from FAIL, incurred usage, cancelled-output rejection,
command/stdout/stderr failures, concurrent isolation and RunRecord provenance.
No additional scheduler or normative RunRecord change was required.

### Frozen Golden execution evidence

The first integrity attempt in the implementation checkout stopped before execution:
Git had checked specification files out with CRLF while frozen hashes describe LF.
The successful runs used the **unchanged bc41342 worktree**, whose integrity check
passed (12,151 registered cases; 71 spec files; 99 checksummed files). Only 51
selected cases were requested. Python preloaded OpenVerify from this branch's
`C:/Users/siddh/OneDrive/Desktop/openverify/src`, and printed/asserted the imported
source path before executing the frozen runner. Frozen tools/tests/fixtures were
not copied, modified, or merged.

Results: **50 PASS, one BLOCKED_BY_SPEC, zero failures**. All twelve malformed
policy cases, all three reported replacement-port failures, Windows directory scope,
related file/range/action paths and twelve provider error-vocabulary cases passed.
The frozen `standard.action_policy.allowed` expectation explicitly blocks `tmp`
versus `tmp/` spelling and does not execute the implementation. Its historical
blocker remains unchanged, despite the local production choice now being documented.

Reports remain in `.pytest_cache/production-targeted-final/report.{json,md}`.
Other evidence uses `.pytest_cache/production-*` logs. These are local execution
artifacts, not revised Golden expectations. No full Golden conformance is claimed;
the complete frozen suite is left to the independent final audit.

## Remaining decisions and Golden-only work

NEEDS_SPEC_DECISION: no new normative decision was needed for these fixes.
Exact Decision error-code precedence, portable floating-point rounding, coherent
provenance authenticity and simultaneous parallel-cancellation representation
remain unresolved; their behavior was not guessed or redesigned.

GOLDEN_ONLY: deadline Decimal precision; provider-schema oracle false acceptances;
missing provenance assertions; 167 incomplete independent expectations; missing
availability/custom-provider coverage; synthetic mutation limitations; historical
frozen expectations/blockers; and the existing Golden lint/type/format debt.
None was repaired in production or by modifying Golden.

## Verdicts

| Requested verdict | Result |
| --- | --- |
| POLICY_OUTPUT BUG FIXED | YES (already present, all twelve cases verified) |
| CATALOG/BINDER BOUNDARIES FIXED | YES |
| WINDOWS PATH HANDLING FIXED | YES |
| ERROR CONTRACT CORRECT | YES for the audited contracts |
| TARGETED GOLDEN PASSES | NO if every selected case must PASS: 50 PASS, one historical frozen blocker, zero failures |
| EXISTING CONFORMANCE PASSES | YES |
| NO GOLDEN MODIFICATIONS | YES |
| SAFE TO RUN FINAL INDEPENDENT AUDIT | YES |
