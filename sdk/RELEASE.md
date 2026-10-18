# Independent SDK releases

Current exact-name publication preparation: [FIRST_PUBLICATION.md](../FIRST_PUBLICATION.md). Prior verification artifacts retain their original package identities and hashes.

Nothing in this change publishes packages, creates external repositories, pushes
Git refs or changes registry settings. All steps below are for an authorized
maintainer after review. Local package archives are under `dist/sdk/`.

## First-time GitHub setup

1. Merge the reviewed SDK implementation into the public source repository
   `openverifyproject/openverify` after applicable CI passes. Review the bounded
   support statement; do not describe these packages as full VCP conformance.
2. Create environments `sdk-node`, `sdk-python`, `sdk-rust`, `sdk-go`, `sdk-jvm`,
   `sdk-dotnet`, `sdk-ruby`, and `sdk-php`. Restrict deployments to matching
   `sdk/LANGUAGE/v*` tags and require a release reviewer. Disable self-review.
   Create a tag ruleset that restricts creation, deletion and updates of those
   tags to maintainers. A release tag must point to reviewed code.
3. Configure the language's registry ownership and authentication below. Set
   environment variable `REGISTRY_OWNERSHIP_APPROVED=true` **only after** ownership,
   first-publication approval and the exact package coordinates are confirmed.
   The workflows fail closed without this variable. Environment protection is a
   GitHub account setting; workflow YAML cannot create or guarantee those rules.
4. Explicitly approve the first publication for the chosen SDK in the protected
   environment. A successful local dry run is not publication approval. No
   approval is presumed from an unlisted/unreserved registry name.

The release files are `.github/workflows/sdk-release-LANGUAGE.yml`.
`sdk-verify.yml` is a reusable test/build job with no publishing credentials.
Each tag triggers only its language's release file, which verifies the exact
tagged checkout, native fixtures, packages and clean consumer installation before
requesting entry to the protected publish environment. All eight releases are
independent; no workflow changes another package's version or tags.

## Registry setup

