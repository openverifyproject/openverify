# OpenVerify first GitHub handoff

**Source handoff: READY. Package publication: BLOCKED pending the owner steps below. Full Golden certification remains unproved.**

This preparation makes one complete source monorepo available for a normal branch push and pull request. It does not authorize package publication or claim that the existing semantic release gate passed. No push, repository creation, remote-setting change, main merge, release tag, package publication or existing worktree deletion was performed.

## Branch, history and repository

- Worktree: `C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\openverify-release-v0.1`.
- Prepared branch: `release/openverify-v0.1`. Upload its committed HEAD, including this handoff and its evidence.
- Exact code/history integration: merge `e8c5cd9215dc056dd227cf3fcdee9e2a4128c1fb`, with both complete parent histories preserved.
- Golden parent: `30a37f9e9200384005019a0f8280dffa3e00732d` (`fix/golden-v4-verification`).
- SDK parent: `bd251eb070f8d8fa7d35696d631fd3cbfc4f9191` (`feat/language-sdks`).
- Production/Golden verification commit: `479e59ee580f5578c14846a5bd8c8c1dfe15536b`. Later Node dependency/security changes do not change the Python implementation, normative specifications, schemas or Golden assertions. Per-SDK tested commits and final evidence hashes are in [VERIFICATION.json](docs/github-release/VERIFICATION.json).
- Existing origin: `https://github.com/openverifyproject/openverify.git`. Unauthenticated GitHub metadata confirmed that this repository already exists, is public, is not archived and has default branch `main`.
- Both local `origin/main` and the live remote advertised `4bcf13a53ec2743d2f49e68a1a235fbb0a7c4257` during preflight. No remote ref was moved.

The final handoff commit is a documentation/evidence descendant of the tested code commits. Resolve its exact ID with `git rev-parse release/openverify-v0.1`; a document cannot contain its own Git commit hash. The final preparation response also gives that ID. Original branches, worktrees and uncommitted main-checkout attachments remain intact.

## Complete contents

| Area | Repository paths |
|---|---|
| VCP prose, schemas, profiles and conformance | `spec/`, `schemas/`, `profiles/`, `conformance/` |
| Provider Contract and shared fixtures | `provider-contract/`, `conformance/sdk/` |
| Python Relay, standard providers and public entrypoints | `src/openverify/` |
| Eight independent wire SDKs | `sdk/node`, `sdk/python`, `sdk/rust`, `sdk/go`, `sdk/jvm`, `sdk/dotnet`, `sdk/ruby`, `sdk/php` |
| Golden, canonical and release-review evidence | `tests/golden_v4/`, `tests/golden_v4_reconciliation/`, `conformance/golden-v4/` |
| Documentation, examples and maintenance/release tooling | `docs/`, `examples/`, `tools/`, `sdk/README.md`, `sdk/RELEASE.md` |
| Project and package metadata | `README.md`, `LICENSE`, `.gitignore`, `pyproject.toml`, per-SDK manifests/lockfiles |
| GitHub automation | `.github/workflows/project-ci.yml`, `sdk-ci.yml`, `sdk-verify.yml`, eight `sdk-release-LANGUAGE.yml` files |

