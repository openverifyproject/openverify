# OpenVerify 0.1.0: first package publications

Source: `release/openverify-v0.1`, descended from integrated `e19c37a`, never the
older SDK worktree. Organization/repository: **openverifyproject/openverify**.
All SDK releases are independent. Full Golden/Relay certification is not a
prerequisite for these bounded DRAFT wire libraries. No push, merge, tag or
publication was performed during preparation.

## Names and actual ownership evidence

The live read-only registry queries are retained in
`docs/first-publication/NAME_CHECKS.json`. All requested registry coordinates
were unlisted (HTTP 404). That means **AVAILABLE in the public listing**, not
reserved, owned by us or guaranteed acceptable at registration. No authenticated
registry account was inspected. Ownership is **UNKNOWN** for every registry.
No queried name was confirmed TAKEN or RESERVED. The Go source organization is
user-confirmed owned; authenticated repository write access remains unverified.
The public GitHub API confirms repository owner `openverifyproject`, public
visibility, default branch `main`. `origin` is exactly
`https://github.com/openverifyproject/openverify.git`.

| Registry | Selected distribution | Independent source tag | Publisher |
|---|---|---|---|
| npm | `openverify` | `sdk/node/v0.1.0` | `sdk-release-node.yml` |
| PyPI | `openverify-wire` | `sdk/python/v0.1.0` | `sdk-release-python.yml` |
| crates.io | `openverify` | `sdk/rust/v0.1.0` | `sdk-release-rust.yml` |
| RubyGems | `openverify` | `sdk/ruby/v0.1.0` | `sdk-release-ruby.yml` |
| NuGet | `OpenVerify` | `sdk/dotnet/v0.1.0` | `sdk-release-dotnet.yml` |
| Maven Central | `io.github.openverifyproject:openverify` | `sdk/jvm/v0.1.0` | `sdk-release-jvm.yml` |
| Packagist | `openverify/openverify` | `sdk/php/v0.1.0` (mirror `v0.1.0`) | `sdk-release-php.yml` |
| Go | `github.com/openverifyproject/openverify/sdk/go` | `sdk/go/v0.1.0` | `sdk-release-go.yml` |

Bare names are supported for npm, Cargo, RubyGems and NuGet; Maven/Packagist/Go
require their qualified coordinates. First publication establishes registry
ownership only if the registry accepts it for the authenticated account.

### Python decision

The existing root distribution already declares **`openverify==0.1.0`**, installs
the `openverify` import tree and CLI, requires Python 3.13 and includes Relay.
The wire SDK is **`openverify-wire==0.1.0`**, installs `openverify_sdk`, supports
Python 3.11+, and does not include Relay or require Pydantic.

