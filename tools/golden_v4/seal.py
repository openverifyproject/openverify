"""Seal independent design artifacts before any SUT execution adapter exists."""
from __future__ import annotations

import json
from pathlib import Path

from .discover import OUT, ROOT, digest, write_json, write_lines
from .proofs import derive


def main():
    frozen=OUT/"FROZEN_EXPECTATIONS"
    assert not (frozen/"MANIFEST.json").exists(), "Freeze is immutable"
    rows,proofs=derive()
    cases=[json.loads(s) for s in (OUT/"CASES.jsonl").read_text(encoding="utf-8").splitlines()]
    indexed=[json.loads(s) for s in (OUT/"NORMATIVE_CLAUSES.jsonl").read_text(encoding="utf-8").splitlines()]
    obligations=[]
    for c in indexed:
        obligations.append({"obligation_id":c["obligation_ids"][0],"clause_ids":[c["clause_id"]],"status":"MISSING",
                            "reason":"Conservative extracted unit requires assertion-level review; indexing alone does not prove it.","witness_ids":[]})
    for case in cases:
        for oid in case["obligation_ids"]:
            if not any(o["obligation_id"]==oid for o in obligations):
                obligations.append({"obligation_id":oid,"clause_ids":case["normative_clauses"],"status":"NOT_RUN","witness_ids":[case["case_id"]],"assertion_scope":case["action"]})
    write_lines(OUT/"OBLIGATIONS.jsonl",obligations)
    write_lines(OUT/"WITNESSES.jsonl",[{"witness_id":c["case_id"],"case_id":c["case_id"],"obligation_ids":c["obligation_ids"],"assertion":c["action"],"expected":c["expected"],"mode":c["execution_mode"],"status":"NOT_RUN"} for c in cases])
    modules={}
    for c in cases: modules.setdefault(c["module"],set()).add(c["family"])
    testroot=ROOT/"tests/golden_v4"
    for module,families in modules.items():
        text=['"""Explicit independently enumerated Golden v4 contract families."""','from .reporters.runner import family_cases, run_case','import pytest','']
        for family in sorted(families):
            name=family.removeprefix("V4.").lower().replace(".","_")
            text += [f'@pytest.mark.parametrize("case", family_cases("{family}", "{module}"), ids=lambda c: c["case_id"])',
                     f'def test_{name}(case, request):', '    run_case(case, request)', '']
        (testroot/(module+".py")).write_text("\n".join(text),encoding="utf-8")
    (OUT/"COMPOSITION_PROOFS.md").write_text('''# Composition arguments and tested premises

Edges impose dependency; explicit UPSTREAM_OUTPUT bindings transport values. A
guard gates eligibility. CONTROL routing and ordered Aggregate membership are
separate declarations. No edge-type wire enum is introduced.

For a finite DAG choose a topological ordering. The base requires correct local
execution and immutable authored inputs. Assuming all predecessors are terminal,
typed binding resolution and target validation establish each successor's exact
inputs. Readiness then permits a single attempt; terminal immutability permits
induction. This argument requires noninterference of shared state and separate
proofs of global route exclusion, cancellation, waves and barriers.

Status: UNPROVED for arbitrary DAG size and arbitrary shared services. Small
INDEPENDENT, EDGE, CHAIN, FORK, JOIN, DIAMOND, ROUTE, GUARDED_JOIN, AGG_FANIN,
PARALLEL_BARRIER, STOP_CANCEL and MULTIRUN witnesses test the stated finite
premises. They do not establish universal scheduler or race correctness.

Explicit higher-order obligations: admission+cancellation+record;
filtering+weights+identity; route+guard+join; completion+cancellation+usage;
features+event kind+VCP compatibility. Pairwise success is not a proof of these.
Cross-module independence and a complete pair-obligation graph remain subject to
the fail-closed inventory gate; no implicit proof is claimed.
''',encoding="utf-8")
    (OUT/"DOMAIN_LIMITS.md").write_text('''# Declared limits

UNSUPPORTED: cycles, dynamic expansion, external/nested/dynamic schema resolution,
automatic retries, durable replay/recovery, required unknown extensions, remote
Provider transports, multi-attempt recorded cancellation and universal host API
feature parity. Check rejection only where specified.

EXCLUDED: Byzantine providers, malformed external events in real Relay, malicious
replacement ports, provider attestation and coordinated consistent record forgery.
Local malformed objects remain cheap rejection cases.

UNBOUNDED: JSON payloads, strings, schemas, numeric precision, graph sizes above
four, member lengths, event histories, custom provider/policy logic and scheduling
histories. Finite partitions and samples do not establish arbitrary-domain proof.

SAMPLED: logical reducer sequences through length five; severity through length
four; numeric extrema/means over explicit authored boundaries. Larger domains have
UNPROVED residuals in REDUCTION_LEDGER.jsonl.

CONDITIONAL: raw availability coordinates require port requiredness, producer
role, target schema, ancestor relation and trace. They are coordinate-space checks,
not a universal V/I/N split. Missing normative clause-to-assertion reviews are
MISSING coverage and prevent certification.

AMBIGUOUS: exact error precedence is asserted only when mandated. Source-supported
rejection categories whose precedence is not fixed are checked as rejection only.
Portable numeric rounding, canonical identities and clock trust remain open.
''',encoding="utf-8")
    frozen.mkdir(exist_ok=True)
    (frozen/"cases.jsonl").write_bytes((OUT/"CASES.jsonl").read_bytes())
    paths=[OUT/n for n in ("BLUEPRINT.md","CASES.jsonl","OBLIGATIONS.jsonl","WITNESSES.jsonl","NORMATIVE_CLAUSES.jsonl","NORMATIVE_SOURCE_HASHES.json","ERROR_INVENTORY.json","PROJECTIONS.json","REDUCTION_LEDGER.jsonl","CONTRACT_INVENTORY.md","COUNT_PROOFS.md","COMPOSITION_PROOFS.md","DOMAIN_LIMITS.md","FROZEN_EXPECTATIONS/cases.jsonl")]
    paths += list((testroot/"oracle").glob("*.py"))
    paths += [ROOT/f"tools/golden_v4/{name}.py" for name in ("discover","freeze","witness_authoring","proofs","seal")]
    write_json(frozen/"MANIFEST.json",{"format":"golden-v4-freeze-1","files":{p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in paths},"authoring":"Independent prose/schema calculations. No production imports or recorded production outputs.","adjudications":["D-001: 53 error declarations; 33 normative VCP, 8 normative Provider, 2 SDK diagnostics, 10 Relay-specific; explicitly approved by user."]})
    print(f"Sealed {len(cases)} authored cases; {len(obligations)} indexed/case obligations. No coverage certification is inferred.")


if __name__ == "__main__":main()
