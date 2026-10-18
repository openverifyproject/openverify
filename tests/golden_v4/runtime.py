"""Real Relay execution with contract-compliant authored providers and barriers."""
from __future__ import annotations

import asyncio
import copy
import time
from pathlib import Path

from openverify import Relay, ProtocolError, parse_definition, parse_run_record
from openverify.lifecycle import Cancellation
from openverify.provider import Outcome, ProviderError, ProviderEvent, parse_provider_manifest
from openverify.serialization import to_data
from openverify.relay.adapters.catalog import Catalog
from openverify.relay.adapters.memory import MemoryStore
from openverify.relay.adapters.logging import CallbackObserver
from openverify.relay.config import RuntimeConfig

from .oracle import model as m
from .sut import accepted


class ScriptedProvider:
    """Only legal Provider Events/Outcomes. VCP rejection is a separate host boundary."""
    def __init__(self,outputs,calls=None,hook=None,events=None,usage=None,manifest=None):
        self.outputs=outputs;self.calls=calls if calls is not None else [];self.hook=hook
        self.events=events or [];self.usage=usage;self.specification=parse_provider_manifest(manifest or m.manifest())
        self.cancelled=set()

    def manifest(self):return self.specification

    async def cancel(self,invocation_id,reason=None):self.cancelled.add(invocation_id)

    async def invoke(self,invocation):
        key=invocation.config.get("v4_node","n")
        values=copy.deepcopy(invocation.input);config=copy.deepcopy(invocation.config)
        self.calls.append((key,values,config,invocation.invocation_id))
        if self.hook:await self.hook(key,invocation)
        for seq,kind,payload in self.events:
            yield ProviderEvent(invocation_id=invocation.invocation_id,sequence=seq,kind=kind,payload=copy.deepcopy(payload))
        output={"result":m.known(verdict="PASS")} if key.startswith("v4_seed_") else self.outputs[key]
        if callable(output):output=output(values)
        if isinstance(output,Exception):
            yield Outcome(invocation_id=invocation.invocation_id,state="ERROR",error=ProviderError(code="com.example.golden.failed",message=str(output)),**({"resource_usage":self.usage} if self.usage is not None else {}))
        else:
            yield Outcome(invocation_id=invocation.invocation_id,state="COMPLETED",output=copy.deepcopy(output),**({"resource_usage":self.usage} if self.usage is not None else {}))


def catalog_for(outputs,calls=None,hook=None,events=None,usage=None,manifest=None,concurrent=True):
    c=Catalog();c.register(ScriptedProvider(outputs,calls,hook,events,usage,manifest),concurrency_safe=concurrent);return c


def configured(d):
    d=copy.deepcopy(d)
    for n in d["graph"]["nodes"]:
        if n["operation"]["capability_id"]!="openverify.aggregate":n["config"]={**n.get("config",{}),"v4_node":n["id"]}
    for role,p in d["execution_policy"].items():
        if "operation" in p:p["config"]={**p.get("config",{}),"v4_node":role.upper()}
    return parse_definition(d)


async def run(relay,d,node,inputs=None,**kw):
    node.v4_relay_calls=getattr(node,"v4_relay_calls",0)+1
    start=time.monotonic()
    d=copy.deepcopy(d)
    try:return await relay.run(configured(d),inputs=inputs or {},opportunity_id="v4-authored-opportunity",**kw)
    finally:node.v4_relay_seconds=getattr(node,"v4_relay_seconds",0)+time.monotonic()-start


def primary(kind):
    if kind in {"EVALUATE","AGGREGATE"}:return {"result":m.known(verdict="PASS")}
    if kind=="CONTROL":return {"decision":{"protocol":"draft","kind":"CONTINUE"}}
    return {}


async def simple_record(node,kind="DERIVE",result=None,outputs=None):
    n=m.node("n",kind)
    out=primary(kind) if outputs is None else outputs
    if result is not None:out={"result":result}
    relay=Relay(catalog=catalog_for({"n":out}))
    return (await run(relay,m.definition([n]),node)).record


