"""Regression tests for package isolation, offline bundling and release guards."""
# ruff: noqa: E402 -- repository-local maintenance modules require tools on sys.path

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import core_release
import sdk_bundle
import sdk_mirror
import sdk_release
import sdk_verify
import sdk_workflows


def test_bundled_normative_resources_are_exact():
    bundle = sdk_bundle.build()
    for path in (ROOT / "sdk").rglob("bundle.json"):
        if any(
            part in path.parts
            for part in ("vendor", "target", "node_modules", ".sdk-cache", "build", "bin", "obj")
        ):
            continue
        assert json.loads(path.read_text(encoding="utf-8")) == bundle
    for folder in ("schemas/draft", "provider-contract/schemas/draft"):
        for path in (ROOT / folder).glob("*.json"):
            schema = json.loads(path.read_text())
            assert bundle["schemas"][schema["$id"]] == schema


def test_fixture_inventory_and_unique_ids():
    root = ROOT / "conformance/sdk"
    paths = json.loads((root / "manifest.json").read_text())["cases"]
    cases = [json.loads((root / p).read_text()) for p in paths]
    assert len({c["id"] for c in cases}) == len(cases)
    assert {c["contract"] for c in cases} == {"vcp", "provider"}
    assert all(c["features"] and c["version"] and c["expected"] for c in cases)
    assert set(paths) == {
        p.relative_to(root).as_posix()
        for folder in ("vcp", "provider")
        for p in (root / folder).glob("*.json")
    }


@pytest.mark.parametrize("language", sdk_workflows.LANGUAGES)
def test_release_filters_only_one_language(language):
    text = (ROOT / f".github/workflows/sdk-release-{language}.yml").read_text()
    assert f"tags: ['sdk/{language}/v*']" in text
    assert f"environment: sdk-{language}" in text
    assert "needs: verify" in text and "--evidence" in text
    assert "--registry-only" in text
    assert "REGISTRY_OWNERSHIP_APPROVED" in text


@pytest.mark.parametrize("language", sdk_workflows.LANGUAGES)
def test_publish_permissions_and_checkout_credentials(language):
    text = (ROOT / f".github/workflows/sdk-release-{language}.yml").read_text()
    assert ("id-token: write" in text) == (language in ("node", "python", "ruby", "rust", "dotnet"))
    assert "persist-credentials: false" in text


def test_sdk_ci_runs_for_every_pull_request():
    text = (ROOT / ".github/workflows/sdk-ci.yml").read_text()
    assert "pull_request:" in text
    assert "paths:" not in text
    assert "release/openverify-v0.1" in text


def test_all_remote_actions_are_pinned():
    import re

    for path in (ROOT / ".github/workflows").glob("*.yml"):
        for reference in re.findall(r"uses:\s+([^\s#]+)", path.read_text()):
            if not reference.startswith("./"):
                assert re.fullmatch(r"[^@]+@[a-f0-9]{40}", reference), (path, reference)


def test_source_push_cannot_trigger_sdk_publication():
    for path in (ROOT / ".github/workflows").glob("sdk-release-*.yml"):
        trigger = path.read_text().split("permissions:", 1)[0]
        assert "tags:" in trigger
        assert "branches:" not in trigger
        assert "workflow_dispatch:" not in trigger
        assert "pull_request:" not in trigger


@pytest.mark.parametrize("language", sdk_workflows.LANGUAGES)
def test_independent_runtime_versions(language):
    import re

    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", sdk_verify.validate_version(language))


def test_release_wrong_language_never_queries_registry():
    with patch.object(sdk_release, "fetch", side_effect=AssertionError("network must not run")):
        with pytest.raises(RuntimeError, match="Tag must"):
            sdk_release.preflight("node", "sdk/rust/v0.1.0")


def test_release_metadata_mismatch_never_queries_registry():
    with patch.object(sdk_release, "fetch", side_effect=AssertionError("network must not run")):
        with pytest.raises(RuntimeError, match="mismatch"):
            sdk_release.preflight("node", "sdk/node/v99.0.0")


