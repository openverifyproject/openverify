"""Fail-closed, read-only preflight for the independent Python harness release."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

from sdk_release import fetch, require_merged_source
from sdk_verify import ROOT

PRODUCTS = {
    "relay": ROOT / "packages/relay/pyproject.toml",
    "code": ROOT / "packages/code/pyproject.toml",
    "english": ROOT / "packages/english/pyproject.toml",
    "python": ROOT / "pyproject.toml",
}


def required_published_products(metadata):
    dependencies = []
    pattern = re.compile(
        r"^(verifyanything|openverify-(?:relay|code|english))(?:\[[^]]+\])?==([0-9]+\.[0-9]+\.[0-9]+)$"
    )
    for declaration in metadata.get("dependencies", []):
        match = pattern.fullmatch(declaration)
        if match:
            dependencies.append(match.groups())
        elif declaration.startswith(("verifyanything", "openverify-")):
            raise RuntimeError("Core product dependency is not exactly pinned: " + declaration)
    return dependencies


def preflight(tag, evidence, package_directory, product="python", stage_dir=None):
    if product not in PRODUCTS:
        raise RuntimeError("Unknown core product")
    if not re.fullmatch(rf"core/{product}/v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise RuntimeError(f"Expected core/{product}/vX.Y.Z")
    metadata = tomllib.loads(PRODUCTS[product].read_text())["project"]
    name, version = metadata["name"], metadata["version"]
    if tag != f"core/{product}/v{version}":
        raise RuntimeError("Core tag/package metadata mismatch")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tagged = subprocess.check_output(
        ["git", "rev-parse", tag + "^{commit}"], cwd=ROOT, text=True,
    ).strip()
    if head != tagged:
        raise RuntimeError("Checkout is not the tagged core commit")
    require_merged_source(head)
    proof = json.loads(Path(evidence).read_text())
    expected = {"sdk-alone", "core-alone", "sdk-then-core", "core-then-sdk"}
    if (
        proof.get("status") != "PASS" or proof.get("commit") != head
        or proof.get("dirty_worktree", True)
        or len(proof["scenarios"]) != 4
        or {s["scenario"] for s in proof["scenarios"] if s["status"] == "PASS"} != expected
    ):
        raise RuntimeError("Core consumer evidence does not match exact clean release source")
    files = list(Path(package_directory).iterdir())
    prefix = name.replace("-", "_") + "-" + version
    wheels = [p for p in files if p.name.startswith(prefix + "-") and p.suffix == ".whl"]
    sources = [p for p in files if p.name == prefix + ".tar.gz"]
    if len(wheels) != 1 or len(sources) != (1 if product == "python" else 0):
        raise RuntimeError(f"Unexpected distributions for {name}=={version}")
    for package in (*wheels, *sources):
        digest = hashlib.sha256(package.read_bytes()).hexdigest()
        if digest != proof["artifacts"].get(package.name):
            raise RuntimeError("Core artifact checksum mismatch: " + package.name)
    status, body = fetch(f"https://pypi.org/pypi/{name}/json")
    if status == 200 and version in json.loads(body).get("releases", {}):
        raise RuntimeError("Core version is already published")
    if status not in (200, 404):
        raise RuntimeError(f"Cannot verify PyPI version availability: HTTP {status}")
    for dependency, required_version in required_published_products(metadata):
        dependency_status, dependency_body = fetch(f"https://pypi.org/pypi/{dependency}/json")
        if (
            dependency_status != 200
            or required_version not in json.loads(dependency_body).get("releases", {})
        ):
            raise RuntimeError(
                f"Required PyPI dependency is unpublished: {dependency}=={required_version}"
            )
    if stage_dir is not None:
        destination = Path(stage_dir)
        destination.mkdir(parents=True, exist_ok=False)
        for package in (*wheels, *sources):
            shutil.copyfile(package, destination / package.name)
    print(json.dumps({"package": name, "version": version, "commit": head}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--package-directory", required=True)
    parser.add_argument("--product", choices=PRODUCTS, default="python")
    parser.add_argument("--stage-dir")
    args = parser.parse_args()
    preflight(args.tag, args.evidence, args.package_directory, args.product, args.stage_dir)
