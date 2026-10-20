"""Build and install the Python product and SDK independently and in both orders.

Uses only local wheels for the products; dependencies may come from PyPI.
Does not publish, change accounts, or use source imports for consumer checks.
"""
# pyright: basic

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def run(*command, cwd=ROOT):
    print("+", *map(str, command), flush=True)
    subprocess.run(list(map(str, command)), cwd=cwd, check=True)


def build(directory, output):
    run(sys.executable, "-m", "build", "--outdir", output, cwd=directory)
    wheels = list(output.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected one wheel in {output}: {wheels}")
    return wheels[0]


def verify(core, sdk, output):
    core, sdk = core.resolve(), sdk.resolve()
    wheelhouse = core.parent
    components = [
        next(wheelhouse.glob(name + "-*.whl"))
        for name in ("openverify_relay", "openverify_code", "openverify_english")
    ]
    payloads = []
    for path, namespace in [
        (core, None),
        (sdk, "verifyanything"),
        (components[0], "openverify"),
        (components[1], "openverify_code"),
        (components[2], "openverify_english"),
    ]:
        with ZipFile(path) as archive:
            files = set(archive.namelist())
            if namespace is not None:
                assert f"{namespace}/__init__.py" in files, (path, namespace)
            payloads.append({n for n in files if ".dist-info/" not in n})
            if namespace == "verifyanything":
                assert not any(n.startswith("openverify/") for n in files)
                assert not any(n.endswith("entry_points.txt") for n in files)
    assert all(
        not left & right for i, left in enumerate(payloads) for right in payloads[i + 1 :]
    ), "Products overwrite the same package files"
    cache = ROOT / ".sdk-cache/python-products"
    cache.mkdir(parents=True, exist_ok=True)
    results = []
    for scenario, wheels in [
        ("sdk-alone", [sdk]),
        ("core-alone", [core]),
        ("sdk-then-core", [sdk, core]),
        ("core-then-sdk", [core, sdk]),
    ]:
        with tempfile.TemporaryDirectory(prefix=scenario + "-", dir=cache) as temporary:
            destination = Path(temporary)
            venv.EnvBuilder(with_pip=True).create(destination)
            python = destination / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            for wheel in wheels:
                targets = [wheel, sdk, *components] if wheel == core else [wheel]
                run(
                    python,
                    "-I",
                    "-m",
                    "pip",
                    "install",
                    "--find-links",
                    wheelhouse,
                    *targets,
                    cwd=destination,
                )
            run(python, "-I", "-m", "pip", "check", cwd=destination)
            has_core = core in wheels
            has_sdk = True  # The product depends on Relay, which depends on verifyanything.
            script = (
                "import importlib.util, importlib.metadata\n"
                f"assert (importlib.util.find_spec('verifyanything') is not None) == {has_sdk}\n"
                f"assert (importlib.util.find_spec('openverify') is not None) == {has_core}\n"
            )
            if has_sdk:
                script += (
                    "import verifyanything as s\n"
                    "assert s.__version__ == importlib.metadata.version('verifyanything')\n"
                    'v=s.parse(\'vcp\',\'decision\',\'{"protocol":"draft","kind":"CONTINUE"}\')\n'
                    "assert s.serialize(v) and v.data['kind']=='CONTINUE'\n"
                )
            if has_core:
                script += (
                    "import openverify\n"
                    "from openverify import Graph, Relay\n"
                    "assert callable(Graph) and callable(Relay)\n"
                    "import openverify_code, openverify_english\n"
                )
            run(python, "-I", "-c", script, cwd=destination)
            if has_core:
                executable = destination / (
                    "Scripts/openverify.exe" if os.name == "nt" else "bin/openverify"
                )
                run(executable, "rules", "list", cwd=destination)
                sample = destination / "sample"
                sample.mkdir()
                (sample / "clean.py").write_text("value = 1\n", encoding="utf-8")
                run(executable, "code", "check", "--root", sample, "--json", cwd=destination)
                run(
                    python,
                    "-I",
                    ROOT / "conformance/golden-v4/release-review-v0.1/consumer_check.py",
                    cwd=destination,
                )
            results.append({"scenario": scenario, "status": "PASS"})
    report = {
        "status": "PASS",
        "scenarios": results,
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip(),
        "dirty_worktree": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=ROOT,
                text=True,
            ).strip()
        ),
        "wheels": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (core, sdk, *components)
        },
        "artifacts": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [core, sdk, *components, *core.parent.glob("*.tar.gz")]
        },
        "scope": (
            "Local wheel isolation, installation order, API, resources and CLI; "
            "not universal conformance"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-wheel", type=Path)
    parser.add_argument("--sdk-wheel", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/python-products/verification.json",
    )
    args = parser.parse_args()
    core = args.core_wheel or build(ROOT, ROOT / "dist/core-python")
    sdk = args.sdk_wheel or build(ROOT / "sdk/python", ROOT / "dist/sdk/python")
    verify(core, sdk, args.output)


if __name__ == "__main__":
    main()