async def resolve(s,node):
    kind,status,handler=s["kind"],s["status"],s["handler"]
    producer=m.node("p");producer["outputs"]=[{"name":"value","schema":True,"role":"INFORMATION"}]
    consumer=m.node("c",kind)
    target_schema={"type":"integer"}
    p=m.port("x",target_schema,required=handler=="BLOCK",handler=handler)
    if handler=="DEFAULT":p["default"]=m.constant(29)
    consumer["inputs"].append(p)
    d=m.definition([producer,consumer],[{"from_node":"p","to_node":"c"}])
    inputs={};pout={"value":17}
    if status=="ABSENT":
        d["run_inputs"]=[m.port("optional",required=False)]
        consumer["bindings"]["x"]={"kind":"RUN_INPUT","name":"optional"}
    else:consumer["bindings"]["x"]={"kind":"UPSTREAM_OUTPUT","node_id":"p","output":"value"}
    if status=="PRODUCER_NOT_EXECUTED":
        # Guard disables producer. Edges alone do not propagate this to consumers.
        root=m.node("root");d["graph"]["nodes"].insert(0,root)
        d["graph"]["edges"].insert(0,{"from_node":"root","to_node":"p","guard":{"source":m.constant(True),"pointer":"","value":False}})
    if status=="PRODUCER_ERROR":pout=RuntimeError("authored execution failure")
    if status=="OUTPUT_MISSING":pout={}
    if status=="INVALID":pout={"value":"authored wrong target type"}
    calls=[];outputs={"p":pout,"c":primary(kind),"root":{}}
    record=(await run(Relay(catalog=catalog_for(outputs,calls)),d,node,inputs)).record
    rec=next(r for r in record.nodes if r.node_id=="c")
    resolution=rec.input_resolutions["x"]
    invoked=any(c[0]=="c" for c in calls)
    actual={"status":resolution.status,"invoked":invoked,"used_default":resolution.used_default}
    if invoked:
        sent=next(c[1] for c in calls if c[0]=="c")
        if resolution.status=="AVAILABLE":assert sent["x"]==17
        elif handler=="DEFAULT":assert sent["x"]==29
        else:assert "x" not in sent
        assert to_data(resolution.source)==consumer["bindings"]["x"]
        assert rec.input_values==sent
    else:
        assert rec.reason=="INPUT_UNAVAILABLE"
        assert rec.observation is None
        assert "c" not in record.provider_bindings
    parse_run_record(to_data(record))
    return actual


def resolution_bits(s,node):
    # Probe the actual resolver on local snapshots; these are conditional local
    # resolution objects, not malformed external Provider streams.
    from openverify.dataflow import resolve_inputs
    from openverify.model import Graph, Node, NodeRecord
    n=m.node("c");p=m.port("x",required=s["handler"]=="BLOCK",handler=s["handler"])
    if s["handler"]=="DEFAULT":p["default"]=m.constant(None)
    n["inputs"]=[p]
    status=s["status"]
    n["bindings"]={"x":{"kind":"UPSTREAM_OUTPUT","node_id":"p","output":"value"}}
    producer=m.node("p");producer["outputs"]=[{"name":"value","role":"INFORMATION","schema":True}]
    nr={"node_id":"p","kind":"DERIVE","operation":producer["operation"],"upstream_node_ids":[],"upstream_results":{},"input_values":{},"input_resolutions":{},"started_at":"2026-01-01T00:00:00Z","finished_at":"2026-01-01T00:00:01Z","usage":{},"state":"SUCCESS","information":{}}
    if status=="AVAILABLE":nr["information"]={"value":None}
    if status=="ABSENT":n["bindings"]={}
    if status=="PRODUCER_NOT_EXECUTED":nr["state"]="NONEXECUTED"
    if status=="PRODUCER_ERROR":nr["state"]="ERROR"
    if status=="OUTPUT_MISSING":nr.update(state="ERROR",reason="OUTPUT_MISSING")
    if status=="INVALID":nr.update(state="ERROR",reason="OUTPUT_INVALID",observation={"outputs":{"value":"wrong"},"usage":{},"evidence":[]})
    _,resolutions,_=resolve_inputs(Node.model_validate(n),{}, {"p":NodeRecord.model_validate(nr)},Graph.model_validate({"nodes":[producer,n],"edges":[{"from_node":"p","to_node":"c"}]}))
    observed=resolutions["x"]
    return {"accepted":observed.status==status and observed.used_default==s["used_default"] and ("value" in observed.model_fields_set)==s["present"]}


