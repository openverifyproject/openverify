"""Native tests, real packages, repeat-build checks and isolated consumer installs.

Run from any directory: python tools/sdk_verify.py LANGUAGE [--skip-tests].
No publication, repository creation, credential changes, or remote Git writes.
"""
# ruff: noqa: E501 -- literal external-consumer programs

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist/sdk"
NPM = "npm.cmd" if os.name == "nt" else "npm"
MVN = "mvn.cmd" if os.name == "nt" else "mvn"
GEM = "gem.cmd" if os.name == "nt" else "gem"
COMPOSER = "composer.bat" if os.name == "nt" else "composer"


def run(*args, cwd=ROOT, env=None):
    print("+", *map(str, args), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def content_hash(path):
    """Compare every distributed file, ignoring only archive container timestamps.

    Package identity/contents are reproducible; signatures are added afterwards.
    This is intentionally NOT a claim that all native archive bytes reproduce.
    """
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            entries = [
                (n, archive.read(n)) for n in sorted(archive.namelist()) if not n.endswith("/")
            ]
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as archive:
            entries = [
                (m.name, archive.extractfile(m).read())
                for m in sorted(archive.getmembers(), key=lambda m: m.name)
                if m.isfile()
            ]
    else:
        entries = [(path.name, path.read_bytes())]
    digest = hashlib.sha256()
    for name, data in entries:
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def latest(pattern):
    paths = sorted(ROOT.glob(pattern))
    if not paths:
        raise RuntimeError("Missing package: " + pattern)
    if len(paths) != 1:
        raise RuntimeError("Ambiguous package outputs (clean stale builds): " + pattern)
    return paths[0]


def test(language):
    directory = ROOT / "sdk" / language
    commands = {
        "node": [(NPM, "ci", "--ignore-scripts"), (NPM, "test")],
        "rust": [("cargo", "test", "--locked")],
        "go": [("go", "test", "./...")],
        "jvm": [(MVN, "-B", "verify")],
        "dotnet": [("dotnet", "test", "OpenVerify.Sdk.Tests", "--configuration", "Release")],
        "ruby": [
            ("ruby", "-S", "bundle", "install"),
            ("ruby", "-S", "bundle", "exec", "ruby", "test/shared_test.rb"),
        ],
        "php": [
            (COMPOSER, "install", "--no-interaction", "--prefer-dist"),
            ("php", "vendor/phpunit/phpunit/phpunit", "tests"),
        ],
        "python": [(sys.executable, "-m", "pytest", "tests", "-q")],
    }
    env = os.environ.copy()
    if language == "python":
        env["PYTHONPATH"] = os.pathsep.join([str(directory / "src"), str(ROOT / "src")])
    for command in commands[language]:
        run(*command, cwd=directory, env=env)


def build(language):
    directory = ROOT / "sdk" / language
    destination = OUT / language
    destination.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("SOURCE_DATE_EPOCH", "1792195200")
    if language == "node":
        run(NPM, "pack", "--pack-destination", destination, cwd=directory, env=env)
        return latest("dist/sdk/node/*.tgz")
    if language == "rust":
        run("cargo", "package", "--locked", cwd=directory, env=env)
        source = latest("sdk/rust/target/package/verifyanything-[0-9]*.crate")
    elif language == "go":
        # A distributable source snapshot; public Go resolution is checked only after tagging.
        source = destination / "openverify-go.zip"
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(directory.rglob("*")):
                if path.is_file() and not any(
                    p.startswith(".") for p in path.relative_to(directory).parts
                ):
                    archive.writestr(
                        zipfile.ZipInfo(
                            path.relative_to(directory).as_posix(), (2026, 10, 17, 0, 0, 0)
                        ),
                        path.read_bytes(),
                    )
        return source
    elif language == "jvm":
        run(MVN, "-B", "package", "-DskipTests", cwd=directory, env=env)
        source = ROOT / "sdk/jvm/target" / ("verifyanything-" + version("jvm") + ".jar")
        for extra in directory.glob("target/verifyanything-" + version("jvm") + "-sources.jar"):
            shutil.copy2(extra, destination)
        for extra in directory.glob("target/verifyanything-" + version("jvm") + "-javadoc.jar"):
            shutil.copy2(extra, destination)
    elif language == "dotnet":
        run(
            "dotnet",
            "pack",
            "OpenVerify.Sdk/OpenVerify.Sdk.csproj",
            "-c",
            "Release",
            "-p:PackageOutputPath=" + str(destination),
            cwd=directory,
            env=env,
        )
        return latest("dist/sdk/dotnet/VerifyAnything.[0-9]*.nupkg")
    elif language == "ruby":
        run(
            GEM,
            "build",
            "openverify.gemspec",
            "--output",
            destination / "verifyanything.gem",
            cwd=directory,
            env=env,
        )
        return destination / "verifyanything.gem"
    elif language == "php":
        # Composer infers the mirror tag version at release; an archive uses explicit metadata.
        source = destination / "verifyanything.zip"
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(directory.rglob("*")):
                relative = path.relative_to(directory)
                if path.is_file() and relative.parts[0] in (
                    "src",
                    "resources",
                    "composer.json",
                    "LICENSE",
                    "README.md",
                    "VERSION",
                ):
                    data = path.read_bytes()
                    if relative.as_posix() == "composer.json":
                        value = json.loads(data)
                        value["version"] = (directory / "VERSION").read_text().strip()
                        data = (json.dumps(value, indent=2) + "\n").encode()
                    archive.writestr(
                        zipfile.ZipInfo(relative.as_posix(), (2026, 10, 17, 0, 0, 0)), data
                    )
        return source
    else:
        run(sys.executable, "-m", "build", "--outdir", destination, cwd=directory, env=env)
        return latest("dist/sdk/python/*.whl")
    target = destination / source.name
    shutil.copy2(source, target)
    return target


def consumer(language, artifact=None, registry=False):
    consumer_root = ROOT / ".sdk-cache/consumers"
    consumer_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="openverify-consumer-", dir=consumer_root) as temporary:
        directory = Path(temporary)
        if language == "node":
            write(directory / "package.json", '{"type":"module","private":true}')
            run(
                NPM,
                "install",
                "--ignore-scripts",
                "@openverifyproject/verifyanything@" + version(language) if registry else artifact,
                cwd=directory,
            )
            write(
                directory / "test.mjs",
                "import {parse,serialize} from '@openverifyproject/verifyanything'; const v=parse('vcp','decision','{\"protocol\":\"draft\",\"kind\":\"CONTINUE\"}'); if(JSON.parse(serialize(v)).kind!=='CONTINUE')throw Error('consumer');",
            )
            run("node", "test.mjs", cwd=directory)
        elif language == "rust":
            if registry:
                dependency = '{package="verifyanything",version="=' + version(language) + '"}'
            else:
                with tarfile.open(artifact) as archive:
                    archive.extractall(directory / "package", filter="data")
                package = next((directory / "package").iterdir()).as_posix()
                dependency = '{package="verifyanything",path=' + json.dumps(package) + "}"
            write(
                directory / "Cargo.toml",
                '[package]\nname="external-consumer"\nversion="0.0.0"\nedition="2024"\n[dependencies]\nverifyanything='
                + dependency
                + "\n",
            )
            write(
                directory / "src/main.rs",
                'fn main(){let v=verifyanything::parse("vcp","decision",r#"{"protocol":"draft","kind":"CONTINUE"}"#).unwrap();assert!(verifyanything::serialize(&v).unwrap().contains("CONTINUE"));}',
            )
            run("cargo", "run", "--quiet", cwd=directory)
        elif language == "go":
            if not registry:
                with zipfile.ZipFile(artifact) as archive:
                    archive.extractall(directory / "package")
            replacement = (
                ""
                if registry
                else "replace github.com/openverifyproject/openverify/sdk/go => "
                + json.dumps((directory / "package").as_posix())
                + "\n"
            )
            write(
                directory / "go.mod",
                "module external-consumer\n\ngo 1.24.0\nrequire github.com/openverifyproject/openverify/sdk/go v"
                + version(language)
                + "\n"
                + replacement,
            )
            write(
                directory / "main.go",
                'package main\nimport("github.com/openverifyproject/openverify/sdk/go")\nfunc main(){_,e:=openverify.Parse("vcp","decision",[]byte(`{"protocol":"draft","kind":"CONTINUE"}`));if e!=nil{panic(e)}}',
            )
            run("go", "mod", "tidy", cwd=directory)
            run("go", "run", ".", cwd=directory)
        elif language == "jvm":
            if not registry:
                run(MVN, "-B", "install", "-DskipTests", cwd=ROOT / "sdk/jvm")
            write(
                directory / "pom.xml",
                '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion><groupId>test</groupId><artifactId>consumer</artifactId><version>0.0.0</version><properties><maven.compiler.release>17</maven.compiler.release></properties><dependencies><dependency><groupId>io.github.openverifyproject</groupId><artifactId>verifyanything</artifactId><version>'
                + version("jvm")
                + "</version></dependency></dependencies><build><plugins><plugin><groupId>org.apache.maven.plugins</groupId><artifactId>maven-compiler-plugin</artifactId><version>3.14.0</version></plugin><plugin><groupId>org.codehaus.mojo</groupId><artifactId>exec-maven-plugin</artifactId><version>3.5.0</version></plugin></plugins></build></project>",
            )
            # Use Java text blocks to avoid shell or source quoting conversions.
            write(
                directory / "src/main/java/Consumer.java",
                'import org.openverify.sdk.Sdk; public class Consumer {public static void main(String[] args){var v=Sdk.parse("vcp","decision", """\n{"protocol":"draft","kind":"CONTINUE"}\n""");if(!Sdk.serialize(v).contains("CONTINUE"))throw new AssertionError();}}',
            )
            extra = ["-Dmaven.repo.local=" + str(directory / "maven-cache")] if registry else []
            run(
                MVN,
                "-B",
                *extra,
                "compile",
                "exec:java",
                "-Dexec.mainClass=Consumer",
                cwd=directory,
            )
        elif language == "dotnet":
            write(
                directory / "Consumer.csproj",
                '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework></PropertyGroup><ItemGroup><PackageReference Include="VerifyAnything" Version="'
                + version("dotnet")
                + '"/></ItemGroup></Project>',
            )
            local = (
                "" if registry else '<add key="local" value="' + artifact.parent.as_posix() + '"/>'
            )
            write(
                directory / "NuGet.Config",
                "<configuration><packageSources><clear/>"
                + local
                + '<add key="nuget" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>',
            )
            write(
                directory / "Program.cs",
                'var v=OpenVerify.Sdk.Parse("vcp","decision", """{"protocol":"draft","kind":"CONTINUE"}""");if(!OpenVerify.Sdk.Serialize(v).Contains("CONTINUE"))throw new System.Exception();',
            )
            env = os.environ.copy()
            if registry:
                env["NUGET_PACKAGES"] = str(directory / "nuget-cache")
            run("dotnet", "run", "--project", "Consumer.csproj", cwd=directory, env=env)
        elif language == "ruby":
            install = directory / "gems"
            package_args = (
                ["verifyanything", "--version", version(language)] if registry else [artifact]
            )
            run(
                GEM,
                "install",
                *package_args,
                "--install-dir",
                install,
                "--no-document",
                cwd=directory,
            )
            env = os.environ.copy()
            env["GEM_HOME"] = str(install)
            env["GEM_PATH"] = str(install)
            run(
                "ruby",
                "-e",
                "require 'verifyanything'; v=VerifyAnything.parse('vcp','decision','{\"protocol\":\"draft\",\"kind\":\"CONTINUE\"}');raise unless VerifyAnything.serialize(v).include?('CONTINUE')",
                cwd=directory,
                env=env,
            )
        elif language == "php":
            # Composer's package repository installs the exact built archive and
            # works without its optional artifact-repository PHP zip extension.
            metadata = {"name": "external/consumer", "require": {"openverify/verifyanything": version("php")}}
            if not registry:
                with zipfile.ZipFile(artifact) as archive:
                    package = json.loads(archive.read("composer.json"))
                package["dist"] = {
                    "url": artifact.as_uri(),
                    "type": "zip",
                    "shasum": hashlib.sha1(artifact.read_bytes()).hexdigest(),
                }
                metadata["repositories"] = [{"type": "package", "package": package}]
            write(directory / "composer.json", json.dumps(metadata))
            run(COMPOSER, "install", "--no-interaction", cwd=directory)
            write(
                directory / "test.php",
                '<?php require __DIR__."/vendor/autoload.php"; $v=OpenVerify\\Sdk::parse("vcp","decision",\'{"protocol":"draft","kind":"CONTINUE"}\');if(!str_contains(OpenVerify\\Sdk::serialize($v),"CONTINUE"))throw new Exception();',
            )
            run("php", "test.php", cwd=directory)
        else:
            run(sys.executable, "-m", "venv", directory / "venv")
            python = (
                directory / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            )
            run(
                python,
                "-I",
                "-m",
                "pip",
                "install",
                "verifyanything==" + version(language) if registry else artifact,
                cwd=directory,
            )
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            run(
                python,
                "-I",
                "-c",
                'import verifyanything as s; v=s.parse("vcp","decision",\'{"protocol":"draft","kind":"CONTINUE"}\'); assert "CONTINUE" in s.serialize(v)',
                cwd=directory,
                env=env,
            )


