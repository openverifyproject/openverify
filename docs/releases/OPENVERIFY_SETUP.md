# OpenVerify Python execution harness publication setup

`pip install openverify==0.1.1` supplies the Python Relay, graph authoring API,
standard providers, Code and English checks, and `openverify` CLI. Python 3.13 is required.
`pip install verifyanything` supplies the independent portable wire SDK under
`verifyanything`, Python 3.11+. Neither distribution overwrites the other's import
package or owns the other's release/version. The harness retains its existing
public `openverify` APIs; Relay depends on `verifyanything==0.1.0`.

Both packages can be installed together:

```powershell
python -m pip install openverify verifyanything
python -c "import openverify, verifyanything; print(openverify.__file__); print(verifyanything.__file__)"
openverify --help
```

These are post-publication commands; before publication use tested local wheels.
`verifyanything==0.1.0` and the earlier monolithic `openverify==0.1.0` are already
on PyPI. The component projects and the new root version are not yet published.

## Verification and actual release scope

From a clean worktree with Python 3.13:

```powershell
uv sync --frozen
uv build sdk/python --wheel --out-dir dist/python
uv build packages/relay --wheel --out-dir dist/python
uv build packages/code --wheel --out-dir dist/python
uv build packages/english --wheel --out-dir dist/python
uv build --out-dir dist/python
$core = (Get-ChildItem dist/python/openverify-*.whl | Select-Object -First 1).FullName
$sdk = (Get-ChildItem dist/python/verifyanything-*.whl | Select-Object -First 1).FullName
uv run --frozen python tools/python_products_verify.py --core-wheel $core --sdk-wheel $sdk
```

The verifier builds actual distributions, checks disjoint wheel payloads, and
uses fresh environments for SDK-only, core-only, SDK-then-core and core-then-SDK.
Every pip operation and import smoke runs with `-I`. SDK-only must not expose
`openverify`; core-only installs `verifyanything` through Relay. Combined installations
must expose both independently. The unchanged installed-wheel harness consumer
checks standard text evaluation, CLI help, 24 VCP schemas, 9 Provider schemas,
typing marker and standard profile from site-packages. `pip check` must pass.

Core CI runs existing production/unit/integration/property/Relay tests, the historical pinned Golden V4,
all revision regressions/mutation probes, frozen integrity, source/wheel builds
and these independent-install checks on Ubuntu and Windows. The historical
Golden baseline is fetched by exact commit SHA because it is not reachable from
the current main branch in a fresh clone. The changed branch needs green hosted
checks after review and merge.

Passing bounded SDK or harness checks is not universal Golden certification. The
existing canonical/release reviews and their disclosed limitations remain intact.
The historical [release verdict](../../conformance/golden-v4/release-review-v0.1/RELEASE_VERDICT.md)
still records 1 verified, 396 partial and 218 blocker dispositions across 615
records. This packaging task does not discharge those assertion-sufficiency
residuals or declare that historical full-scope release gate READY. Review and
explicitly accept the disclosed DRAFT harness scope before approving its upload;
these harness coverage limitations do not hold the independent SDKs' releases.
No normative VCP/Provider spec, frozen expectation, original shared fixture or
production semantic implementation is modified by package identity separation.
No optional future Node harness is claimed.

## First PyPI setup

The owner is `openverifyproject` and repository is `openverify` for all four
GitHub Trusted Publishers:

| PyPI project | Workflow filename | GitHub environment | Tag |
| --- | --- | --- | --- |
| `openverify-relay` | `core-release-relay.yml` | `core-relay` | `core/relay/v0.1.0` |
| `openverify-code` | `core-release-code.yml` | `core-code` | `core/code/v0.1.0` |
| `openverify-english` | `core-release-english.yml` | `core-english` | `core/english/v0.1.0` |
| `openverify` | `core-release-python.yml` | `core-python` | `core/python/v0.1.1` |

Create pending publishers for the first three on the PyPI account Publishing
page. Add or verify the `openverify` publisher on that existing project's
Publishing page. A pending publisher does not reserve a project name. These
publishers are distinct from the `verifyanything` SDK publisher.

GitHub environment creation, tag restrictions and safe configuration are
performed by `tools/release_github_setup.py --apply`. No manual environment or
variable creation is required. Each publisher job alone has OIDC write permission
and verifies merged source, the exact tag, unpublished version and tested artifact
hashes. The three component releases are wheel only; the root also has a source
distribution. The Relay source distribution cannot currently rebuild after
extraction because its source tree lies outside the component package directory.

## Source review, merge and independent release

Use the push/PR/review commands in [VerifyAnything setup](VERIFYANYTHING_SETUP.md).
Do not publish from an unreviewed/unmerged source commit. Do not push any tag until
the relevant registry publication is individually authorized.

After approved merge and publisher setup, publish Relay, then Code and English,
then the root product. Each tag requires separate authorization. The first tag is:

```powershell
git fetch origin
$releaseCommit = git rev-parse origin/main
$tag = 'core/relay/v0.1.0'
git tag -a $tag $releaseCommit -m "$tag"
git push origin "refs/tags/$tag"
```

This triggers only `.github/workflows/core-release-relay.yml`. Once the Relay
package is available, use `core/code/v0.1.0` and `core/english/v0.1.0`; once both
are available, use `core/python/v0.1.1`. Ordinary pushes and PRs cannot publish.

After public publication, in a fresh Python 3.13 environment:

```powershell
python -m venv .sdk-cache/published-harness-consumer
& .\.sdk-cache\published-harness-consumer\Scripts\python.exe -I -m pip install openverify==0.1.1 verifyanything==0.1.0
& .\.sdk-cache\published-harness-consumer\Scripts\python.exe -I -m pip check
& .\.sdk-cache\published-harness-consumer\Scripts\python.exe -I conformance/golden-v4/release-review-v0.1/consumer_check.py
& .\.sdk-cache\published-harness-consumer\Scripts\python.exe -I -c "import verifyanything as s; print(s.__version__)"
```

No GitHub settings, accounts, registries, tags or remote branches have been changed
by this preparation. Only push/PR creation after authorization can establish the
new CI result; only successful authenticated publication can establish registry
ownership and public installation.
