"""Maintain independent, tag-filtered CI/release workflows from one template."""
# ruff: noqa: E501 -- literal workflow YAML and embedded shell commands

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ["node", "python", "rust", "go", "jvm", "dotnet", "ruby", "php"]
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
    "rust": "      - uses: dtolnay/rust-toolchain@stable\n",
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
    "node": """      - name: Publish verified tarball using npm OIDC
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
          CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_REGISTRY_TOKEN }}
        run: |
          mkdir -p .sdk-release/crate
          tar -xzf dist/sdk/rust/*.crate -C .sdk-release/crate
          cd .sdk-release/crate/openverify-sdk-*
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
          NUGET_API_KEY: ${{ secrets.NUGET_API_KEY }}
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
""",
}


def main():
    directory = ROOT / ".github/workflows"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "sdk-verify.yml").write_text(VERIFY, encoding="utf-8", newline="\n")
    ci = """name: SDK CI
on:
  pull_request:
    paths: ['sdk/**', 'conformance/sdk/**', 'tools/sdk_*.py', '.github/workflows/sdk-*.yml']
  push:
    branches: ['main', 'feat/language-sdks']
    paths: ['sdk/**', 'conformance/sdk/**', 'tools/sdk_*.py', '.github/workflows/sdk-*.yml']
  workflow_dispatch:
permissions:
  contents: read
jobs:
  sdk:
    strategy:
      fail-fast: false
      matrix:
        language: [node, python, rust, go, jvm, dotnet, ruby, php]
    uses: ./.github/workflows/sdk-verify.yml
    with:
      language: ${{ matrix.language }}
"""
    (directory / "sdk-ci.yml").write_text(ci, encoding="utf-8", newline="\n")
    for language in LANGUAGES:
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
      id-token: write
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
          REGISTRY_OWNERSHIP_APPROVED: ${{{{ vars.REGISTRY_OWNERSHIP_APPROVED }}}}
        run: |
          test "$REGISTRY_OWNERSHIP_APPROVED" = true
          python tools/sdk_release.py preflight --language {language} --tag "$RELEASE_TAG" --evidence dist/sdk/{language}/verification.json
{SETUP[language]}{PUBLISH[language]}      - name: Verify registry availability and a fresh external installation
        env:
          SDK_LANGUAGE: {language}
        run: python tools/sdk_verify.py "$SDK_LANGUAGE" --registry-only
"""
        (directory / f"sdk-release-{language}.yml").write_text(
            template, encoding="utf-8", newline="\n"
        )


if __name__ == "__main__":
    main()
