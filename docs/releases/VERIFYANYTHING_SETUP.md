# Automated VerifyAnything releases

The npm package is **@openverifyproject/verifyanything**. Version 0.1.0 is already
published. The launcher queries real registries and skips it; neither source
push nor the setup script publishes anything. Other package coordinates and
portable wire-library scope remain unchanged. SDKs are not Relay engines.

GitHub setup is performed by `tools/release_github_setup.py --apply`, not by manual
UI work. It creates nine tag-restricted environments, safe non-secret variables,
admin-bypass-only release-tag rules, and an empty distribution-only PHP mirror.
It is idempotent and preserves unexpected existing policies for review. It does
not claim external registry authorization or set an unverified ownership flag.

External GitHub OIDC bindings all use owner `openverifyproject`, repository
`openverify`, with the exact filename/environment below:

| Product | Workflow filename | Environment | Authorization |
|---|---|---|---|
| npm (future versions) | sdk-release-node.yml | sdk-node | Existing scoped package trusted publisher |
| Python SDK | sdk-release-python.yml | sdk-python | PyPI pending publisher: verifyanything |
| Python harness | core-release-python.yml | core-python | PyPI pending publisher: openverify |
| Ruby | sdk-release-ruby.yml | sdk-ruby | RubyGems pending publisher: verifyanything |
| NuGet | sdk-release-dotnet.yml | sdk-dotnet | NuGet policy: package glob VerifyAnything; allow first publication |
| Rust | sdk-release-rust.yml | sdk-rust | First crate bootstrap token; OIDC optionally after initial publication |
| JVM | sdk-release-jvm.yml | sdk-jvm | Verified io.github.openverifyproject namespace, Portal token and signing key |
| PHP | sdk-release-php.yml | sdk-php | Restricted mirror-write token and Packagist main token |
| Go | sdk-release-go.yml | sdk-go | Owned public source repository; no registry credential |

`tools/Set-ReleaseCredentials.ps1` securely uploads required secrets through stdin
and configures actual NuGet/Packagist account names as variables. It skips existing
inputs, never writes secret files, and never prints credential values. Environment
configuration is already automated. Registry/account authorization is not assumed.

After source review/green PR and explicit merge approval, check out clean latest
origin/main and invoke `tools/release_launch.py --push --wait-for-ci`. It performs
no builds locally. It requires both main CI workflows green, checks required
credential names, queries published versions, and pushes only missing independent
version tags. Publication builds/tests run inside GitHub Actions. Existing tags
are never rewritten. Already published versions are never uploaded again.

Each SDK retains sdk/LANGUAGE/vX.Y.Z tags. Python harness uses core/python/vX.Y.Z.
Go keeps its required sdk/go nested-module prefix. PHP subtree tags translate to
mirror vX.Y.Z; the workflow registers or updates Packagist automatically with a
Bearer authorization header, never credentials in query parameters. It refuses
to take over a package tied to another source repository. No manual Composer
source repository, package build, environment or variable creation is required.

The full shared corpus, native tests, repeat builds and isolated consumer checks
remain mandatory. This is bounded DRAFT package evidence, not universal protocol
or Golden certification. Existing harness coverage limitations remain disclosed.
No normative specification or frozen expectation is modified by automation.

Registry authorization references:
- https://docs.npmjs.com/trusted-publishers/
- https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
- https://guides.rubygems.org/trusted-publishing/
- https://learn.microsoft.com/en-us/nuget/nuget-org/trusted-publishing
- https://central.sonatype.org/register/namespace/
- https://packagist.org/apidoc
