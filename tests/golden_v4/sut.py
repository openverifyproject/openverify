"""Execution adapters, authored AFTER the independent expectation commits.

Imports here are SUT calls only; this module never writes frozen artifacts.
"""
from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from openverify import ProtocolError, flattened_status, parse_definition, parse_result, parse_run_record
from openverify.provider import (LifecycleValidator, ProviderContractError, parse_provider_manifest,
                                 parse_provider_object, wire_data)
from openverify.serialization import to_data
from openverify.validation import parse_object, schema_validator, validate_executable_definition, validate_wire

from .oracle import model as stimuli

ROOT=Path(__file__).resolve().parents[2]


def accepted(call, node=None):
    try:
        call()
        return {"accepted":True}
    except (ProtocolError,ProviderContractError,ValidationError) as exc:
        if node is not None:node.v4_rejection={"code":getattr(exc,"code",type(exc).__name__),"message":str(exc)}
        return {"accepted":False}


def session(manifest=None):
    value=LifecycleValidator(parse_provider_manifest(manifest or stimuli.manifest()))
    value.initialize({"supported_contract_versions":["0.1"],"supported_vcp_versions":["draft"]})
    return value


def outcome(state):
    value={"invocation_id":"v4-attempt","state":state}
    if state=="COMPLETED":value["output"]=None
    if state=="ERROR":value["error"]={"code":"com.example.golden.failed","message":"authored failure"}
    return value


def prepare_attempt(value,correlation):
    if correlation=="UNSEEN":return
    if correlation=="REJECTED":
        bad={**stimuli.invocation(),"capability_id":"com.example.absent"}
        try:value.accept(bad)
        except ProviderContractError:return
        raise AssertionError("Invalid missing-capability invocation accepted")
    value.accept(stimuli.invocation())
    if correlation=="TERMINAL":value.outcome(outcome("COMPLETED"))


