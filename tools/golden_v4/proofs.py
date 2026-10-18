"""Arithmetic derivations independent of production validators and reducers."""
from __future__ import annotations

import itertools as it
import json
from collections import Counter
from math import comb, factorial

from .discover import OUT, ROOT, write_json, write_lines


def derive():
    rows=[]
    def row(family, formula, c, v=None, i=None, n=0, q=0, **kw):
        if v is not None and i is not None: assert c == v+i+n+q
        rows.append({"family":family,"formula":formula,"C":c,"VALID":v,"INVALID":i,"IMPOSSIBLE":n,"UNRESOLVED":q,**kw})
    # These field sets are read from normative schema declarations, not SUT models.
    presence=[("DEF","verification-definition",None),("CRITERION","verification-definition","criterion"),
              ("ARTIFACT","artifact-ref",None),("EXEC_OBS","execution-observation",None),
              ("RUN_RECORD","run-record",None),("NODE_RECORD","run-record","node")]
    reductions=[]
    for family,name,sub in presence:
        s=json.loads((ROOT/f"schemas/draft/{name}.schema.json").read_text())
        if sub == "criterion": s=s["properties"]["criterion"]
        if sub == "node": s=s["properties"]["nodes"]["items"]
        r=len(s["required"]);o=len(s["properties"])-r
        assert len(set(s["required"]))==r and set(s["required"])<=s["properties"].keys()
        row(f"V4.VCP.{family}.PRESENCE",f"2^({r}+{o}); V=2^{o}",2**(r+o),2**o,2**(r+o)-2**o,required=s["required"],optional=sorted(set(s["properties"])-set(s["required"])))
        if family in {"RUN_RECORD","NODE_RECORD"}:
            # Syntactic theorem: a required array is an unconditional conjunction.
            assert not any(k in s for k in ("if","then","else","oneOf","anyOf","allOf","not","dependentRequired"))
            reductions.append({"proof_id":f"V4.P.{family}.REQUIRED_CONJUNCTION","family":f"V4.VCP.{family}.PRESENCE",
                               "formula":f"2^{r+o}-2^{o}-{r}","omitted_count":2**(r+o)-2**o-r,
                               "law":"Any omitted required field falsifies the unconditional required conjunction, regardless of other fields.",
                               "assumptions":["structural presence only","all included field contents separately valid","schema has unconditional required array","no conditional root combinators"],
                               "premise_case_families":[f"V4.VCP.{family}.PRESENCE"],"checker":"tools.golden_v4.proofs.derive","status":"PROVED"})
    row("V4.VCP.EVIDENCE.MEANING","(2^4-1)*2^3; invalid=2^3",128,15*8,8)
    partitions=[3*2**4,2**3,2**2,2,4]
    row("V4.VCP.RESULT.WIRE_AXIS","4*4^4; V=3*2^4+2^3+2^2+2+4",4*4**4,sum(partitions),4*4**4-sum(partitions),partitions=partitions)
    row("V4.VCP.RESULT.SEMANTIC_AXIS","4*3^4; V=3+1+1+1+3",4*3**4,3+1+1+1+3,4*3**4-9)
    row("V4.VCP.RESULT.OBS_MASK","9*2^8; V=3*2^8+6*2^5",9*2**8,3*2**8+6*2**5,9*2**8-(3*2**8+6*2**5))
    row("V4.VCP.RESULT.PROJECTION","9 semantic states; 2 binary+UNKNOWN+ERROR+SKIP",9,5,4,partition_labels=["defined","undefined"])
    row("V4.VCP.DECISION.DEST","6*4; V=1+5*2",24,11,13)
    row("V4.VCP.NODE.ROLE","4*3; V=4 INFORMATION+2 RESULT+1 DECISION",12,7,5)
    row("V4.VCP.NODE.INVOKED_RESULT","2*9; 2*(ERROR+NOT_APPLICABLE+UNKNOWN+3 KNOWN)",18,12,6)
    row("V4.VCP.BIND.IDENTITY","2^4; conjunction of four equalities",16,1,15)
    row("V4.VCP.PORT.HANDLING","2*3; required BLOCK, optional OMIT/DEFAULT",6,3,3)
    row("V4.VCP.PORT.DEFAULT","2 presence states",2,1,1)
    row("V4.VCP.SOURCE.KIND","4 disjoint source constructors",4,4,0)
    row("V4.VCP.SOURCE.POLICY","4*3; only 3 pregraph source kinds",12,9,3)
    for suffix,c,formula in [("HANDLER",18,"6*3"),("CONSUMER",72,"4*6*3"),("RAW",288,"4*4*6*3"),("UNBOUND",72,"4*1*6*3")]:
        row("V4.VCP.RESOLVE."+suffix,formula,c,q="conditional",classification="No V/I/N split from these axes alone")
    row("V4.VCP.RESOLVE.RECORD_BITS","6*3*2*2; V=3 AVAILABLE+5*3 unavailable",72,18,54)
    row("V4.VCP.SCHEMA.PRIMITIVE","7*7; seven diagonal + integer/number both ways",49,9,40)
    row("V4.VCP.GUARD.OPERATOR","equality only",1,1,0)
    row("V4.VCP.GUARD.SOURCE","4 source constructors; reachability conditional",4,q="conditional")
    row("V4.VCP.GUARD.BOOL","2*2; equality diagonal",4,2,2,partition_labels=["true","false"])
    # Independent inclusion/exclusion recurrence by the nonempty set of sources.
    dags=[1]
    for n in range(1,5):
        dags.append(sum((-1)**(k+1)*comb(n,k)*2**(k*(n-k))*dags[n-k] for k in range(1,n+1)))
    c=sum(2**(n*(n-1)) for n in range(5))
    row("V4.VCP.GRAPH.DAG_0_4","sum(n=0..4) 2^(n(n-1)); source-set inclusion/exclusion recurrence",c,sum(dags),c-sum(dags),dag_counts_by_n=dags)
    row("V4.VCP.GRAPH.FEATURES","2^2 feature subsets",4,4,0,supported=1,unsupported=3)
    row("V4.VCP.AGG.MEMBER_ROLE","4*3; EVALUATE/AGGREGATE RESULT only",12,2,10)
    row("V4.VCP.AGG.SEMANTIC","2 kinds*2 semantic snapshots + aggregate members",5,5,0)
    row("V4.VCP.AGG.HANDLING_MAP","8*2^7",8*2**7,8*2**7,0)
    row("V4.VCP.AGG.EXCEPTION","8*7*2 behavior laws",112,112,0,partition_labels=["laws","not validity split"])
    row("V4.VCP.AGG.WEIGHT_SIGN_2","3^2; V=2^2-1",9,3,6)
    row("V4.VCP.AGG.WEIGHT_GENERAL","C=3^n; V=2^n-1; I=3^n-2^n+1","unbounded",partition="symbolic n>=1")
    row("V4.VCP.POLICY.DECLARATIONS","2*2*3",12,12,0)
    row("V4.VCP.POLICY.PATH","1 inactive+1 unselected+3 admitted",5,5,0)
    row("V4.VCP.POLICY.ROLE_RESULT","3*3; role/type diagonal",9,3,6)
    row("V4.VCP.POLICY.EVAL_ORDER","3!; exactly one required order",factorial(3),1,5)
    row("V4.VCP.RESOURCE.PRESENCE_BINARY","4*2^3; one nonnull pattern per kind",32,4,28)
    row("V4.VCP.RESOURCE.PRESENCE_TRINARY","4*3^3; V=2*2^2+2+2^3",108,18,90)
    row("V4.VCP.RESOURCE.RANGE_ORDER","<,=,>; <= admits first two",3,2,1)
    row("V4.VCP.LIFECYCLE.PHASES","4*4; five progression + four stutter + seven other",16,5,7,n=4,partition_labels=["progression","other","stutter"])
    row("V4.VCP.LIFECYCLE.RESULT","4*4 per kind; SUCCESS1+ERROR1+NONEXECUTED3+CANCELLED1",16,6,10,per_kind=True)
    row("V4.VCP.LIFECYCLE.REASON","nine distinct cause mappings",9,9,0)
    row("V4.VCP.CANCEL.ELIGIBILITY","2*3; admission RUN only",6,2,4)
    row("V4.VCP.EXT.REQUIRED","2*2; required AND unsupported excluded",4,3,1)
    row("V4.PROVIDER.FEATURE_FLAGS","2^4 independent booleans",16,16,0)
    row("V4.PROVIDER.VCP_COMPAT","2*2; declaration implies manifest support",4,3,1)
    row("V4.PROVIDER.INIT","success / reject-and-close; version list space unbounded",2,2,0)
    row("V4.PROVIDER.INVOKE.DEADLINE","2*2; presence implies feature",4,3,1)
    row("V4.PROVIDER.INVOKE.BUDGET","2*2; presence implies VCP",4,3,1)
    row("V4.PROVIDER.OUTCOME.SHAPE","4*2*2; one shape per terminal kind",16,4,12)
    row("V4.PROVIDER.OUTCOME.USAGE","2*4*2*2; absent16 + present with both flags4",32,20,12)
    row("V4.PROVIDER.EVENT.ELIGIBILITY","6*2^3; 3 advisory*4 + 2 VCP*2 + 1 usage",48,17,31)
    row("V4.PROVIDER.ATTEMPT.TRANSITION","4*4; unseen accept1+running3+terminal cancel1",16,5,11)
    row("V4.PROVIDER.CANCEL.ELIGIBILITY","4*2; terminal2+supported running1",8,3,5)
    row("V4.PROVIDER.DEADLINE.RACE","4*2*3; absent5+unexpired5+expired2",24,12,12)
    row("V4.PROVIDER.TRANSPORT.METHOD","3 request methods + 1 notification",4,4,0)
    row("V4.ERROR.NAMES","33 normative VCP + 8 Provider + 2 SDK + 10 Relay",53,53,0)
    row("V4.WIRE.ROOTS","24 VCP + 9 Provider",33,33,0)
    row("V4.RELAY.PORTS","6 Protocols, seven direct methods; plus EventSink.emit",7,7,0)
    # Preserve every blueprint row. Unbounded rows are not assigned fictional totals.
    families=json.loads((OUT/"FAMILY_INVENTORY.json").read_text())
    for f in families:
        if not any(r["family"]==f["family"] for r in rows):
            row(f["family"],f["domain"],"unbounded" if "∞" in f["blueprint_formula"] else "conditional",q="conditional")
    write_json(OUT/"PROJECTIONS.json",rows)
    reductions += [
        {"proof_id":"V4.P.RESULT.PARTITIONS","family":"V4.VCP.RESULT.WIRE_AXIS","formula":"48+8+4+2+4=66", "omitted_count":0,"law":"disjoint first-divergence branches of the Result constraints", "assumptions":["categorical fields only; no arbitrary observation payloads"],"premise_case_families":["V4.VCP.RESULT.WIRE_AXIS","V4.VCP.RESULT.SEMANTIC_AXIS"],"checker":"tools.golden_v4.proofs.derive","status":"PROVED"},
        {"proof_id":"V4.P.DAG.INDUCTION","family":"V4.RELAY.SCHEDULER","formula":"all finite DAGs by topological induction", "omitted_count":"unbounded", "law":"node-local correctness + resolved typed inputs + readiness + state isolation implies successor correctness", "assumptions":["complete node correctness","binding correctness","no shared mutable state interference","global route/cancellation/barrier effects separately proved"], "premise_case_families":["V4.RELAY.SCHEDULER","V4.VCP.RESOLVE.CONSUMER"],"checker":None,"status":"UNPROVED"},
        {"proof_id":"V4.P.REDUCER.UNBOUNDED","family":"V4.VCP.AGG.LOGICAL","formula":"2^n at each n>=1", "omitted_count":"unbounded", "law":"multiset reduction requires identity and evidence-order invariance", "assumptions":["ordering retained separately","weights attached to member identity","all unbounded numeric and length domains"],"premise_case_families":["V4.VCP.AGG.LOGICAL","V4.VCP.AGG.WEIGHT_IDENTITY"],"checker":None,"status":"UNPROVED"}]
    write_lines(OUT/"REDUCTION_LEDGER.jsonl",reductions)
    text=["# Independent count derivations\n", "Each row is a distinct projection. There is no grand candidate sum. Structural presence does not imply full semantic validity.\n",
          "Result branch proof: nonexecution forces all four optional axes to bottom, giving 3*2^4. ERROR forces three bottoms, giving 2^3. NOT_APPLICABLE forces two, giving 2^2. UNKNOWN forces verdict bottom, giving 2. KNOWN admits bottom/PASS/FAIL at wire multiplicities 2/1/1, giving 4. These first-divergence branches are disjoint.\n",
          "Absent/null are identified only for nullable categorical controls; explicit judgment/output null remains present data. The observation-mask derivation fixes true judgment_schema and valid payloads. Three KNOWN classes permit eight fields; six remaining classes permit five fields.\n",
          "DAG recurrence: a nonempty source set of size k contributes choose(n,k)*2^(k(n-k))*DAG(n-k); inclusion/exclusion over source sets yields [1,1,3,25,543]. Enumeration tests independently use cycle detection. Topology is not full definition validity.\n",
          "Record presence: all required bits must be 1; optional bits are free. Invalid masks missing a required bit remain invalid under all deletions/additions of other fields. Only the presence subconstraint is reduced. All optional masks and each single required deletion are executed.\n",
          "| Family | Formula | C | V | I | N | Q |\n| --- | --- | --- | --- | --- | --- | --- |"]
    text += [f"| {r['family']} | {r['formula']} | {r['C']} | {r['VALID']} | {r['INVALID']} | {r['IMPOSSIBLE']} | {r['UNRESOLVED']} |" for r in rows]
    (OUT/"COUNT_PROOFS.md").write_text("\n".join(text)+"\n",encoding="utf-8")
    return rows,reductions


if __name__ == "__main__": derive()
