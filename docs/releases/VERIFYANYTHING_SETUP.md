# VerifyAnything SDK publication setup

VerifyAnything is the portable VCP + Provider Contract SDK product. OpenVerify is
its separate Python Relay harness. Source stays in **openverifyproject/openverify**.
All package versions start at 0.1.0 and evolve independently. Protocol status is
DRAFT. This change does not create another engine or change normative contracts.

## Actual support and preserved APIs

All eight packages retain the existing native implementations, offline schema
bundles and common 52 VCP + 45 Provider fixtures. They provide JSON-backed wire
models, serialization, structural validation, the documented semantic subset,
version constants and protocol/local diagnostics. No native SDK implements Relay.
No provider server, invocation transport, lifecycle state machine or complete
semantic graph/dataflow/provenance validator is advertised. See [actual support](../../sdk/README.md).

| Language | Distribution | Native API/import |
|---|---|---|
| Node | `verifyanything` | `import {parse, serialize} from 'verifyanything'` |
| Rust | `verifyanything` | `verifyanything::parse`, `verifyanything::serialize` |
| Ruby | `verifyanything` | `require 'verifyanything'`; `VerifyAnything.parse`; existing `OpenVerify` alias retained |
| Go | `github.com/openverifyproject/openverify/sdk/go` | existing package `openverify`; callers may alias the import |
| Python | `verifyanything` | `from verifyanything import parse, serialize`; Python 3.11+ |
| .NET | `VerifyAnything` | existing `OpenVerify.Sdk` API/assembly; .NET 8+ |
| JVM | `io.github.openverifyproject:verifyanything` | existing `org.openverify.sdk.Sdk`; Java 17+ |
| PHP | `openverify/verifyanything` | existing `OpenVerify\Sdk` PSR-4 API; PHP 8.2+ |

Java/.NET/PHP namespaces intentionally remain compatible; registry identity does
not require a native namespace rename. Python supplies only `verifyanything/`,
never `openverify/`, no CLI, no Relay and no dependency on the core distribution.
The harness does not depend on this SDK. Shared schemas are bundled exact source
copies, not a new normative definition or another independent semantic engine.

## Names, versions and ownership

Read-only endpoint results and timestamps are in [REGISTRY_STATUS.json](REGISTRY_STATUS.json).
The npm, Cargo, RubyGems, PyPI, NuGet, Maven and Packagist coordinates were unlisted;
Go's version list was empty. No requested version was observed published. A 404
is not a reservation, successful name-registration check or ownership proof.
No registry-specific account/namespace ownership has been authenticated here.
GitHub admin access to the public repository was independently confirmed. It
confers no npm, Maven, Packagist or other registry rights.

The previous npm `openverify` rejection due to similarity to `open-verify` is
user-reported. No publish attempt for `verifyanything` has been made; npm may
still reject it. If rejected, retain the error and stop only npm; do not silently
rename or block the other SDKs.

## Source review and first GitHub action

New worktree: `C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\verifyanything-packages`.
Branch: `feat/verifyanything-packages`, based on merged/green main `4706c3f`.
Existing branches, worktrees, frozen artifacts, fixtures and history are retained.
No push, PR, tag, registry publication or account modification was performed.

Run only after authorizing the GitHub push:

```powershell
Set-Location 'C:\Users\siddh\OneDrive\Desktop\openverify\.worktrees\verifyanything-packages'
git push --no-follow-tags -u origin feat/verifyanything-packages
gh pr create -R openverifyproject/openverify --base main --head feat/verifyanything-packages --title 'Separate VerifyAnything SDKs from OpenVerify harness' --body 'Rename portable SDK packages; preserve Relay APIs and protocol contracts; validate native packages and Python coexistence; add independent release setup.'
gh pr checks -R openverifyproject/openverify --watch
```

After review and every required check is green, separately authorize the merge:

```powershell
gh pr merge -R openverifyproject/openverify --merge
```

Do not publish this unmerged branch. Before any manual publication, from this
worktree verify clean state and that its exact source is merged:

```powershell
git fetch origin
if (git status --porcelain) { throw 'Publication needs a clean tree' }
git merge-base --is-ancestor HEAD origin/main
if ($LASTEXITCODE -ne 0) { throw 'Publication source is not merged into origin/main' }
uv sync --frozen
# Install the native toolchain for the selected language, then:
uv run --with build python tools/sdk_verify.py node
```

SDK CI runs native tests, the common corpus, two package builds/content comparison
and a clean native consumer for each language. Core CI additionally runs Python/
Golden/revision checks and all four Python installation scenarios on Ubuntu and
Windows. New GitHub runs cannot be validated until this branch is pushed; the
base's two workflows are already green. [LOCAL_VERIFICATION.json](LOCAL_VERIFICATION.json)
records local results and their source state; these are scoped checks, not universal
Golden certification. Release CI regenerates clean, exact-tag evidence.

