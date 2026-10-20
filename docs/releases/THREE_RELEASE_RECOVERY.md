# Recovery of the three 2026-10-20 release failures

Base: `a023fd6d37d13bfc3f58863e26f6336a045e76c7` (`origin/main`).
Branch: `fix/three-release-failures`; worktree: `.worktrees/release-recovery`.
All three latest failed runs are pushes of the original `sdk/*/v0.1.0` tags at
that exact commit. No tags, published versions or other worktrees were changed.

## Independent failure findings

### Rust: workflow preparation defect; nothing published

[Run 39348741470](https://github.com/openverifyproject/openverify/actions/runs/39348741470)
fails during job preparation, before checkout or any `cargo publish`:

```text
Unable to resolve action rust-lang/crates-io-auth-action@ebc737b6fc418a6ca0073cf116ec8dc156d8b81e,
unable to find version ebc737b6fc418a6ca0073cf116ec8dc156d8b81e
```

GitHub resolves this action even though its step's condition is false:
`sdk-rust` has `REGISTRY_AUTH_MODE=token`. The environment already contains a
`CARGO_REGISTRY_TOKEN` secret (updated 2026-10-20T00:17:52Z); its value was never
read. This failure provides no evidence of a token or package-name rejection.

Corrected the generator and generated workflow to upstream release `v1.0.5`,
commit `c6f97d42243bad5fab37ca0427f495c86d5b1a18`, independently resolved through
GitHub's tags API and inspected its action descriptor. The old `v1` ref and
recorded commit could not be resolved. Source implementation remains unchanged.

Both crate metadata and lockfile advance to **0.1.1**. Re-running the old run
would use its old broken workflow; preserve `sdk/rust/v0.1.0` and publish from a
new `sdk/rust/v0.1.1` tag only after the fix is reviewed and merged.

The crates.io package API returns 404 for `verifyanything`: no public 0.1.0 or
0.1.1 was found. This establishes unlisted status, not guaranteed first-publish
acceptance or token permissions. The failed job never attempted an upload.
No new external account action is currently established.

### NuGet: upload succeeded; post-upload propagation check failed

[Run 39348757171](https://github.com/openverifyproject/openverify/actions/runs/39348757171)
successfully exchanged OIDC for account `srmani`, then executed:

```sh
dotnet nuget push dist/sdk/dotnet/*.nupkg --api-key "$NUGET_API_KEY" --source https://api.nuget.org/v3/index.json
```

At 00:38:42Z, NuGet returned `Created` and `Your package was pushed.` The failing
command was the **subsequent** `python tools/sdk_verify.py dotnet --registry-only`:
`dotnet run --project Consumer.csproj` reported NU1101, package absent from the
nuget source. The final failed check was at 00:41:46Z. This is observed initial
unavailability after acceptance; the server's exact validation/indexing stage
is not exposed by these logs. There is no evidence of an authentication, name,
code or packaging rejection.

Live flat-container metadata now lists **0.1.0**, and the public
[package page](https://www.nuget.org/packages/VerifyAnything/0.1.0) lists owner
`srmani`. A new consumer with its own empty package cache successfully restored
and ran that exact version. Release complete; **do not re-upload or rerun the
original publish job**. Preflight correctly rejects an already published version.
No NuGet package/workflow change, timeout increase, retry increase, skip or
version bump was made. The historical red run remains an accurate record.

### Maven: signed staging bundle rejected; not published

[Run 39348760982](https://github.com/openverifyproject/openverify/actions/runs/39348760982)
executed `mvn -B -f sdk/jvm/pom.xml -Prelease -Dgpg.passphrase=... deploy`.
Signing four artifacts and authenticated upload succeeded. Deployment
`d4b907ab-c20e-4d48-a52f-868ecc63cf46` then failed validation:

```text
Bundle has content that does NOT have a .pom file: io/github/openverifyproject/verifyanything
```

Independent local reproduction with Maven 3.10.0 and plugin 0.11.0 generated a
bundle containing `maven-metadata-local.xml` at the artifact directory (outside
the version directory), `_remote.repositories` with checksums, and `.locks`.
The reproduction used synthetic credentials and `centralBaseUrl=http://127.0.0.1:9`;
the expected connection refusal prevented external upload. This reproduces the
specific malformed layout, rather than assuming an authorization problem.

[Sonatype's 0.12.0 release notes](https://central.sonatype.org/publish/publish-portal-maven/#0120-13-oct-2026)
identify this exact Maven 3.10 compatibility defect and its fix. Updated only the
Central plugin to **0.12.0**, package version and matching Java version constant
to **0.1.1**. Existing signing, namespace, publication wait and authentication
configuration remain intact. No error proves a name or ownership conflict.

With plugin 0.12.0, `-DskipUpload=true` produces the corrected local bundle and
explicitly stops before upload. Inspection finds exactly 20 entries: POM, main,
sources and javadoc artifacts with four checksums each, all inside
`io/github/openverifyproject/verifyanything/0.1.1/`, with no metadata, repository
tracking or lock files. Signing was disabled for this local structural check;
the original hosted run independently established that signing works. Local
bundle SHA256: `db01997f1bad82f465b3ddbd9a3de7534046fafb4953b392de94317a14e0c388`.

Public Maven metadata is still 404; neither 0.1.0 nor 0.1.1 is listed. The
uploaded 0.1.0 deployment is FAILED, not a partially published release. It may
remain in the account's deployment history; no deletion is required or performed.
Use a new `sdk/jvm/v0.1.1` tag of corrected merged source. Re-running the old
workflow would rebuild using plugin 0.11.0 and repeat the defect. Existing Portal
credentials and signing succeeded; no new account action is established.

## Local validation

Only affected native packages were built. Portable fixtures, specifications,
Golden expectations, production code and the six successful products are intact.

| Check | Result |
|---|---|
| `python tools/sdk_verify.py rust` | PASS: 2 native functions, shared 52 VCP + 45 Provider cases, two identical-content package builds, clean extracted-package consumer |
| Extract verified crate, `cargo publish --dry-run --locked` | PASS: package verification succeeds; upload explicitly aborted by dry-run |
| `python tools/sdk_verify.py jvm` (Maven 3.10.0) | PASS: 98 tests, zero failures/errors/skips; repeated package contents identical; clean external consumer |
| Maven 3.10.0 release profile, plugin 0.12.0, `-Dgpg.skip=true -DskipUpload=true clean deploy` | PASS: 98 tests; corrected bundle structure verified; no upload |
| `python tools/sdk_verify.py dotnet --registry-only` | PASS: public VerifyAnything 0.1.0 installed into a new package cache and consumer ran |
| `python -m pytest sdk/tests -q` | 64 PASS |
| Ruff, changed Python files | PASS |
| Actionlint, three affected release workflows | PASS |

The Rust and JVM pre-commit verification manifests correctly say
`dirty_worktree=true` and reference the base commit. They are local validation
evidence, **not** publishable tag proofs. The workflows must regenerate clean,
exact-commit evidence on the new tags. No freeze artifacts were altered.

Raw local logs and artifacts are ignored under `.sdk-cache/` and `dist/sdk/`.
Current authoritative hosted failure evidence remains linked above. Initial
sandbox-only .NET/Javadoc attempts encountered host access restrictions; host
executions succeeded. These environment failures were not patched into source.

## Recovery boundary

Review/push this correction branch, open and merge its PR after green checks,
then wait for both main CI workflows at the actual merge commit. Confirm 0.1.1
remains unpublished and new tags do not already exist. Create/push only
`sdk/rust/v0.1.1` and `sdk/jvm/v0.1.1`, separately, from that merged commit.
For NuGet, only recheck the published consumer; never publish 0.1.0 again.
Do not run the all-products launcher for this recovery. The launcher now accepts
`--only rust` or `--only jvm`, querying and releasing only that product. It derives
the release commit dynamically from clean HEAD, requires exact latest
`origin/main` and green main CI, and never uses a hardcoded correction SHA.
Run `python tools/release_launch.py --push --wait-for-ci --only rust` first;
only after hosted Rust release success and registry verification run the same
command with `--only jvm`. Selection regressions bring tooling tests to 66 PASS.

Remaining limits: first-crate token permissions/name acceptance and new Central
server-side validation can only be established by authorized publication. Local
build/consumer success is not universal Golden certification.

## Follow-up after Rust `sdk/rust/v0.1.1` failed before upload

[The Rust 0.1.1 run](https://github.com/openverifyproject/openverify/actions/runs/39354837860)
passed package verification, then `cargo publish --locked` refused the six
uncommitted files extracted under `.sdk-release/` inside Git. The earlier local
dry-run used an ignored directory and missed this checkout interaction. Version
0.1.1 remains unpublished; its immutable tag is preserved.

The Rust workflow and its reusable verification job now call the same
`tools/sdk_rust_publish.py` helper. It requires `RUNNER_TEMP` outside Git, extracts
the verified `.crate` there, and runs `cargo publish --locked`. Verification uses
`--dry-run` and installs the *repackaged* crate that Cargo generated. The existing
`--allow-dirty` packaging flag was also removed. Rust package metadata and lockfile
advance to **0.1.2**; all other package versions remain unchanged.

Before this follow-up was committed, 68 tooling tests passed; Rust native/shared
tests, two identical-content package builds from an external source snapshot,
the original package consumer, actual external-path `cargo publish --locked
--dry-run`, and the repackaged crate consumer all passed. The source snapshot was
needed only because pre-commit source files are intentionally dirty; the hosted
tag run will build from a clean exact commit. The local dry-run made no upload.
