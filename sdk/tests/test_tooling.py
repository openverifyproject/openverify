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
    assert ("id-token: write" in text) == (language in ("node", "python", "ruby"))
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


def test_registry_failures_are_not_name_availability():
    with patch.object(sdk_release, "fetch", side_effect=OSError("offline")):
        assert all(
            p["http_status"] is None and "query failed" in p["status"]
            for p in sdk_release.names()["packages"]
        )


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
    answers = ["a" * 40, "b" * 40 + "\trefs/heads/main", "", '{"name":"openverify/sdk"}']
    calls = []

    def run(command, **kwargs):
        assert command[:2] == ["git", "merge-base"], "must not push"
        calls.append(command)
        return subprocess.CompletedProcess(command, 1)

    with patch.object(sdk_mirror, "git", side_effect=answers), patch.object(subprocess, "run", run):
        with pytest.raises(RuntimeError, match="Unrelated or rewritten"):
            sdk_mirror.main()
    assert len(calls) == 2