**One GitHub source repository is sufficient.** Go uses a nested module in that repository. PHP's current Packagist strategy additionally needs an automated distribution-only mirror with root `composer.json`; it is not another independently maintained source tree. No mirror was created here. If you require literally one GitHub repository including distribution mirrors, PHP Packagist publication is unavailable under this layout; source and the other packages still work. [Packagist's repository layout](https://packagist.org/).

Worktrees, environments, dependency installations, build outputs and temporary/cache directories are ignored and untracked. Intentional schema bundles, portable fixtures and Golden audit artifacts remain tracked. Three preserved Golden blobs produce GitHub's >50 MiB warning, but none exceeds its 100 MiB hard limit. Use Git, not browser/ZIP upload. See [SECURITY_REVIEW.md](docs/github-release/SECURITY_REVIEW.md) for exact sizes, secret-scan findings and privacy metadata retained in history.

## Actual verification and blockers

The machine-readable [VERIFICATION.json](docs/github-release/VERIFICATION.json), [SDK_VERIFICATION.json](docs/github-release/SDK_VERIFICATION.json), JUnit XML and compressed logs record exact commands, counts, timings, imports and artifact hashes. [VERIFICATION.md](docs/github-release/VERIFICATION.md) explains their scope.

| Verification | Result |
|---|---|
| Golden V4 | 15,236 passed |
| Revision regressions, including mutation checks | 388 passed |
| Existing production/unit/integration/property/conformance/Relay tests | 1,037 passed; one Windows skip for POSIX path semantics |
| Release/SDK maintenance guards | 37 passed |
| Python wire and original Python compatibility checks | 197 passed, no expected failures |
| Every SDK's shared corpus | 52 VCP + 45 Provider cases passed in each of eight languages |
| Eight SDK packages | Native tests, two main-package content comparisons, and disposable external consumers passed |
| Root Python package | Wheel/source build and isolated installed API/CLI/resource consumer passed |
| Workflow validation | All 11 workflows pass actionlint 1.7.7; shellcheck/pyflakes were not enabled; remote Actions execution is pending |

The former original-Python standalone `vcp_version` compatibility error is fixed by the integrated production history. Its stale `xfail` escape was removed, so accepting the invalid marker would now fail the audit. The unused-default distinction is explicitly scoped: these wire SDKs do not implement semantic Definition/input-resolution validation; `SDK_UNSUPPORTED` is required for semantic Definition parsing. Structural schema acceptance is not semantic acceptance. Schema `default` annotation noninsertion is covered by the shared corpus. CUSTOM-empty membership and snapshot availability remain implemented and tested in the Python Relay profile.

An npm audit found Ajv 8.17.1's moderate `$data` advisory. Node now pins 8.20.0; its native/package/consumer checks were rerun. Final npm audit reports zero advisories. This is not an all-ecosystem dependency vulnerability certificate. No credentials/private keys were confirmed by the tracked/history scans; all six initial candidates were reviewed false positives. Historical Windows paths and Git author identity remain public metadata if you push.

**Publication blockers are finite and explicit:**

1. The root `openverify` Python Relay distribution is **UNRELEASABLE under the existing v0.1 semantic release gate**: 615 records have dispositions, but only one isolated projection is verified, 396 are partial and 218 lack reviewed assertion links. See [the existing verdict](conformance/golden-v4/release-review-v0.1/RELEASE_VERDICT.md) and [exact blocker IDs](conformance/golden-v4/release-review-v0.1/RELEASE_BLOCKERS.md). No automatic root-package publisher is provided. Source installation and bounded test passes do not discharge this gate.
2. All eight wire SDKs passed their stated local scope, but publication is **not enabled or approved**. Registry ownership, credentials/trusted publishers, environment protection and the first remote CI run are pending. Those are owner/account decisions, not missing monorepo architecture. Registry 404 observations reserve no names.
3. PHP publication additionally needs its authorized mirror and Packagist registration. Go public module resolution cannot be measured before its owner-approved tag exists.
4. Windows evidence does not establish every supported OS/runtime version. .NET tests targeted net8.0 using the available .NET 10 runtime with roll-forward; JVM code targeted Java 17 on the available JDK. CI explicitly selects .NET 8/Java 17 and Ubuntu. Archive-content comparisons ignore native container timestamps and do not certify cross-host byte reproducibility.

No failing test is hidden or disabled for these limits. The SDKs remain bounded DRAFT wire libraries, with graph/policy/provenance execution and Provider sessions/transport outside their advertised semantic implementation. They are not eight Relay ports or full cross-language conformance proofs.

## Owner commands: connect and upload the source branch

Run these only after reviewing this handoff. The repository is already public: pushing the branch exposes its reachable history immediately, before any PR merge. No registry credentials are needed for this source upload.

```powershell
# Install the CLI if it is absent, then open a fresh PowerShell if PATH changed.
winget install --id GitHub.cli --exact
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
gh auth status
gh repo view openverifyproject/openverify --json nameWithOwner,url,visibility,viewerPermission,defaultBranchRef

Set-Location 'C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\openverify-release-v0.1'
if ((git branch --show-current) -ne 'release/openverify-v0.1') { throw 'Wrong branch' }
if (git status --porcelain) { throw 'Review uncommitted files before upload' }
if ((git remote get-url origin) -ne 'https://github.com/openverifyproject/openverify.git') { throw 'Unexpected origin; do not overwrite it' }
git rev-parse HEAD
git merge-base --is-ancestor 30a37f9e9200384005019a0f8280dffa3e00732d HEAD
if ($LASTEXITCODE -ne 0) { throw 'Golden history missing' }
git merge-base --is-ancestor bd251eb070f8d8fa7d35696d631fd3cbfc4f9191 HEAD
if ($LASTEXITCODE -ne 0) { throw 'SDK history missing' }
git ls-remote origin refs/heads/main

# Upload only this branch. Do not use --all, --mirror, --force or --tags.
git push --no-follow-tags --set-upstream origin release/openverify-v0.1
if ($LASTEXITCODE -ne 0) { throw 'Push failed; inspect the reason without forcing' }
gh pr create --repo openverifyproject/openverify --base main --head release/openverify-v0.1 --title 'Prepare complete OpenVerify v0.1 source monorepo' --body-file docs/github-release/PR_BODY.md
gh pr checks --repo openverifyproject/openverify release/openverify-v0.1 --watch
```

Use an account with WRITE/MAINTAIN/ADMIN permission and any required organization SSO authorization. `gh auth status` identifies its credential storage; do not use insecure storage or put tokens in the repository. A rejected push is not a reason to reset or force the existing remote. [CLI authentication](https://cli.github.com/manual/gh_auth_login), [PR creation](https://cli.github.com/manual/gh_pr_create).

The source push triggers verification only. Every committed SDK publishing workflow has a tag-only `sdk/LANGUAGE/v*` trigger; branch pushes and PR events cannot start those publishers. No release tag exists because of this preparation. Review any pre-existing external GitHub Apps/webhooks separately if your account has configured automation outside this repository.

## Exact initial GitHub settings

In `openverifyproject/openverify` Settings, before approving publication:

1. **General:** keep `main` as default; enable merge commits. Use a normal merge commit for this PR to retain both histories. Disable automatic head-branch deletion if you want to retain the prepared branch. Do not require linear history for this merge-based repository.
2. **Actions → General:** enable Actions for this repository; permit the pinned actions from `actions`, `pypa`, `dtolnay`, `ruby`, `rubygems` and `shivammathur` present in YAML. Set default workflow permissions to read repository contents/packages; leave “Allow GitHub Actions to create and approve pull requests” disabled. Require approval for outside-contributor workflows. Use GitHub-hosted runners.
3. **Rules → branch ruleset for `main`:** require a PR, conversation resolution and successful status checks; block deletion and force updates. Require an independent approval when a reviewer is available. After the first PR produces contexts, select both `Python and Golden (ubuntu-latest)` / `(windows-latest)` checks and all eight `SDK (LANGUAGE) / verify` checks shown by GitHub. Do not invent required checks that have never run. Wait for all ten before merging. [Ruleset controls](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).
4. **Rules → tag ruleset:** protect `sdk/*/v*`; restrict creation to release maintainers and block updates/deletion. Tags must reference reviewed merged code. For Go, this creation restriction is the publication approval boundary because the tag itself is the release.
5. **Environments:** create `sdk-node`, `sdk-python`, `sdk-rust`, `sdk-go`, `sdk-jvm`, `sdk-dotnet`, `sdk-ruby`, `sdk-php`. In each select deployment branches/tags → selected tags → only `sdk/LANGUAGE/v*`. Add an independent required reviewer and prevent self-review. Keep registry secrets scoped to their own environment. Configure `REGISTRY_OWNERSHIP_APPROVED=true` only after the corresponding ownership and first-publication decision. Environment protections require owner configuration; YAML does not install them. [Environment setup](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).
6. **Security:** enable dependency graph/alerts and secret scanning/push protection where available. Check existing webhooks/apps for unwanted branch-publication automation. Review the retained machine-path/author metadata before the first source push.

No account setting above was changed by this task. Remote CI and an authenticated publication have not been run locally.

## Registry setup, one package at a time

All SDK package versions currently start at independent `0.1.0`. Protocol version `draft` / Provider `0.1` is separate from package version. The initial registry observations are in [REGISTRY_OBSERVATIONS.json](docs/github-release/REGISTRY_OBSERVATIONS.json); all proposed names returned 404, including the separately checked root Python name. That proves no ownership or reservation.

| SDK | Package | Owner setup and environment credentials |
|---|---|---|
| Node | `@openverify/sdk` | Authorize npm scope `openverify`. Configure trusted publisher for owner `openverifyproject`, repo `openverify`, workflow `sdk-release-node.yml`, environment `sdk-node`. Node 24/current npm in the workflow meets OIDC prerequisites. If npm requires an owner bootstrap, explicitly approve the first verified tarball through npm's supported initial-publication flow; do not republish that version through CI. No long-lived npm token fallback is configured. [npm setup](https://docs.npmjs.com/trusted-publishers/) |
| Python wire | `openverify-wire` | Create a PyPI pending trusted publisher: owner/repo above, workflow `sdk-release-python.yml`, environment `sdk-python`. No API token is required. Import name is `openverify_sdk`, distinct from the withheld root `openverify` distribution. [PyPI setup](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) |
| Rust | `openverify-sdk` | Confirm crates.io ownership; store a short-lived, crate-scoped publish token as `CARGO_REGISTRY_TOKEN` in `sdk-rust`. [Cargo publishing](https://doc.rust-lang.org/cargo/commands/cargo-publish.html) |
| Go | `github.com/openverifyproject/openverify/sdk/go` | No registry token or mirror. Reviewed source must be public; the exact nested-module tag is `sdk/go/v0.1.0`. Pushing it makes that version public, before the verification job completes. [Go tag rules](https://go.dev/ref/mod#vcs-version) |
| JVM | `io.github.openverifyproject:openverify-sdk` | Verify the `io.github.openverifyproject` namespace in Central Portal. In `sdk-jvm`, set Portal user-token `CENTRAL_USERNAME`, `CENTRAL_PASSWORD`, armored `MAVEN_GPG_PRIVATE_KEY` and `MAVEN_GPG_PASSPHRASE`. The release Maven profile signs and uses Central Portal, not retired OSSRH. [Maven setup](https://central.sonatype.org/publish/publish-portal-maven/) |
| .NET | `OpenVerify.Sdk` | Confirm NuGet ownership; put an expiring package-scoped push key in `sdk-dotnet` as `NUGET_API_KEY`. [NuGet setup](https://learn.microsoft.com/en-us/nuget/nuget-org/publish-a-package) |
| Ruby | `openverify-sdk` | Create a pending RubyGems trusted publisher for owner/repo above, `sdk-release-ruby.yml`, environment `sdk-ruby`. No long-lived gem key. [RubyGems setup](https://guides.rubygems.org/trusted-publishing/) |
| PHP | `openverify/sdk` | Authorize an empty distribution mirror, e.g. `openverifyproject/sdk-php`, without an initial README/license commit. In `sdk-php`, set variable `SDK_PHP_MIRROR=openverifyproject/sdk-php` and secret `SDK_PHP_MIRROR_TOKEN`, a fine-grained token for **that mirror only**, Contents read/write. Register the mirror on Packagist and configure its GitHub synchronization/webhook. Source tags are `sdk/php/vX.Y.Z`; the tool creates mirror `vX.Y.Z` tags atomically without force. [Packagist setup](https://packagist.org/about) |

The PHP mirror tool derives its tree with `git subtree split --prefix=sdk/php`, rejects conflicting tags and unrelated/nonempty unexpected histories, and never force-pushes. Local guard tests pass; live mirror synchronization is intentionally untested without owner setup. The token is supplied only inside the protected PHP job. See [sdk/RELEASE.md](sdk/RELEASE.md) for detailed registry and mirror behavior.

Secrets can be entered interactively, without placing their values in command history or files in this repository:

```powershell
# Examples AFTER the environments and ownership are approved; these prompt for values.
gh secret set CARGO_REGISTRY_TOKEN --repo openverifyproject/openverify --env sdk-rust
gh secret set NUGET_API_KEY --repo openverifyproject/openverify --env sdk-dotnet
gh secret set CENTRAL_USERNAME --repo openverifyproject/openverify --env sdk-jvm
gh secret set CENTRAL_PASSWORD --repo openverifyproject/openverify --env sdk-jvm
gh secret set MAVEN_GPG_PRIVATE_KEY --repo openverifyproject/openverify --env sdk-jvm
gh secret set MAVEN_GPG_PASSPHRASE --repo openverifyproject/openverify --env sdk-jvm
gh secret set SDK_PHP_MIRROR_TOKEN --repo openverifyproject/openverify --env sdk-php
gh variable set SDK_PHP_MIRROR --body 'openverifyproject/sdk-php' --repo openverifyproject/openverify --env sdk-php

# Set ONLY the chosen environment after ownership and publication approval.
gh variable set REGISTRY_OWNERSHIP_APPROVED --body true --repo openverifyproject/openverify --env sdk-node
```

## Future independent releases, after explicit approval

Never run this section as part of the first source push. A tag can publish an artifact; Go publication happens at tag push itself. Do not bulk-create tags.

| Language | Metadata/runtime files to update for that language only |
|---|---|
| node | `sdk/node/package.json`, lockfile and `src/index.ts` SDK_VERSION |
| python | `sdk/python/pyproject.toml`, `src/openverify_sdk/__init__.py` |
| rust | `sdk/rust/Cargo.toml` and lockfile; runtime version derives from Cargo |
| go | `sdk/go/openverify.go` SDKVersion; module path remains unchanged for v0/v1 |
| jvm | `sdk/jvm/pom.xml`, `Sdk.java` VERSION |
| dotnet | SDK `.csproj` Version and `Sdk.cs` Version |
| ruby | gemspec, runtime SDK_VERSION and the package's lockfile |
| php | `sdk/php/VERSION` and `src/Sdk.php` VERSION; Composer registry version comes from its mirror tag |

Update that package's own version assertions/docs as needed. Do not bump another SDK. Verify, commit, push the version-change branch and merge its reviewed PR normally. The following example assumes that chosen version is already reviewed on `origin/main`:

```powershell
$sdkLanguage = 'node' # Choose exactly one of node/python/rust/go/jvm/dotnet/ruby/php.
$sdkVersion = '0.1.0' # First approved unpublished version, or the next version you reviewed.
$sdkTag = "sdk/$sdkLanguage/v$sdkVersion"

# Only after the reviewed version change has merged and publication is approved:
git fetch origin main --no-tags
$approvedCommit = (git rev-parse origin/main).Trim()
$commonGitDirectory = (git rev-parse --path-format=absolute --git-common-dir).Trim()
$sourceDirectory = Split-Path -Parent $commonGitDirectory
$checkDirectory = Join-Path $sourceDirectory ".worktrees/sdk-release-$sdkLanguage-$sdkVersion"
if (Test-Path $checkDirectory) { throw 'Use a new check worktree path; preserve existing work' }
git worktree add --detach $checkDirectory $approvedCommit
if ($LASTEXITCODE -ne 0) { throw 'Could not create release-check worktree' }
Push-Location $checkDirectory
try {
    uv venv --python 3.13 .venv
    if ($LASTEXITCODE -ne 0) { throw 'Maintenance environment creation failed' }
    uv pip install --python .venv/Scripts/python.exe build pytest jsonschema pydantic
    if ($LASTEXITCODE -ne 0) { throw 'Maintenance dependencies failed' }
    $maintPython = (Resolve-Path .venv/Scripts/python.exe).Path
    & $maintPython tools/sdk_verify.py $sdkLanguage
    if ($LASTEXITCODE -ne 0) { throw 'Verification failed; do not tag or publish' }
    $proofPath = "dist/sdk/$sdkLanguage/verification.json"
    $proof = Get-Content $proofPath -Raw | ConvertFrom-Json
    if ($proof.version -ne $sdkVersion -or $proof.commit -ne $approvedCommit -or $proof.dirty_worktree) { throw 'Version/source proof mismatch' }
    git tag -a $sdkTag $approvedCommit -m "Release $sdkLanguage SDK $sdkVersion"
    if ($LASTEXITCODE -ne 0) { throw 'Tag already exists or creation failed; never force' }
    & $maintPython tools/sdk_release.py preflight --language $sdkLanguage --tag $sdkTag --evidence $proofPath
    if ($LASTEXITCODE -ne 0) { throw 'Publication preflight failed; do not push the tag' }
    git show --no-patch $sdkTag
    git push --no-follow-tags origin "refs/tags/$sdkTag"
    if ($LASTEXITCODE -ne 0) { throw 'Tag push rejected; inspect without forcing' }
} finally {
    Pop-Location
}
```

These commands retain the check worktree even on failure. They never reset or
delete an existing checkout. A failed preflight can leave an unpushed local tag;
inspect its cause rather than moving/deleting it or overwriting a registry version.

If npm requires the first package to exist before trusted-publisher configuration,
an authorized owner can instead bootstrap the **verified** first tarball with
`npm.cmd login --auth-type=web --scope=@openverify`, followed by
`npm.cmd publish .\dist\sdk\node\openverify-sdk-0.1.0.tgz --access public`.
This is publication and requires separate explicit approval. Then configure npm's
trusted publisher and use the next reviewed Node version for the first CI publish;
do not retry the bootstrap version through its publishing workflow.

The matching workflow reruns tests/builds/clean consumer on the exact tag, checks package/runtime versions and artifact checksums, rejects already-published versions and asks for protected-environment approval. It publishes only that SDK and then checks a fresh registry consumer. A post-upload availability failure can occur after publication succeeded: inspect the registry before retrying; never move a tag or overwrite a version. No tag or publish command above was executed during preparation.

The root Python Relay package has no analogous authorized publication step while its semantic release gate remains blocked. No requirement has been silently removed to make the source upload ready.
