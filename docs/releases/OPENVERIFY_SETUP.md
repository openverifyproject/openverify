# OpenVerify Python execution harness publication setup

`pip install openverify` supplies the existing Python Relay, graph authoring API,
standard providers, integrations and `openverify` CLI. Python 3.13 is required.
`pip install verifyanything` supplies the independent portable wire SDK under
`verifyanything`, Python 3.11+. Neither distribution overwrites the other's import
package or owns the other's release/version. The harness retains its existing
public `openverify` APIs; this change adds no dependency on VerifyAnything.

Both packages can be installed together:

```powershell
python -m pip install openverify verifyanything
python -c "import openverify, verifyanything; print(openverify.__file__); print(verifyanything.__file__)"
openverify --help
```

These are post-publication commands; before publication use the tested local
wheels and the validation command below. This source change does not assert that
either package is already public. [Registry evidence](REGISTRY_STATUS.json) found
`openverify` unlisted on PyPI; ownership/name acceptance is unverified.

## Verification and actual release scope

From the new isolated package worktree:

```powershell
uv sync --frozen
uv run --with build python tools/python_products_verify.py
```

The verifier builds actual distributions, checks disjoint wheel payloads, and
uses fresh environments for SDK-only, core-only, SDK-then-core and core-then-SDK.
Every pip operation and import smoke runs with `-I`. SDK-only must not expose
`openverify`; core-only must not expose `verifyanything`. Combined installations
must expose both independently. The unchanged installed-wheel harness consumer
checks standard text evaluation, CLI help, 24 VCP schemas, 9 Provider schemas,
typing marker and standard profile from site-packages. `pip check` must pass.

Core CI runs existing production/unit/integration/property/Relay tests, Golden V4,
all revision regressions/mutation probes, frozen integrity, source/wheel builds
and these independent-install checks on Ubuntu and Windows. Current local results
are in [LOCAL_VERIFICATION.json](LOCAL_VERIFICATION.json). The base main's GitHub
workflows are green; the changed branch needs its own PR checks after push.

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

Reuse your existing PyPI account at https://pypi.org/manage/account/publishing/.
Add a pending GitHub publisher with:

- Project: `openverify`
- Owner: `openverifyproject`
- Repository: `openverify`
- Workflow filename: `core-release-python.yml`
- GitHub environment: `core-python`

This is distinct from SDK project `verifyanything`, its workflow
`sdk-release-python.yml` and environment `sdk-python`. The two pending publishers
do not grant each other publishing permission. Follow [PyPI pending publisher
instructions](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).
A pending publisher is not a guaranteed reservation/acceptance of a project name.

GitHub environment creation, tag restrictions and safe configuration are
performed by `tools/release_github_setup.py --apply`. No manual environment or
variable creation is required. The independent PyPI publisher uses `core-python`
and requires actual PyPI OIDC authorization. No ownership-approval boolean is
used as a substitute for authentication. The publisher job alone has OIDC write
permission; it verifies merged source, the exact tag and tested artifact hashes.
The automated launcher skips already published versions.

## Source review, merge and independent release

Use the push/PR/review commands in [VerifyAnything setup](VERIFYANYTHING_SETUP.md).
Do not publish from an unreviewed/unmerged source commit. Do not push any tag until
the relevant registry publication is individually authorized.

After approved merge and publisher setup:

```powershell
git fetch origin
$releaseCommit = git rev-parse origin/main
$tag = 'core/python/v0.1.0'
git tag -a $tag $releaseCommit -m "$tag"
git push origin "refs/tags/$tag"
```

This triggers only `.github/workflows/core-release-python.yml`. Ordinary pushes,
PRs and all `sdk/*` tags cannot publish the harness. Subsequent core releases
update root `pyproject.toml` and `uv.lock` as needed, preserve SDK versions, merge
reviewed changes, and use `core/python/vX.Y.Z`.

For an explicitly approved manual first upload instead of the automated first
tag, verify the clean source is merged, then build and test:

```powershell
uv run --with build python tools/python_products_verify.py
uv run --with twine python -m twine check .\dist\core-python\*
uv run --with twine python -m twine upload .\dist\core-python\*
```

Twine authenticates interactively or through approved host credential stores;
never commit `.pypirc` or share tokens in chat. Choose either manual or automatic
publication for a version. After a manual upload, start automatic tagged uploads
at the next version: the preflight intentionally rejects re-upload of 0.1.0.

After public publication, in a fresh Python 3.13 environment:

```powershell
python -m venv .sdk-cache/published-harness-consumer
& .\.sdk-cache\published-harness-consumer\Scripts\python.exe -I -m pip install openverify==0.1.0 verifyanything==0.1.0
& .\.sdk-cache\published-harness-consumer\Scripts\python.exe -I -m pip check
& .\.sdk-cache\published-harness-consumer\Scripts\python.exe -I conformance/golden-v4/release-review-v0.1/consumer_check.py
& .\.sdk-cache\published-harness-consumer\Scripts\python.exe -I -c "import verifyanything as s; print(s.__version__)"
```

No GitHub settings, accounts, registries, tags or remote branches have been changed
by this preparation. Only push/PR creation after authorization can establish the
new CI result; only successful authenticated publication can establish registry
ownership and public installation.
