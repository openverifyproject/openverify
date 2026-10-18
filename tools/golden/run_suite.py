"""One command for integrity checks, public-boundary execution and audit reports."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tools.golden.verify_manifest import baseline, cases, verify


def args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile", choices=("vcp", "provider", "relay-local", "integration", "all"), default="all"
    )
    parser.add_argument("--case", action="append", default=[], help="exact case ID; repeatable")
    parser.add_argument(
        "--self-check", action="store_true", help="suite audit only; never invokes OpenVerify"
    )
    parser.add_argument(
        "--audit-plan", action="store_true", help="emit declared coverage without SUT execution"
    )
    parser.add_argument(
        "--report-dir", type=Path, default=ROOT / ".pytest_cache/golden-current-reports"
    )
    return parser.parse_args()


async def run(selected):
    from tools.golden.execution import execute_case

    rows = []
    for i, case in enumerate(selected, 1):
        start = time.monotonic()
        row = await execute_case(case)
        row["duration_seconds"] = time.monotonic() - start
        rows.append(row)
        if row["status"] != "PASS" or i % 100 == 0:
            print(f"{i}/{len(selected)} {row['id']} {row['status']}", flush=True)
    return rows


def main():
    options = args()
    integrity = verify()
    print(json.dumps(integrity), flush=True)
    from tools.golden.coverage import report, markdown

    if options.self_check:
        from tools.golden.selfcheck import run as check

        results = check()
        print(json.dumps(results, indent=2))
        return 0 if results["passed"] else 1
    selected = [
        c
        for c in cases()
        if options.profile in ("all", c["profile"])
        and (not options.case or c["id"] in options.case)
    ]
    missing = set(options.case) - {c["id"] for c in selected}
    if missing:
        raise SystemExit("unknown case IDs or wrong profile: " + str(sorted(missing)))
    if not selected:
        raise SystemExit("no cases selected")
    rows = [] if options.audit_plan else asyncio.run(run(selected))
    coverage = report(rows)
    destination = options.report_dir.resolve()
    if destination.is_relative_to(baseline().resolve()) or destination == baseline().resolve():
        raise SystemExit("reports cannot be written inside the immutable baseline")
    destination.mkdir(parents=True, exist_ok=True)
    data = {
        "suite_id": "openverify-golden-current",
        "suite_version": "0.1.0",
        "profile": options.profile,
        "integrity": integrity,
        "stage": "AUDIT_PLAN_NO_SUT_EXECUTION"
        if options.audit_plan
        else "STAGE_C_PUBLIC_BOUNDARY_EXECUTION",
        "selected_unique_cases": len(selected),
        "cases": rows,
        "coverage": coverage,
        "complete": False,
    }
    (destination / "report.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (destination / "coverage.json").write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    details = [
        "# Golden execution report",
        "",
        f"Stage: {data['stage']}",
        "",
        f"Selected unique cases: {len(selected)}. SUT executed: {coverage['unique_sut_executed_cases']}.",
        "",
        "| Case | Status | Details / reproduction |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        detail = str(row.get("detail", row.get("scope", ""))).replace("|", "\\|").replace("\n", " ")
        details.append(f"| {row['id']} | {row['status']} | {detail}; `{row['reproduce']}` |")
    (destination / "report.md").write_text(
        "\n".join(details) + "\n\n" + markdown(coverage), encoding="utf-8"
    )
    (destination / "coverage.md").write_text(markdown(coverage), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(destination / "report.json"),
                "statuses": coverage["statuses"],
                "complete": False,
            },
            indent=2,
        )
    )
    if options.audit_plan:
        return 0
    return (
        1
        if any(r["status"] in ("FAIL", "ERROR") for r in rows)
        else 2
        if any(r["status"] == "ENVIRONMENT_UNAVAILABLE" for r in rows)
        else 3
        if any(r["status"] == "BLOCKED_BY_SPEC" for r in rows)
        else 4
        if options.profile == "all" and coverage["known_gaps"]
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
