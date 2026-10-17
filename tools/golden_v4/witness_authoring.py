"""Explicit independent behavior stimuli for non-product and conditional families."""
from __future__ import annotations

import copy
import itertools as it


def author(add, accept, refs, m):
    def witness(family, coord, action, stimulus, expected, source, module, mode="cheap"):
        add(family,coord,action,stimulus,expected,refs(source),module,mode=mode)

    for name,text,valid in [("UTF8",'{"protocol":"draft","disposition":"SKIPPED","output":"雪"}',True),
                            ("DUPLICATE",'{"protocol":"draft","protocol":"draft","disposition":"SKIPPED"}',False),
                            ("NAN",'{"protocol":"draft","disposition":"SKIPPED","output":NaN}',False),
                            ("INFINITY",'{"protocol":"draft","disposition":"SKIPPED","output":Infinity}',False),
                            ("UNKNOWN_PROPERTY",'{"protocol":"draft","disposition":"SKIPPED","unknown":0}',False),
                            ("VERSION",'{"protocol":"other","disposition":"SKIPPED"}',False),
                            ("NESTED_DUPLICATE",'{"protocol":"draft","disposition":"SKIPPED","output":{"x":1,"x":2}}',False),
                            ("INVALID_UTF8","INVALID_UTF8",False),
                            ("NEGATIVE_INFINITY",'{"protocol":"draft","disposition":"SKIPPED","output":-Infinity}',False)]:
        witness("V4.WIRE.JSON",name,"json",{"text":text},{"accepted":valid},"spec/draft/wire-format.md","test_vcp_wire")
    for name,field,value,valid in [("SCORE_ZERO","score",0,True),("SCORE_ONE","score",1,True),("SCORE_NEGATIVE","score",-0.01,False),
                                   ("SCORE_HIGH","score",1.01,False),("SCORE_BOOL","score",True,False),("SCORE_STRING","score","0.5",False),
                                   ("SCORE_NULL","score",None,True),("JUDGMENT_NULL","judgment",None,True),
                                   ("OUTPUT_NULL","output",None,True),("EVIDENCE_EMPTY","evidence",[{}],False),
                                   ("USAGE_NEGATIVE","usage",{"u":{"unit":"u","kind":"EXACT","value":-1}},False),
                                   ("SEVERITY_OPAQUE","severity",{"domain":"unknown:version","label":"unknown"},True)]:
        accept("V4.VCP.RESULT.VALUES",name,"result",m.known(**{field:value}),valid,"spec/draft/result.md","test_vcp_result_observations")
    for name,schema,valid in [("TRUE",True,True),("FALSE",False,True),("LOCAL_REF",{"$defs":{"x":{"type":"integer"}},"$ref":"#/$defs/x"},True),
                              ("EXTERNAL",{"$ref":"https://invalid.example/schema"},False),("UNRESOLVED",{"$ref":"#/$defs/missing"},False),
                              ("ANCHOR",{"$anchor":"x"},False),("DYNAMIC",{"$dynamicRef":"#x"},False),
                              ("NESTED_ID",{"properties":{"x":{"$id":"nested"}}},False),
                              ("INVALID_TYPE",{"type":"not-a-json-type"},False),("ANNOTATION",{"description":{"$ref":"https://example.invalid"}},True)]:
        d=m.definition();d["judgment_schema"]=schema
        accept("V4.VCP.SCHEMA.FULL",name,"verification-definition",d,valid,"spec/draft/dataflow.md","test_vcp_schemas_guards")
    for mutation in ("SELF_LOOP","DUPLICATE_EDGE","MISSING_ENDPOINT","DUPLICATE_NODE","UNORDERED_BINDING","UNKNOWN_INPUT","UNKNOWN_OUTPUT"):
        p=m.node("a");p["outputs"]=[{"name":"x","schema":True,"role":"INFORMATION"}]
        c=m.node("b");c["inputs"]=[m.port("x")];c["bindings"]={"x":{"kind":"UPSTREAM_OUTPUT","node_id":"a","output":"x"}}
        d=m.definition([p,c],[{"from_node":"a","to_node":"b"}])
        if mutation == "SELF_LOOP": d["graph"]["edges"].append({"from_node":"a","to_node":"a"})
        if mutation == "DUPLICATE_EDGE": d["graph"]["edges"] *= 2
        if mutation == "MISSING_ENDPOINT": d["graph"]["edges"][0]["from_node"]="absent"
        if mutation == "DUPLICATE_NODE": c["id"]="a"
        if mutation == "UNORDERED_BINDING": d["graph"]["edges"]=[]
        if mutation == "UNKNOWN_INPUT": c["bindings"]["unknown"]=m.constant(1)
        if mutation == "UNKNOWN_OUTPUT": c["bindings"]["x"]["output"]="absent"
        accept("V4.VCP.GRAPH.DEFINITION",mutation,"verification-definition",d,False,"spec/draft/composition.md","test_vcp_graph_structure")
    for kind,role in it.product(m.KINDS,m.ROLES):
        p=m.node("producer",kind)
        primary={"RESULT":"result","DECISION":"decision","INFORMATION":"data"}[role]
        if not any(v["name"]==primary for v in p["outputs"]): p["outputs"].append({"name":primary,"schema":True,"role":role})
        c=m.node("aggregate","AGGREGATE");c["inputs"].append(m.port("member"));c["bindings"]["member"]={"kind":"UPSTREAM_OUTPUT","node_id":"producer","output":primary}
        c["aggregate_inputs"]=["member"];c["bindings"]["members"]=m.constant(["member"])
        accept("V4.VCP.AGG.MEMBER_ROLE",kind+"-"+role,"verification-definition",m.definition([p,c],[{"from_node":"producer","to_node":"aggregate"}]),kind in {"EVALUATE","AGGREGATE"} and role == "RESULT","spec/draft/dataflow.md","test_vcp_aggregation")
    for kind,key in [("EVALUATE","subject"),("EVALUATE","criterion"),("AGGREGATE","subject"),("AGGREGATE","criterion"),("AGGREGATE","members")]:
        for valid in (False,True):
            n=m.node(kind=kind)
            if not valid: n["bindings"][key]=m.constant({"incorrect":"authored"})
            accept("V4.VCP.AGG.SEMANTIC",kind+"-"+key.upper()+f"-MATCH{int(valid)}","verification-definition",m.definition([n]),valid,"spec/draft/dataflow.md","test_vcp_aggregation")
    for n in range(1,9):
        witness("V4.VCP.AGG.WEIGHT_GENERAL",f"N{n}","weight_proof",{"n":n},{"candidates":3**n,"valid":2**n-1,"invalid":3**n-2**n+1},"spec/draft/aggregation.md","test_vcp_aggregation")
    for name,vals,weights,expected in [("UNEQUAL",[0.25,0.75],[1,3],0.625),("PERMUTED",[0.75,0.25],[3,1],0.625)]:
        witness("V4.VCP.AGG.WEIGHT_IDENTITY",name,"reduce",{"reducer":"WEIGHTED_AVERAGE","values":[m.known(score=v) for v in vals],"weights":weights},{"score":expected},"spec/draft/aggregation.md","test_vcp_aggregation")
    for act,sel,adm in it.product(("BUILTIN","CUSTOM"),("BUILTIN","CUSTOM"),("ALWAYS","PROBABILITY","CUSTOM")):
        d=m.definition()
        for role,choice in [("activation",act),("selection",sel),("admission",adm)]:
            if choice == "CUSTOM":d["execution_policy"][role]={"operation":{"capability_id":m.CAPABILITY,"capability_version":"1"},"inputs":[],"bindings":{},"config":{}}
            if choice == "PROBABILITY":d["execution_policy"][role]={"strategy":"PROBABILITY","probability":0.5}
        accept("V4.VCP.POLICY.DECLARATIONS","-".join((act,sel,adm)),"verification-definition",d,True,"spec/draft/execution-policy.md","test_vcp_policies")
    for path,expected in [("INACTIVE",None),("UNSELECTED",None),("RUN","RUN"),("SKIP","SKIP"),("DEFER","DEFER")]:
        witness("V4.VCP.POLICY.PATH",path,"policy_path",{"path":path},{"admission":expected,"invoked":path == "RUN"},"spec/draft/execution-policy.md","test_vcp_policies","runtime")
    for role,outcome in it.product(("ACTIVATION","SELECTION","ADMISSION"),("ACTIVATION","SELECTION","ADMISSION")):
        witness("V4.VCP.POLICY.ROLE_RESULT",role+"-"+outcome,"policy_role",{"role":role,"outcome_role":outcome},{"accepted":role==outcome},"spec/draft/execution-policy.md","test_vcp_policies","runtime")
    for order in it.permutations(("ACTIVATION","SELECTION","ADMISSION")):
        witness("V4.VCP.POLICY.EVAL_ORDER","-".join(order),"policy_order",{"order":list(order)},{"accepted":order == ("ACTIVATION","SELECTION","ADMISSION")},"spec/draft/provenance.md","test_vcp_policies","runtime")
    for bits in it.product((0,1),repeat=4):
        witness("V4.VCP.BIND.IDENTITY","BITS_"+"".join(map(str,bits)),"binding",{"equality_bits":list(bits)},{"accepted":all(bits)},"spec/draft/provider-binding.md","test_vcp_bindings_sources")
    for kind,source,status,handler in it.product(m.KINDS,(*m.SOURCES,"UNBOUND"),m.STATUSES,m.HANDLERS):
        family="V4.VCP.RESOLVE.UNBOUND" if source == "UNBOUND" else "V4.VCP.RESOLVE.RAW"
        # This is explicitly a coordinate-space proof, NOT a fabricated reachability verdict.
        add(family,"-".join((kind,source,status,handler)),"coordinate",{"kind":kind,"source":source,"status":status,"handler":handler},{"classification":"CONDITIONAL","missing_axes":["requiredness","producer_role","target_schema","ancestor","trace"]},refs("spec/draft/dataflow.md"),"test_vcp_resolution",classification="CONDITIONAL")
    for kind in m.KINDS:
        for status,handler in it.product(m.STATUSES,m.HANDLERS):
            # Concrete live stimuli use compliant outputs only. INVALID/OUTPUT_MISSING
            # are induced by host VCP port constraints, not malformed Provider output.
            witness("V4.VCP.RESOLVE.CONSUMER","-".join((kind,status,handler)),"resolve",{"kind":kind,"status":status,"handler":handler},{"status":status,"invoked":status == "AVAILABLE" or handler != "BLOCK","used_default":status != "AVAILABLE" and handler == "DEFAULT"},"spec/draft/dataflow.md","test_vcp_resolution","runtime")
    for status,handler in it.product(m.STATUSES,m.HANDLERS):
        witness("V4.VCP.RESOLVE.HANDLER",status+"-"+handler,"resolve",{"kind":"DERIVE","status":status,"handler":handler},{"status":status,"invoked":status == "AVAILABLE" or handler != "BLOCK","used_default":status != "AVAILABLE" and handler == "DEFAULT"},"spec/draft/dataflow.md","test_vcp_resolution","runtime")
    for name,pointer,source,value,valid in [("WHOLE","",m.constant(True),True,True),("NESTED","/x/0",m.constant({"x":[True]}),True,True),
                                          ("ESCAPED","/a~1b",m.constant({"a/b":True}),True,True),("ABSENT","/missing",{"kind":"RUN_INPUT","name":"x"},True,False)]:
        witness("V4.VCP.GUARD.POINTER",name,"guard_pointer",{"pointer":pointer,"source":source,"value":value},{"invoked":valid},"spec/draft/dataflow.md","test_vcp_schemas_guards","runtime")
    for kind in m.SOURCES:
        witness("V4.VCP.GUARD.SOURCE",kind,"guard_source",{"source_kind":kind},{"invoked":True},"spec/draft/dataflow.md","test_vcp_schemas_guards","runtime")
    witness("V4.VCP.GUARD.OPERATOR","EQUALITY_ONLY","guard_operator",{}, {"fields":["source","pointer","value"]},"spec/draft/dataflow.md","test_vcp_schemas_guards")
    phases=("PENDING","READY","RUNNING","TERMINAL")
    arcs={("PENDING","READY"),("PENDING","TERMINAL"),("READY","RUNNING"),("READY","TERMINAL"),("RUNNING","TERMINAL")}
    for a,b in it.product(phases,repeat=2):
        witness("V4.VCP.LIFECYCLE.PHASES",a+"-"+b,"phase",{"from":a,"to":b},{"category":"STUTTER" if a==b else ("PROGRESSION" if (a,b) in arcs else "OTHER")},"spec/draft/lifecycle.md","test_vcp_lifecycle_cancel")
    for phase,admission in it.product(("BEFORE_START","RUNNING"),("RUN","SKIP","DEFER")):
        witness("V4.VCP.CANCEL.ELIGIBILITY",phase+"-"+admission,"cancel_record",{"phase":phase,"admission":admission},{"accepted":admission=="RUN"},"spec/draft/lifecycle.md","test_vcp_lifecycle_cancel","runtime")
    reasons={"ADMISSION_SKIP":"SKIPPED","ADMISSION_DEFER":"DEFERRED","CANCELLATION":"CANCELLED","CONTROL_STOP":"SKIPPED","CONTROL_DEFER":"DEFERRED","RETRY_REQUESTED":"SKIPPED","ROUTE_EXCLUDED":"SKIPPED","GUARD_FALSE":"SKIPPED","INPUT_UNAVAILABLE":"SKIPPED"}
    for reason,disposition in reasons.items():
        witness("V4.VCP.LIFECYCLE.REASON",reason,"reason",{"reason":reason},{"reason":reason,"disposition":disposition},"spec/draft/lifecycle.md","test_vcp_lifecycle_cancel","runtime")
    for name in ("VALID","INPUT_VALUE","SOURCE_IDENTITY","UPSTREAM_SNAPSHOT","EXECUTOR_VERSION","USAGE","TIME"):
        witness("V4.VCP.RECORD.LINEAGE",name,"lineage",{"mutation":name},{"accepted":name=="VALID"},"spec/draft/provenance.md","test_vcp_records","runtime")
    for name in ("DIRECT_SUCCESSOR","NON_SUCCESSOR","SHARED_JOIN","INDEPENDENT_PRESERVED"):
        witness("V4.VCP.DECISION.ROUTE",name,"route",{"scenario":name},{"accepted":name != "NON_SUCCESSOR"},"spec/draft/lifecycle.md","test_vcp_decision","runtime")
    for name in ("initialize","invoke","cancel","event"):
        witness("V4.PROVIDER.TRANSPORT.METHOD",name.upper(),"transport_method",{"method":name},{"accepted":True},"provider-contract/spec/draft/transports.md","test_provider_transport","integration")
    # Each motif has its own exact invocation, consumed snapshots and record assertions.
    for motif,module in [("INDEPENDENT","test_relay_independent_node"),("EDGE","test_relay_typed_connections"),
                         ("CHAIN","test_relay_composition_motifs"),("FORK","test_relay_composition_motifs"),
                         ("JOIN","test_relay_composition_motifs"),("DIAMOND","test_relay_composition_motifs"),
                         ("ROUTE","test_relay_policies_control"),("GUARDED_JOIN","test_relay_policies_control"),
                         ("AGG_FANIN","test_relay_aggregation"),("PARALLEL_BARRIER","test_relay_scheduler"),
                         ("STOP_CANCEL","test_relay_cancellation_resources"),("MULTIRUN","test_relay_record_lineage")]:
        witness("V4.RELAY.SCHEDULER",motif,"motif",{"motif":motif},{"assertions":"authored snapshots, readiness, invocation and record isolation"},"docs/relay/architecture.md",module,"runtime")
    for name,module in [("CATALOG.PROVIDERS","test_relay_ports_catalog_binder"),("BINDER.BIND","test_relay_ports_catalog_binder"),
                        ("DRIVER.EXECUTE","test_relay_ports_driver_transport"),("TRANSPORT.INVOKE","test_relay_ports_driver_transport"),
                        ("STORE.PUT","test_relay_ports_store_observer"),("STORE.GET","test_relay_ports_store_observer"),
                        ("STORE.GET.NONE","test_relay_ports_store_observer"),("OBSERVER.OBSERVE","test_relay_ports_store_observer"),
                        ("SINK.EMIT","test_relay_ports_driver_transport")]:
        witness("V4.RELAY.PORTS",name,"port",{"method":name},{"accepted":True},"docs/relay/architecture.md",module,"runtime")
    for name in ("PYTHON","CLI_PASS","CLI_FAIL","MCP_LIST","MCP_RUN","HTTP_HEALTH","HTTP_VERIFY","HTTP_FAIL","HTTP_AUTH","HTTP_BODY_LIMIT","HTTP_BAD_GRAPH"):
        witness("V4.RELAY.ENTRYPOINT",name,"entrypoint",{"surface":name},{"accepted":True},"docs/relay/integration.md","test_entrypoints","integration")
    for name in ("PARTIAL_READ","COALESCED_READ","UTF8_BYTES","BAD_HEADER","TRUNCATED","UNKNOWN_METHOD"):
        witness("V4.PROVIDER.TRANSPORT.METHOD",name,"framing",{"scenario":name},{"accepted":name not in {"BAD_HEADER","TRUNCATED"}},"provider-contract/spec/draft/transports.md","test_provider_transport","integration")
    for kind,resource,vcp in it.product(m.EVENTS,(False,True),(False,True)):
        if m.event_allowed(kind,True,resource,vcp):
            witness("V4.PROVIDER.EVENT.ELIGIBILITY",f"LIVE.{kind.upper()}-RESOURCE{int(resource)}-VCP{int(vcp)}","live_event",
                    {"kind":kind,"resource":resource,"vcp":vcp},{"events":[{"sequence":1,"kind":kind,"payload":m.payload(kind)}]},
                    "provider-contract/spec/draft/lifecycle.md","test_provider_events_outcomes","runtime")
    for name in ("FINAL_SUPERSEDES_PARTIAL","PARTIAL_ERROR","CANCELLED_USAGE","DEADLINE_EXPIRED","ZERO_EVENTS","GAPPED_EVENTS"):
        witness("V4.RELAY.SCHEDULER",name,"resource_path",{"scenario":name},{"accepted":True},
                "provider-contract/spec/draft/lifecycle.md","test_relay_cancellation_resources","runtime")
    for name in ("RESULT_STATE","OPTIONAL_OBSERVATION","DECISION","AVAILABILITY","WEIGHT_IDENTITY","POLICY_NONINVOCATION","PROVIDER_ORDER","RECORD_LINEAGE","CANCELLATION"):
        witness("V4.AUDIT.MUTATION",name,"mutation",{"family":name},{"detected":True},"spec/draft/conformance.md","test_oracle_mutation_sensitivity")
    for diagnostic in ("POLICY_ERROR","RESULT_PROJECTION"):
        witness("V4.ERROR.NAMES","SDK_BOUNDARY."+diagnostic,"sdk_diagnostic",{"code":diagnostic},{"code":diagnostic},"spec/draft/conformance.md","test_errors_extensions")
    for name in ("INVENTORY","FREEZE","CASE_IDS","PROOFS"):
        witness("V4.AUDIT.INVENTORY",name,"audit",{"check":name},{"accepted":True},"spec/draft/conformance.md","test_inventory_coverage_gate")