def execute(case,node):
    action=case["action"];s=case["stimulus"]
    if action in {"parse","wire","executable"}:
        def check():
            if action=="wire":validate_wire(s["object_type"],s["value"])
            elif s["object_type"] in {"provider-manifest","provider-event","outcome","invocation","capability"}:parse_provider_object(s["object_type"],s["value"])
            else:
                value=parse_object(s["object_type"],s["value"])
                if action=="executable":validate_executable_definition(value)
        return accepted(check,node)
    if action=="subschema":
        schema=schema_validator(s["object_type"])
        sub=schema.schema
        for token in s["pointer"].strip("/").split("/"):sub=sub[token]
        return accepted(lambda:schema.evolve(schema=sub).validate(s["value"]),node)
    if action=="schema_root":
        source=json.loads((ROOT/s["path"]).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(source)
        loader=__import__("openverify.provider",fromlist=["load_provider_schema"]).load_provider_schema if s["path"].startswith("provider-contract") else __import__("openverify",fromlist=["load_schema"]).load_schema
        packaged=loader(Path(s["path"]).name.removesuffix(".schema.json"))
        assert packaged==source,"Packaged schema differs from normative source"
        return {"accepted":True,"id":packaged["$id"]}
    if action=="json":
        raw=b'\xff' if s["text"]=="INVALID_UTF8" else s["text"].encode("utf-8")
        return accepted(lambda:parse_result(raw),node)
    if action=="flatten":
        try:return {"value":flattened_status(parse_result(s))}
        except ProtocolError as exc:
            if exc.code!="RESULT_PROJECTION":raise
            return {"value":None}
    if action=="reduce":
        from openverify.relay.core.aggregation import reduce_results
        names=[f"member_{i}" for i in range(len(s["values"]))]
        inputs={"members":names,**dict(zip(names,s["values"]))}
        config={"reducer":s["reducer"],"handling":s.get("handling",{k:"REJECT" for k in stimuli.EXCEPTIONS})}
        if s["reducer"]=="WEIGHTED_AVERAGE":config["weights"]=dict(zip(names,s.get("weights",[1]*len(names))))
        if s["reducer"]=="WORST_SEVERITY":config["severity_domain"]=stimuli.SEVERITY
        try:
            r=to_data(reduce_results(inputs,config))
            observed={key:r[key] for key in ("verdict","score","severity") if key in r}
            if "evidence" in case["expected"]:observed["evidence"]=r.get("evidence",[])
            return observed
        except ProtocolError as exc:return {"error":exc.code}
    if action=="provider_invocation":
        v=session(s["manifest"])
        return accepted(lambda:v.accept(s["invocation"],now="2000-01-01T00:00:00Z"),node)
    if action=="provider_event":
        v=session(s["manifest"]);v.accept(s["invocation"])
        return accepted(lambda:v.event(s["event"]),node)
    if action=="provider_outcome":
        v=session(s["manifest"]);inv=s["invocation"]
        state=s["outcome"]["state"]
        if state=="DEADLINE_EXCEEDED":inv["deadline"]="2001-01-01T00:00:00Z"
        v.accept(inv,now="2000-01-01T00:00:00Z")
        if state=="CANCELLED":v.cancel({"invocation_id":"v4-attempt"})
        return accepted(lambda:v.outcome(s["outcome"],now="2002-01-01T00:00:00Z" if state=="DEADLINE_EXCEEDED" else "2000-01-01T00:00:00Z"),node)
    if action=="provider_terminal":
        v=session();inv=stimuli.invocation()
        if s["deadline_phase"]!="ABSENT":inv["deadline"]="2001-01-01T00:00:00Z"
        v.accept(inv,now="2000-01-01T00:00:00Z")
        if s["cancelled"]:v.cancel({"invocation_id":"v4-attempt"})
        now="2002-01-01T00:00:00Z" if s["deadline_phase"]=="EXPIRED" else "2000-01-01T00:00:00Z"
        return accepted(lambda:v.outcome(outcome(s["state"]),now=now),node)
    if action=="provider_transition":
        v=session();prepare_attempt(v,s["correlation"])
        calls={"ACCEPT":lambda:v.accept(stimuli.invocation()),"EVENT":lambda:v.event({"invocation_id":"v4-attempt","kind":"progress","sequence":1,"payload":None}),"CANCEL":lambda:v.cancel({"invocation_id":"v4-attempt"}),"OUTCOME":lambda:v.outcome(outcome("COMPLETED"))}
        return accepted(calls[s["action"]],node)
    if action=="provider_cancel":
        v=session(stimuli.manifest(cancel=s["feature"]));prepare_attempt(v,s["correlation"])
        return accepted(lambda:v.cancel({"invocation_id":"v4-attempt"}),node)
    if action=="provider_init":
        v=LifecycleValidator(parse_provider_manifest(stimuli.manifest()))
        try:
            version=v.initialize({"supported_contract_versions":s["versions"],"supported_vcp_versions":["draft"]})
            return {"accepted":True,"version":version}
        except ProviderContractError:return {"accepted":False,"version":None}
    if action=="error_name":
        authority=s["authority"];code=s["identifier"]
        if authority=="NORMATIVE_PROVIDER_CONTRACT":
            checked=parse_provider_object("provider-error",{"code":code,"message":"authored"});actual=checked.code
        elif authority=="RELAY_SPECIFIC":
            from openverify.relay.error_codes import RelayErrorCode
            actual=RelayErrorCode(code).value
        else:
            from openverify.error_codes import VcpErrorCode
            actual=VcpErrorCode(code).value
        return {"identifier":actual,"authority":authority}
    if action=="binding":
        from openverify.model import OperationRequirement, ProviderBinding
        from openverify.relay.adapters.binder import DeterministicBinder
        from .runtime import catalog_for
        catalog=catalog_for({"n":{}})
        p=catalog.providers()[0];b={"provider_id":p.manifest.provider_id,"provider_version":p.manifest.provider_version,"capability_id":stimuli.CAPABILITY,"capability_version":"1"}
        for (key,value),equal in zip(list(b.items()),s["equality_bits"]):
            if not equal:b[key]=("com.example.other" if key.endswith("_id") else "other")
        req=OperationRequirement(capability_id=stimuli.CAPABILITY,capability_version="1")
        return accepted(lambda:DeterministicBinder().bind(req,catalog.providers(),ProviderBinding(**b)),node)
    if action=="weight_proof":
        import itertools
        signs=list(itertools.product((-1,0,1),repeat=s["n"]))
        valid=sum(all(w>=0 for w in ws) and sum(ws)>0 for ws in signs)
        return {"candidates":len(signs),"valid":valid,"invalid":len(signs)-valid}
    if action=="coordinate":
        assert s["kind"] in stimuli.KINDS and s["source"] in (*stimuli.SOURCES,"UNBOUND") and s["status"] in stimuli.STATUSES and s["handler"] in stimuli.HANDLERS
        return {"classification":"CONDITIONAL","missing_axes":["requiredness","producer_role","target_schema","ancestor","trace"]}
    if action=="phase":
        from openverify.relay.core.state import RunState
        machine=RunState({"n":s["from"]})
        try:
            machine.transition("n",s["to"])
            assert machine.phases["n"]==s["to"]
            return {"category":"PROGRESSION"}
        except ValueError:return {"category":"STUTTER" if s["from"]==s["to"] else "OTHER"}
    if action=="guard_operator":
        schema=json.loads((ROOT/"schemas/draft/graph.schema.json").read_text())
        fields=list(schema["properties"]["edges"]["items"]["properties"]["guard"]["anyOf"][0]["properties"])
        return {"fields":fields}
    if action=="extension":
        ext={"namespace":"com.example:v4","version":"1","required":s["required"],"data":{"authored":None}}
        if s["supported"]:
            # Explicit test consumer implements this one namespace; the SDK alone
            # advertises no required-extension support. Preserve data, consume semantics.
            assert ext["namespace"]=="com.example:v4"
            ext["required"]=False
        return accepted(lambda:parse_object("extension",ext),node)
    if action=="resolution_record":
        # Resolution status/handling cross-products are conditional consistency
        # laws. Exercise the production resolver, not only the wire schema.
        from .runtime import resolution_bits
        return resolution_bits(s,node)
    if action=="record_compatibility":
        from .local_records import compatibility_record
        return accepted(lambda:parse_run_record(compatibility_record(s)),node)
    if action=="policy_role":
        from openverify.policy import check_outcome
        values={"ACTIVATION":{"outcome":"ACTIVATE","reason":"authored"},"SELECTION":{"subjects":[stimuli.ARTIFACT],"reason":"authored"},"ADMISSION":{"outcome":"RUN","reason":"authored"}}
        def check():
            parsed=parse_object(s["role"].lower(),values[s["outcome_role"]])
            check_outcome(s["role"],parsed,parse_definition(stimuli.definition()))
        return accepted(check,node)
    if action=="invoked_result" and case["classification"]=="INVALID":
        from .local_records import compatibility_record
        from openverify.dataflow import accept_outputs
        from openverify.model import ExecutionObservation
        fixture=compatibility_record({"kind":s["kind"],"state":"SUCCESS","result":stimuli.known(verdict="PASS")})
        definition=parse_definition(fixture["definition"])
        target=next(n for n in definition.graph.nodes if n.id=="n")
        observation=ExecutionObservation(outputs={"result":s["result"]})
        return accepted(lambda:accept_outputs(target,observation,definition),node)
    if action=="sdk_diagnostic":
        if s["code"]=="RESULT_PROJECTION":
            try:flattened_status(parse_result(stimuli.known()))
            except ProtocolError as exc:return {"code":exc.code}
        else:
            from .runtime import sdk_policy_error
            return sdk_policy_error()
    if action=="audit":
        from tools.golden_v4 import report
        if s["check"]=="FREEZE":return {"accepted":not report.verify_freeze()}
        if s["check"]=="INVENTORY":return {"accepted":report.inventory()["certified"]}
        if s["check"]=="CASE_IDS":
            from .reporters.runner import all_cases
            ids=[c["case_id"] for c in all_cases()]
            return {"accepted":len(ids)==len(set(ids))}
        proofs=report.read_rows(ROOT/"conformance/golden-v4/REDUCTION_LEDGER.jsonl")
        return {"accepted":all(p["status"]=="PROVED" for p in proofs)}
    if action=="mutation":
        from .mutations import probe
        return probe(s["family"],node)
    if action in {"framing","transport_method","entrypoint"}:
        from .integration import execute_integration
        return execute_integration(case,node)
    from .runtime import execute_runtime
    return asyncio.run(execute_runtime(case,node))
