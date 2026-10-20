"""Publish verified crate contents outside Git; use the same path for dry-runs."""

import argparse
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

from sdk_verify import consumer, version


def publish(artifact, dry_run=False):
    runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    inside_git = subprocess.run(
        ["git", "-C", str(runner_temp), "rev-parse", "--show-toplevel"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    if inside_git.returncode == 0:
        raise RuntimeError("RUNNER_TEMP must be outside every Git checkout")
    with tempfile.TemporaryDirectory(prefix="verifyanything-crate-", dir=runner_temp) as root:
        with tarfile.open(Path(artifact).resolve(strict=True)) as archive:
            archive.extractall(root, filter="data")
        package = Path(root) / ("verifyanything-" + version("rust"))
        if not (package / "Cargo.toml").is_file():
            raise RuntimeError("Verified crate does not contain the expected package version")
        env = os.environ.copy()
        env["CARGO_TARGET_DIR"] = str(package / "target")
        command = ["cargo", "publish", "--locked"]
        if dry_run:
            command.append("--dry-run")
        print("Extracted verified crate outside Git:", package, flush=True)
        subprocess.run(command, cwd=package, env=env, check=True)
        if dry_run:
            # Install the actual repackaged publication artifact, not just the input.
            packages = list((package / "target/package").rglob(package.name + ".crate"))
            if len(packages) != 1:
                raise RuntimeError("Cargo dry-run did not produce one repackaged crate")
            consumer("rust", packages[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    publish(args.artifact, args.dry_run)
