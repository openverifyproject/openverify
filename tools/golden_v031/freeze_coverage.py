"""Freeze effective coverage for initial expectations plus explicit spec errata."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "conformance/golden-v0.3.1"


def main():
    path = BASE / "coverage-effective.json"
    if path.exists():
        raise SystemExit("Refusing to overwrite effective frozen coverage")
    data = json.loads((BASE / "coverage.json").read_text(encoding="utf-8"))
    corrections = json.loads((BASE / "expectation-errata.json").read_text(encoding="utf-8"))["corrections"]
    for r in data:
        c = corrections.get(r["requirement_id"])
        if c is not None:
            if not c["runtime_applicable"]:
                r.update(suite="STRUCTURE", independently_frozen_expectation={"error_code": c["static_rejection"]},
                         finite_domain_or_interface_law=c["reason"])
            else:
                r["independently_frozen_expectation"] = c["stimulus"]["expected"]
    for q in json.loads((BASE / "questions.json").read_text()):
        data.append({"requirement_id": q["id"], "normative_section": ["docs/relay/architecture.md"],
            "finite_domain_or_interface_law": q["reason"], "scenario_ids": [], "suite": "OUTSIDE",
            "independently_frozen_expectation": None, "mutation_witness": None, "status": q["status"]})
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    files = (path, Path(__file__).resolve())
    checks = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_text(encoding="utf-8").encode()).hexdigest() for p in files}
    (BASE / "checksums-coverage.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
