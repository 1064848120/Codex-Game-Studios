"""Offline tests of Codex's director ledger; no external model invocation."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/ai"))
import workflow as w
import validate

def spec(ident,skill="design-system",phase="systems-design",role="game-designer"):
    return {"id":ident,"workflow":skill,"phase":phase,"role":role,"arguments":ident,
            "acceptance":[ident+" verified"],"outputs":["evidence/"+ident+".md"]}

class DirectorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="codex 工作室 space ")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for kind in ("skills","roles"):
            directory=self.root/"ai"/kind
            directory.mkdir(parents=True)
            (directory/"index.json").write_bytes((ROOT/"ai"/kind/"index.json").read_bytes())
    def init(self,steps=None,rigor="standard"):
        return w.init(self.root,{"objective":"Complete a bounded game milestone","rigor":rigor,
                                 "steps":steps or [spec("design"),spec("review","design-review")]})
    def receipt(self,step):
        for name in step["outputs"]:
            path=self.root/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text("Fixture evidence for dispatch tests only.",encoding="utf-8")
        return {"step_id":step["id"],"verdict":"pass","checks":dict.fromkeys(step["acceptance"],True),
                "evidence":step["outputs"],"questions":[],"summary":"Fixture assertions passed"}
    def finish(self):
        step=w.next_step(self.root)["step"]
        return w.complete(self.root,self.receipt(step))
    def walk(self):
        visited=[]
        while w.next_step(self.root)["status"]=="running":
            step=w.next_step(self.root)["step"]
            visited.append(step["workflow"])
            self.finish()
        return visited
    def test_new_full_project_routes_all_phases_without_user_skill_handoffs(self):
        route=[
          spec("start","start","intake","producer"),
          spec("concept","brainstorm","concept"),
          spec("engine","setup-engine","concept","godot-specialist"),
          spec("map","map-systems"),
          spec("combat"),spec("economy","design-system",role="economy-designer"),
          spec("balance","balance-check",role="economy-designer"),
          spec("design-review","review-all-gdds"),
          spec("architecture","create-architecture","technical-setup","technical-director"),
          spec("ux","ux-design","pre-production","ux-designer"),
          spec("stories","create-stories","pre-production","producer"),
          spec("build","dev-story","production","godot-specialist"),
          spec("code-review","code-review","production","lead-programmer"),
          spec("acceptance","story-done","production","qa-lead"),
          spec("polish","balance-check","polish","economy-designer"),
          spec("release-ready","release-checklist","release","release-manager")]
        self.init(route,"full")
        self.assertEqual(self.walk(),[s["workflow"] for s in route])
        self.assertEqual(w.next_step(self.root)["status"],"done")
    def test_existing_project_starts_with_inspection_not_onboarding(self):
        route=[spec("detect","project-stage-detect","intake","producer"),
               spec("adopt","adopt","intake","producer"),spec("retrofit"),spec("review","design-review")]
        self.init(route)
        self.assertEqual(self.walk(),["project-stage-detect","adopt","design-system","design-review"])
    def test_design_only_stops_without_implementation(self):
        self.init()
        self.assertEqual(self.walk(),["design-system","design-review"])
    def test_minimal_path_needs_no_full_gdd_gate(self):
        route=[spec("engine","setup-engine","concept","godot-specialist"),
               spec("brief","brainstorm","concept"),spec("story","create-stories","pre-production","producer"),
               spec("build","dev-story","production","godot-specialist"),
               spec("done","story-done","production","qa-lead")]
        self.init(route,"minimal")
        self.assertEqual(self.walk(),[s["workflow"] for s in route])
    def test_repeatable_systems_are_distinct_and_ordered(self):
        self.init([spec("combat"),spec("economy"),spec("progression")])
        self.finish()
        self.assertEqual(w.next_step(self.root)["step"]["id"],"economy")
    def test_completion_returns_next_step_internally(self):
        self.init()
        result=self.finish()
        self.assertEqual(result["step"]["workflow"],"design-review")
        self.assertIn("Codex:",result["action"])
        self.assertTrue(result["workflow_path"].endswith("design-review/SKILL.md"))
    def test_cold_resume_reads_state_without_onboarding(self):
        self.init();self.finish()
        process=subprocess.run([sys.executable,str(ROOT/"tools/ai/workflow.py"),"next","--root",str(self.root)],
                               capture_output=True,text=True,encoding="utf-8",env=dict(__import__("os").environ,PYTHONIOENCODING="utf-8"))
        self.assertEqual(process.returncode,0,process.stderr)
        self.assertEqual(json.loads(process.stdout)["step"]["id"],"review")
    def test_pending_decision_blocks_then_resumes_same_step(self):
        self.init(); w.block(self.root,"Player must choose game mode")
        self.assertEqual(w.next_step(self.root)["status"],"blocked")
        with self.assertRaises(ValueError): w.resume(self.root,"missing.md")
        (self.root/"answer.md").write_text("User selected solo mode.")
        self.assertEqual(w.resume(self.root,"answer.md")["step"]["id"],"design")
    def test_receipt_with_questions_cannot_complete(self):
        step=self.init()["step"]; receipt=self.receipt(step)
        receipt["questions"]=["Unresolved economy target"]
        with self.assertRaises(ValueError): w.complete(self.root,receipt)
        self.assertEqual(w.next_step(self.root)["step"]["id"],"design")
    def test_failed_gate_cannot_complete(self):
        step=self.init()["step"]; receipt=self.receipt(step);receipt["verdict"]="fail"
        with self.assertRaises(ValueError): w.complete(self.root,receipt)
    def test_missing_or_empty_evidence_cannot_complete(self):
        step=self.init()["step"];receipt=self.receipt(step)
        path=self.root/receipt["evidence"][0]
        path.write_text("")
        with self.assertRaises(ValueError):w.complete(self.root,receipt)
        path.unlink()
        with self.assertRaises(ValueError):w.complete(self.root,receipt)
    def test_all_acceptance_checks_required(self):
        step=self.init()["step"];receipt=self.receipt(step)
        receipt["checks"]={}
        with self.assertRaises(ValueError):w.complete(self.root,receipt)
        receipt["checks"]={step["acceptance"][0]:"true"}
        with self.assertRaises(ValueError):w.complete(self.root,receipt)
    def test_later_step_cannot_skip_current(self):
        self.init()
        receipt=self.receipt(spec("review","design-review"))
        with self.assertRaises(ValueError):w.complete(self.root,receipt)
    def test_required_outputs_cannot_be_substituted(self):
        step=self.init()["step"]; receipt=self.receipt(step)
        (self.root/"other.txt").write_text("Other unrelated report")
        receipt["evidence"]=["other.txt"]
        with self.assertRaises(ValueError):w.complete(self.root,receipt)
    def test_changed_evidence_reopens_dependent_suffix(self):
        self.init();self.walk()
        (self.root/"evidence/design.md").write_text("Changed rules")
        self.assertEqual(w.next_step(self.root)["status"],"blocked")
        with self.assertRaises(ValueError):w.archive(self.root)
        w.reopen(self.root,"design","Updated economy rules")
        self.assertEqual(w.next_step(self.root)["step"]["id"],"design")
        state=w.load(self.root)
        self.assertTrue(all(s["status"]=="pending" for s in state["steps"]))
        self.assertEqual(len(state["history"][-1]["previous_receipts"]),2)
    def test_insert_repairs_preserve_original_work(self):
        self.init()
        result=w.insert(self.root,spec("dependency","map-systems"))
        self.assertEqual(result["step"]["id"],"dependency")
        self.assertEqual(self.walk(),["map-systems","design-system","design-review"])
    def test_insertion_does_not_clear_unanswered_blocker(self):
        self.init();w.block(self.root,"Choose platform")
        result=w.insert(self.root,spec("dependency","map-systems"))
        self.assertEqual(result["status"],"blocked")
    def test_cannot_overwrite_active_run(self):
        self.init();before=(self.root/w.STATE).read_bytes()
        with self.assertRaises(ValueError):self.init()
        self.assertEqual(before,(self.root/w.STATE).read_bytes())
    def test_completed_run_archive_and_new_objective(self):
        self.init();self.walk()
        out=w.archive(self.root)
        self.assertTrue((self.root/out["archived"]).exists())
        self.assertEqual(self.init()["status"],"running")
    def test_unfinished_run_cannot_archive(self):
        self.init()
        with self.assertRaises(ValueError):w.archive(self.root)
    def test_unknown_workflow_role_and_duplicate_ids_rejected(self):
        for key,value in (("workflow","made-up"),("role","made-up"),("phase","made-up")):
            step=spec("bad");step[key]=value
            with self.assertRaises(ValueError):self.init([step])
        with self.assertRaises(ValueError):self.init([spec("same"),spec("same")])
    def test_escape_paths_rejected(self):
        step=spec("bad");step["outputs"]=["../escape"]
        with self.assertRaises(ValueError):self.init([step])
    def test_full_manifest_and_phase_references(self):
        result=validate.check(ROOT)
        self.assertEqual(result["portable_catalogs"],dict(roles=49,skills=74,rules=14))
        self.assertGreater(result["phase_references_checked"],100)
    def test_generator_roundtrip_and_edit_protection(self):
        module_spec=importlib.util.spec_from_file_location("exporter",ROOT/"tools/ai/export-universal.py")
        exporter=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(exporter)
        source=self.root/".claude/skills/example/SKILL.md";source.parent.mkdir(parents=True)
        source.write_text("---\nname: example\ndescription: Example\n---\n# Example\n",encoding="utf-8")
        exporter.run(root=self.root)
        before=(self.root/"ai/manifest.json").read_bytes()
        exporter.run(root=self.root)
        self.assertEqual(before,(self.root/"ai/manifest.json").read_bytes())
        target=self.root/"ai/skills/example/SKILL.md";target.write_text("Local change")
        with self.assertRaises(ValueError):exporter.run(root=self.root)

if __name__=="__main__":
    unittest.main()

