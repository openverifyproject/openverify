"""Authored in-memory records for cross-field rejection, without executing Relay."""
from __future__ import annotations

import copy

from openverify import fingerprint,parse_definition
from .oracle import model as m


def compatibility_record(s):
    target=m.node("n",s["kind"]);nodes=[target];edges=[]
    if s["kind"]=="AGGREGATE":
        seed=m.node("seed","EVALUATE");nodes=[seed,target];edges=[{"from_node":"seed","to_node":"n"}]
        target["inputs"].append(m.port("member"));target["bindings"]["member"]={"kind":"UPSTREAM_OUTPUT","node_id":"seed","output":"result"}
        target["aggregate_inputs"]=["member"];target["bindings"]["members"]=m.constant(["member"])
    d=m.definition(nodes,edges);disp=s["result"]["disposition"]
    admission="RUN"
    if disp in {"SKIPPED","DEFERRED"}:
        admission="SKIP" if disp=="SKIPPED" else "DEFER"
        d["execution_policy"]["admission"]={"operation":{"capability_id":m.CAPABILITY,"capability_version":"1"},"inputs":[],"bindings":{},"config":{}}
    adm={"outcome":admission,"reason":"authored admission"}
    def evaluation(role,outcome):return {"role":role,"input_values":{},"input_resolutions":{},"outcome":outcome}
    raw={"protocol":"draft","run_id":"authored-local-record","definition":d,"definition_fingerprint":fingerprint(parse_definition(d)),
         "subject":copy.deepcopy(m.ARTIFACT),"initial_context":{},"run_inputs":{},"opportunity_id":"authored-opportunity","admission":adm,
         "policy_evaluations":[evaluation("ACTIVATION",{"outcome":"ACTIVATE","reason":"authored activation"}),evaluation("SELECTION",{"subjects":[m.ARTIFACT],"reason":"authored selection"}),evaluation("ADMISSION",adm)],
         "started_at":"2026-01-01T00:00:00Z","finished_at":"2026-01-01T00:00:10Z","nodes":[],"final_results":{}}
    if disp=="CANCELLED":raw["cancellation"]={"node_id":"n","phase":"RUNNING" if s["state"]=="CANCELLED" else "BEFORE_START","reason":"authored cancellation"}
    prior={}
    for index,n in enumerate(nodes):
        is_target=n["id"]=="n"
        result=copy.deepcopy(s["result"] if is_target else m.known(verdict="PASS"))
        reason=None;state="ERROR" if result.get("execution_outcome")=="ERROR" else "SUCCESS"
        if admission!="RUN":
            reason="ADMISSION_"+admission;result={"protocol":"draft","disposition":disp,"output":{"reason":reason}};state="NONEXECUTED"
        elif is_target and disp=="CANCELLED":
            reason="CANCELLATION";result={"protocol":"draft","disposition":"CANCELLED","output":{"reason":reason}}
            state="CANCELLED" if s["state"]=="CANCELLED" else "NONEXECUTED"
        # Explicit authored empty evidence and usage avoid any reliance on schema
        # defaults or an implementation's omission/serialization preferences.
        result["evidence"]=[];result["usage"]={}
        values={};resolutions={}
        for name,source in n["bindings"].items():
            value=copy.deepcopy(source["value"] if source["kind"]=="CONSTANT" else prior[source["node_id"]])
            values[name]=value;resolutions[name]={"source":source,"status":"AVAILABLE","used_default":False,"value":value}
        rec={"node_id":n["id"],"kind":n["kind"],"operation":n["operation"],"upstream_node_ids":["seed"] if is_target and len(nodes)>1 else [],
             "upstream_results":{"seed":prior["seed"]} if is_target and len(nodes)>1 else {},"input_values":values,"input_resolutions":resolutions,
             "started_at":f"2026-01-01T00:00:0{index}Z","finished_at":f"2026-01-01T00:00:0{index+1}Z","usage":{},"state":state,"information":{},"result":result}
        if reason:rec["reason"]=reason
        else:rec["executor_ref"]="authored-local";rec["observation"]={"outputs":{"result":result},"usage":{},"evidence":[]}
        if is_target:rec["state"]=s["state"]
        raw["nodes"].append(rec);prior[n["id"]]=result;raw["final_results"][n["id"]]=result
    return raw
