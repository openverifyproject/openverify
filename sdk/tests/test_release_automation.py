"""Executable guards for first releases, namespace identity and registry requests."""
# ruff: noqa: E402

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import release_github_setup
import release_launch
import sdk_packagist
import sdk_release
import sdk_workflows


def test_published_scoped_npm_version_is_not_a_candidate_for_another_upload():
    assert sdk_release.NAMES["node"] == "@openverifyproject/verifyanything"
    with patch.object(sdk_release, "fetch", return_value=(200, json.dumps({
        "versions": {"0.0.0-stage": {}, "0.1.0": {}},
    }))):
        assert sdk_release.is_published("node", "0.1.0")
        with pytest.raises(RuntimeError, match="already published"):
            sdk_release.unpublished("node", "0.1.0")


def test_launcher_skips_existing_npm_but_retains_both_python_products():
    with (
        patch.object(release_launch, "is_published", side_effect=lambda lang, ver: lang == "node"),
        patch.object(release_launch, "fetch", return_value=(404, "")),
    ):
        rows = release_launch.plan()
    assert rows[0]["action"] == "SKIP_PUBLISHED"
    assert len([r for r in rows if r["action"] == "PUSH_TAG"]) == 8
    assert {r["tag"] for r in rows if r["product"] in ("python", "core")} == {
        "sdk/python/v0.1.0", "core/python/v0.1.0",
    }


def test_all_nine_environments_have_only_their_own_exact_tag_prefix():
    envs = release_github_setup.ENVIRONMENTS
    assert len(envs) == 9
    assert envs["core-python"] == "core/python/v*"
    for language in release_launch.ORDER[:-1]:
        assert envs["sdk-" + language] == "sdk/" + language + "/v*"


@pytest.mark.parametrize("product", ["rust", "jvm"])
def test_selected_release_does_not_query_other_registries(product):
    with patch.object(release_launch, "is_published", return_value=False) as published:
        rows = release_launch.plan([product])
    assert [r["product"] for r in rows] == [product]
    assert published.call_args_list == [((product, rows[0]["version"]),)]


def test_launcher_cannot_write_tags_from_dirty_source():
    with patch.object(release_launch, "git", return_value=" M changed.py") as git:
        with pytest.raises(RuntimeError, match="clean"):
            release_launch.launch()
    assert [c.args for c in git.call_args_list] == [("status", "--porcelain")]


def test_failed_main_ci_is_a_release_blocker():
    with patch.object(release_launch, "api", return_value={"workflow_runs": [{
        "status": "completed", "conclusion": "failure",
    }]}):
        with pytest.raises(RuntimeError, match="CI failed"):
            release_launch.green("a" * 40)


def test_central_waits_for_published_state_before_registry_consumer():
    from xml.etree import ElementTree

    pom = ElementTree.parse(ROOT / "sdk/jvm/pom.xml")
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    plugins = pom.findall(".//m:profile/m:build/m:plugins/m:plugin", ns)
    central = next(p for p in plugins if p.findtext("m:artifactId", namespaces=ns)
                   == "central-publishing-maven-plugin")
    assert central.findtext("m:configuration/m:autoPublish", namespaces=ns) == "true"
    assert central.findtext("m:configuration/m:waitUntil", namespaces=ns) == "published"
    # 0.11.0 bundles Maven 3.10's local metadata, repository tracking and locks.
    assert tuple(map(int, central.findtext("m:version", namespaces=ns).split("."))) >= (0, 12, 0)


def test_rust_auth_revision_is_the_resolved_upstream_release():
    reference = "rust-lang/crates-io-auth-action@v1.0.5"
    revision = "c6f97d42243bad5fab37ca0427f495c86d5b1a18"
    assert sdk_workflows.ACTION_REVISIONS[reference] == revision
    text = (ROOT / ".github/workflows/sdk-release-rust.yml").read_text()
    assert sdk_workflows.pin_actions(sdk_workflows.SETUP["rust"]) in text
    # A skipped action is still resolved when GitHub prepares the job.
    assert "ebc737b6fc418a6ca0073cf116ec8dc156d8b81e" not in text


