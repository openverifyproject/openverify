"""Idempotent GitHub release setup; creates no release tags or packages."""

import argparse
import json
import os
import shutil
import subprocess

from sdk_workflows import LANGUAGES

REPO = "openverifyproject/openverify"
MIRROR = "openverifyproject/verifyanything-php"
ENVIRONMENTS = {f"sdk-{language}": f"sdk/{language}/v*" for language in LANGUAGES}
ENVIRONMENTS["core-python"] = "core/python/v*"
for product in ("relay", "code", "english"):
    ENVIRONMENTS[f"core-{product}"] = f"core/{product}/v*"


def gh(*args, body=None):
    executable = os.environ.get("GH_CLI") or shutil.which("gh")
    if not executable:
        executable = r"C:\Program Files\GitHub CLI\gh.exe"
    result = subprocess.run(
        [executable, *args], input=json.dumps(body) if body is not None else None,
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


def api(path, method="GET", body=None):
    return gh("api", "-X", method, path, *(["--input", "-"] if body is not None else []), body=body)


def setup():
    base = f"repos/{REPO}"
    existing = {e["name"] for e in api(base + "/environments")["environments"]}
    for name, pattern in ENVIRONMENTS.items():
        path = base + "/environments/" + name
        if name not in existing:
            api(path, "PUT", {"deployment_branch_policy": {
                "protected_branches": False, "custom_branch_policies": True,
            }})
        else:
            state = api(path)
            if state.get("deployment_branch_policy") != {
                "protected_branches": False, "custom_branch_policies": True,
            }:
                raise RuntimeError(f"Review existing broader environment policy: {name}")
        policies = api(path + "/deployment-branch-policies")["branch_policies"]
        if any(p["name"] != pattern or p["type"] != "tag" for p in policies):
            raise RuntimeError(f"Unexpected deployment policy in {name}; preserve for review")
        if not policies:
            api(path + "/deployment-branch-policies", "POST", {"name": pattern, "type": "tag"})
        variables = {"RELEASE_TAG_PATTERN": pattern}
        if name == "sdk-rust":
            variables["REGISTRY_AUTH_MODE"] = "token"  # First crate needs bootstrap authorization.
        if name == "sdk-php":
            variables["SDK_PHP_MIRROR"] = MIRROR
        current = {v["name"]: v["value"] for v in api(path + "/variables")["variables"]}
        for key, value in variables.items():
            if key not in current:
                api(path + "/variables", "POST", {"name": key, "value": value})
            elif current[key] != value and key != "REGISTRY_AUTH_MODE":
                raise RuntimeError(f"Existing variable differs: {name}/{key}")
        print("Configured:", name, pattern)
    ruleset = {
        "name": "release-tag-integrity", "target": "tag", "enforcement": "active",
        "conditions": {"ref_name": {
            "include": ["refs/tags/sdk/*/v*", "refs/tags/core/*/v*"], "exclude": [],
        }},
        "bypass_actors": [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}],
        "rules": [{"type": t} for t in ("creation", "update", "deletion")],
    }
    matching = [r for r in api(base + "/rulesets") if r["name"] == ruleset["name"]]
    api(base + "/rulesets" + ("/" + str(matching[0]["id"]) if matching else ""),
        "PUT" if matching else "POST", ruleset)
    pages = gh("api", "--paginate", "--slurp", "orgs/openverifyproject/repos")
    repositories = [repository for page in pages for repository in page]
    if not any(r["full_name"] == MIRROR for r in repositories):
        api("orgs/openverifyproject/repos", "POST", {
            "name": "verifyanything-php", "private": False, "auto_init": False,
            "description": (
                "Distribution-only PHP SDK mirror; source: openverifyproject/openverify"
            ),
            "has_issues": False, "has_projects": False, "has_wiki": False,
        })
    print("Configured: admin-only release-tag creation/update/deletion bypass; empty PHP mirror")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", required=True)
    parser.parse_args()
    setup()
