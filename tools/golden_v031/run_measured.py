"""Monotonic hard timeout launcher for one full or explicitly targeted suite."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", choices=("A", "B"))
    parser.add_argument("--cases", help="Comma-separated exact IDs; no implicit skipping")
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    folder = root / ".pytest_cache/golden-v031/launches"
    folder.mkdir(parents=True, exist_ok=True)
    stem = folder / (args.suite + "-" + ("targeted-" if args.cases else "full-") + uuid4().hex)
    env = os.environ.copy()
    env["GOLDEN_SHARD_COUNT"], env["GOLDEN_SHARD_INDEX"] = "1", "0"
    if args.cases:
        env["GOLDEN_CASE_IDS"] = args.cases
    else:
        env.pop("GOLDEN_CASE_IDS", None)
    env["PYTHONUNBUFFERED"] = "1"
    command = [sys.executable, "-m", "pytest", "-q", "tests/golden_v03/" + (
        "test_contract_structure.py" if args.suite == "A" else "test_master_execution.py")]
    start = time.perf_counter_ns()
    timed_out = False
    with stem.with_suffix(".console.txt").open("w", encoding="utf-8") as console:
        process = subprocess.Popen(command, cwd=root, env=env, stdout=console, stderr=subprocess.STDOUT)
        try:
            process.wait(timeout=max(0, args.timeout - (time.perf_counter_ns() - start) / 1e9))
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.wait(timeout=5)
    data = {"suite": args.suite, "targeted_cases": args.cases, "command": command,
            "timeout_limit_seconds": args.timeout, "timeout": timed_out,
            "total_elapsed_seconds": (time.perf_counter_ns() - start) / 1e9,
            "returncode": process.returncode, "console": str(stem.with_suffix(".console.txt"))}
    stem.with_suffix(".json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data, indent=2))
    return process.returncode if not timed_out else 124


if __name__ == "__main__":
    raise SystemExit(main())
