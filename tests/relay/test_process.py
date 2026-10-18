"""Physical process bounds and descendant cleanup on the running platform."""

import asyncio
import os
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from openverify.relay.adapters.process import capture


def test_capture_preserves_selected_virtualenv(tmp_path: Path) -> None:
    environment = tmp_path / "venv"
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    site_packages = subprocess.check_output(
        [str(python), "-I", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        text=True,
    ).strip()
    (Path(site_packages) / "openverify_venv_probe.py").write_text(
        "VALUE = 'venv-only'\n", encoding="utf-8"
    )
    result = asyncio.run(
        capture(
            [
                str(python),
                "-I",
                "-c",
                "import sys, openverify_venv_probe; "
                "print(sys.prefix); print(openverify_venv_probe.VALUE)",
            ],
            str(tmp_path),
        )
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [str(environment), "venv-only"]


def test_capture_bounds_and_environment(tmp_path: Path) -> None:
    async def scenario() -> None:
        result = await capture(
            [sys.executable, "-c", "import os; print(os.getenv('RELAY_EXPLICIT'))"],
            str(tmp_path),
            env={"RELAY_EXPLICIT": "visible"},
        )
        assert result.stdout.strip() == "visible"
        with pytest.raises(ValueError, match="exceeded"):
            await capture([sys.executable, "-c", "print('x'*10000)"], str(tmp_path), limit=100)

    asyncio.run(scenario())


def test_timeout_kills_descendants_after_tool_parent_exits(tmp_path: Path) -> None:
    async def scenario() -> None:
        started = tmp_path / "started"
        leaked = tmp_path / "leaked"
        child = (
            "from pathlib import Path; import sys,time; "
            "Path(sys.argv[1]).write_text('started'); time.sleep(3); "
            "Path(sys.argv[2]).write_text('leaked')"
        )
        parent = (
            "import subprocess,sys,time; from pathlib import Path; "
            "subprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2],sys.argv[3]]); "
            "deadline=time.monotonic()+1; "
            "exec('while not Path(sys.argv[2]).exists() and time.monotonic()<deadline: "
            "time.sleep(.01)')"
        )
        try:
            await capture(
                [sys.executable, "-c", parent, child, str(started), str(leaked)],
                str(tmp_path),
                timeout=1.5,
            )
        except TimeoutError:
            pass  # POSIX keeps the process group alive until the runner terminates it.
        assert started.exists(), (
            "Child must actually start for the orphan regression to be meaningful"
        )
        await asyncio.sleep(3)
        assert not leaked.exists()

    asyncio.run(scenario())
