"""Automated PHP subtree mirror. Only run inside an approved release environment.

No remote is created. Existing mismatched tags, unrelated histories or names fail.
"""

import json
import os
import re
import subprocess

from sdk_verify import ROOT, version


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    tag = os.environ["GITHUB_REF_NAME"]
    if tag != "sdk/php/v" + version("php") or not re.fullmatch(
        r"sdk/php/v[0-9]+\.[0-9]+\.[0-9]+", tag
    ):
        raise RuntimeError("Invalid PHP release identity")
    repository = os.environ["SDK_PHP_MIRROR"]
    if (
        not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
        or repository == "openverifyproject/openverify"
    ):
        raise RuntimeError("Dedicated GitHub mirror owner/repository required")
    remote = "https://github.com/" + repository + ".git"
    split = git("subtree", "split", "--prefix=sdk/php", tag)
    standard_tag = "v" + version("php")
    advertised = dict(
        (line.split()[1], line.split()[0])
        for line in git(
            "ls-remote", remote, "refs/heads/main", "refs/tags/" + standard_tag
        ).splitlines()
        if line
    )
    existing = advertised.get("refs/tags/" + standard_tag)
    if existing:
        if existing != split:
            raise RuntimeError("Mirror tag already exists with different content/history")
        print("Mirror already synchronized:", standard_tag, split)
        return
    branch = advertised.get("refs/heads/main")
    refs = [split + ":refs/tags/" + standard_tag]
    if branch:
        git("fetch", "--no-tags", remote, "refs/heads/main")
        document = json.loads(git("show", branch + ":composer.json"))
        if document.get("name") != "openverify/sdk":
            raise RuntimeError("Mirror package name mismatch")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", branch, split], cwd=ROOT
        ).returncode
        if ancestor == 0:
            refs.insert(0, split + ":refs/heads/main")
        elif (
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", split, branch], cwd=ROOT
            ).returncode
            != 0
        ):
            raise RuntimeError("Unrelated or rewritten mirror history; refusing update")
    else:
        if git("ls-remote", remote):
            raise RuntimeError("Nonempty mirror has no expected main branch")
        refs.insert(0, split + ":refs/heads/main")
    # Atomic and never forced. Credentials are supplied by the protected workflow.
    subprocess.run(["git", "push", "--atomic", remote, *refs], cwd=ROOT, check=True)
    print("Synchronized", repository, standard_tag, split)


if __name__ == "__main__":
    main()
