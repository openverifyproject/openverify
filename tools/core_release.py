"""Fail-closed, read-only preflight for the independent Python harness release."""

import argparse
import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path

from sdk_release import fetch, require_merged_source
from sdk_verify import ROOT


def preflight(tag, evidence, package_directory):
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    if not re.fullmatch(r"core/python/v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise RuntimeError("Expected core/python/vX.Y.Z")
    if tag != "core/python/v" + version:
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
    packages = list(Path(package_directory).iterdir())
    wheel = [p for p in packages if p.suffix == ".whl"]
    if len(wheel) != 1 or not wheel[0].name.startswith("openverify-" + version + "-"):
        raise RuntimeError("Expected exactly the named core wheel")
    if not any(p.name == "openverify-" + version + ".tar.gz" for p in packages):
        raise RuntimeError("Missing core source distribution")
    for package in packages:
        if package.name.endswith((".whl", ".tar.gz")):
            digest = hashlib.sha256(package.read_bytes()).hexdigest()
            if digest != proof["artifacts"].get(package.name):
                raise RuntimeError("Core artifact checksum mismatch: " + package.name)
    status, body = fetch("https://pypi.org/pypi/openverify/json")
    if status == 200 and version in json.loads(body).get("releases", {}):
        raise RuntimeError("Core version is already published")
    print(json.dumps({"package": "openverify", "version": version, "commit": head}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--package-directory", required=True)
    args = parser.parse_args()
    preflight(args.tag, args.evidence, args.package_directory)