def custom_policy(role):return {"operation":{"capability_id":m.CAPABILITY,"capability_version":"1"},"inputs":[],"bindings":{},"config":{}}


async def policy_path(s,node):
    path=s["path"];d=m.definition([m.node("n")]);calls=[]
    for role in ("activation","selection","admission"):d["execution_policy"][role]=custom_policy(role)
    outputs={"ACTIVATION":{"outcome":"DO_NOT_ACTIVATE" if path=="INACTIVE" else "ACTIVATE","reason":"authored activation"},
             "SELECTION":{"subjects":[] if path=="UNSELECTED" else [m.ARTIFACT],"reason":"authored selection"},
             "ADMISSION":{"outcome":path if path in {"RUN","SKIP","DEFER"} else "RUN","reason":"authored admission"},"n":{}}
    store=MemoryStore();relay=Relay(catalog=catalog_for(outputs,calls),store=store)
    try:
        record=(await run(relay,d,node)).record
        assert [p.role for p in record.policy_evaluations]==["ACTIVATION","SELECTION","ADMISSION"]
        assert to_data(record.subject)==m.ARTIFACT
        assert store.get(record.run_id)==record
        for p in record.policy_evaluations:assert to_data(p.outcome)==outputs[p.role]
        if path!="RUN":
            assert record.nodes[0].reason=="ADMISSION_"+path
            assert record.nodes[0].observation is None
        return {"admission":record.admission.outcome,"invoked":any(c[0]=="n" for c in calls)}
    except ProtocolError as exc:
        if exc.code!="NO_OCCURRENCE":raise
        assert not any(c[0]=="n" for c in calls)
        assert [c[0] for c in calls]==(["ACTIVATION"] if path=="INACTIVE" else ["ACTIVATION","SELECTION"])
        return {"admission":None,"invoked":False}


async def route(s,node):
    control=m.node("control","CONTROL");a=m.node("a");b=m.node("b");join=m.node("join");independent=m.node("independent")
    edges=[{"from_node":"control","to_node":"a"},{"from_node":"control","to_node":"b"},{"from_node":"a","to_node":"join"},{"from_node":"b","to_node":"join"}]
    target="join" if s["scenario"]=="NON_SUCCESSOR" else "a"
    d=m.definition([control,a,b,join,independent],edges);calls=[]
    out={"control":{"decision":{"protocol":"draft","kind":"ROUTE","destination":target}},"a":{},"b":{},"join":{},"independent":{}}
    record=(await run(Relay(catalog=catalog_for(out,calls)),d,node)).record
    nr={r.node_id:r for r in record.nodes}
    if target=="join":return {"accepted":nr["control"].state=="SUCCESS"}
    assert nr["b"].reason=="ROUTE_EXCLUDED"
    assert {key for key,*_ in calls}=={"control","a","join","independent"}
    assert nr["join"].state=="SUCCESS" and nr["independent"].state=="SUCCESS"
    assert nr["control"].decision.destination=="a"
    return {"accepted":True}


async def guard_case(action,s,node):
    p=m.node("p");c=m.node("c");source=m.constant(s.get("left",True));pointer="";value=s.get("right",True);inputs={}
    if action=="guard_pointer":source=s["source"];pointer=s["pointer"];value=s["value"]
    if action=="guard_source":
        source={"CONSTANT":m.constant(True),"RUN_INPUT":{"kind":"RUN_INPUT","name":"x"},
                "EXTERNAL_REFERENCE":{"kind":"EXTERNAL_REFERENCE","reference":m.ARTIFACT},"UPSTREAM_OUTPUT":{"kind":"UPSTREAM_OUTPUT","node_id":"p","output":"value"}}[s["source_kind"]]
        if s["source_kind"]=="EXTERNAL_REFERENCE":value=m.ARTIFACT
    d=m.definition([p,c],[{"from_node":"p","to_node":"c","guard":{"source":source,"pointer":pointer,"value":value}}])
    if source["kind"]=="RUN_INPUT":d["run_inputs"]=[m.port("x",required=False)];inputs={"x":True} if action=="guard_source" else {}
    if source["kind"]=="UPSTREAM_OUTPUT":p["outputs"]=[{"name":"value","role":"INFORMATION","schema":True}]
    calls=[];out={"p":{"value":True} if p["outputs"] else {},"c":{}}
    rec=(await run(Relay(catalog=catalog_for(out,calls)),d,node,inputs)).record
    invoked=any(key=="c" for key,*_ in calls)
    c_record=next(n for n in rec.nodes if n.node_id=="c")
    if not invoked:assert c_record.reason=="GUARD_FALSE" and c_record.observation is None
    return {"value":invoked} if action=="guard" else {"invoked":invoked}


