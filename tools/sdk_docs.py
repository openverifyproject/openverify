"""Generate package introductions from the shared support description."""
# ruff: noqa: E501 -- literal example programs and generated Markdown

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "node": (
        "openverify",
        "npm",
        "npm ci && npm test",
        "import {parse, serialize} from 'openverify';\nconst object = parse('vcp', 'decision', '{\"protocol\":\"draft\",\"kind\":\"CONTINUE\"}');\nconsole.log(serialize(object));",
        "typescript",
    ),
    "rust": (
        "openverify",
        "crates.io",
        "cargo test --locked",
        'let object = openverify_sdk::parse("vcp", "decision", r#"{"protocol":"draft","kind":"CONTINUE"}"#)?;\nlet json = openverify_sdk::serialize(&object)?;',
        "rust",
    ),
    "go": (
        "github.com/openverifyproject/openverify/sdk/go",
        "Go modules",
        "go test ./...",
        'object, err := openverify.Parse("vcp", "decision", []byte(`{"protocol":"draft","kind":"CONTINUE"}`))\nif err != nil { panic(err) }\njson, err := openverify.Serialize(object)',
        "go",
    ),
    "jvm": (
        "io.github.openverifyproject:openverify",
        "Maven Central",
        "mvn verify",
        'var object = org.openverify.sdk.Sdk.parse("vcp", "decision", """\n{"protocol":"draft","kind":"CONTINUE"}\n""");\nvar json = org.openverify.sdk.Sdk.serialize(object);',
        "java",
    ),
    "dotnet": (
        "OpenVerify",
        "NuGet",
        "dotnet test OpenVerify.Sdk.Tests",
        'var value = OpenVerify.Sdk.Parse("vcp", "decision", """{"protocol":"draft","kind":"CONTINUE"}""");\nvar json = OpenVerify.Sdk.Serialize(value);',
        "csharp",
    ),
    "ruby": (
        "openverify",
        "RubyGems",
        "bundle install && bundle exec ruby test/shared_test.rb",
        "require 'openverify'\nobject = OpenVerify.parse('vcp', 'decision', '{\"protocol\":\"draft\",\"kind\":\"CONTINUE\"}')\nputs OpenVerify.serialize(object)",
        "ruby",
    ),
    "php": (
        "openverify/openverify",
        "Packagist",
        "composer install && composer test",
        "require 'vendor/autoload.php';\n$object = OpenVerify\\Sdk::parse('vcp', 'decision', '{\"protocol\":\"draft\",\"kind\":\"CONTINUE\"}');\necho OpenVerify\\Sdk::serialize($object);",
        "php",
    ),
    "python": (
        "openverify-wire",
        "PyPI",
        "python -m pip install -e . pytest && python -m pytest",
        'from openverify_sdk import parse, serialize\nvalue = parse(\'vcp\', \'decision\', \'{"protocol":"draft","kind":"CONTINUE"}\')\nprint(serialize(value))',
        "python",
    ),
}

if __name__ == "__main__":
    for language, (name, registry, command, example, syntax) in PACKAGES.items():
        extra = (
            "\nThe module import is `github.com/openverifyproject/openverify/sdk/go`. Its\nrelease tag is **sdk/go/v0.1.0**, the Go nested-module tag (no extra v directory).\n"
            if language == "go"
            else ""
        )
        extra += (
            "\nThis independently packaged wire-only library uses module `openverify_sdk` and\nproject `openverify-wire`. The original `openverify` Python distribution and its\nRelay API remain unchanged. Both are checked against the common fixtures.\n"
            if language == "python"
            else ""
        )
        if language == "rust":
            extra += '\nKeep existing Rust imports with this Cargo dependency alias:\n```toml\n[dependencies]\nopenverify_sdk = { package = "openverify", version = "0.1.0" }\n```\nThe library target remains `openverify_sdk`; the registry crate is `openverify`.\n'
        text = f"""# {name}

OpenVerify DRAFT wire SDK for {language}. Independently versioned package **0.1.0**,
intended registry: {registry}. Names/ownership must be confirmed before publication.

VCP means portable verification semantics; Provider Contract means the portable
verifier interface; Relay is the separate Python reference execution engine.

This SDK bundles every normative VCP/Provider schema at source revision
`5f17f402a270882f244a54dde25eda92a085eb39`. VCP marker: `draft`;
Provider Contract: exact `0.1`. Both remain DRAFT with no stable 1.0 promise.
Validation does not fetch schemas, artifact content or URLs.

```{syntax}
{example}
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

From this directory: `{command}`.
From the source repository root: `python tools/sdk_verify.py {language}` runs the
native runner over the same versioned `conformance/sdk/manifest.json`, builds
twice, compares package file contents and installs into a separate consumer.
Dependency installation can use the network; actual schema validation is offline.
The shared corpus is a bounded compatibility test, **not full protocol certification**.
{extra}
## Release

Tag only this language: `sdk/{language}/vX.Y.Z` after updating only its package.
The protected release environment is `sdk-{language}`. First publication requires
owner setup and explicit approval; no package has been published by this change.
License: MIT (included in the distribution).
"""
        (ROOT / "sdk" / language / "README.md").write_text(text, encoding="utf-8", newline="\n")
