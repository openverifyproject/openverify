"""Fail-closed release preflight. Read-only network queries; no publication."""

import argparse
import datetime
import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from sdk_verify import ROOT, validate_version, version

NAMES = {
    "node": "@openverify/sdk",
    "python": "openverify-wire",
    "rust": "openverify-sdk",
    "go": "github.com/openverifyproject/openverify/sdk/go",
    "jvm": "io.github.openverifyproject:openverify-sdk",
    "dotnet": "OpenVerify.Sdk",
    "ruby": "openverify-sdk",
    "php": "openverify/sdk",
}
NAME_URLS = {
    "node": "https://registry.npmjs.org/@openverify%2fsdk",
    "python": "https://pypi.org/pypi/openverify-wire/json",
    "rust": "https://crates.io/api/v1/crates/openverify-sdk",
    "go": "https://proxy.golang.org/github.com/openverifyproject/openverify/sdk/go/@v/list",
    "jvm": "https://repo.maven.apache.org/maven2/io/github/openverifyproject/openverify-sdk/maven-metadata.xml",
    "dotnet": "https://api.nuget.org/v3-flatcontainer/openverify.sdk/index.json",
    "ruby": "https://rubygems.org/api/v1/gems/openverify-sdk.json",
    "php": "https://repo.packagist.org/p2/openverify/sdk.json",
}


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OpenVerifySDKReleasePreflight/0.1 (https://github.com/openverifyproject/openverify)"
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 404, ""
        raise


def names():
    rows = []
    for language, url in NAME_URLS.items():
        try:
            status, _ = fetch(url)
            state = (
                "listed; ownership unverified"
                if status == 200
                else "not listed; availability and ownership unreserved"
            )
        except Exception as error:
            status, state = None, "query failed: " + str(error)
        rows.append(
            {
                "language": language,
                "package": NAMES[language],
                "url": url,
                "http_status": status,
                "status": state,
            }
        )
    return {"checked_at": datetime.datetime.now(datetime.UTC).isoformat(), "packages": rows}


def unpublished(language, release_version):
    status, body = fetch(NAME_URLS[language])
    if status == 404:
        return
    data = json.loads(body) if language not in ("jvm", "go") else body
    present = {
        "node": lambda: release_version in data.get("versions", {}),
        "python": lambda: release_version in data.get("releases", {}),
        "rust": lambda: any(v["num"] == release_version for v in data.get("versions", [])),
        "dotnet": lambda: release_version.lower() in data["versions"],
        "jvm": lambda: "<version>" + release_version + "</version>" in data,
        "go": lambda: "v" + release_version in data.splitlines(),
        "ruby": lambda: any(
            v["number"] == release_version
            for v in json.loads(
                fetch("https://rubygems.org/api/v1/versions/openverify-sdk.json")[1]
            )
        ),
        "php": lambda: any(
            v.get("version_normalized") == release_version + ".0"
            or v.get("version", "").lstrip("v") == release_version
            for v in data.get("packages", {}).get("openverify/sdk", [])
        ),
    }[language]()
    if present:
        raise RuntimeError(f"{language} {release_version} is already published; refusing overwrite")


def preflight(language, tag, evidence=None):
    match = re.fullmatch(r"sdk/([a-z]+)/v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag)
    if not match or match[1] != language:
        raise RuntimeError("Tag must identify only the requested SDK and an exact X.Y.Z version")
    release_version = tag.split("/v")[-1]
    if release_version != version(language):
        raise RuntimeError("Tag/package metadata mismatch")
    validate_version(language)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tagged = subprocess.check_output(
        ["git", "rev-parse", tag + "^{commit}"], cwd=ROOT, text=True
    ).strip()
    if head != tagged:
        raise RuntimeError("Checkout is not the tagged commit")
    if evidence:
        proof = json.loads(Path(evidence).read_text())
        if (
            proof.get("dirty_worktree", True)
            or proof["commit"] != head
            or proof["language"] != language
            or proof["version"] != release_version
            or not proof["tests_run"]
            or proof["consumer"] != "passed"
            or proof["repeated_package_contents"] != "identical"
        ):
            raise RuntimeError("Applicable test/build/consumer proof does not match exact tag")
        package = Path(evidence).parent / proof["artifact"]
        import hashlib

        if hashlib.sha256(package.read_bytes()).hexdigest() != proof["sha256"]:
            raise RuntimeError("Package artifact checksum mismatch")
    # Go publication is the Git tag itself, which already exists at this point.
    # Exact tagged commit identity is checked above; module resolution follows.
    if language != "go":
        unpublished(language, release_version)
    print(
        json.dumps(
            {
                "language": language,
                "package": NAMES[language],
                "version": release_version,
                "commit": head,
                "unpublished": True,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["names", "preflight"])
    parser.add_argument("--language", choices=list(NAMES))
    parser.add_argument("--tag")
    parser.add_argument("--evidence")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.command == "names":
        result = names()
        text = json.dumps(result, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8", newline="\n")
        print(text)
    else:
        if not args.language or not args.tag:
            parser.error("preflight requires --language and --tag")
        preflight(args.language, args.tag, args.evidence)
