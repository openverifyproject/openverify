"""Targeted diagnosis runner; no expectation writes and no global rerun."""

import argparse
import asyncio
import json
import time
from pathlib import Path
from tools.golden_v02.execution import execute_case
from tools.golden_v02.verify_manifest import cases


async def run(prefixes, output):
    selected = [c for c in cases() if any(c["id"].startswith(p) for p in prefixes)]
    rows = []
    start = time.monotonic()
    for c in selected:
        tick = time.monotonic()
        row = await execute_case(c)
        row["duration_seconds"] = time.monotonic() - tick
        rows.append(row)
        if row["status"] != "PASS":
            print(row["id"], row["status"], row.get("detail", ""), flush=True)
    from collections import Counter

    summary = {
        "unique_cases": len(rows),
        "statuses": dict(Counter(r["status"] for r in rows)),
        "elapsed_seconds": time.monotonic() - start,
        "cases": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "cases"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prefix", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    asyncio.run(run(options.prefix, options.output))
