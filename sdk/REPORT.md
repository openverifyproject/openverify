# SDK implementation verification

Implementation is isolated on `feat/language-sdks`, based on production
`5f17f402a270882f244a54dde25eda92a085eb39`. The complete support boundary is in
[README.md](README.md). This is a bounded DRAFT wire SDK release candidate, not
full VCP/Provider Contract certification.

Native package verification was run on clean implementation commit
`06660630ec061c5fc61cfe3ed0760ed379ff92c4` on Windows. The final reporting commit
adds this report, checked-in verification evidence, and lets the original-Python
audit skip when only the independent wire package is installed. SDK runtime source,
fixtures and distributions were tested on the implementation commit.

Every language read the same **97 shared cases: 52 VCP and 45 Provider Contract**.
The Provider count includes standalone object and explicit capability-schema
instance checks, not invocation/transport execution. Counts describe this bounded
corpus, not a percentage of the entire normative protocol.

| Language | Package / registry | VCP passed/total | Provider passed/total | Clean package installation | Independently publishable package | Release workflow |
| --- | --- | --- | --- | --- | --- | --- |
| Node/TypeScript | `@openverify/sdk` / npm | 52/52 | 45/45 | PASS, built tarball in fresh npm consumer | Yes, ESM library with declarations | Implemented; local lint passes; ownership/OIDC setup pending |
| Rust | `openverify-sdk` / crates.io | 52/52 | 45/45 | PASS, extracted verified crate in fresh Cargo consumer | Yes, serde-enabled crate | Implemented; scoped publishing token pending |
| Go | `github.com/openverifyproject/openverify/sdk/go` / Git + Go modules | 52/52 | 45/45 | PASS, extracted module and local replace in fresh consumer | Yes, correct nested module/tag layout | Implemented; public tag/module resolution pending |
| JVM | `io.github.openverifyproject:openverify-sdk` / Maven Central | 52/52 | 45/45 | PASS, locally installed Maven artifact in separate consumer | Yes, binary/source/Javadoc JARs | Implemented; Portal namespace, credentials and signing pending |
| .NET | `OpenVerify.Sdk` / NuGet | 52/52 | 45/45 | PASS, local NuGet archive in fresh consumer | Yes, .NET 8 library with XML docs | Implemented; scoped NuGet API key pending |
| Ruby | `openverify-sdk` / RubyGems | 52/52 | 45/45 | PASS, built gem installed into separate GEM_HOME | Yes, native Ruby API | Implemented; pending trusted publisher setup |
| PHP | `openverify/sdk` / Packagist | 52/52 | 45/45 | PASS, exact ZIP installed through Composer into fresh consumer | Yes, PSR-4 package | Implemented; dedicated mirror, token and Packagist registration pending |
| Python wire library | `openverify-wire` / PyPI | 52/52 | 45/45 | PASS, built wheel in a fresh venv | Yes, wire-only library independent of Relay | Implemented; pending PyPI trusted publisher setup |

“Independently publishable” means a real self-contained distribution was built,
installed and called without another SDK or Relay. **No package is authorized or
configured for public publication yet.** Namespace ownership is unverified, no
release environment has been created/configured by this task, and GitHub Actions
has not been executed remotely. The workflows are locally linted implementations,
not proof of a successful authenticated registry release.

## Actual functionality and limits

All eight new packages provide native JSON-backed wire models, serialization,
strict parsing and offline Draft 2020-12 schema validation. They implement the
same standalone Result/Decision/Evidence/Resource/Extension subset and Provider
manifest/capability/Outcome/input/config/output checks described in
[README.md](README.md). All package distributions contain schemas and the project
and bundled metaschema license notices. Node is ESM-only; no CJS compatibility
claim is made. Rust exposes a public serde-compatible wrapper; Go exports native
APIs; JVM targets Java 17; .NET targets .NET 8; Ruby requires >=3.2; PHP requires
>=8.2; the independent Python wire library requires >=3.11.