def version(language):
    import re
    import tomllib

    directory = ROOT / "sdk" / language
    if language == "node":
        return json.loads((directory / "package.json").read_text())["version"]
    if language in ("rust", "python"):
        data = tomllib.loads(
            (directory / ("Cargo.toml" if language == "rust" else "pyproject.toml")).read_text()
        )
        return data["package" if language == "rust" else "project"]["version"]
    if language == "php":
        return (directory / "VERSION").read_text().strip()
    paths = {
        "go": ("openverify.go", r'SDKVersion\s*=\s*"([^"]+)"'),
        "ruby": ("openverify.gemspec", r"s.version\s*=\s*'([^']+)'"),
        "jvm": ("pom.xml", r"<artifactId>verifyanything</artifactId><version>([^<]+)</version>"),
        "dotnet": ("OpenVerify.Sdk/OpenVerify.Sdk.csproj", r"<Version>([^<]+)</Version>"),
    }
    path, pattern = paths[language]
    return re.search(pattern, (directory / path).read_text()).group(1)


def validate_version(language):
    """Runtime identification must match this package, without coupling languages."""
    import re

    expected = version(language)
    paths = {
        "node": ("src/index.ts", r"SDK_VERSION\s*=\s*'([^']+)'"),
        "python": ("src/verifyanything/__init__.py", r'__version__\s*=\s*"([^"]+)"'),
        "go": ("openverify.go", r'SDKVersion\s*=\s*"([^"]+)"'),
        "jvm": ("src/main/java/org/openverify/sdk/Sdk.java", r'VERSION\s*=\s*"([^"]+)"'),
        "dotnet": ("OpenVerify.Sdk/Sdk.cs", r'Version\s*=\s*"([^"]+)"'),
        "ruby": ("lib/openverify.rb", r"SDK_VERSION\s*=\s*'([^']+)'"),
        "php": ("src/Sdk.php", r"VERSION\s*=\s*'([^']+)'"),
    }
    if language in paths:
        path, pattern = paths[language]
        match = re.search(pattern, (ROOT / "sdk" / language / path).read_text())
        if not match or match[1] != expected:
            raise RuntimeError("Runtime/package version mismatch for " + language)
    return expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "language", choices=["node", "rust", "go", "jvm", "dotnet", "ruby", "php", "python"]
    )
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--registry-only", action="store_true")
    args = parser.parse_args()
    validate_version(args.language)
    if args.registry_only:
        import time

        for attempt in range(12):
            try:
                consumer(args.language, registry=True)
                return
            except subprocess.CalledProcessError:
                if attempt == 11:
                    raise
                print("Waiting 15 seconds for registry propagation", flush=True)
                time.sleep(15)
    if not args.skip_tests:
        test(args.language)
    first = build(args.language)
    digest = content_hash(first)
    second = build(args.language)
    if content_hash(second) != digest:
        raise RuntimeError("Repeated package contents differ")
    consumer(args.language, second)
    manifest = json.loads((ROOT / "conformance/sdk/manifest.json").read_text())
    fixtures = [json.loads((ROOT / "conformance/sdk" / p).read_text()) for p in manifest["cases"]]
    dirty = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=normal"], cwd=ROOT, text=True
        ).strip()
    )
    result = {
        "language": args.language,
        "version": version(args.language),
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "dirty_worktree": dirty,
        "tests_run": not args.skip_tests,
        "vcp_total": sum(c["contract"] == "vcp" for c in fixtures),
        "provider_total": sum(c["contract"] == "provider" for c in fixtures),
        "consumer": "passed",
        "repeated_package_contents": "identical",
        "artifact": second.name,
        "sha256": hashlib.sha256(second.read_bytes()).hexdigest(),
        "contents_sha256": digest,
    }
    write(OUT / args.language / "verification.json", json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
