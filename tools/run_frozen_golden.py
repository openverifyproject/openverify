"""Exercise the frozen Golden V4 baseline in its original production revision.

Golden V4 seals source hashes. New feature branches must not rewrite those
historical hashes or pretend their current source is the frozen baseline.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "83b8e1ec0e5c5b4e0c9ef9e5c587121b5d38e242"


def main() -> int:
    checkout = ROOT / ".pytest_cache/github/golden-baseline"
    checkout.parent.mkdir(parents=True, exist_ok=True)
    if not checkout.exists():
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(checkout), BASELINE],
            cwd=ROOT,
            check=True,
        )
    elif (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
        != BASELINE
    ):
        raise RuntimeError("Golden baseline checkout has a different revision")
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["OPENVERIFY_GOLDEN_SOURCE_REVISION"] = str(
        checkout / "docs/github-release/SOURCE_REVISION.json"
    )
    environment["OPENVERIFY_GOLDEN_EXPECTATION_REVISION"] = str(
        checkout / "conformance/golden-v4/verification-final/EXPECTATION_CORRECTIONS.json"
    )
    environment["GOLDEN_V4_ARTIFACTS"] = str(ROOT / ".pytest_cache/golden-v4/ci")
    (checkout / ".pytest_cache/golden-v4").mkdir(parents=True, exist_ok=True)
    junit = ROOT / ".pytest_cache/github/golden.xml"
    subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-c",
            "tests/golden_v4/pytest.ini",
            "tests/golden_v4",
            f"--junitxml={junit}",
        ],
        cwd=checkout,
        env=environment,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "tools.golden_v4.report", "--verify-freeze"],
        cwd=checkout,
        env=environment,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
