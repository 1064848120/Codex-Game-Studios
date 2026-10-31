"""Portable structural and JSON checks. Not a substitute for Godot/playtest QA."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parents[2]

def validate_schema(value, schema, location="$"):
    types = {"object":dict,"array":list,"string":str,"integer":int,"number":(int,float),"boolean":bool}
    expected = schema.get("type")
    if expected and (not isinstance(value,types[expected]) or
                     expected in ("integer","number") and isinstance(value,bool)):
        raise ValueError(f"{location}: expected {expected}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{location}: invalid enum value")
    if isinstance(value,str):
        if len(value) < schema.get("minLength",0):
            raise ValueError(f"{location}: string too short")
        if "pattern" in schema and not re.search(schema["pattern"],value):
            raise ValueError(f"{location}: invalid format")
    if isinstance(value,dict):
        if set(schema.get("required",[])) - set(value):
            raise ValueError(f"{location}: missing required fields")
        props = schema.get("properties",{})
        if schema.get("additionalProperties") is False and set(value) - set(props):
            raise ValueError(f"{location}: unexpected fields")
        for k,v in value.items():
            if k in props:
                validate_schema(v,props[k],location+"."+k)
    if isinstance(value,list) and "items" in schema:
        for i,v in enumerate(value):
            validate_schema(v,schema["items"],location+f"[{i}]")

def check(root=ROOT):
    spec = importlib.util.spec_from_file_location("studio_export",root/"tools/ai/export-universal.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run(check=True,root=root)
    counts = json.loads((root/"ai/manifest.json").read_text())["counts"]
    for category in ("roles","skills","rules"):
        catalog = json.loads((root/f"ai/{category}/index.json").read_text(encoding="utf-8"))
        if len(catalog) != counts[category]:
            raise ValueError("Catalog count mismatch: "+category)
        for entry in catalog:
            if not (root/entry["path"]).is_file():
                raise ValueError("Missing artifact: "+entry["path"])
    refs = 0
    for skill in (root/"ai/skills").glob("*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        if re.search(r"^!`|\$\{CLAUDE_SKILL_DIR\}",text,re.M):
            raise ValueError("Untranslated Claude execution in "+str(skill))
        for ref in set(re.findall(r"references/[a-zA-Z0-9_./-]+\.md",text)):
            if not (skill.parent/ref).is_file():
                raise ValueError(f"Missing skill reference: {skill.parent/ref}")
            refs += 1
    for path in (root/".agents/skills").glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\nname: studio-") or "\ndescription: " not in text:
            raise ValueError("Invalid skill frontmatter: "+str(path))
    from workflow import STATE, load, next_step
    state_path = root / STATE
    if state_path.exists():
        load(root)
    director_state = next_step(root)["status"] if state_path.exists() else "not-started"
    data = list((root/"assets/data").rglob("*.json"))
    for path in data:
        json.loads(path.read_text(encoding="utf-8-sig"))
    return {"portable_catalogs":counts,"phase_references_checked":refs,"director_state":director_state,
            "game_data_json_checked":len(data),
            "gameplay_validation":"NOT ASSESSED — no game run by this validator"}

if __name__ == "__main__":
    try:
        print(json.dumps(check(),ensure_ascii=False,indent=2))
    except (ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr)
        raise SystemExit(1)