These are real wire libraries, **not full field-by-field model sets or complete
semantic implementations**. Full graph/definition/dataflow/policy/profile/
provenance semantics and Provider sessions/transport/contextual matching remain
unimplemented. Timestamp-bearing Provider objects fail clearly as unsupported.
No native provider-serving helpers, scheduler, runner, CLI or domain-specific
verifier is included. Those gaps block any claim of full protocol conformance.

## Additional measured checks

- Node: **105 native tests passed**, including the 97 shared cases and duplicate,
  precision, overflow, prototype-key preservation and unsupported-feature checks.
- Rust: both native test functions pass; the shared function executes all 97
  cases. `cargo package` also builds/verifies the crate before external use.
- Go: shared corpus, duplicate-key and invalid UTF-8 tests pass.
- JVM: **98 native tests passed**, including the shared corpus and duplicate keys.
- .NET: **98 native tests passed**, including the shared corpus and duplicate keys.
- Ruby: **99 native tests, 154 assertions passed**; no failures/errors/skips.
- PHP: **3 native test functions, 194 assertions passed**, including all shared cases.
- Python: **196 passed, one expected failure** across the new wire library and
  original-SDK audit. The new wire library's 100 tests all pass; the existing SDK
  audit is **52/52 VCP and 44/45 Provider**, with the unknown standalone VCP version
  case recorded as expected failure. Existing production code remains unchanged.
- SDK maintenance/release/mirror regression tests: **24 passed**.
- Ruff lint/format: pass for the new Python SDK/tests and maintenance tools.
- All ten SDK workflow files: **actionlint passes** (shellcheck not enabled).
- All eight package builds repeated with identical distributed main-archive
  contents. Native container timestamps are normalized for that comparison;
  clean-room cross-host byte reproducibility/signing is not certified.
- Every SDK's final verification record reports a clean Git tree at the tested
  implementation commit. [verification.json](verification.json) records the
  package SHA-256 values, artifact names, source commit and fixture totals.
- Git diff against the production base contains no Golden/canonical-review,
  normative schema/spec, production Python/Relay or original-test edits.

The Windows host has .NET 10 runtime and SDK; the library targets .NET 8. Local
tests used `DOTNET_ROLL_FORWARD=Major`; CI explicitly installs .NET 8. Ruby,
Javadoc and Python venv creation needed sandbox execution exceptions, then passed.
The other commands used worktree-local caches. Those host-specific settings are
not package/runtime dependencies.

## Credentials and first-time blockers

Exact registry coordinates, environment names, OIDC fields, secret names,
namespace/signing requirements, Go tag mapping, PHP mirror behavior and subsequent
one-language release steps are in [RELEASE.md](RELEASE.md). Pending setup is:

- npm scope/package ownership and trusted-publisher connection; npm may require
  an explicitly approved owner bootstrap before that connection exists.
- PyPI and RubyGems accounts and pending trusted publishers.
- crates.io package ownership and scoped publishing token.
- NuGet package ownership and scoped API key.
- Central Portal verified namespace, Portal user token and signing credentials.
- Public Go source/tag availability, then registry module-resolution verification.
- Dedicated PHP mirror authorization, repository-scoped token, Packagist project
  registration and VCS/webhook synchronization. No mirror has been created/pushed.
- Protected GitHub release environments and explicit first-publication approval.

Registry checks on 2026-10-17 returned HTTP 404 for each proposed coordinate.
[registry-check.json](registry-check.json) retains the exact endpoints and time.
These observations reserve nothing and establish no ownership. Live publication,
OIDC exchange, signing acceptance, PHP remote sync and post-publication registry
consumer installs are **not tested**. They require owner setup and authorization.

No package publication, external repository creation, branch/tag push or registry
setting change has been performed. Golden, canonical-review, normative specs and
production Python/Relay files are unchanged.