async def motif(name,node):
    if name=="ROUTE":await route({"scenario":"SHARED_JOIN"},node);return
    if name=="AGG_FANIN":
        await aggregate_fanin(node);return
    if name=="STOP_CANCEL":await cancellation_witness(node);return
    if name=="MULTIRUN":
        entered=set();both=asyncio.Event();calls=[]
        async def hook(key,inv):
            entered.add(inv.input["x"])
            if len(entered)==2:both.set()
            await asyncio.wait_for(both.wait(),5)
        n=m.node();n["inputs"]=[m.port("x")];n["bindings"]={"x":{"kind":"RUN_INPUT","name":"x"}};n["outputs"]=[{"name":"value","schema":True,"role":"INFORMATION"}]
        d=m.definition([n]);d["run_inputs"]=[m.port("x")]
        relay=Relay(catalog=catalog_for({"n":lambda inputs:{"value":inputs["x"]}},calls,hook))
        a,b=await asyncio.gather(run(relay,d,node,{"x":"alpha"}),run(relay,d,node,{"x":"beta"}))
        assert a.record.run_id!=b.record.run_id
        for r,value in [(a,"alpha"),(b,"beta")]:
            assert r.record.run_inputs=={"x":value}
            assert r.record.nodes[0].input_values=={"x":value}
            assert r.record.nodes[0].information=={"value":value}
            assert relay.store.get(r.record.run_id)==r.record
        assert len({call[3] for call in calls})==2
        return
    shapes={"INDEPENDENT":(["a","b"],[]),"EDGE":(["a","b"],[("a","b")]),"CHAIN":(["a","b","c"],[("a","b"),("b","c")]),
            "FORK":(["a","b","c"],[("a","b"),("a","c")]),"JOIN":(["a","b","c"],[("a","c"),("b","c")]),
            "DIAMOND":(["a","b","c","d"],[("a","b"),("a","c"),("b","d"),("c","d")]),
            "GUARDED_JOIN":(["a","b","c"],[("a","c"),("b","c")]),"PARALLEL_BARRIER":(["a","b","control","c"],[])}
    names,pairs=shapes[name];nodes={key:m.node(key,"CONTROL" if key=="control" else "DERIVE") for key in names}
    expected_inputs={};outputs={};calls=[];settled=set();entered=set();both=asyncio.Event()
    for key,n in nodes.items():
        if key=="control":outputs[key]=primary("CONTROL");expected_inputs[key]={};continue
        n["outputs"]=[{"name":"value","schema":True,"role":"INFORMATION"}]
        n["inputs"]=[m.port("authored")];n["bindings"]={"authored":m.constant({"node":key})}
        expected_inputs[key]={"authored":{"node":key}}
        for source,target in pairs:
            if target==key:
                field="from_"+source;n["inputs"].append(m.port(field));n["bindings"][field]={"kind":"UPSTREAM_OUTPUT","node_id":source,"output":"value"}
                expected_inputs[key][field]={"producer":source,"value":[source,17]}
        outputs[key]={"value":{"producer":key,"value":[key,17]}}
    async def hook(key,inv):
        assert inv.input==expected_inputs[key]
        for a,b in pairs:
            if b==key:assert a in settled
        if name in {"INDEPENDENT","PARALLEL_BARRIER"} and key in {"a","b"}:
            entered.add(key)
            if entered=={"a","b"}:both.set()
            await asyncio.wait_for(both.wait(),5)
        if name=="PARALLEL_BARRIER" and key=="control":assert {"a","b"}<=settled
        if name=="PARALLEL_BARRIER" and key=="c":assert "control" in settled
        settled.add(key)
    edges=[{"from_node":a,"to_node":b} for a,b in pairs]
    if name=="GUARDED_JOIN":edges[0]["guard"]={"source":m.constant(True),"pointer":"","value":False}
    record=(await run(Relay(catalog=catalog_for(outputs,calls,hook),config=RuntimeConfig(max_concurrency=4)),m.definition(list(nodes.values()),edges),node)).record
    for r in record.nodes:
        assert r.input_values==expected_inputs[r.node_id]
        if name=="GUARDED_JOIN" and r.node_id=="c":
            assert r.reason=="GUARD_FALSE" and r.observation is None;continue
        assert r.state=="SUCCESS"
        if r.kind=="DERIVE":assert r.information==outputs[r.node_id]
        assert r.provider_binding.provider_id==m.PROVIDER and r.provider_binding.provider_version=="1"
        assert r.executor_ref==m.PROVIDER and r.executor_version=="1"
        for field,resolution in r.input_resolutions.items():
            assert resolution.value==expected_inputs[r.node_id][field]
    # Reference wave acceptance order is the authored order, irrespective of completions.
    assert [r.node_id for r in record.nodes]==names
    assert len({c[3] for c in calls})==len(calls)
    parse_run_record(to_data(record))


