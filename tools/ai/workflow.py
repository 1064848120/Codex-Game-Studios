"""Codex's local workflow ledger. Stores/routs work; never calls another AI."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
PHASES = {"intake","concept","systems-design","technical-setup","pre-production",
          "production","polish","release"}
STATE = "production/studio/run.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def path_in(root, relative):
    if not isinstance(relative,str) or not relative or Path(relative).is_absolute():
        raise ValueError("Expected a project-relative path.")
    path=(root/relative).resolve()
    if ".." in Path(relative).parts or not path.is_relative_to(root.resolve()):
        raise ValueError("Path escapes project: "+relative)
    return path

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    temp.replace(path)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def catalog(root,kind):
    return {entry["name"]:entry for entry in read_json(root/f"ai/{kind}/index.json")}

def string_list(value,label):
    if not isinstance(value,list) or not value or any(not isinstance(x,str) or not x.strip() for x in value):
        raise ValueError(label+" must be a nonempty list of nonempty strings.")
    if len(set(value)) != len(value):
        raise ValueError(label+" contains duplicates.")
    return value

def validate_step(root,step):
    required={"id","workflow","role","arguments","phase","acceptance","outputs"}
    if not isinstance(step,dict) or set(step)!=required:
        raise ValueError("Step must contain exactly: "+", ".join(sorted(required)))
    if not isinstance(step["id"],str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}",step["id"]):
        raise ValueError("Invalid step ID.")
    if step["workflow"] not in catalog(root,"skills"):
        raise ValueError("Unknown workflow: "+str(step["workflow"]))
    if step["role"] not in catalog(root,"roles"):
        raise ValueError("Unknown role: "+str(step["role"]))
    if step["phase"] not in PHASES or not isinstance(step["arguments"],str):
        raise ValueError("Invalid phase/arguments.")
    string_list(step["acceptance"],"acceptance")
    for out in string_list(step["outputs"],"outputs"):
        path_in(root,out)
        if out == STATE or out.startswith("production/studio/history/"):
            raise ValueError("Ledger cannot be used as completion evidence.")
    return step

def event(state,kind,message):
    state["updated_at"]=now()
    state["history"].append({"at":now(),"event":kind,"message":message})

def load(root):
    state=read_json(root/STATE)
    if state.get("version")!=1 or state.get("status") not in ("running","blocked","done"):
        raise ValueError("Invalid workflow state.")
    ids=set()
    for step in state["steps"]:
        validate_step(root,step["spec"])
        ident=step["spec"]["id"]
        if ident in ids or step["status"] not in ("pending","done"):
            raise ValueError("Invalid/duplicate step state.")
        ids.add(ident)
    return state

def save(root,state):
    write_json(root/STATE,state)

def init(root,plan):
    if (root/STATE).exists():
        raise ValueError("A run already exists. Resume it or archive a verified completed run.")
    if not isinstance(plan,dict) or set(plan)!={"objective","rigor","steps"}:
        raise ValueError("Plan needs objective, rigor, steps.")
    if not isinstance(plan["objective"],str) or not plan["objective"].strip():
        raise ValueError("Missing objective.")
    if plan["rigor"] not in ("minimal","standard","full"):
        raise ValueError("Invalid rigor.")
    if not isinstance(plan["steps"],list) or not plan["steps"]:
        raise ValueError("No steps.")
    specs=[validate_step(root,s) for s in plan["steps"]]
    if len({s["id"] for s in specs})!=len(specs):
        raise ValueError("Duplicate step IDs.")
    state={"version":1,"objective":plan["objective"],"rigor":plan["rigor"],
           "status":"running","created_at":now(),"updated_at":now(),"blocker":None,
           "history":[],"steps":[{"spec":s,"status":"pending","receipt":None} for s in specs]}
    event(state,"init","Authorized objective recorded.")
    save(root,state)
    return next_step(root)

def stale_evidence(root,state):
    for step in state["steps"]:
        if step["status"]!="done":
            continue
        receipt=step.get("receipt")
        if not isinstance(receipt,dict) or not receipt.get("evidence"):
            return step["spec"]["id"]+": missing receipt"
        for evidence in receipt["evidence"]:
            path=path_in(root,evidence["path"])
            if not path.is_file() or digest(path)!=evidence["sha256"]:
                return step["spec"]["id"]+": evidence changed/missing: "+evidence["path"]
    return None

def next_step(root):
    state=load(root)
    stale=stale_evidence(root,state)
    if stale:
        return {"status":"blocked","reason":stale,
                "action":"Codex: assess affected work and reopen the earliest stale step internally."}
    if state["status"]=="blocked":
        return {"status":"blocked","reason":state["blocker"],
                "action":"Resolve the material blocker; do not request a skill command from the user."}
    pending=next((s for s in state["steps"] if s["status"]=="pending"),None)
    if not pending:
        return {"status":"done","objective":state["objective"]}
    spec=pending["spec"]
    return {"status":"running","objective":state["objective"],"step":spec,
            "workflow_path":catalog(root,"skills")[spec["workflow"]]["path"],
            "role_path":catalog(root,"roles")[spec["role"]]["path"],
            "action":"Codex: read these files, execute the step, verify evidence, complete it, then continue internally."}

def current(state):
    step=next((s for s in state["steps"] if s["status"]=="pending"),None)
    if step is None:
        raise ValueError("No pending work.")
    return step

def complete(root,receipt):
    state=load(root)
    if state["status"]!="running":
        raise ValueError("Run is not active.")
    if stale_evidence(root,state):
        raise ValueError("Earlier evidence is stale; reopen affected work.")
    step=current(state)
    if not isinstance(receipt,dict) or set(receipt)!={"step_id","verdict","checks","evidence","questions","summary"}:
        raise ValueError("Receipt needs step_id, verdict, checks, evidence, questions, summary.")
    if receipt["step_id"]!=step["spec"]["id"]:
        raise ValueError("Cannot finish a later or different step.")
    if receipt["verdict"]!="pass" or receipt["questions"]!=[]:
        raise ValueError("Unresolved question/failed gate cannot complete a step.")
    if not isinstance(receipt["summary"],str) or not receipt["summary"].strip():
        raise ValueError("Missing evidence summary.")
    checks=receipt["checks"]
    if not isinstance(checks,dict) or set(checks)!=set(step["spec"]["acceptance"]) or any(v is not True for v in checks.values()):
        raise ValueError("Every planned acceptance criterion needs an explicit passing check.")
    evidence=string_list(receipt["evidence"],"evidence")
    if not set(step["spec"]["outputs"]).issubset(evidence):
        raise ValueError("Required output missing from evidence.")
    hashes=[]
    for name in evidence:
        path=path_in(root,name)
        if name==STATE or not path.is_file() or not path.stat().st_size:
            raise ValueError("Missing or empty evidence: "+name)
        hashes.append({"path":name,"sha256":digest(path)})
    step["status"]="done"
    step["receipt"]={**receipt,"evidence":hashes,"at":now()}
    if all(s["status"]=="done" for s in state["steps"]):
        state["status"]="done"
    event(state,"complete",step["spec"]["id"])
    save(root,state)
    return next_step(root)

def block(root,reason):
    if not isinstance(reason,str) or not reason.strip():
        raise ValueError("Provide the actual blocker.")
    state=load(root); current(state)
    state["status"]="blocked"; state["blocker"]=reason
    event(state,"block",reason); save(root,state)
    return next_step(root)

def resume(root,resolution):
    state=load(root)
    if state["status"]!="blocked":
        raise ValueError("Run is not blocked; use next.")
    path=path_in(root,resolution)
    if not path.is_file() or not path.stat().st_size:
        raise ValueError("Resolution must name an existing nonempty file.")
    state["status"]="running"; state["blocker"]=None
    event(state,"resume",resolution); save(root,state)
    return next_step(root)

def insert(root,spec):
    state=load(root)
    validate_step(root,spec)
    if any(s["spec"]["id"]==spec["id"] for s in state["steps"]):
        raise ValueError("Duplicate step ID.")
    position=state["steps"].index(current(state))
    state["steps"].insert(position,{"spec":spec,"status":"pending","receipt":None})
    # A material unanswered question stays blocking until its resolution is recorded.
    event(state,"insert",spec["id"]); save(root,state)
    return next_step(root)

def reopen(root,step_id,reason):
    state=load(root)
    if not reason.strip(): raise ValueError("Provide the change reason.")
    position=next((i for i,s in enumerate(state["steps"]) if s["spec"]["id"]==step_id),None)
    if position is None: raise ValueError("Unknown step.")
    # Preserve previous evidence receipts in history; invalidate dependent suffix.
    previous=[{"id":s["spec"]["id"],"receipt":s["receipt"]} for s in state["steps"][position:] if s["receipt"]]
    for step in state["steps"][position:]:
        step.update(status="pending",receipt=None)
    state["status"]="running"; state["blocker"]=None
    event(state,"reopen",reason)
    state["history"][-1]["previous_receipts"]=previous
    save(root,state)
    return next_step(root)

def archive(root):
    state=load(root)
    if state["status"]!="done" or next_step(root)["status"]!="done":
        raise ValueError("Only a verified completed objective can be archived.")
    name=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")+".json"
    path=root/"production/studio/history"/name
    write_json(path,state)
    (root/STATE).unlink()
    return {"archived":path.relative_to(root).as_posix()}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",choices=["init","next","status","complete","block","resume","insert","reopen","archive"])
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--plan",type=Path)
    p.add_argument("--receipt",type=Path)
    p.add_argument("--step",type=Path)
    p.add_argument("--reason",default="")
    p.add_argument("--step-id",default="")
    p.add_argument("--resolution",default="")
    a=p.parse_args(); root=a.root.resolve()
    try:
        if a.command=="init":
            if not a.plan: raise ValueError("--plan required")
            result=init(root,read_json(a.plan))
        elif a.command=="complete":
            if not a.receipt: raise ValueError("--receipt required")
            result=complete(root,read_json(a.receipt))
        elif a.command=="insert":
            if not a.step: raise ValueError("--step required")
            result=insert(root,read_json(a.step))
        elif a.command=="block": result=block(root,a.reason)
        elif a.command=="resume": result=resume(root,a.resolution)
        elif a.command=="reopen": result=reopen(root,a.step_id,a.reason)
        elif a.command=="archive": result=archive(root)
        else: result=next_step(root)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 2 if result.get("status")=="blocked" else 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(str(exc),file=sys.stderr); return 2
if __name__=="__main__":
    raise SystemExit(main())

