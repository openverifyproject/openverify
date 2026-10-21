"""Exercise each independent PyPI release guard without contacting a registry."""

import hashlib
import json
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import core_release  # noqa: E402


@pytest.mark.parametrize("product", ["relay", "code", "english", "python"])
def test_core_product_preflight_stages_only_its_verified_artifacts(product, tmp_path, monkeypatch):
    metadata = tomllib.loads(core_release.PRODUCTS[product].read_text())["project"]
    name, version = metadata["name"], metadata["version"]
    prefix = name.replace("-", "_") + "-" + version
    wheel = tmp_path / (prefix + "-py3-none-any.whl")
    wheel.write_bytes((product + " wheel").encode())
    files = [wheel]
    if product == "python":
        source = tmp_path / (prefix + ".tar.gz")
        source.write_bytes(b"root source archive")
        files.append(source)
    proof = {
        "status": "PASS",
        "commit": "a" * 40,
        "dirty_worktree": False,
        "scenarios": [{"scenario": name, "status": "PASS"} for name in (
            "sdk-alone", "core-alone", "sdk-then-core", "core-then-sdk"
        )],
        "artifacts": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    }
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps(proof))
    monkeypatch.setattr(core_release.subprocess, "check_output", lambda *args, **kwargs: "a" * 40)
    monkeypatch.setattr(core_release, "require_merged_source", lambda head: None)
    monkeypatch.setattr(core_release, "fetch", lambda url: (404, ""))
    stage = tmp_path / "stage"
    with pytest.raises(RuntimeError, match="Required PyPI dependency is unpublished"):
        core_release.preflight(
            f"core/{product}/v{version}", evidence, tmp_path, product, stage
        )
    assert not stage.exists()

    def registry(url):
        if url.endswith("/" + name + "/json"):
            return (404, "") if product != "python" else (200, '{"releases":{"0.1.0":[]}}')
        return 200, '{"releases":{"0.1.0":[],"0.1.1":[]}}'

    monkeypatch.setattr(core_release, "fetch", registry)
    core_release.preflight(
        f"core/{product}/v{version}", evidence, tmp_path, product, stage
    )
    assert {p.name for p in stage.iterdir()} == {p.name for p in files}
    assert all((stage / p.name).read_bytes() == p.read_bytes() for p in files)


@pytest.mark.parametrize("product,expected", [
    ("relay", [("verifyanything", "0.1.0")]),
    ("code", [("openverify-relay", "0.1.1")]),
    ("english", [("openverify-relay", "0.1.1")]),
    (
        "python",
        [
            ("openverify-relay", "0.1.1"),
            ("openverify-code", "0.1.1"),
            ("openverify-english", "0.1.1"),
        ],
    ),
])
def test_dependency_release_order_is_pinned(product, expected):
    metadata = tomllib.loads(core_release.PRODUCTS[product].read_text())["project"]
    assert core_release.required_published_products(metadata) == expected


@pytest.mark.parametrize("product", ["relay", "code", "english", "python"])
def test_core_product_workflow_scopes_publisher(product):
    workflow = ROOT / ".github/workflows" / f"core-release-{product}.yml"
    text = workflow.read_text(encoding="utf-8")
    assert f"tags: ['core/{product}/v*']" in text
    assert f"environment: core-{product}" in text
    assert "uses: ./.github/workflows/project-ci.yml" in text
    assert "id-token: write" in text
    assert "needs: verify" in text
    assert f"packages-dir: dist/publish/{product}/" in text
    assert "skip-existing: false" in text