## Independent protected releases

In GitHub repository Settings -> Environments create `sdk-node`, `sdk-rust`,
`sdk-ruby`, `sdk-go`, `sdk-python`, `sdk-dotnet`, `sdk-jvm`, `sdk-php` and the
separate `core-python`. Require reviewer approval and restrict deployment tags to
the corresponding product. Restrict release tag creation using repository rulesets.
Keep Actions default permissions read-only. Only publisher jobs request OIDC;
PHP's credential is confined to its dedicated distribution mirror.

In each environment set `REGISTRY_OWNERSHIP_APPROVED=true` only after the operator
has reviewed the intended registry account, namespace and initial registration
attempt. This variable is an operator gate, not evidence that a name is owned.
Never paste tokens in chat, source files, command arguments recorded in this repo,
or committed configuration. Enter secrets using GitHub's secret UI or secure tools.

| Priority | Environment / workflow | First-publication setup |
|---|---|---|
| A npm | `sdk-node` / `sdk-release-node.yml` | Reuse npm account; sign in/2FA. For first tagged release use a short-lived, minimum-scope granular `NPM_TOKEN` secret permitted to create/publish `verifyanything`. After successful creation, configure npm trusted publisher owner `openverifyproject`, repository `openverify`, workflow `sdk-release-node.yml`, environment `sdk-node`; remove bootstrap token. |
| B Cargo | `sdk-rust` / `sdk-release-rust.yml` | First publish needs account token: set environment variable `REGISTRY_AUTH_MODE=token` and restricted `CARGO_REGISTRY_TOKEN` secret. After first creation, configure crate trusted publisher with this repo/workflow/environment; remove token and set auth mode to `oidc`. Workflow defaults to OIDC. |
| C Ruby | `sdk-ruby` / `sdk-release-ruby.yml` | Sign in -> profile -> pending trusted publishers -> Create; gem `verifyanything`, owner `openverifyproject`, repository `openverify`, workflow `sdk-release-ruby.yml`, environment `sdk-ruby`. No permanent publishing token needed. |
| D Go | `sdk-go` / `sdk-release-go.yml` | Repository/module path is confirmed. No registry account; publication is pushing `sdk/go/v0.1.0` after merge. Environment approval cannot prevent an already pushed public tag becoming resolvable: approve before pushing it. |
| E PyPI | `sdk-python` / `sdk-release-python.yml` | Existing PyPI account -> Publishing -> Add pending GitHub publisher; project `verifyanything`, owner `openverifyproject`, repository `openverify`, filename `sdk-release-python.yml`, environment `sdk-python`. |
| F NuGet | `sdk-dotnet` / `sdk-release-dotnet.yml` | Account -> Trusted Publishing -> new policy; package glob exactly `VerifyAnything`, scope permits first package/new versions, owner `openverifyproject`, repo `openverify`, filename `sdk-release-dotnet.yml`, environment `sdk-dotnet`. Set environment variable `NUGET_USER` to the actual NuGet profile username, not email. Official NuGet/login obtains short-lived keys. |
| G Central | `sdk-jvm` / `sdk-release-jvm.yml` | Sign into Central -> username -> View Namespaces -> confirm VERIFIED `io.github.openverifyproject`, or Add Namespace and follow verification. GitHub organization namespaces are not auto-provisioned from personal login. Portal may require a temporary verification-key repo or support review; none was created. Configure `CENTRAL_USERNAME`, `CENTRAL_PASSWORD` (Portal-generated token pair), `MAVEN_GPG_PRIVATE_KEY`, `MAVEN_GPG_PASSPHRASE` as environment secrets. Keep local Maven credentials outside Git. |
| H Packagist | `sdk-php` / `sdk-release-php.yml` | No mirror exists in the organization. Authorize one distribution-only PHP subtree mirror (suggested `openverifyproject/verifyanything-php`), not eight source repos. Set `SDK_PHP_MIRROR` to its actual owner/name and `SDK_PHP_MIRROR_TOKEN` to a fine-grained token restricted to that mirror's contents. Submit that public mirror URL on Packagist, confirm permission to vendor `openverify`, and enable its GitHub update hook. No mirror/account was created here. |

An npm first manual publish is also supported below, but choose one bootstrap
route per version. After a manual first upload, do not push its tag into an
uploading workflow: preflight deliberately rejects an already published version.
Start automated tagged releases at the next package version. This same caution
applies to manual Cargo, Ruby, PyPI, NuGet and Maven publication.

## Exact manual first-publication commands (ONLY after merge and approval)

