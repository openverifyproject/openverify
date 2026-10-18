# VerifyAnything

VerifyAnything DRAFT wire SDK for dotnet. Independently versioned package **0.1.0**,
intended registry: NuGet. Names/ownership must be confirmed before publication.

VCP means portable verification semantics; Provider Contract means the portable
verifier interface; Relay is the separate Python reference execution engine.

This SDK bundles every normative VCP/Provider schema at source revision
`5f17f402a270882f244a54dde25eda92a085eb39`. VCP marker: `draft`;
Provider Contract: exact `0.1`. Both remain DRAFT with no stable 1.0 promise.
Validation does not fetch schemas, artifact content or URLs.

```csharp
var value = OpenVerify.Sdk.Parse("vcp", "decision", """{"protocol":"draft","kind":"CONTINUE"}""");
var json = OpenVerify.Sdk.Serialize(value);
```

## Actual support

The public wire object is a native JSON object view, retaining absent fields,
explicit null payloads and unknown optional extensions. It is not a complete
generated field-by-field static model of every protocol object. Structure-only
validation covers all shipped schema roots. Parse/semantic validation supports
Result, Decision, Resource, Evidence, ArtifactRef, Extension and ResourceDimension.
It checks Result state axes, Decision destinations, meaningful Evidence,
resource kinds/ranges, required extensions and nested evidence/usage/extensions.

Provider standalone validation covers manifest structure, capability identity
uniqueness and advertised VCP membership, self-contained capability schemas,
Outcome state/output/error conditionals, and invocation version/resource-budget
checks. `validateData` (snake_case in Python/Ruby/Rust) validates capability
input, config or output with an explicit error classification; formats are
annotations. There is no implicit capability matching or session initialization.

Semantic validation of graphs, definitions, profiles, execution-policy objects,
dataflow and provenance is **not implemented** in these new wire libraries.
It fails with the local diagnostic `SDK_UNSUPPORTED`; callers may explicitly
request structure-only validation. Provider session/lifecycle, transport,
deadline enforcement and contextual invocation matching are also unimplemented.
Parsing objects carrying deadline/timestamp fields fails with SDK_UNSUPPORTED;
call structure-only validation if that explicit limitation is acceptable.
Standalone parsing does not establish those properties. Detailed support/gaps and
release gates are in the repository's `sdk/README.md` and `sdk/RELEASE.md`.

Errors expose stable codes where the source contract specifies them. Decision
rejection uses a local structural classification because the source prose does
not specify a Decision-specific diagnostic. No portable canonicalization or
hashing is claimed. Serialize preserves data and inserts no schema defaults.
Mutable native containers must be validated again after mutation.

## Build and test

From this directory: `dotnet test OpenVerify.Sdk.Tests`.
From the source repository root: `python tools/sdk_verify.py dotnet` runs the
native runner over the same versioned `conformance/sdk/manifest.json`, builds
twice, compares package file contents and installs into a separate consumer.
Dependency installation can use the network; actual schema validation is offline.
The shared corpus is a bounded compatibility test, **not full protocol certification**.

## Release

Tag only this language: `sdk/dotnet/vX.Y.Z` after updating only its package.
The protected release environment is `sdk-dotnet`. First publication requires
owner setup and explicit approval; no package has been published by this change.
License: MIT (included in the distribution).

Package setup: [VerifyAnything publication guide](https://github.com/openverifyproject/openverify/blob/main/docs/releases/VERIFYANYTHING_SETUP.md).
