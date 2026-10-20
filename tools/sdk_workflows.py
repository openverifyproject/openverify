"""Maintain independent, tag-filtered CI/release workflows from one template."""
# ruff: noqa: E501 -- literal workflow YAML and embedded shell commands

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ["node", "python", "rust", "go", "jvm", "dotnet", "ruby", "php"]
# Resolved from the upstream refs on 2026-10-18 UTC. Review updates explicitly.
# crates-io-auth-action corrected against upstream v1.0.5 on 2026-10-20 UTC.
ACTION_REVISIONS = {
    "rust-lang/crates-io-auth-action@v1.0.5": "c6f97d42243bad5fab37ca0427f495c86d5b1a18",
    "NuGet/login@v1": "8d196754b4036150537f80ac539e15c2f1028841",
    "actions/checkout@v4": "11d5960a326750d5838078e36cf38b85af677262",
    "actions/setup-python@v5": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "actions/setup-node@v4": "49933ea5288caeca8642d1e84afbd3f7d6820020",
    "dtolnay/rust-toolchain@stable": "b725eda525362e7cf34af9a7243cac1e3f01a7ec",
    "actions/setup-go@v5": "40f1582b2485089dde7abd97c1529aa768e1baff",
    "actions/setup-java@v4": "cf277c60eb25467037889841efdb72551f06f6c3",
    "actions/setup-dotnet@v4": "67a3573c9a986a3f9c594539f4ab511d57bb3ce9",
    "ruby/setup-ruby@v1": "651ff0d62c5c79bed6d53ec518387aae20e72c1a",
    "shivammathur/setup-php@v2": "eb7c497e18156a6bbabfef1d3a82760b9eda3962",
    "actions/upload-artifact@v4": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/download-artifact@v4": "d3f86a106a0bac45b974a628896c90dbdf5c8093",
    "pypa/gh-action-pypi-publish@release/v1": "dc37677b2e1c63e2034f94d8a5b11f265b73ba33",
}


def pin_actions(text):
    for reference, revision in ACTION_REVISIONS.items():
        repository = reference.split("@")[0]
        text = text.replace(
            "uses: " + reference + "\n",
            "uses: " + repository + "@" + revision + " # " + reference + "\n",
        )
    return text


VERIFY = """name: SDK verification
on:
  workflow_call:
    inputs:
      language:
        type: string
        required: true
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: python -m pip install build pytest jsonschema pydantic
      - run: python -m pytest sdk/tests -q
      - uses: actions/setup-node@v4
        if: inputs.language == 'node'
        with:
          node-version: '24'
      - uses: dtolnay/rust-toolchain@stable
        if: inputs.language == 'rust'
      - uses: actions/setup-go@v5
        if: inputs.language == 'go'
        with:
          go-version: '1.24.x'
          cache-dependency-path: sdk/go/go.sum
      - uses: actions/setup-java@v4
        if: inputs.language == 'jvm'
        with:
          distribution: temurin
          java-version: '17'
      - uses: actions/setup-dotnet@v4
        if: inputs.language == 'dotnet'
        with:
          dotnet-version: '8.0.x'
      - uses: ruby/setup-ruby@v1
        if: inputs.language == 'ruby'
        with:
          ruby-version: '3.4'
      - uses: shivammathur/setup-php@v2
        if: inputs.language == 'php'
        with:
          php-version: '8.3'
          tools: composer:v2
          extensions: mbstring, dom, xml, xmlwriter
      - name: Shared fixtures, native tests, repeat build and clean consumer
        env:
          SDK_LANGUAGE: ${{ inputs.language }}
        run: python tools/sdk_verify.py "$SDK_LANGUAGE"
      - uses: actions/upload-artifact@v4
        with:
          name: sdk-${{ inputs.language }}-${{ github.sha }}
          path: dist/sdk/${{ inputs.language }}/
          if-no-files-found: error
"""