@pytest.mark.parametrize("code", [1, 128])
def test_release_rejects_unmerged_or_unknown_main(code):
    with (
        patch.object(subprocess, "check_output", return_value="https://github.com/openverifyproject/openverify.git\n"),
        patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], code)),
    ):
        with pytest.raises(RuntimeError, match="merged into origin/main"):
            sdk_release.require_merged_source("a" * 40)


def test_release_rejects_different_repository():
    with patch.object(subprocess, "check_output", return_value="https://github.com/unrelated/openverify.git"):
        with pytest.raises(RuntimeError, match="openverifyproject/openverify"):
            sdk_release.require_merged_source("a" * 40)


@pytest.mark.parametrize("remote", [
    "https://github.com/openverifyproject/openverify",
    "https://github.com/openverifyproject/openverify.git",
    "git@github.com:openverifyproject/openverify.git",
])
def test_release_accepts_merged_source_and_checkout_origin_forms(remote):
    with (
        patch.object(subprocess, "check_output", return_value=remote),
        patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0)),
    ):
        sdk_release.require_merged_source("a" * 40)


def test_exact_package_identities_and_preserved_language_apis():
    import tomllib

    assert json.loads((ROOT / "sdk/node/package.json").read_text())["name"] == "verifyanything"
    rust = tomllib.loads((ROOT / "sdk/rust/Cargo.toml").read_text())
    assert rust["package"]["name"] == "verifyanything"
    assert rust["lib"]["name"] == "verifyanything"
    dotnet = ROOT / "sdk/dotnet/OpenVerify.Sdk/OpenVerify.Sdk.csproj"
    assert "<PackageId>VerifyAnything</PackageId>" in dotnet.read_text()
    assert '<artifactId>verifyanything</artifactId>' in (ROOT / "sdk/jvm/pom.xml").read_text()
    assert "s.name = 'verifyanything'" in (ROOT / "sdk/ruby/openverify.gemspec").read_text()
    php = json.loads((ROOT / "sdk/php/composer.json").read_text())
    assert php["name"] == "openverify/verifyanything"
    python = tomllib.loads((ROOT / "sdk/python/pyproject.toml").read_text())
    assert python["project"]["name"] == "verifyanything"
    assert sdk_release.NAME_URLS["node"] == "https://registry.npmjs.org/verifyanything"


def test_registry_failures_are_not_name_availability():
    with patch.object(sdk_release, "fetch", side_effect=OSError("offline")):
        assert all(
            p["http_status"] is None and "query failed" in p["status"]
            and p["classification"] == "UNKNOWN"
            for p in sdk_release.names()["packages"]
        )


def test_unlisted_name_is_not_registration_acceptance_or_ownership():
    with patch.object(sdk_release, "fetch", return_value=(404, "")):
        rows = sdk_release.names()["packages"]
    assert all(row["classification"] == "UNLISTED" for row in rows)
    assert all(row["ownership"].startswith("UNKNOWN") for row in rows)
    assert all("unverified" in row["status"] for row in rows)


def test_empty_go_proxy_list_does_not_mean_a_version_is_published():
    with patch.object(sdk_release, "fetch", return_value=(200, "")):
        go = next(p for p in sdk_release.names()["packages"] if p["language"] == "go")
    assert go["classification"] == "UNLISTED"


@pytest.mark.parametrize("tag", ["sdk/python/v0.1.0", "core/node/v0.1.0", "core/python/v0.1"])
def test_core_rejects_other_release_tags_before_network_or_publication(tag):
    with patch.object(core_release, "fetch", side_effect=AssertionError("no network")):
        with pytest.raises(RuntimeError, match="Expected core/python"):
            core_release.preflight(tag, "unused", "unused")