async def aggregate_fanin(node):
    a=m.node("a","EVALUATE");b=m.node("b","EVALUATE");agg=m.node("aggregate","AGGREGATE")
    agg["operation"]={"capability_id":"openverify.aggregate","capability_version":"1"}
    agg["aggregate_inputs"]=["second","first"]
    agg["bindings"]["members"]=m.constant(["second","first"])
    for name,p in [("second","b"),("first","a")]:
        agg["inputs"].append(m.port(name));agg["bindings"][name]={"kind":"UPSTREAM_OUTPUT","node_id":p,"output":"result"}
    agg["config"]={"reducer":"WEIGHTED_AVERAGE","handling":{k:"REJECT" for k in m.EXCEPTIONS},"weights":{"first":1,"second":3}}
    from openverify.standard import standard_catalog
    catalog=standard_catalog()
    catalog.register(ScriptedProvider({"a":{"result":m.known(score=0.25,evidence=[{"message":"a"}])},"b":{"result":m.known(score=0.75,evidence=[{"message":"b"}])}}),concurrency_safe=True)
    r=(await run(Relay(catalog=catalog),m.definition([a,b,agg],[{"from_node":"a","to_node":"aggregate"},{"from_node":"b","to_node":"aggregate"}]),node)).record
    assert r.final_results["aggregate"].score==0.625
    assert [e.message for e in r.final_results["aggregate"].evidence]==["b","a"]
    assert r.nodes[-1].input_values["members"]==["second","first"]
    assert r.nodes[-1].input_values["subject"]==m.ARTIFACT
    assert r.nodes[-1].input_values["criterion"]==m.CRITERION


async def cancellation_witness(node,phase="RUNNING",admission="RUN"):
    token=Cancellation();calls=[];started=asyncio.Event()
    async def hook(key,inv):
        if key=="b" and phase=="RUNNING":started.set();token.cancel("authored cancellation")
    d=m.definition([m.node("a"),m.node("b"),m.node("c")],[{"from_node":"a","to_node":"b"},{"from_node":"b","to_node":"c"}])
    if admission!="RUN":
        d["execution_policy"]["admission"]=custom_policy("admission")
    outputs={"a":{},"b":{},"c":{},"ADMISSION":{"outcome":admission,"reason":"authored"}}
    if phase=="BEFORE_START":token.cancel("authored cancellation")
    usage={"tokens":{"unit":"token","kind":"EXACT","value":3}}
    record=(await run(Relay(catalog=catalog_for(outputs,calls,hook,usage=usage)),d,node,cancellation=token)).record
    if admission=="RUN":
        if phase=="RUNNING":
            assert record.nodes[0].state=="SUCCESS"
            assert record.nodes[1].state=="CANCELLED" and record.nodes[1].information=={}
            assert record.nodes[1].observation.usage["tokens"].value==3
            assert record.nodes[2].state=="NONEXECUTED"
            assert [c[0] for c in calls]==["a","b"]
        else:assert not calls and all(r.state=="NONEXECUTED" for r in record.nodes)
        assert record.cancellation.phase==phase
        assert record.nodes[-1].result.disposition=="CANCELLED"
    return record


