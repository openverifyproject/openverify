"""Independent stimuli/expectation authoring. No production imports or outputs."""
from __future__ import annotations

import ast
import copy
import importlib.util
import itertools as it
import json
import math
from collections import Counter
from pathlib import Path

from .discover import BLUEPRINT, OUT, ROOT, digest, write_json, write_lines

spec = importlib.util.spec_from_file_location("v4_independent_model", ROOT / "tests/golden_v4/oracle/model.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
CASES = []
CLAUSES = []


def refs(path, text=None):
    matches = [c for c in CLAUSES if c["path"] == path and (text is None or text in str(c["rule"]))]
    return [c["clause_id"] for c in matches]


def add(family, coordinate, action, stimulus, expected, sources, module, mode="cheap", classification=None, obligations=None):
    cid = family + "." + coordinate
    accepted = expected.get("accepted", True) if isinstance(expected, dict) else True
    CASES.append({"case_id": cid, "family": family, "action": action, "stimulus": copy.deepcopy(stimulus),
                  "expected": copy.deepcopy(expected), "classification": classification or ("VALID" if accepted else "INVALID"),
                  "normative_clauses": sources, "obligation_ids": obligations or ["V4.O.CASE." + cid[3:]],
                  "execution_mode": mode, "module": module, "status": "NOT_RUN"})


def accept(family, coord, obj, value, expected, path, module, action="parse", **kw):
    add(family, coord, action, {"object_type":obj,"value":value}, {"accepted":bool(expected)}, refs(path), module, **kw)


def mask_fields(family, obj, values, required, path, module, pointer=None, reduce=False):
    fields = list(values)
    masks = range(1 << len(fields))
    if reduce:
        masks = [mask for mask in masks if all(mask & (1<<fields.index(k)) for k in required)]
        full = (1<<len(fields))-1
        masks += [full ^ (1<<fields.index(k)) for k in required]
    for mask in masks:
        value = {k: v for i,(k,v) in enumerate(values.items()) if mask & (1<<i)}
        valid = set(required) <= value.keys()
        stimulus = {"object_type":obj, "value":value}
        if pointer: stimulus["pointer"] = pointer
        add(family, "BITS_" + format(mask,f"0{len(fields)}b"), "wire" if not pointer else "subschema", stimulus,
            {"accepted":valid}, refs(path), module)


def categorical_cases():
    # Presence is a structural projection, independent of cross-field semantic validity.
    d = m.definition(); d.update(satisfaction_mapping={},metadata={},extensions=[])
    mask_fields("V4.VCP.DEF.PRESENCE", "verification-definition", d,
                list(m.definition()), "schemas/draft/verification-definition.schema.json", "test_vcp_definition")
    mask_fields("V4.VCP.CRITERION.PRESENCE", "verification-definition", {**m.CRITERION,"metadata":{},"extensions":[]},
                ["id","description"], "schemas/draft/verification-definition.schema.json", "test_vcp_definition", "/properties/criterion")
    mask_fields("V4.VCP.ARTIFACT.PRESENCE", "artifact-ref", {**m.ARTIFACT,"schema_id":"v4:schema","metadata":{},"extensions":[]},
                list(m.ARTIFACT), "schemas/draft/artifact-ref.schema.json", "test_vcp_artifact_evidence")
    ev = {"message":"authored", "artifact_ref":m.ARTIFACT,"locator":{},"structured_data":{},"id":"e","metadata":{},"extensions":[]}
    for bits in it.product((0,1), repeat=7):
        value = {k:v for k,v,b in zip(ev,ev.values(),bits) if b}
        accept("V4.VCP.EVIDENCE.MEANING", "BITS_"+"".join(map(str,bits)), "evidence",value,any(bits[:4]),
               "spec/draft/knowledge.md","test_vcp_artifact_evidence")
    for wire in (True,False):
        family = "V4.VCP.RESULT." + ("WIRE_AXIS" if wire else "SEMANTIC_AXIS")
        domains = [("ABSENT", "NULL", *v) if wire else ("ABSENT", *v) for v in m.AXES.values()]
        for disp in m.DISPOSITIONS:
            for coords in it.product(*domains):
                r = {"protocol":"draft","disposition":disp}
                for key,val in zip(m.AXES,coords):
                    if val != "ABSENT": r[key] = None if val == "NULL" else val
                accept(family,"-".join((disp,*coords)),"result",r,m.result_valid(r),"spec/draft/result.md","test_vcp_result_axes")
    obs = {"judgment":None,"score":0.25,"severity":{"domain":"v4:severity:1","label":"low"},
           "evidence":[{"message":"authored"}],"output":None,"usage":{},"metadata":{},"extensions":[]}
    for index, state in enumerate(m.semantic_results()):
        name = "-".join(str(state.get(k,"ABSENT")) for k in ("disposition",*m.AXES))
        for mask in range(256):
            r = {**state, **{k:v for i,(k,v) in enumerate(obs.items()) if mask & (1<<i)}}
            accept("V4.VCP.RESULT.OBS_MASK",name+".BITS_"+format(mask,"08b"),"result",r,m.result_valid(r),
                   "spec/draft/result.md","test_vcp_result_observations")
        add("V4.VCP.RESULT.PROJECTION",name,"flatten",state,{"value":m.flatten(state)},refs("spec/draft/result.md"),"test_vcp_result_axes")
    for kind,dest in it.product(("CONTINUE","STOP_SUCCESS","STOP_FAILURE","ROUTE","RETRY","DEFER"),("ABSENT","NULL","EMPTY","NONEMPTY")):
        value = {"protocol":"draft","kind":kind}
        if dest != "ABSENT": value["destination"] = {"NULL":None,"EMPTY":"","NONEMPTY":"target"}[dest]
        valid = (dest == "NONEMPTY") if kind == "ROUTE" else dest in {"ABSENT","NULL"}
        accept("V4.VCP.DECISION.DEST",kind+"-"+dest,"decision",value,valid,"spec/draft/result.md","test_vcp_decision")
    for kind,role in it.product(m.KINDS,m.ROLES):
        n = m.node(kind=kind)
        permitted = role == "INFORMATION" or (role == "RESULT" and kind in {"EVALUATE","AGGREGATE"}) or (role == "DECISION" and kind == "CONTROL")
        if not any(p["role"] == role for p in n["outputs"]): n["outputs"].append({"name":"aux","schema":True,"role":role})
        accept("V4.VCP.NODE.ROLE",kind+"-"+role,"verification-definition",m.definition([n]),permitted,"spec/draft/dataflow.md","test_vcp_node_roles")
    for kind in ("EVALUATE","AGGREGATE","CONTROL"):
        for mutation in ("VALID","MISSING","WRONG_NAME","DUPLICATE","FALSE_SCHEMA"):
            n = m.node(kind=kind)
            if mutation == "MISSING": n["outputs"] = []
            if mutation == "WRONG_NAME": n["outputs"][0]["name"] = "incorrect"
            if mutation == "DUPLICATE": n["outputs"].append({**n["outputs"][0],"name":"other"})
            if mutation == "FALSE_SCHEMA": n["outputs"][0]["schema"] = False
            accept("V4.VCP.NODE.PRIMARY",kind+"-"+mutation,"verification-definition",m.definition([n]), mutation == "VALID", "spec/draft/dataflow.md","test_vcp_node_roles")
    for kind,state in it.product(("EVALUATE","AGGREGATE"),list(m.semantic_results())):
        name = "-".join(str(state.get(k,"ABSENT")) for k in ("disposition",*m.AXES))
        add("V4.VCP.NODE.INVOKED_RESULT",kind+"-"+name,"invoked_result",{"kind":kind,"result":state},
            {"accepted":state["disposition"] == "EXECUTED"},refs("spec/draft/lifecycle.md"),"test_vcp_node_roles",mode="runtime")
    for req,handler in it.product((False,True),m.HANDLERS):
        n = m.node(); n["inputs"] = [m.port("x",required=req,handler=handler)]; n["bindings"] = {"x":m.constant(None)}
        accept("V4.VCP.PORT.HANDLING",f"REQUIRED{int(req)}-{handler}","verification-definition",m.definition([n]),
               (req and handler == "BLOCK") or (not req and handler != "BLOCK"),"spec/draft/dataflow.md","test_vcp_bindings_sources")
    for present in (False,True):
        n = m.node(); p = m.port("x",required=False,handler="DEFAULT")
        if not present: del p["default"]
        n["inputs"]=[p]
        accept("V4.VCP.PORT.DEFAULT",f"VALUE_PRESENT{int(present)}","verification-definition",m.definition([n]),present,"spec/draft/dataflow.md","test_vcp_bindings_sources")
    for kind in m.SOURCES:
        v = {"CONSTANT":m.constant(None),"RUN_INPUT":{"kind":"RUN_INPUT","name":"x"},
             "EXTERNAL_REFERENCE":{"kind":"EXTERNAL_REFERENCE","reference":m.ARTIFACT},
             "UPSTREAM_OUTPUT":{"kind":"UPSTREAM_OUTPUT","node_id":"a","output":"x"}}[kind]
        accept("V4.VCP.SOURCE.KIND",kind,"value-source",v,True,"spec/draft/dataflow.md","test_vcp_bindings_sources",action="wire")
        for role in ("activation","selection","admission"):
            d=m.definition(); d["run_inputs"]=[m.port("x")]
            d["execution_policy"][role]={"operation":{"capability_id":m.CAPABILITY,"capability_version":"1"},"inputs":[m.port("x")],"bindings":{"x":v},"config":{}}
            accept("V4.VCP.SOURCE.POLICY",kind+"-"+role.upper(),"verification-definition",d,kind != "UPSTREAM_OUTPUT","spec/draft/execution-policy.md","test_vcp_bindings_sources")
    primitive = ("null","boolean","object","array","number","integer","string")
    for a,b in it.product(primitive, repeat=2):
        p=m.node("a"); p["outputs"]=[{"name":"x","role":"INFORMATION","schema":{"type":a}}]
        c=m.node("b"); c["inputs"]=[m.port("x",{"type":b})]; c["bindings"]={"x":{"kind":"UPSTREAM_OUTPUT","node_id":"a","output":"x"}}
        accept("V4.VCP.SCHEMA.PRIMITIVE",a.upper()+"-"+b.upper(),"verification-definition",m.definition([p,c],[{"from_node":"a","to_node":"b"}]),m.primitive_overlap(a,b),"spec/draft/dataflow.md","test_vcp_schemas_guards")
    for n in range(5):
        potential = [(a,b) for a in range(n) for b in range(n) if a != b]
        for mask in range(1<<len(potential)):
            edges=[e for i,e in enumerate(potential) if mask & (1<<i)]
            value=m.definition([m.node(str(i)) for i in range(n)], [{"from_node":str(a),"to_node":str(b)} for a,b in edges])
            accept("V4.VCP.GRAPH.DAG_0_4",f"N{n}.EDGEBITS_"+format(mask,f"0{max(1,len(potential))}b"),"verification-definition",value,m.acyclic(n,edges),"spec/draft/composition.md","test_vcp_graph_structure")
    for mask in range(4):
        d=m.definition();d["graph"]["features"]=[f for i,f in enumerate(("CYCLES","DYNAMIC_EXPANSION")) if mask & (1<<i)]
        accept("V4.VCP.GRAPH.FEATURES",f"BITS_{mask:02b}","verification-definition",d,mask == 0,"spec/draft/composition.md","test_vcp_graph_structure",action="executable")
    for base,arity in [("PRESENCE_BINARY",2),("PRESENCE_TRINARY",3)]:
        for kind,coords in it.product(("EXACT","ESTIMATED","RANGE","UNKNOWN"),it.product(range(arity),repeat=3)):
            v={"unit":"token","kind":kind}
            vals=[]
            for field,c in zip(("value","minimum","maximum"),coords):
                val = None if c == 0 or (arity == 3 and c == 1) else 2
                vals.append(val)
                if c: v[field]=val
            accept("V4.VCP.RESOURCE."+base,kind+"-"+"".join(map(str,coords)),"resource",v,m.resource_valid(kind,vals),"spec/draft/resources.md","test_vcp_resources")
    for relation,maximum in (("LESS",3),("EQUAL",2),("GREATER",1)):
        accept("V4.VCP.RESOURCE.RANGE_ORDER",relation,"resource",{"unit":"u","kind":"RANGE","minimum":2,"maximum":maximum},maximum>=2,"spec/draft/resources.md","test_vcp_resources")
    mask_fields("V4.VCP.EXEC_OBS.PRESENCE","execution-observation",{"outputs":{},"usage":{},"evidence":[],"error":{"code":"e","message":"authored"}},["outputs","usage","evidence"],"schemas/draft/execution-observation.schema.json","test_vcp_resources")
    record={"protocol":"draft","run_id":"v4-run","definition":m.definition(),"definition_fingerprint":"local-sha256:"+"0"*64,
            "subject":m.ARTIFACT,"initial_context":{},"run_inputs":{},"opportunity_id":"authored","admission":{"outcome":"RUN","reason":"authored"},
            "policy_evaluations":[],"started_at":"2026-01-01T00:00:00Z","finished_at":"2026-01-01T00:00:01Z","nodes":[],"final_results":{}}
    rr={**record,"cancellation":{"node_id":"n","phase":"BEFORE_START","reason":"authored"},"provider_bindings":{},"metadata":{},"extensions":[]}
    mask_fields("V4.VCP.RUN_RECORD.PRESENCE","run-record",rr,list(record),"schemas/draft/run-record.schema.json","test_vcp_records",reduce=True)
    nr={"node_id":"n","kind":"DERIVE","operation":{"capability_id":m.CAPABILITY,"capability_version":"1"},"upstream_node_ids":[],"upstream_results":{},"input_values":{},"input_resolutions":{},"started_at":"2026-01-01T00:00:00Z","finished_at":"2026-01-01T00:00:01Z","usage":{},"state":"SUCCESS","information":{}}
    nv={**nr,"executor_ref":"local","executor_version":"1","provider_binding":{"provider_id":m.PROVIDER,"provider_version":"1","capability_id":m.CAPABILITY,"capability_version":"1"},"provider_output_error":{"code":"INVALID_PROVIDER_OUTPUT","message":"authored"},"reason":"authored","observation":{"outputs":{},"usage":{},"evidence":[]},"result":m.known(),"decision":{"protocol":"draft","kind":"CONTINUE"}}
    mask_fields("V4.VCP.NODE_RECORD.PRESENCE","run-record",nv,list(nr),"schemas/draft/run-record.schema.json","test_vcp_records","/properties/nodes/items",reduce=True)


def provider_cases():
    for flags in it.product((False,True),repeat=4):
        stream,cancel,deadline,resource=flags
        value=m.manifest(stream,resource,True,cancel,deadline)
        accept("V4.PROVIDER.FEATURE_FLAGS","BITS_"+"".join(str(int(v)) for v in flags),"provider-manifest",value,True,"provider-contract/spec/draft/capabilities.md","test_provider_manifest_capability")
    for declared,support in it.product((False,True),repeat=2):
        v=m.manifest(vcp=declared);v["supported_vcp_versions"]=["draft"] if support else []
        accept("V4.PROVIDER.VCP_COMPAT",f"DECLARED{int(declared)}-SUPPORTED{int(support)}","provider-manifest",v,not declared or support,"provider-contract/spec/draft/capabilities.md","test_provider_manifest_capability")
    for feature,present in it.product((False,True),repeat=2):
        v=m.invocation()
        if present: v["deadline"]="2026-01-01T00:00:00Z"
        add("V4.PROVIDER.INVOKE.DEADLINE",f"FEATURE{int(feature)}-PRESENT{int(present)}","provider_invocation",{"manifest":m.manifest(deadlines=feature),"invocation":v},{"accepted":not present or feature},refs("provider-contract/spec/draft/capabilities.md"),"test_provider_init_invoke")
    for present,vcp in it.product((False,True),repeat=2):
        v=m.invocation(vcp)
        if present: v["resource_budget"]={"tokens":{"unit":"token","kind":"EXACT","value":4}}
        add("V4.PROVIDER.INVOKE.BUDGET",f"PRESENT{int(present)}-VCP{int(vcp)}","provider_invocation",{"manifest":m.manifest(vcp=vcp),"invocation":v},{"accepted":not present or vcp},refs("provider-contract/spec/draft/versioning.md"),"test_provider_init_invoke")
    for state,out,err in it.product(m.TERMINALS,(False,True),(False,True)):
        value={"invocation_id":"v4-attempt","state":state}
        if out: value["output"]=None
        if err: value["error"]={"code":"com.example.golden.failed","message":"authored"}
        valid=out == (state == "COMPLETED") and err == (state == "ERROR")
        accept("V4.PROVIDER.OUTCOME.SHAPE",f"{state}-OUTPUT{int(out)}-ERROR{int(err)}","outcome",value,valid,"provider-contract/spec/draft/wire-format.md","test_provider_events_outcomes")
    for present,state,resource,vcp in it.product((False,True),m.TERMINALS,(False,True),(False,True)):
        value={"invocation_id":"v4-attempt","state":state}
        if state == "COMPLETED": value["output"]=None
        if state == "ERROR": value["error"]={"code":"com.example.golden.failed","message":"authored"}
        if present: value["resource_usage"]={}
        add("V4.PROVIDER.OUTCOME.USAGE",f"PRESENT{int(present)}-{state}-RESOURCE{int(resource)}-VCP{int(vcp)}","provider_outcome",{"manifest":m.manifest(resource=resource,vcp=vcp),"invocation":m.invocation(vcp),"outcome":value},{"accepted":not present or (resource and vcp)},refs("provider-contract/spec/draft/capabilities.md")+refs("provider-contract/spec/draft/versioning.md"),"test_provider_events_outcomes")
    for kind,stream,resource,vcp in it.product(m.EVENTS,(False,True),(False,True),(False,True)):
        event={"invocation_id":"v4-attempt","sequence":1,"kind":kind,"payload":m.payload(kind)}
        add("V4.PROVIDER.EVENT.ELIGIBILITY",f"{kind.upper()}-STREAM{int(stream)}-RESOURCE{int(resource)}-VCP{int(vcp)}","provider_event",{"manifest":m.manifest(stream,resource,vcp),"invocation":m.invocation(vcp),"event":event},{"accepted":m.event_allowed(kind,stream,resource,vcp)},refs("provider-contract/spec/draft/capabilities.md")+refs("provider-contract/spec/draft/versioning.md"),"test_provider_events_outcomes")
    for state,cancelled,phase in it.product(m.TERMINALS,(False,True),("ABSENT","UNEXPIRED","EXPIRED")):
        add("V4.PROVIDER.DEADLINE.RACE",f"{state}-CANCEL{int(cancelled)}-{phase}","provider_terminal",{"state":state,"cancelled":cancelled,"deadline_phase":phase},{"accepted":m.terminal_allowed(state,cancelled,phase)},refs("provider-contract/spec/draft/lifecycle.md"),"test_provider_lifecycle")
    for correlation,action in it.product(("UNSEEN","REJECTED","RUNNING","TERMINAL"),("ACCEPT","EVENT","CANCEL","OUTCOME")):
        valid=(correlation == "UNSEEN" and action == "ACCEPT") or (correlation == "RUNNING" and action in {"EVENT","CANCEL","OUTCOME"}) or (correlation == "TERMINAL" and action == "CANCEL")
        add("V4.PROVIDER.ATTEMPT.TRANSITION",correlation+"-"+action,"provider_transition",{"correlation":correlation,"action":action},{"accepted":valid},refs("provider-contract/spec/draft/lifecycle.md"),"test_provider_lifecycle")
    for correlation,feature in it.product(("UNSEEN","REJECTED","RUNNING","TERMINAL"),(False,True)):
        add("V4.PROVIDER.CANCEL.ELIGIBILITY",f"{correlation}-FEATURE{int(feature)}","provider_cancel",{"correlation":correlation,"feature":feature},{"accepted":correlation == "TERMINAL" or (correlation == "RUNNING" and feature)},refs("provider-contract/spec/draft/lifecycle.md"),"test_provider_lifecycle")
    for name,versions,expected in [("COMMON",["0.1"],True),("REJECT",["other"],False),("PREFERENCE",["other","0.1"],True)]:
        add("V4.PROVIDER.INIT",name,"provider_init",{"versions":versions},{"accepted":expected,"version":"0.1" if expected else None},refs("provider-contract/spec/draft/versioning.md"),"test_provider_init_invoke")
    for seq,valid in [(1,True),(1.0,True),(0,False),(-1,False),(9007199254740991,True),(9007199254740992,False),(True,False),("1",False),(1.5,False)]:
        accept("V4.PROVIDER.EVENT.SEQUENCE",type(seq).__name__.upper()+"-"+str(seq),"provider-event",{"invocation_id":"v4-attempt","sequence":seq,"kind":"progress","payload":None},valid,"provider-contract/spec/draft/wire-format.md","test_provider_events_outcomes")


def aggregate_cases():
    for reducer,mask in it.product(m.REDUCERS, range(128)):
        handling={k:"IGNORE" if mask & (1<<i) else "REJECT" for i,k in enumerate(m.EXCEPTIONS)}
        add("V4.VCP.AGG.HANDLING_MAP",reducer+f".MASK_{mask:07b}","reduce",{"reducer":reducer,"handling":handling,"values":[m.known(verdict="PASS",score=0.25,severity={"domain":m.SEVERITY["id"],"label":"low"})],"weights":[2]},m.reduce_values(reducer,["PASS"] if reducer in m.REDUCERS[:3] else (["low"] if reducer == "WORST_SEVERITY" else [0.25]),[2]),refs("spec/draft/aggregation.md"),"test_vcp_aggregation")
    for reducer,category,action in it.product(m.REDUCERS,m.EXCEPTIONS,("REJECT","IGNORE")):
        good=m.known(verdict="PASS",score=0.25,severity={"domain":m.SEVERITY["id"],"label":"low"},evidence=[{"message":"retained"}])
        handling={k:"REJECT" for k in m.EXCEPTIONS};handling[category]=action
        expected={"error":"AGGREGATE_INPUT"} if action == "REJECT" else {**m.reduce_values(reducer,["PASS"] if reducer in m.REDUCERS[:3] else (["low"] if reducer == "WORST_SEVERITY" else [0.25]),[2]),"evidence":[{"message":"retained"}]}
        add("V4.VCP.AGG.EXCEPTION",reducer+"-"+category+"-"+action,"reduce",{"reducer":reducer,"handling":handling,"values":[good,m.exceptional(category)],"weights":[2,7]},expected,refs("spec/draft/aggregation.md"),"test_vcp_aggregation")
    for reducer in m.REDUCERS[:3]:
        for n in range(1,6):
            for vals in it.product(("PASS","FAIL"),repeat=n):
                add("V4.VCP.AGG.LOGICAL",reducer+"-"+"-".join(vals),"reduce",{"reducer":reducer,"values":[m.known(verdict=v) for v in vals]},m.reduce_values(reducer,vals),refs("spec/draft/aggregation.md"),"test_vcp_aggregation")
    for reducer in m.REDUCERS[3:7]:
        for vals in [(0,1),(0.25,0.75),(0,0),(1,1),(0.5,0.5)]:
            weights=[1,3]
            add("V4.VCP.AGG.SCORE",reducer+"-"+"-".join(map(str,vals)),"reduce",{"reducer":reducer,"values":[m.known(score=v) for v in vals],"weights":weights},m.reduce_values(reducer,vals,weights),refs("spec/draft/aggregation.md"),"test_vcp_aggregation")
    for weights in it.product((-1,0,2),repeat=2):
        add("V4.VCP.AGG.WEIGHT_SIGN_2","-".join(map(str,weights)),"reduce",{"reducer":"WEIGHTED_AVERAGE","values":[m.known(score=0.25),m.known(score=0.75)],"weights":list(weights)},m.reduce_values("WEIGHTED_AVERAGE",[0.25,0.75],weights),refs("spec/draft/aggregation.md"),"test_vcp_aggregation")
    for n in range(1,5):
        for labels in it.product(("low","high"),repeat=n):
            add("V4.VCP.AGG.SEVERITY","-".join(labels),"reduce",{"reducer":"WORST_SEVERITY","values":[m.known(severity={"domain":m.SEVERITY["id"],"label":v}) for v in labels]},m.reduce_values("WORST_SEVERITY",labels),refs("spec/draft/aggregation.md"),"test_vcp_aggregation")


def other_cases():
    roots=json.loads((OUT/"NORMATIVE_SOURCE_HASHES.json").read_text())["schema_roots"]
    for layer,paths in roots.items():
        for path in paths:
            add("V4.WIRE.ROOTS",layer+"-"+Path(path).stem,"schema_root",{"path":path},{"accepted":True,"id":json.loads((ROOT/path).read_text())["$id"]},refs(path),"test_vcp_wire")
    for entry in json.loads((OUT/"ERROR_INVENTORY.json").read_text())["declarations"]:
        add("V4.ERROR.NAMES",entry["declaration_id"].removeprefix("V4.ERROR."),"error_name",entry,{"identifier":entry["identifier"],"authority":entry["authority"]},[],"test_errors_extensions",obligations=entry["obligation_ids"])
    for state in m.semantic_results():
        for role in ("EVALUATE","AGGREGATE"):
            for terminal in ("SUCCESS","ERROR","NONEXECUTED","CANCELLED"):
                disp=state["disposition"]
                compatible = ((terminal == "SUCCESS" and disp == "EXECUTED" and state["execution_outcome"] == "SUCCESS") or (terminal == "ERROR" and disp == "EXECUTED" and state["execution_outcome"] == "ERROR") or (terminal == "NONEXECUTED" and disp != "EXECUTED") or (terminal == "CANCELLED" and disp == "CANCELLED"))
                # Full semantic refinement; disposition-only projection is separately counted.
                name="-".join(str(state.get(k,"ABSENT")) for k in ("disposition",*m.AXES))
                add("V4.VCP.LIFECYCLE.RESULT",role+"-"+terminal+"-"+name,"record_compatibility",{"kind":role,"state":terminal,"result":state},{"accepted":compatible},refs("spec/draft/lifecycle.md"),"test_vcp_lifecycle_cancel")
    for required,support in it.product((False,True),repeat=2):
        add("V4.VCP.EXT.REQUIRED",f"REQUIRED{int(required)}-SUPPORTED{int(support)}","extension",{"required":required,"supported":support},{"accepted":not required or support},refs("spec/draft/extensions.md"),"test_errors_extensions")
    for a,b in it.product((False,True),repeat=2):
        add("V4.VCP.GUARD.BOOL",f"{str(a).upper()}-{str(b).upper()}","guard",{"left":a,"right":b},{"value":a == b},refs("spec/draft/dataflow.md"),"test_vcp_schemas_guards",mode="runtime")
    for req in (True,False):
        for status,handler,default,present in it.product(m.STATUSES,m.HANDLERS,(False,True),(False,True)):
            if not req: break
            usable=status == "AVAILABLE"
            valid=(not default and present) if usable else ((default and present) if handler == "DEFAULT" else (not default and not present))
            add("V4.VCP.RESOLVE.RECORD_BITS",f"{status}-{handler}-DEFAULT{int(default)}-VALUE{int(present)}","resolution_record",{"status":status,"handler":handler,"used_default":default,"present":present},{"accepted":valid},refs("spec/draft/dataflow.md"),"test_vcp_resolution")
    # Remaining families have explicitly authored witnesses, not invented finite totals.
    witness_families={
        "V4.WIRE.JSON":"test_vcp_wire", "V4.VCP.RESULT.VALUES":"test_vcp_result_observations",
        "V4.VCP.DECISION.ROUTE":"test_vcp_decision", "V4.VCP.BIND.IDENTITY":"test_vcp_bindings_sources",
        "V4.VCP.RESOLVE.HANDLER":"test_vcp_resolution", "V4.VCP.RESOLVE.CONSUMER":"test_vcp_resolution",
        "V4.VCP.RESOLVE.RAW":"test_vcp_resolution", "V4.VCP.RESOLVE.UNBOUND":"test_vcp_resolution",
        "V4.VCP.SCHEMA.FULL":"test_vcp_schemas_guards", "V4.VCP.GUARD.OPERATOR":"test_vcp_schemas_guards",
        "V4.VCP.GUARD.SOURCE":"test_vcp_schemas_guards", "V4.VCP.GUARD.POINTER":"test_vcp_schemas_guards",
        "V4.VCP.GRAPH.DEFINITION":"test_vcp_graph_structure", "V4.VCP.AGG.MEMBER_ROLE":"test_vcp_aggregation",
        "V4.VCP.AGG.SEMANTIC":"test_vcp_aggregation", "V4.VCP.AGG.WEIGHT_GENERAL":"test_vcp_aggregation",
        "V4.VCP.AGG.WEIGHT_IDENTITY":"test_vcp_aggregation", "V4.VCP.POLICY.DECLARATIONS":"test_vcp_policies",
        "V4.VCP.POLICY.PATH":"test_vcp_policies", "V4.VCP.POLICY.ROLE_RESULT":"test_vcp_policies",
        "V4.VCP.POLICY.EVAL_ORDER":"test_vcp_policies", "V4.VCP.RECORD.LINEAGE":"test_vcp_records",
        "V4.VCP.LIFECYCLE.PHASES":"test_vcp_lifecycle_cancel", "V4.VCP.LIFECYCLE.REASON":"test_vcp_lifecycle_cancel",
        "V4.VCP.CANCEL.ELIGIBILITY":"test_vcp_lifecycle_cancel", "V4.PROVIDER.TRANSPORT.METHOD":"test_provider_transport",
        "V4.RELAY.PORTS":"test_relay_ports_catalog_binder", "V4.RELAY.SCHEDULER":"test_relay_scheduler",
        "V4.RELAY.ENTRYPOINT":"test_entrypoints"}
    write_json(OUT/"AUTHORING_REMAINDER.json",witness_families)


def main():
    global CLAUSES
    assert not (OUT/"FROZEN_EXPECTATIONS/MANIFEST.json").exists(), "Immutable freeze already exists"
    CLAUSES=[json.loads(s) for s in (OUT/"NORMATIVE_CLAUSES.jsonl").read_text(encoding="utf-8").splitlines()]
    categorical_cases();provider_cases();aggregate_cases();other_cases()
    from .witness_authoring import author
    author(add,accept,refs,m)
    ids=[c["case_id"] for c in CASES];assert len(ids)==len(set(ids)),"Duplicate case ID"
    write_lines(OUT/"CASES.jsonl",CASES)
    totals={family:dict(Counter(c["classification"] for c in CASES if c["family"]==family)) for family in sorted({c["family"] for c in CASES})}
    write_json(OUT/"DERIVED_COUNTS.json",totals)
    print(json.dumps({"authored_cases":len(CASES),"families_with_cases":len(totals)}))


if __name__ == "__main__": main()
