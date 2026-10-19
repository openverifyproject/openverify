"""Register/update the approved PHP mirror. Runs only in its tagged publisher job."""

import json
import os
import urllib.error
import urllib.request

from sdk_release import fetch
from sdk_verify import version


def post(endpoint, repository, username, token):
    request = urllib.request.Request(
        "https://packagist.org/api/" + endpoint,
        data=json.dumps({"repository": repository}).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + username + ":" + token,
            "User-Agent": "OpenVerifyRelease/0.1 https://github.com/openverifyproject/openverify",
        }, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Packagist {endpoint} rejected (HTTP {error.code})") from None
    if result.get("status") != "success":
        raise RuntimeError("Packagist rejected " + endpoint)


def main():
    if os.environ.get("GITHUB_REF_NAME") != "sdk/php/v" + version("php"):
        raise RuntimeError("Packagist registration requires the exact PHP release tag")
    mirror = os.environ["SDK_PHP_MIRROR"]
    if mirror != "openverifyproject/verifyanything-php":
        raise RuntimeError("Unapproved PHP distribution mirror")
    username, token = os.environ["PACKAGIST_USERNAME"], os.environ["PACKAGIST_API_TOKEN"]
    if not username or not token:
        raise RuntimeError("Packagist account authorization is missing")
    repository = "https://github.com/" + mirror
    status, body = fetch("https://packagist.org/packages/openverify/verifyanything.json")
    if status == 404:
        post("create-package", repository, username, token)
    elif json.loads(body)["package"]["repository"].removesuffix(".git") != repository:
        raise RuntimeError("Packagist name belongs to another source; refusing change")
    post("update-package", repository, username, token)
    print("Packagist mirror registration/update accepted; registry consumer verifies version next")


if __name__ == "__main__":
    main()
