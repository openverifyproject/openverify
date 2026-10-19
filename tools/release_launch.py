"""Plan or trigger unpublished versions from green, clean, merged main. No builds."""

import argparse
import json
import subprocess
import time
import tomllib

from release_github_setup import REPO, api
from sdk_release import fetch, is_published
from sdk_verify import ROOT, validate_version

ORDER = ["node", "rust", "ruby", "go", "python", "dotnet", "jvm", "php", "core"]


def plan():
    rows = []
    for product in ORDER:
        release_version = (
            tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
            if product == "core" else validate_version(product)
        )
        if product == "core":
            status, body = fetch("https://pypi.org/pypi/openverify/json")
            published = status == 200 and release_version in json.loads(body).get("releases", {})
        else:
            published = is_published(product, release_version)
        prefix = "core/python" if product == "core" else "sdk/" + product
        rows.append({"product": product, "version": release_version,
                     "tag": prefix + "/v" + release_version,
                     "action": "SKIP_PUBLISHED" if published else "PUSH_TAG"})
    return rows


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def green(sha):
    for workflow in ("project-ci.yml", "sdk-ci.yml"):
        runs = api(f"repos/{REPO}/actions/workflows/{workflow}/runs?head_sha={sha}&event=push")
        current = runs["workflow_runs"]
        if not current or current[0]["status"] != "completed":
            return False
        if current[0]["conclusion"] != "success":
            raise RuntimeError("Merged main CI failed: " + workflow)
    return True


def require_credentials(rows):
    requirements = {
        "rust": (["CARGO_REGISTRY_TOKEN"], []),
        "dotnet": ([], ["NUGET_USER"]),
        "jvm": (["CENTRAL_USERNAME", "CENTRAL_PASSWORD", "MAVEN_GPG_PRIVATE_KEY",
                 "MAVEN_GPG_PASSPHRASE"], []),
        "php": (["SDK_PHP_MIRROR_TOKEN", "PACKAGIST_API_TOKEN"], ["PACKAGIST_USERNAME"]),
    }
    for row in rows:
        if row["action"] != "PUSH_TAG" or row["product"] not in requirements:
            continue
        env = "sdk-" + row["product"]
        base = f"repos/{REPO}/environments/{env}"
        secret_names = {s["name"] for s in api(base + "/secrets")["secrets"]}
        variables = {v["name"]: v["value"] for v in api(base + "/variables")["variables"]}
        secrets, names = requirements[row["product"]]
        if row["product"] == "rust" and variables.get("REGISTRY_AUTH_MODE") != "token":
            secrets = []
        if any(s not in secret_names for s in secrets) or any(not variables.get(n) for n in names):
            raise RuntimeError("Missing secure authorization inputs for " + env)


def launch(wait=False):
    if git("status", "--porcelain"):
        raise RuntimeError("Release source must be clean")
    git("fetch", "origin")
    sha = git("rev-parse", "HEAD")
    if sha != git("rev-parse", "origin/main"):
        raise RuntimeError("Release command must run from exact latest origin/main")
    deadline = time.monotonic() + 3600
    while not green(sha):
        if not wait or time.monotonic() >= deadline:
            raise RuntimeError("Merged main must pass both CI workflows before tagging")
        print("Waiting for existing main CI; no build or publication started", flush=True)
        time.sleep(15)
    rows = plan()  # Registry state is checked immediately before any tag writes.
    require_credentials(rows)
    for row in rows:
        if row["action"] == "SKIP_PUBLISHED":
            print(row["product"], row["version"], "already published; skipped", flush=True)
            continue
        tag = row["tag"]
        remote = git("ls-remote", "origin", "refs/tags/" + tag, "refs/tags/" + tag + "^{}")
        if remote:
            refs = dict(line.split()[::-1] for line in remote.splitlines())
            commit = refs.get("refs/tags/" + tag + "^{}", refs.get("refs/tags/" + tag))
            if commit != sha:
                raise RuntimeError("Existing tag points elsewhere; refusing rewrite: " + tag)
            print(tag, "already triggered; no duplicate push", flush=True)
            continue
        local = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", "refs/tags/" + tag], cwd=ROOT,
        )
        if local.returncode == 0:
            if git("rev-parse", tag + "^{commit}") != sha:
                raise RuntimeError("Local tag conflicts: " + tag)
        else:
            git("tag", "-a", tag, sha, "-m", tag)
        # One tag per push: GitHub suppresses tag workflows for pushes with >3 tags.
        git("push", "--no-follow-tags", "origin", "refs/tags/" + tag)
        print("Triggered", tag, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--wait-for-ci", action="store_true")
    args = parser.parse_args()
    if args.push:
        launch(args.wait_for_ci)
    else:
        print(json.dumps(plan(), indent=2))