def test_published_nuget_release_cannot_be_republished_after_consumer_failure():
    with patch.object(sdk_release, "fetch", return_value=(200, '{"versions":["0.1.0"]}')):
        assert sdk_release.is_published("dotnet", "0.1.0")
        with pytest.raises(RuntimeError, match="already published"):
            sdk_release.unpublished("dotnet", "0.1.0")


def test_published_only_launch_performs_no_git_tag_or_push():
    def git(*args):
        if args in [("status", "--porcelain"), ("fetch", "origin")]:
            return ""
        assert args in [("rev-parse", "HEAD"), ("rev-parse", "origin/main")]
        return "a" * 40

    with (
        patch.object(release_launch, "git", side_effect=git),
        patch.object(release_launch, "green", return_value=True),
        patch.object(release_launch, "plan", return_value=[{
            "product": "node", "version": "0.1.0", "action": "SKIP_PUBLISHED",
        }]),
    ):
        release_launch.launch()


def test_each_release_uses_a_separate_explicit_tag_push():
    calls = []

    def git(*args):
        calls.append(args)
        return "a" * 40 if args[0] == "rev-parse" else ""

    rows = [{"product": p, "version": "0.1.0", "tag": t, "action": "PUSH_TAG"}
            for p, t in [("go", "sdk/go/v0.1.0"), ("core", "core/python/v0.1.0")]]
    with (
        patch.object(release_launch, "git", side_effect=git),
        patch.object(release_launch, "green", return_value=True),
        patch.object(release_launch, "plan", return_value=rows),
        patch.object(release_launch.subprocess, "run") as run,
    ):
        run.return_value.returncode = 1  # Neither local tag exists.
        release_launch.launch()
    assert [c for c in calls if c[0] == "push"] == [
        ("push", "--no-follow-tags", "origin", "refs/tags/sdk/go/v0.1.0"),
        ("push", "--no-follow-tags", "origin", "refs/tags/core/python/v0.1.0"),
    ]


def test_packagist_first_release_registers_and_updates_without_credentials_in_url(monkeypatch):
    monkeypatch.setenv("GITHUB_REF_NAME", "sdk/php/v0.1.0")
    monkeypatch.setenv("SDK_PHP_MIRROR", "openverifyproject/verifyanything-php")
    monkeypatch.setenv("PACKAGIST_USERNAME", "account")
    monkeypatch.setenv("PACKAGIST_API_TOKEN", "synthetic-not-a-secret")
    with (
        patch.object(sdk_packagist, "fetch", return_value=(404, "")),
        patch.object(sdk_packagist, "post") as post,
    ):
        sdk_packagist.main()
    assert [c.args[0] for c in post.call_args_list] == ["create-package", "update-package"]
    assert all(c.args[1] == "https://github.com/openverifyproject/verifyanything-php"
               for c in post.call_args_list)


def test_packagist_cannot_take_over_another_repository(monkeypatch):
    monkeypatch.setenv("GITHUB_REF_NAME", "sdk/php/v0.1.0")
    monkeypatch.setenv("SDK_PHP_MIRROR", "openverifyproject/verifyanything-php")
    monkeypatch.setenv("PACKAGIST_USERNAME", "account")
    monkeypatch.setenv("PACKAGIST_API_TOKEN", "synthetic-not-a-secret")
    with (
        patch.object(sdk_packagist, "fetch", return_value=(200, json.dumps({
            "package": {"repository": "https://github.com/other/source"},
        }))),
        patch.object(sdk_packagist, "post", side_effect=AssertionError("must not write")),
    ):
        with pytest.raises(RuntimeError, match="another source"):
            sdk_packagist.main()


def test_packagist_uses_bearer_header_not_query_parameters():
    response = type("Response", (), {
        "__enter__": lambda self: self, "__exit__": lambda *args: None,
        "read": lambda self: b'{"status":"success"}',
    })()
    with patch.object(sdk_packagist.urllib.request, "urlopen", return_value=response) as open_url:
        sdk_packagist.post("create-package", "https://github.com/org/repo", "user", "token")
    request = open_url.call_args.args[0]
    assert request.full_url == "https://packagist.org/api/create-package"
    assert request.get_header("Authorization") == "Bearer user:token"
    assert json.loads(request.data) == {"repository": "https://github.com/org/repo"}
