# OpenVerify language SDKs

OpenVerify is the universal verification ecosystem. VCP supplies portable
verification semantics, Provider Contract supplies the portable verifier interface,
and Relay is the separate Python reference execution engine.

These packages are functional **DRAFT wire libraries with a bounded semantic
subset**. They are not full protocol implementations or Relay ports. Every package
has its own metadata, dependency graph, bundled offline schemas, native tests and
release workflow. No package depends on another language runtime.

The normative baseline is production commit
`5f17f402a270882f244a54dde25eda92a085eb39`, from
`fix/relay-production-boundaries`. VCP marker `draft` is revision-sensitive;
Provider Contract version is exact `0.1`. Golden and canonical-review have not
been used as implementation or certification sources.

| SDK | Proposed package | Registry | Native validator |
| --- | --- | --- | --- |
| Node/TypeScript | `@openverify/sdk` | npm | Ajv 8, Draft 2020-12 |
| Rust | `openverify-sdk` | crates.io | jsonschema, Draft 2020-12 |
| Go | `github.com/openverifyproject/openverify/sdk/go` | Git/Go modules | santhosh-tekuri/jsonschema v6, ECMAScript regex adapter |
| JVM | `io.github.openverifyproject:openverify-sdk` | Maven Central | NetworkNT, Draft 2020-12 |
| .NET | `OpenVerify.Sdk` | NuGet | JsonSchema.Net, Draft 2020-12 |
| Ruby | `openverify-sdk` | RubyGems | json_schemer, Draft 2020-12 |
| PHP | `openverify/sdk` | Packagist | Opis JSON Schema, Draft 2020-12 |
| Python wire library | `openverify-wire` (`openverify_sdk`) | PyPI | jsonschema, Draft 2020-12 |

All begin at package version 0.1.0; these versions are independent. The original
`openverify` Python package remains unchanged. Its API is audited separately
against the shared corpus; its additional engine functionality is not copied.

## Supported functionality

All normative VCP and Provider schema roots are distributed and can be used for
explicit structural validation. No schema resolution needs network access.
Native public wire object views preserve JSON object shape, optional-field
presence, payload null and unknown optional extensions. Node exports TypeScript
types; Rust has serde integration. Other packages expose native JSON-backed
objects. Complete field-by-field static model generation is not implemented.

The semantic parser supports Result, Decision, Resource, Evidence, ArtifactRef,
Extension and ResourceDimension: Result axes and observations; ROUTE destination;
meaningful Evidence; resource kind/value/range ordering; unsupported required
extensions; and nested evidence, artifact references, usage and extensions.
It rejects unsupported VCP semantic types with local `SDK_UNSUPPORTED` instead
of treating schema acceptance as semantic validity.

Provider support includes standalone manifests/capabilities, duplicate capability
identities, advertised VCP membership, capability schema validity/self-contained
references, invocation versions and exact resource budgets, Outcome conditionals,
and embedded VCP Evidence/Artifact/Resource event semantics. Input/config/output
validation is an explicit native API with stable specified error codes. Schema
defaults do not insert data; capability `format` is annotation-only. No provider
invocation, transport or native provider-serving helper is advertised.

Unimplemented: graph/definition/dataflow/policy/profile/provenance semantics;
Provider session initialization/selection, correlation and lifecycle state;
contextual capability matching; clock/deadline semantics and enforcement; and
transport framing. Parsing deadline/timestamp-bearing Provider objects explicitly
fails with `SDK_UNSUPPORTED`. Structural validation remains separately available.
No scheduler, runner, CLI, domain verifier or canonical hashing is supplied.

The new numeric parsers reject unsupported lossy/nonfinite values where their
native representation would lose data. Native direct object construction cannot
recover precision lost before the API was called. No common binary arithmetic or
canonical serialization is promised by this draft.

## Tests and packages

`conformance/sdk/manifest.json` owns the shared JSON expectations. All eight native
runners read the same files; no language maintains a private expectation copy.
The suite is intentionally bounded and does not establish complete conformance.

Run `python tools/sdk_verify.py LANGUAGE` from the repository root after installing
that language's toolchain and Python build/pytest/jsonschema/pydantic tooling.
It runs native tests, builds a real distribution twice, checks repeatable packaged
file contents and installs the resulting package in a separate consumer project.
Registry downloads for dependencies are permitted; validation itself is offline.
Go's local consumer uses an extracted module and a local replacement because the
SDK tag is not public yet. Registry module resolution is a later release check.

Results and built artifacts are in ignored `dist/sdk/LANGUAGE/`. Verification
records state the Git commit, dirty-tree status, counts and artifact checksums.
Dirty-tree verification is useful locally but is rejected by release preflight.
Native archive container timestamps are ignored for the content comparison;
byte-for-byte archive reproducibility across hosts is not claimed.

Schema packaging is reproducible using `python tools/sdk_bundle.py` with
jsonschema installed. It copies original normative schemas exactly, records
their hashes, and derives local-only resource bundles and narrowly documented
prose checks. `sdk/tests` verifies drift, fixtures and release/mirror guards.
These generated copies are not independently maintained schemas or protocol specs.

Read [RELEASE.md](RELEASE.md) for exact first-time setup and subsequent releases,
[REPORT.md](REPORT.md) for measured results and blockers, and
[open-questions.md](open-questions.md) for public contract questions deferred by
this change. No registry has been modified and nothing has been published.
