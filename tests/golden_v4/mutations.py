"""Targeted semantic corruptions evaluated by the real frozen assertions."""
from __future__ import annotations

import copy
from unittest.mock import patch

from .reporters.runner import all_cases,compare


def probe(family,node):
    from .sut import execute
    from . import runtime
    from openverify.provider import LifecycleValidator
    import openverify.validation as validation
    import openverify.dataflow as dataflow
    import openverify.relay.core.aggregation as aggregation
    import openverify.relay.application.policies as policies
    import openverify.relay.application.run as coordinator
    from openverify.model import Admission,InputResolution,RunRecord
    choices={
        "RESULT_STATE":("V4.VCP.RESULT.WIRE_AXIS.EXECUTED-ABSENT-ABSENT-ABSENT-ABSENT",patch.object(validation,"_result",lambda r:None)),
        "OPTIONAL_OBSERVATION":("V4.VCP.RESULT.OBS_MASK.EXECUTED-SUCCESS-APPLICABLE-UNKNOWN-ABSENT.BITS_00000001",patch.object(validation,"_result",lambda r:None)),
        "DECISION":("V4.VCP.DECISION.DEST.CONTINUE-NONEMPTY",patch.object(validation,"semantic",lambda value:None)),
        "RECORD_LINEAGE":("V4.VCP.RECORD.LINEAGE.INPUT_VALUE",patch.object(runtime,"parse_run_record",lambda raw:RunRecord.model_validate(raw))),
        "CANCELLATION":("V4.RELAY.SCHEDULER.STOP_CANCEL",patch.object(runtime.Cancellation,"cancel",lambda self,reason="":None)),
    }
    if family=="AVAILABILITY":
        original=dataflow.resolve_source
        def corrupt(source,values,records,graph):
            r=original(source,values,records,graph)
            return InputResolution(source=r.source,status="AVAILABLE",value=17) if r.status=="ABSENT" else r
        choices[family]=("V4.VCP.RESOLVE.CONSUMER.DERIVE-ABSENT-BLOCK",patch.object(dataflow,"resolve_source",corrupt))
    if family=="WEIGHT_IDENTITY":
        original=aggregation.reduce_results
        def corrupt(inputs,config):
            config=copy.deepcopy(config)
            keys=list(config["weights"]);vals=list(config["weights"].values())
            config["weights"]=dict(zip(keys,reversed(vals)))
            return original(inputs,config)
        choices[family]=("V4.VCP.AGG.WEIGHT_IDENTITY.UNEQUAL",patch.object(aggregation,"reduce_results",corrupt))
    if family=="POLICY_NONINVOCATION":
        original=policies.evaluate_policies
        async def corrupt(*args,**kwargs):
            records=await original(*args,**kwargs)
            records[-1]=records[-1].model_copy(update={"outcome":Admission(outcome="RUN",reason="mutant bypasses SKIP")})
            return records
        choices[family]=("V4.VCP.POLICY.PATH.SKIP",patch.object(coordinator,"evaluate_policies",corrupt))
    if family=="PROVIDER_ORDER":
        original=LifecycleValidator._lookup
        def corrupt(self,data,*,terminal_ok=False):return original(self,data,terminal_ok=True)
        choices[family]=("V4.PROVIDER.ATTEMPT.TRANSITION.TERMINAL-EVENT",patch.object(LifecycleValidator,"_lookup",corrupt))
    case_id,mutation=choices[family]
    case=next(c for c in all_cases() if c["case_id"]==case_id)
    # Baseline must pass this exact assertion before its mutant can count.
    baseline=execute(copy.deepcopy(case),node)
    if not compare(case["expected"],baseline):
        raise AssertionError(f"Mutation baseline fails: {case_id}; expected={case['expected']}; actual={baseline}")
    with mutation:
        try:
            actual=execute(copy.deepcopy(case),node)
            detected=not compare(case["expected"],actual)
        except AssertionError as exc:
            actual={"assertion":str(exc)};detected=True
    node.v4_mutation_evidence={"mutant":family,"real_case_id":case_id,"baseline":baseline,"mutated_actual":actual,"detected":detected}
    return {"detected":detected}
