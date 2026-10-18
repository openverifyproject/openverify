"""Exercise the actual consumer workflow with misleading source metadata."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path
from zipfile import ZipFile


def test_consumer_workflow_installs_wheel_despite_source_egg_info(tmp_path):
    workflow = (
        Path(__file__).resolve().parents[2] / ".github/workflows/project-ci.yml"
    ).read_text(encoding="utf-8")
    step = workflow.split(
        "      - name: Install wheel into a fresh consumer and exercise shipped API/CLI\n",
        1,
    )[1].split("      - uses:", 1)[0]
    script = textwrap.dedent(step.split("        run: |\n", 1)[1])

    # This is what setuptools leaves behind after the preceding CI build.
    metadata = "Metadata-Version: 2.1\nName: openverify\nVersion: 0.1.0\n"
    source = tmp_path / "src"
    egg_info = source / "openverify.egg-info"
    egg_info.mkdir(parents=True)
    (egg_info / "PKG-INFO").write_text(metadata, encoding="utf-8")
    environment = dict(os.environ, PYTHONPATH="src", PIP_NO_INDEX="1")

    # A real dependency-free wheel makes the regression offline and independent
    # of the installed project. The consumer must find its installed payload.
    dist = tmp_path / "dist/python"
    dist.mkdir(parents=True)
    with ZipFile(dist / "openverify-0.1.0-py3-none-any.whl", "w") as wheel:
        files = {
            "openverify/__init__.py": "INSTALLED_PAYLOAD = 'from-wheel'\n",
            "openverify-0.1.0.dist-info/METADATA": metadata,
            "openverify-0.1.0.dist-info/WHEEL": (
                "Wheel-Version: 1.0\nGenerator: regression\n"
                "Root-Is-Purelib: true\nTag: py3-none-any\n"
            ),
        }
        files["openverify-0.1.0.dist-info/RECORD"] = "".join(
            f"{name},,\n" for name in [*files, "openverify-0.1.0.dist-info/RECORD"]
        )
        for name, contents in files.items():
            wheel.writestr(name, contents)

    consumer = tmp_path / "conformance/golden-v4/release-review-v0.1/consumer_check.py"
    consumer.parent.mkdir(parents=True)
    consumer.write_text(
        "from pathlib import Path\n"
        "import importlib.metadata, openverify\n"
        "assert openverify.INSTALLED_PAYLOAD == 'from-wheel'\n"
        "assert 'site-packages' in Path(openverify.__file__).parts\n"
        "assert importlib.metadata.version('openverify') == '0.1.0'\n",
        encoding="utf-8",
    )
    # Establish that the inherited environment really exposes the false install.
    probe = subprocess.run(
        [
            sys.executable, "-c",
            "import importlib.metadata; print(importlib.metadata.version('openverify'))",
        ],
        cwd=tmp_path, env=environment, capture_output=True, text=True, check=True,
    )
    assert probe.stdout.strip() == "0.1.0"
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=tmp_path, env=environment, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Successfully installed openverify-0.1.0" in result.stdout