| Language | Exact setup and credentials |
| --- | --- |
| Node | Use an authorized npm account to register the unscoped package `openverify`; no npm organization or scope is required. Configure GitHub trusted publisher: owner `openverifyproject`, repository `openverify`, workflow `sdk-release-node.yml`, environment `sdk-node`. The workflow uses GitHub-hosted Node 24 and current npm (OIDC requires npm >=11.5.1 and Node >=22.14). If npm requires an existing package before publisher setup, an authorized owner must explicitly bootstrap the first verified tarball through npm's supported initial-publication flow, then configure OIDC for subsequent versions. The provided workflow intentionally has no long-lived npm token fallback. Never try to republish that bootstrap version. [npm instructions](https://docs.npmjs.com/trusted-publishers/). |
| Python | Create a PyPI account and a pending trusted publisher for project `openverify-wire`. Select GitHub, owner `openverifyproject`, repository `openverify`, workflow `sdk-release-python.yml`, environment `sdk-python`. Module name is `openverify_sdk`; the original `openverify` project is untouched. No API token secret is needed. [PyPI setup](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/). |
| Rust | Create/authorize a crates.io account; confirm ownership/name `openverify`. Generate a publishing token scoped to this crate with the shortest suitable expiry. Put it in `sdk-rust` as `CARGO_REGISTRY_TOKEN`. The workflow publishes from the verified extracted crate, not arbitrary files in the repository. [cargo publish](https://doc.rust-lang.org/cargo/commands/cargo-publish.html). |
| Go | Ensure `openverifyproject/openverify` is public and maintainers can create the source tag. Module is `github.com/openverifyproject/openverify/sdk/go`. Nested-module tag **`sdk/go/v0.1.0`** is already the correct Go tag, not `v0.1.0` or `sdk/go/v0.1.0/v1`. No registry credentials, upload or mirror is needed. The Git tag itself makes the module available. Protect the tag before release; preflight checks its exact commit rather than incorrectly requiring an already-created Go tag to be absent from the proxy. [module layout/version tags](https://go.dev/ref/mod#vcs-version). |
| JVM | Create a Sonatype Central Portal account; verify namespace `io.github.openverifyproject` through control of the GitHub organization. Confirm artifact `openverify`. Generate a **Central Portal user token**, and store its token username/password as `CENTRAL_USERNAME` and `CENTRAL_PASSWORD` in `sdk-jvm`. Create a signing key, publish its public part to an appropriate keyserver and store the armored private key as `MAVEN_GPG_PRIVATE_KEY`, passphrase as `MAVEN_GPG_PASSPHRASE`. The Maven release profile uses `central-publishing-maven-plugin` with server ID `central`, sources, Javadocs, license, developers and SCM metadata. It uses the current Portal API, not retired OSSRH staging URLs. [Central Maven setup](https://central.sonatype.org/publish/publish-portal-maven/). |
| .NET | Create/authorize a NuGet.org account and confirm package ID `OpenVerify`. Generate an API key limited to pushing this package ID/prefix, with expiry. Store as `NUGET_API_KEY` in `sdk-dotnet`. Package targets .NET 8, enables nullable checking and ships XML documentation. [NuGet publishing](https://learn.microsoft.com/en-us/nuget/nuget-org/publish-a-package). |
| Ruby | Create a RubyGems.org account. Create a pending trusted publisher for gem `openverify`, owner `openverifyproject`, repository `openverify`, workflow `sdk-release-ruby.yml`, environment `sdk-ruby`. No long-lived key is used; the pinned RubyGems credential action exchanges OIDC for a short-lived publish credential. [new-gem trusted publishing](https://guides.rubygems.org/trusted-publishing/). |
| PHP | Authorize/create a dedicated, initially empty public GitHub package repository, for example `openverifyproject/sdk-php`, **without** a generated README, license or unrelated initial commit. Set `SDK_PHP_MIRROR=openverifyproject/sdk-php` in `sdk-php`. Store a fine-grained GitHub token, restricted to **that mirror repository** with Contents read/write, as `SDK_PHP_MIRROR_TOKEN`. Register the mirror repository URL on Packagist under the authorized account and configure its GitHub webhook/VCS synchronization. The mirror has `composer.json` at its root; no package files are copied by hand. [Packagist submission](https://packagist.org/about#how-to-update-packages). |

Name observations are in [registry-check.json](registry-check.json), including
timestamp, endpoint and HTTP result. A 404 means unlisted at the observation time,
not a reservation, registry policy approval, namespace ownership or guarantee
that publication will succeed. Repeat `python tools/sdk_release.py names` before
first publication.

## PHP mirror behavior

`tools/sdk_mirror.py` computes `git subtree split --prefix=sdk/php` from the source
release tag and atomically pushes its commit to mirror `main` and standard
`vX.Y.Z`. The transformation is automatic and deterministic from Git history.
An existing identical mirror tag is a no-op. A conflicting tag, unrelated/rebased
history, unexpected nonempty repository or package-name mismatch stops the job.
It never force-pushes. Releasing an older package version may add its missing tag
without rewinding a newer mirror main branch. Packagist follows the standard
mirror tag; the monorepo continues to use `sdk/php/vX.Y.Z`.

The mirror is not created by CI. The source checkout does not retain source-repo
push credentials; the mirror credential is supplied only inside `sdk-php`.
Actual remote synchronization and Packagist availability remain untested until
the owner configures and explicitly authorizes the first release.

## Subsequent releases

1. Choose **one** language and a previously unpublished `X.Y.Z`.
2. Update that package's metadata and runtime version constant. Rust derives its
   runtime version from Cargo metadata. PHP keeps its version in `VERSION` and
   `Sdk::VERSION`; Composer derives the registry version from its mirror tag.
   Do not bump other SDKs. Update the chosen package's README/release notes.
3. Run `python tools/sdk_verify.py LANGUAGE`. `validate_version` rejects mismatched
   runtime/package versions. Build contents and the exact artifact SHA are recorded.
4. Merge reviewed code, then create/push only `sdk/LANGUAGE/vX.Y.Z` through the
   maintainer's approved release process. No tag has been created or pushed here.
5. CI reruns applicable tests on that exact tagged commit. Publish preflight
   rejects dirty checkouts, version mismatches, missing exact-commit evidence,
   altered archives, registry query failures and existing versions (Go is the
   tag-publication exception described above). Reusing an already-published
   version is an error; do not delete or move tags to retry with different bytes.
6. The protected job publishes one package, then attempts a fresh consumer install
   from its registry with propagation retries. PHP waits for Packagist sync; Go
   resolves the nested-module tag. A registry failure makes the job fail even if
   upload succeeded. Check the registry before retrying; choose a new version if
   the old one was already published.

## Local dry runs and current limits

`tools/sdk_verify.py` creates npm tarballs, verified Cargo crates, Go source ZIPs,
Maven binary/source/Javadoc JARs, NuGet packages, Ruby gems, Composer distribution
ZIPs and Python wheel/sdist artifacts. Each is installed in an external consumer
project. This does not require package ownership or publication credentials.

Build verification compares the contents of native package containers. Container
timestamps and signing metadata are not portable reproducible bytes. Signed Maven
publication rebuilds from the same tested tag; signing and Portal acceptance can
only be verified after owner setup. Ruby native dependency installation and all
registry installs may need normal build tooling/network access. The monorepo's
Linux GitHub jobs and real registry publication have not run locally; local
Windows build/test evidence and workflow lint are reported separately.