def test_core_release_is_independent_and_gated_by_harness_checks():
    text = (ROOT / ".github/workflows/core-release-python.yml").read_text()
    trigger = text.split("permissions:", 1)[0]
    assert "tags: ['core/python/v*']" in trigger
    assert "branches:" not in trigger and "pull_request:" not in trigger
    assert "environment: core-python" in text and "needs: verify" in text
    assert "uses: ./.github/workflows/project-ci.yml" in text
    assert "tools/core_release.py" in text and "--evidence" in text


def test_portable_python_namespace_does_not_supply_harness_or_cli():
    import tomllib

    metadata = tomllib.loads((ROOT / "sdk/python/pyproject.toml").read_text())
    assert metadata["project"]["name"] == "verifyanything"
    assert not metadata["project"].get("scripts")
    assert not any(d.startswith("openverify") for d in metadata["project"]["dependencies"])
    assert (ROOT / "sdk/python/src/verifyanything/__init__.py").is_file()
    assert not (ROOT / "sdk/python/src/openverify").exists()


def test_published_version_is_rejected():
    with patch.object(
        sdk_release, "fetch", return_value=(200, json.dumps({"versions": {"0.1.0": {}}}))
    ):
        with pytest.raises(RuntimeError, match="already published"):
            sdk_release.unpublished("node", "0.1.0")


def test_mirror_is_idempotent(monkeypatch):
    monkeypatch.setenv("GITHUB_REF_NAME", "sdk/php/v0.1.0")
    monkeypatch.setenv("SDK_PHP_MIRROR", "openverifyproject/sdk-php")
    calls = []

    def git(*args):
        calls.append(args)
        if args[0] == "subtree":
            return "a" * 40
        if args[0] == "ls-remote":
            return "a" * 40 + "\trefs/tags/v0.1.0"
        raise AssertionError(args)

    with (
        patch.object(sdk_mirror, "git", side_effect=git),
        patch.object(subprocess, "run", side_effect=AssertionError("must not push")),
    ):
        sdk_mirror.main()
    assert len(calls) == 2


def test_mirror_refuses_conflicting_tag(monkeypatch):
    monkeypatch.setenv("GITHUB_REF_NAME", "sdk/php/v0.1.0")
    monkeypatch.setenv("SDK_PHP_MIRROR", "openverifyproject/sdk-php")
    with (
        patch.object(sdk_mirror, "git", side_effect=["a" * 40, "b" * 40 + "\trefs/tags/v0.1.0"]),
        patch.object(subprocess, "run", side_effect=AssertionError("must not push")),
    ):
        with pytest.raises(RuntimeError, match="different content"):
            sdk_mirror.main()


def test_mirror_refuses_nonempty_unexpected_repository(monkeypatch):
    monkeypatch.setenv("GITHUB_REF_NAME", "sdk/php/v0.1.0")
    monkeypatch.setenv("SDK_PHP_MIRROR", "openverifyproject/sdk-php")
    with (
        patch.object(
            sdk_mirror, "git", side_effect=["a" * 40, "", "b" * 40 + "\trefs/heads/other"]
        ),
        patch.object(subprocess, "run", side_effect=AssertionError("must not push")),
    ):
        with pytest.raises(RuntimeError, match="Nonempty mirror"):
            sdk_mirror.main()


def test_mirror_refuses_unrelated_history(monkeypatch):
    monkeypatch.setenv("GITHUB_REF_NAME", "sdk/php/v0.1.0")
    monkeypatch.setenv("SDK_PHP_MIRROR", "openverifyproject/sdk-php")
    answers = ["a" * 40, "b" * 40 + "\trefs/heads/main", "", '{"name":"openverify/verifyanything"}']
    calls = []

    def run(command, **kwargs):
        assert command[:2] == ["git", "merge-base"], "must not push"
        calls.append(command)
        return subprocess.CompletedProcess(command, 1)

    with patch.object(sdk_mirror, "git", side_effect=answers), patch.object(subprocess, "run", run):
        with pytest.raises(RuntimeError, match="Unrelated or rewritten"):
            sdk_mirror.main()
    assert len(calls) == 2