They can coexist safely under their current distinct distribution/import names.
They cannot both independently evolve as the same PyPI distribution name:
installing a later wire-only `openverify` wheel would replace the core
distribution, dropping its imports/CLI; conversely the core wheel would drop
the wire SDK unless deliberately combined. A genuine combined distribution
would require bundling both import trees, deciding runtime/dependency support,
and coupling their version/release lifecycle. Renaming the wire-only wheel is
not that integration. It would also withhold the 3.11/3.12 library or change core
support. Therefore keep `openverify-wire` independently publishable now; leave
the exact `openverify` name for the existing core. No placeholder is published.
[Distribution/import distinction](https://packaging.python.org/en/latest/discussions/distribution-package-vs-import-package/).

### API preservation

Rust keeps library target `openverify_sdk`; use
`openverify_sdk = { package = "openverify", version = "0.1.0" }` in Cargo.toml.
Ruby still uses `require 'openverify'`; .NET retains namespace/type
`OpenVerify.Sdk`; JVM retains `org.openverify.sdk`; PHP retains `OpenVerify\`.
Node's registry/import specifier is now `openverify`, with unchanged exported
functions/types. No old package was published by this preparation, and an
unpublished old npm specifier cannot be made installable without separately
publishing that old package. Go and Python imports remain unchanged.

## First action: source push and reviewed merge

These are **owner-executed commands after explicit approval**, not commands run
by preparation. They do not force-update main. The source repository is already
public. A branch push triggers tests, not package publishers.

```powershell
winget install --id GitHub.cli --exact
# Open a fresh PowerShell if needed after installation.
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
gh repo view openverifyproject/openverify --json nameWithOwner,visibility,viewerPermission
Set-Location 'C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\openverify-release-v0.1'
if ((git branch --show-current) -ne 'release/openverify-v0.1') { throw 'Wrong branch' }
if (git status --porcelain) { throw 'Uncommitted work' }
if ((git remote get-url origin) -ne 'https://github.com/openverifyproject/openverify.git') { throw 'Wrong origin' }
git push --no-follow-tags --set-upstream origin release/openverify-v0.1
if ($LASTEXITCODE -ne 0) { throw 'Push failed; do not force' }
gh pr create --repo openverifyproject/openverify --base main --head release/openverify-v0.1 --title 'Prepare OpenVerify 0.1.0 SDK publications under exact names' --body-file docs/github-release/PR_BODY.md
gh pr checks release/openverify-v0.1 --repo openverifyproject/openverify --watch
if ($LASTEXITCODE -ne 0) { throw 'Resolve failed CI before merge' }
gh pr merge release/openverify-v0.1 --repo openverifyproject/openverify --merge
if ($LASTEXITCODE -ne 0) { throw 'Merge was not accepted' }
```

If a PR already exists, use it rather than creating another. Wait for both core
CI jobs and all eight SDK jobs. Core test success is required; universal Golden
certification is not. Source gate `sdk_release.require_merged_source` also
rejects a different origin or a tagged commit absent from `origin/main`.

## Build from merged source before any first publication

The following creates a new retained worktree. Run only after the reviewed
merge, using installed language runtimes documented in `sdk/README.md`.

```powershell
git fetch origin main --no-tags
$prepared = (git rev-parse release/openverify-v0.1).Trim()
git merge-base --is-ancestor $prepared origin/main
if ($LASTEXITCODE -ne 0) { throw 'Prepared source is not merged; do not publish' }
$publishPath = 'C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\publish-openverify-v0.1'
if (Test-Path $publishPath) { throw 'Preserve existing worktree; select a new path' }
git worktree add --detach $publishPath origin/main
if ($LASTEXITCODE -ne 0) { throw 'Worktree creation failed' }
Set-Location $publishPath
uv venv --python 3.13 .venv
uv pip install --python .venv/Scripts/python.exe build pytest jsonschema pydantic
$python = (Resolve-Path .venv/Scripts/python.exe).Path
$language = 'node' # Select one independently.
& $python tools/sdk_verify.py $language
if ($LASTEXITCODE -ne 0) { throw 'Verification failed; do not publish' }
$proof = Get-Content "dist/sdk/$language/verification.json" -Raw | ConvertFrom-Json
if ($proof.dirty_worktree -or -not $proof.tests_run -or $proof.consumer -ne 'passed' -or $proof.version -ne '0.1.0' -or $proof.commit -ne (git rev-parse HEAD).Trim()) { throw 'Release evidence mismatch' }
& $python -c "import sys; sys.path.insert(0,'tools'); import sdk_release; sdk_release.require_merged_source('$($proof.commit)'); sdk_release.unpublished('$language','0.1.0')"
if ($LASTEXITCODE -ne 0) { throw 'Wrong source or version is already public; do not publish' }
```

## Fast first-time manual options

Run only the chosen package command, from the freshly verified merged worktree
above, after authenticating interactively and approving publication. No tokens
belong in Git, chat or command arguments typed into shell history.

**npm — unscoped `openverify`, no npm organization required:**

```powershell
npm.cmd login --auth-type=web
npm.cmd whoami
npm.cmd publish .\dist\sdk\node\openverify-0.1.0.tgz --access public
if ($LASTEXITCODE -ne 0) { throw 'Inspect registry result before retrying' }
& $python tools/sdk_verify.py node --registry-only
```

First manual publication can bootstrap npm's trusted publisher. Configure owner
`openverifyproject`, repo `openverify`, workflow `sdk-release-node.yml`, environment
`sdk-node` afterward. Do not republish bootstrap 0.1.0 via its tag workflow; the
next automated release must use the next reviewed version. No tag push is needed
to perform a registry bootstrap from the merged commit. Keep the verified source
commit/artifact evidence for that release. [npm instructions](https://docs.npmjs.com/creating-and-publishing-unscoped-public-packages/).

**Ruby — `openverify`, preserve `require 'openverify'`:**

```powershell
gem.cmd signin
gem.cmd push .\dist\sdk\ruby\openverify.gem
if ($LASTEXITCODE -ne 0) { throw 'Inspect RubyGems before retrying' }
& $python tools/sdk_verify.py ruby --registry-only
```

Alternatively configure a pending RubyGems trusted publisher for gem `openverify`,
owner/repo above, workflow `sdk-release-ruby.yml`, environment `sdk-ruby` and use
the automatic path below, including for 0.1.0. [RubyGems instructions](https://guides.rubygems.org/trusted-publishing/).

**Rust — `openverify`:**

```powershell
cargo login # Interactive credential entry, never paste a token as an argument.
cargo publish --manifest-path sdk/rust/Cargo.toml --locked
if ($LASTEXITCODE -ne 0) { throw 'Inspect crates.io before retrying' }
& $python tools/sdk_verify.py rust --registry-only
```

This publishes real merged source, not an empty name-reservation package. For
automatic later releases store an authorized crate publish token in environment
`sdk-rust` as `CARGO_REGISTRY_TOKEN` using `gh secret set` interactively. As with
npm bootstrap, do not trigger the same already-published version again.

## Independent automatic first releases

Use this path for Go, Python, .NET, JVM and PHP, and optionally Ruby/Rust/Node
when their publishing authentication is configured. No package waits for an
unrelated registry. In GitHub Settings → Environments create only the desired
`sdk-LANGUAGE` environment, restrict it to matching `sdk/LANGUAGE/v*` tags and
configure release approval. Set environment variable
`REGISTRY_OWNERSHIP_APPROVED=true` after that registry's account/name decision.
Keep the complete required setup for other languages independent.

| Language | Exact owner action before its tag |
|---|---|
| python | PyPI account → Publishing → add pending GitHub publisher, project `openverify-wire`, owner `openverifyproject`, repo `openverify`, workflow `sdk-release-python.yml`, environment `sdk-python`. No token. Exact core name remains intentionally unpublished. |
| go | Confirm repository write permission and successful merged-source SDK checks. No registry account/token. Pushing its tag is publication. |
| dotnet | NuGet account → API Keys → create expiring push key authorized for new package `OpenVerify`; run `gh secret set NUGET_API_KEY --repo openverifyproject/openverify --env sdk-dotnet`. |
| jvm | Central Portal → verify namespace `io.github.openverifyproject` using its GitHub ownership verification. Generate Portal token and a signing key accepted by Central; configure `CENTRAL_USERNAME`, `CENTRAL_PASSWORD`, `MAVEN_GPG_PRIVATE_KEY` (armored secret key), `MAVEN_GPG_PASSPHRASE` in `sdk-jvm` using interactive `gh secret set`. Account/namespace/signing are not inferred from GitHub ownership. See `sdk/RELEASE.md`. |
| php | Authorize an empty distribution-only mirror `openverifyproject/sdk-php` (no initial commit), register its URL as `openverify/openverify` at Packagist. Configure mirror webhook/sync. Set `SDK_PHP_MIRROR=openverifyproject/sdk-php` and `SDK_PHP_MIRROR_TOKEN` restricted to that mirror in environment `sdk-php`. Source remains this monorepo. |
| node | Configure npm trusted publisher for existing package `openverify`, exact owner/repo, `sdk-release-node.yml`, environment `sdk-node`. Bootstrap manually first if npm requires an existing package. |
| ruby | Pending trusted publisher for gem `openverify`, exact owner/repo, `sdk-release-ruby.yml`, environment `sdk-ruby`. |
| rust | Authorized crates.io publish token as `CARGO_REGISTRY_TOKEN` in `sdk-rust`. |

Go/PHP require qualified paths; GitHub ownership does not grant the Packagist
vendor, PyPI name, npm name or Central namespace. Registry rejections must be
handled per registry; never report a 404 as ownership confirmation.

After rebuilding/verifying the selected language from merged source as above:

```powershell
# Set only this registry's approval after its owner setup.
gh variable set REGISTRY_OWNERSHIP_APPROVED --body true --repo openverifyproject/openverify --env "sdk-$language"
$tag = "sdk/$language/v0.1.0"
git tag -a $tag HEAD -m "Release $language OpenVerify 0.1.0"
if ($LASTEXITCODE -ne 0) { throw 'Tag exists or creation failed; never force it' }
& $python tools/sdk_release.py preflight --language $language --tag $tag --evidence "dist/sdk/$language/verification.json"
if ($LASTEXITCODE -ne 0) { throw 'Release preflight failed; do not push tag' }
git push --no-follow-tags origin "refs/tags/$tag"
if ($LASTEXITCODE -ne 0) { throw 'Tag push failed; do not force' }
gh run list --repo openverifyproject/openverify --workflow "sdk-release-$language.yml" --limit 5
```

Approve that workflow's protected environment when requested. The workflow tests
and installs before publishing, then uses `tools/sdk_verify.py LANGUAGE
--registry-only` for a fresh published-package install and functional check.
Go additionally resolves the exact public nested-module version. PHP translates
the tag into mirror `v0.1.0`; Packagist must synchronize before registry consumer
verification can pass. If a post-publication consumer fails, inspect the registry
before retrying; an upload may already have succeeded. Never overwrite a release.

## Verification status

Exact-name package reruns and archive hashes are recorded separately under
`docs/first-publication/`; historical frozen files and pre-rename evidence remain
unchanged. This preparation does not grant registry credentials or record any
publication as successful before an authenticated upload and registry consumer
check. Core Relay's unrelated semantic gate remains disclosed, not imposed on
these scoped SDKs.