Run the source gate above and `uv run --with build python tools/sdk_verify.py LANGUAGE`
for the selected language immediately before its command. All artifacts are
functional packages, not name-reservation placeholders. Authentication remains
interactive or in approved local credential stores. Do not run all rows as a batch.

| Registry | First publication | Post-publication installation check |
|---|---|---|
| npm | `npm login` then `npm publish .\dist\sdk\node\verifyanything-0.1.0.tgz --access public` | `uv run --with build python tools/sdk_verify.py node --registry-only` |
| crates.io | `cargo login` then `cargo publish --manifest-path sdk/rust/Cargo.toml --locked` | `uv run --with build python tools/sdk_verify.py rust --registry-only` |
| RubyGems | `gem signin` then `gem push .\dist\sdk\ruby\verifyanything.gem` | `uv run --with build python tools/sdk_verify.py ruby --registry-only` |
| Go | Push ONLY the approved merged `sdk/go/v0.1.0` tag (commands below) | `uv run --with build python tools/sdk_verify.py go --registry-only` |
| PyPI SDK | Prefer pending OIDC + SDK tag; manual alternative: `uv run --with twine python -m twine upload .\dist\sdk\python\verifyanything-0.1.0*` | `uv run --with build python tools/sdk_verify.py python --registry-only` |
| NuGet | Prefer OIDC + SDK tag; manual alternative: `dotnet nuget push .\dist\sdk\dotnet\VerifyAnything.0.1.0.nupkg --source https://api.nuget.org/v3/index.json` using an approved local API-key configuration | `uv run --with build python tools/sdk_verify.py dotnet --registry-only` |
| Maven | `mvn -B -f sdk/jvm/pom.xml -Prelease deploy` with external `central` server credentials and configured GPG | `uv run --with build python tools/sdk_verify.py jvm --registry-only` |
| Packagist | Approve/push PHP SDK tag; protected workflow translates subtree tag to mirror `v0.1.0`; submit/update mirror package on Packagist | `uv run --with build python tools/sdk_verify.py php --registry-only` |

The NuGet manual command requires an API key in NuGet's external configuration;
it does not invent credentials. OIDC avoids that requirement. Registry checks
install exact versions in fresh consumers and execute native parse/serialize smoke
programs. The ordinary source-push and PR workflows never publish packages.

## Exact independent tag commands (after approval; one product at a time)

For the recommended workflow bootstrap, configure that registry first, then use
the exact reviewed merged commit. Do not create these tags until authorized:

```powershell
git fetch origin
$releaseCommit = git rev-parse origin/main
$tag = 'sdk/node/v0.1.0' # Change ONLY this product; see table below.
git tag -a $tag $releaseCommit -m "$tag"
git push origin "refs/tags/$tag"
```

| Product | Initial workflow tag |
|---|---|
| Node | `sdk/node/v0.1.0` |
| Rust | `sdk/rust/v0.1.0` |
| Ruby | `sdk/ruby/v0.1.0` |
| Go | `sdk/go/v0.1.0` |
| Python SDK | `sdk/python/v0.1.0` |
| .NET | `sdk/dotnet/v0.1.0` |
| JVM | `sdk/jvm/v0.1.0` |
| PHP | `sdk/php/v0.1.0` (mirror receives `v0.1.0`) |

Subsequent releases: update only that SDK's package/runtime version and applicable
lockfile, review/merge, obtain clean exact-commit test evidence, then tag that
language `sdk/LANGUAGE/vX.Y.Z`. No SDK tag publishes the harness or another SDK.
Go must retain the nested `sdk/go/` tag prefix; never substitute root `vX.Y.Z`.
PHP mirror updates are atomic, nonforced and reject conflicting tags/unrelated
history. The monorepo remains the sole development source.

## Registry references reviewed for this setup

- [npm trusted publishers](https://docs.npmjs.com/trusted-publishers/)
- [Cargo publishing](https://doc.rust-lang.org/cargo/reference/publishing.html) and [crates.io trusted publishing rollout](https://blog.rust-lang.org/2025/07/11/crates-io-development-update-2025-07/)
- [RubyGems pending publishers](https://guides.rubygems.org/trusted-publishing/)
- [PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [NuGet trusted publishing](https://learn.microsoft.com/en-us/nuget/nuget-org/trusted-publishing)
- [Central namespace verification](https://central.sonatype.org/register/namespace/)
- [Packagist submission](https://packagist.org/about)

Registry acceptance, actual ownership, OIDC exchanges and public installs are
unverified until the authorized first publication. These account-specific blockers
do not block preparation or publication of other registries. No Node harness is
provided or published; `@openverifyproject/openverify` remains a future option.