async def live_event(s,node):
    from openverify.provider import parse_invocation
    from openverify.relay.adapters.local import LocalDriver
    from openverify.relay.ports import InvocationRequest
    manifest=m.manifest(True,s["resource"],s["vcp"])
    catalog=catalog_for({"n":None},events=[(1,s["kind"],m.payload(s["kind"]))],manifest=manifest)
    available=catalog.providers()[0];request=InvocationRequest(available.manifest,parse_invocation(m.invocation(s["vcp"])))
    observed=[]
    report=await LocalDriver().execute(available,request,5,observed.append)
    assert report.error is None and report.output_error is None
    assert report.outcome.invocation_id=="v4-attempt" and report.outcome.state=="COMPLETED"
    assert observed==list(report.events)
    return {"events":[{"sequence":e.sequence,"kind":e.kind,"payload":e.payload} for e in observed]}


async def execute_runtime(case,node):
    action=case["action"];s=case["stimulus"]
    if action=="invoked_result":
        record=await simple_record(node,s["kind"],s["result"])
        nr=next(r for r in record.nodes if r.node_id=="n")
        if s["result"]["disposition"]=="EXECUTED":return {"accepted":nr.state==("ERROR" if s["result"]["execution_outcome"]=="ERROR" else "SUCCESS") and to_data(nr.result)==to_data(__import__("openverify",fromlist=["parse_result"]).parse_result(s["result"]))}
        return {"accepted":nr.state!="ERROR"}
    if action=="resolve":return await resolve(s,node)
    if action=="policy_path":return await policy_path(s,node)
    if action=="policy_role":
        role=s["role"];d=m.definition([m.node()]);d["execution_policy"][role.lower()]=custom_policy(role)
        outputs={"ACTIVATION":{"outcome":"ACTIVATE","reason":"authored"},"SELECTION":{"subjects":[m.ARTIFACT],"reason":"authored"},"ADMISSION":{"outcome":"RUN","reason":"authored"},"n":{}}
        outputs[role]=copy.deepcopy(outputs[s["outcome_role"]])
        try:await run(Relay(catalog=catalog_for(outputs)),d,node);return {"accepted":True}
        except ProtocolError as exc:
            assert exc.code=="POLICY_OUTPUT";return {"accepted":False}
    if action=="policy_order":
        raw=to_data(await simple_record(node));by_role={p["role"]:p for p in raw["policy_evaluations"]}
        raw["policy_evaluations"]=[by_role[r] for r in s["order"]]
        return accepted(lambda:parse_run_record(raw),node)
    if action in {"guard","guard_pointer","guard_source"}:return await guard_case(action,s,node)
    if action=="route":return await route(s,node)
    if action=="motif":
        await motif(s["motif"],node)
        return {"assertions":"authored snapshots, readiness, invocation and record isolation"}
    if action=="live_event":return await live_event(s,node)
    if action=="record_compatibility":
        result=s["result"]
        # Obtain an authentic invoked record, then change only the terminal-state
        # projection; nonexecution is obtained from admission or cancellation.
        if result["disposition"]=="EXECUTED":record=await simple_record(node,s["kind"],result)
        else:
            if result["disposition"]=="CANCELLED":record=await cancellation_witness(node,"BEFORE_START")
            else:
                d=m.definition([m.node("n",s["kind"])]);d["execution_policy"]["admission"]=custom_policy("admission")
                admission="SKIP" if result["disposition"]=="SKIPPED" else "DEFER"
                record=(await run(Relay(catalog=catalog_for({"ADMISSION":{"outcome":admission,"reason":"authored"},"n":primary(s["kind"])})),d,node)).record
        raw=to_data(record);raw["nodes"][0]["state"]=s["state"]
        return accepted(lambda:parse_run_record(raw),node)
    if action=="cancel_record":
        record=await cancellation_witness(node,s["phase"],s["admission"])
        if s["admission"]=="RUN":return {"accepted":record.cancellation is not None}
        raw=to_data(record);raw["cancellation"]={"node_id":raw["nodes"][0]["node_id"],"phase":s["phase"],"reason":"authored forbidden event"}
        return accepted(lambda:parse_run_record(raw),node)
    if action=="reason":return await reason_witness(s["reason"],node)
    if action=="lineage":return await lineage(s["mutation"],node)
    if action=="port":return await port_witness(s["method"],node)
    if action=="resource_path":return await resource_path(s["scenario"],node)
    raise AssertionError("Unimplemented runtime action: "+action)


