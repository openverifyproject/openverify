"""Bounded process primitives shared by transports and trusted tool providers."""

import asyncio
import os
import shutil
import signal
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Captured:
    argv: tuple[str, ...]
    cwd: str
    returncode: int
    stdout: str
    stderr: str


async def spawn(
    argv: Sequence[str], cwd: str, env: dict[str, str] | None = None
) -> asyncio.subprocess.Process:
    if not argv or not os.path.isabs(cwd):
        raise ValueError("Nonempty argv and absolute cwd are required")
    search_path = env.get("PATH") if env is not None else None
    executable = shutil.which(argv[0], path=search_path)
    if executable is None:
        raise FileNotFoundError(f"Configured executable is unavailable: {argv[0]}")
    argv = (str(Path(executable).resolve()), *argv[1:])
    if os.name == "nt":
        # Supervisor establishes a job before spawning the requested executable.
        # Run the stdlib-only supervisor by installed file path. Importing the
        # package here would load the SDK before every tool process unnecessarily.
        argv = (sys.executable, str(Path(__file__).with_name("windows_job.py")), *argv)
        if env is not None:
            # Windows requires SystemRoot for runtime/side-by-side services. Inherit
            # this OS bootstrap setting only, never the rest of the host environment.
            env = dict(env)
            if not any(key.lower() == "systemroot" for key in env):
                env["SystemRoot"] = os.environ["SystemRoot"]
    return await asyncio.create_subprocess_exec(
        *argv,
        cwd=cwd,
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
        if os.name == "nt"
        else 0,
        start_new_session=os.name != "nt",
    )


async def terminate(process: asyncio.subprocess.Process) -> None:
    if os.name == "nt":
        # Terminating the supervisor closes its sole job handle and kills descendants.
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.returncode is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass
    async with asyncio.timeout(2):
        await process.wait()


async def read_bounded(stream: asyncio.StreamReader, limit: int) -> bytes:
    data = bytearray()
    while chunk := await stream.read(65536):
        data.extend(chunk)
        if len(data) > limit:
            raise ValueError(f"Process output exceeded {limit} bytes")
    return bytes(data)


async def capture(
    argv: Sequence[str],
    cwd: str,
    *,
    timeout: float = 30,
    limit: int = 2 * 1024 * 1024,
    env: dict[str, str] | None = None,
    input_data: bytes | None = None,
) -> Captured:
    process = await spawn(argv, cwd, env)
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None
    tasks = [
        asyncio.create_task(read_bounded(process.stdout, limit)),
        asyncio.create_task(read_bounded(process.stderr, limit)),
    ]
    try:
        async with asyncio.timeout(timeout):
            if input_data is not None:
                process.stdin.write(input_data)
                await process.stdin.drain()
            process.stdin.close()
            output, errors = await asyncio.gather(*tasks)
            code = await process.wait()
        return Captured(
            tuple(argv),
            cwd,
            code,
            output.decode("utf-8", errors="replace"),
            errors.decode("utf-8", errors="replace"),
        )
    finally:
        await terminate(process)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