SETUP = {
    "node": """      - uses: actions/setup-node@v4
        with:
          node-version: '24'
          registry-url: https://registry.npmjs.org
      - run: npm install --global npm@latest
""",
    "python": "",
    "rust": """      - uses: dtolnay/rust-toolchain@stable
      - name: Exchange GitHub OIDC for a short-lived crates.io token
        if: vars.REGISTRY_AUTH_MODE != 'token'
        uses: rust-lang/crates-io-auth-action@v1.0.5
        id: rustauth
""",
    "go": """      - uses: actions/setup-go@v5
        with:
          go-version: '1.24.x'
""",
    "jvm": """      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
          server-id: central
          server-username: CENTRAL_USERNAME
          server-password: CENTRAL_PASSWORD
          gpg-private-key: ${{ secrets.MAVEN_GPG_PRIVATE_KEY }}
          gpg-passphrase: MAVEN_GPG_PASSPHRASE
""",
    "dotnet": """      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      - name: Exchange GitHub OIDC for a short-lived NuGet key
        uses: NuGet/login@v1
        id: nugetauth
        with:
          user: ${{ vars.NUGET_USER }}
""",
    "ruby": """      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.4'
""",
    "php": """      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
          tools: composer:v2
""",
}
PUBLISH = {
    "node": """      - name: Publish verified scoped tarball using npm OIDC
        run: npm publish dist/sdk/node/*.tgz --access public --provenance
""",
    "python": """      - name: Publish verified distributions using PyPI OIDC
        run: mkdir -p dist/pypi && cp dist/sdk/python/*.whl dist/sdk/python/*.tar.gz dist/pypi/
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist/pypi/
          skip-existing: false
""",
    "rust": """      - name: Publish the verified crate contents
        env:
          CARGO_REGISTRY_TOKEN: ${{ steps.rustauth.outputs.token || secrets.CARGO_REGISTRY_TOKEN }}
        run: |
          mkdir -p .sdk-release/crate
          tar -xzf dist/sdk/rust/*.crate -C .sdk-release/crate
          cd .sdk-release/crate/verifyanything-[0-9]*
          cargo publish --locked
""",
    "go": """      - name: Verify public nested-module resolution from the pushed tag
        env:
          RELEASE_TAG: ${{ github.ref_name }}
          GOPROXY: https://proxy.golang.org,direct
          GOSUMDB: sum.golang.org
        run: |
          VERSION="${RELEASE_TAG#sdk/go/}"
          mkdir -p "$RUNNER_TEMP/go-registry-consumer"
          cd "$RUNNER_TEMP/go-registry-consumer"
          go mod init registry-consumer
          go get "github.com/openverifyproject/openverify/sdk/go@$VERSION"
          printf '%s\\n' 'package main' 'import sdk "github.com/openverifyproject/openverify/sdk/go"' 'func main(){if sdk.SDKVersion==""{panic("missing version")}}' > main.go
          go run .
""",
    "jvm": """      - name: Sign and publish through current Central Portal
        env:
          CENTRAL_USERNAME: ${{ secrets.CENTRAL_USERNAME }}
          CENTRAL_PASSWORD: ${{ secrets.CENTRAL_PASSWORD }}
          MAVEN_GPG_PASSPHRASE: ${{ secrets.MAVEN_GPG_PASSPHRASE }}
        run: |
          mvn -B -f sdk/jvm/pom.xml -Prelease -Dgpg.passphrase="$MAVEN_GPG_PASSPHRASE" deploy
""",
    "dotnet": """      - name: Publish verified NuGet archive
        env:
          NUGET_API_KEY: ${{ steps.nugetauth.outputs.NUGET_API_KEY }}
        run: dotnet nuget push dist/sdk/dotnet/*.nupkg --api-key "$NUGET_API_KEY" --source https://api.nuget.org/v3/index.json
""",
    "ruby": """      - name: Exchange GitHub OIDC for short-lived RubyGems credential
        uses: rubygems/configure-rubygems-credentials@f5a32efa94076b80b28556b2d3b04cb3707b6df1
      - name: Publish verified gem
        run: gem push dist/sdk/ruby/*.gem
""",
    "php": """      - name: Mirror the package subtree and translate its tag
        env:
          GH_TOKEN: ${{ secrets.SDK_PHP_MIRROR_TOKEN }}
          SDK_PHP_MIRROR: ${{ vars.SDK_PHP_MIRROR }}
        run: |
          gh auth setup-git
          python tools/sdk_mirror.py
      - name: Register or update the mirrored package on Packagist
        env:
          PACKAGIST_USERNAME: ${{ vars.PACKAGIST_USERNAME }}
          PACKAGIST_API_TOKEN: ${{ secrets.PACKAGIST_API_TOKEN }}
          SDK_PHP_MIRROR: ${{ vars.SDK_PHP_MIRROR }}
        run: python tools/sdk_packagist.py
""",
}


def main():
    directory = ROOT / ".github/workflows"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "sdk-verify.yml").write_text(pin_actions(VERIFY), encoding="utf-8", newline="\n")
    ci = """name: SDK CI
on:
  pull_request:
  push:
    branches: ['main', 'release/openverify-v0.1']
  workflow_dispatch:
permissions:
  contents: read
jobs:
  sdk:
    name: SDK (${{ matrix.language }})
    strategy:
      fail-fast: false
      matrix:
        language: [node, python, rust, go, jvm, dotnet, ruby, php]
    uses: ./.github/workflows/sdk-verify.yml
    with:
      language: ${{ matrix.language }}
"""
    (directory / "sdk-ci.yml").write_text(pin_actions(ci), encoding="utf-8", newline="\n")
    for language in LANGUAGES:
        oidc = "      id-token: write\n" if language in ("node", "python", "ruby", "rust", "dotnet") else ""
        template = f"""name: Release {language} SDK
on:
  push:
    tags: ['sdk/{language}/v*']
permissions:
  contents: read
concurrency:
  group: sdk-{language}-release
  cancel-in-progress: false
jobs:
  verify:
    uses: ./.github/workflows/sdk-verify.yml
    with:
      language: {language}
  publish:
    needs: verify
    runs-on: ubuntu-latest
    environment: sdk-{language}
    permissions:
      contents: read
{oidc.rstrip()}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - uses: actions/download-artifact@v4
        with:
          name: sdk-{language}-${{{{ github.sha }}}}
          path: dist/sdk/{language}/
      - name: Check exact tag, test evidence, checksum and unpublished version
        env:
          RELEASE_TAG: ${{{{ github.ref_name }}}}
        run: |
          python tools/sdk_release.py preflight --language {language} --tag "$RELEASE_TAG" --evidence dist/sdk/{language}/verification.json
{SETUP[language]}{PUBLISH[language]}      - name: Verify registry availability and a fresh external installation
        env:
          SDK_LANGUAGE: {language}
        run: python tools/sdk_verify.py "$SDK_LANGUAGE" --registry-only
"""
        (directory / f"sdk-release-{language}.yml").write_text(
            pin_actions(template), encoding="utf-8", newline="\n"
        )


if __name__ == "__main__":
    main()