async def reason_witness(reason,node):
    if reason=="CANCELLATION":r=await cancellation_witness(node);n=r.nodes[-1]
    elif reason in {"ADMISSION_SKIP","ADMISSION_DEFER"}:
        d=m.definition([m.node()]);d["execution_policy"]["admission"]=custom_policy("admission")
        r=(await run(Relay(catalog=catalog_for({"ADMISSION":{"outcome":reason.removeprefix("ADMISSION_"),"reason":"authored"}})),d,node)).record;n=r.nodes[0]
    elif reason=="ROUTE_EXCLUDED":
        c=m.node("control","CONTROL");d=m.definition([c,m.node("a"),m.node("b")],[{"from_node":"control","to_node":"a"},{"from_node":"control","to_node":"b"}])
        r=(await run(Relay(catalog=catalog_for({"control":{"decision":{"protocol":"draft","kind":"ROUTE","destination":"a"}},"a":{}})),d,node)).record;n=next(n for n in r.nodes if n.node_id=="b")
    elif reason in {"CONTROL_STOP","CONTROL_DEFER","RETRY_REQUESTED"}:
        kind={"CONTROL_STOP":"STOP_FAILURE","CONTROL_DEFER":"DEFER","RETRY_REQUESTED":"RETRY"}[reason]
        d=m.definition([m.node("control","CONTROL"),m.node("n")],[{"from_node":"control","to_node":"n"}])
        r=(await run(Relay(catalog=catalog_for({"control":{"decision":{"protocol":"draft","kind":kind}}})),d,node)).record;n=r.nodes[-1]
    elif reason=="GUARD_FALSE":
        d=m.definition([m.node("a"),m.node("n")],[{"from_node":"a","to_node":"n","guard":{"source":m.constant(True),"pointer":"","value":False}}])
        r=(await run(Relay(catalog=catalog_for({"a":{}})),d,node)).record;n=r.nodes[-1]
    else:
        ndef=m.node();ndef["inputs"]=[m.port("x")];ndef["bindings"]={"x":{"kind":"RUN_INPUT","name":"x"}}
        d=m.definition([ndef]);d["run_inputs"]=[m.port("x",required=False)]
        r=(await run(Relay(catalog=catalog_for({})),d,node)).record;n=r.nodes[-1]
    assert n.observation is None and n.provider_binding is None and not n.information
    assert n.result.output=={"reason":reason}
    return {"reason":n.reason,"disposition":n.result.disposition}


async def lineage(mutation,node):
    a=m.node("a","EVALUATE");b=m.node("b")
    b["inputs"]=[m.port("prior")];b["bindings"]={"prior":{"kind":"UPSTREAM_OUTPUT","node_id":"a","output":"result"}}
    usage={"tokens":{"unit":"token","kind":"EXACT","value":3}}
    r=(await run(Relay(catalog=catalog_for({"a":{"result":m.known(verdict="PASS",usage=usage)},"b":{}},usage=usage)),m.definition([a,b],[{"from_node":"a","to_node":"b"}]),node)).record
    assert r.nodes[1].input_values["prior"]["verdict"]=="PASS"
    assert r.nodes[0].input_values["subject"]==m.ARTIFACT and r.nodes[0].input_values["criterion"]==m.CRITERION
    assert r.nodes[0].observation.usage["tokens"].value==3
    raw=to_data(r)
    if mutation=="INPUT_VALUE":raw["nodes"][1]["input_values"]["prior"]["verdict"]="FAIL"
    if mutation=="SOURCE_IDENTITY":raw["nodes"][1]["input_resolutions"]["prior"]["source"]["node_id"]="other"
    if mutation=="UPSTREAM_SNAPSHOT":raw["nodes"][1]["upstream_results"]["a"]["verdict"]="FAIL"
    if mutation=="EXECUTOR_VERSION":raw["nodes"][0]["executor_version"]="other"
    if mutation=="USAGE":raw["nodes"][0]["observation"]["usage"]["tokens"]["value"]=99
    if mutation=="TIME":raw["nodes"][1]["started_at"]="2000-01-01T00:00:00Z"
    return accepted(lambda:parse_run_record(raw),node)


async def port_witness(method,node):
    from openverify.model import OperationRequirement
    from openverify.relay.adapters.binder import DeterministicBinder
    from openverify.relay.adapters.local import LocalDriver
    from openverify.relay.ports import InvocationRequest,RelayEvent
    from openverify.provider import parse_invocation
    catalog=catalog_for({"n":{}})
    if method=="CATALOG.PROVIDERS":
        a=catalog.providers();assert len(a)==1 and a[0].manifest.provider_id==m.PROVIDER
        a[0].manifest.capabilities.clear();assert len(catalog.providers()[0].manifest.capabilities)==1
    elif method=="BINDER.BIND":
        p=DeterministicBinder().bind(OperationRequirement(capability_id=m.CAPABILITY,capability_version="1"),catalog.providers())
        assert p.manifest.provider_version=="1"
    elif method in {"DRIVER.EXECUTE","TRANSPORT.INVOKE","SINK.EMIT"}:
        catalog=catalog_for({"n":{}},events=[(1,"progress",{"authored":True})]);p=catalog.providers()[0]
        req=InvocationRequest(p.manifest,parse_invocation(m.invocation()));events=[]
        if method=="TRANSPORT.INVOKE":outcome=await p.transport.invoke(req,events.append)
        else:
            report=await LocalDriver().execute(p,req,5,events.append)
            assert report.error is None;outcome=report.outcome
        assert outcome.state=="COMPLETED" and outcome.output=={}
        assert len(events)==1 and events[0].payload=={"authored":True}
    elif method=="STORE.GET.NONE":assert MemoryStore().get("absent") is None
    elif method.startswith("STORE"):
        r=await simple_record(node);store=MemoryStore();store.put(r);got=store.get(r.run_id)
        assert got==r;got.run_inputs["mutation"]=1;assert store.get(r.run_id).run_inputs=={}
    else:
        events=[];observer=CallbackObserver(events.append);event=RelayEvent("authored-run","authored-kind")
        assert observer.observe(event) is None and events==[event]
    return {"accepted":True}


async def resource_path(name,node):
    if name=="CANCELLED_USAGE":
        r=await cancellation_witness(node);assert r.nodes[-1].result.disposition=="CANCELLED";return {"accepted":True}
    if name=="DEADLINE_EXPIRED":
        # LocalDriver/host run API has no deadline argument. Test the published
        # accepted-expired lifecycle directly; never invent a deadline Outcome
        # for an invocation which did not request a deadline.
        from .sut import session,outcome
        v=session();inv=m.invocation();inv["deadline"]="2001-01-01T00:00:00Z"
        v.accept(inv,now="2002-01-01T00:00:00Z");v.outcome(outcome("DEADLINE_EXCEEDED"),now="2002-01-01T00:00:00Z");v.finish()
        return {"accepted":True}
    events=[] if name=="ZERO_EVENTS" else [(1,"resource_usage",{"tokens":{"unit":"token","kind":"EXACT","value":2}})]
    if name=="GAPPED_EVENTS":events=[(1,"progress",None),(7,"diagnostic",{"authored":True})]
    final={"tokens":{"unit":"token","kind":"EXACT","value":5}}
    out=RuntimeError("authored execution failure") if name=="PARTIAL_ERROR" else {}
    relay=Relay(catalog=catalog_for({"n":out},events=events,usage=final if name in {"FINAL_SUPERSEDES_PARTIAL","PARTIAL_ERROR"} else None))
    r=(await run(relay,m.definition([m.node()]),node)).record
    n=r.nodes[0]
    if name in {"FINAL_SUPERSEDES_PARTIAL","PARTIAL_ERROR"}:
        assert n.observation.usage["tokens"].value==5
        assert n.observation.usage["tokens"].unit=="token"
    if name=="PARTIAL_ERROR":assert n.state=="ERROR" and n.result.execution_outcome=="ERROR"
    return {"accepted":True}


def sdk_policy_error():
    from openverify.engine import Engine
    from openverify.adapters import Registry
    class Broken:
        def execute(self,inputs,config):raise ValueError("authored SDK policy error")
    registry=Registry();registry.register(m.CAPABILITY,"1",Broken())
    d=m.definition();d["execution_policy"]["activation"]=custom_policy("activation")
    try:Engine(registry).run(parse_definition(d),{},opportunity_id="authored")
    except ProtocolError as exc:return {"code":exc.code}
    raise AssertionError("SDK failed to expose policy failure")
