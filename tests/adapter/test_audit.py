"""Parity and unified-entry-point tests."""
from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ai"))
import audit


class ParityAuditTests(unittest.TestCase):
    def test_every_upstream_hook_has_a_codex_mapping(self):
        result = audit.audit(ROOT)
        self.assertEqual(result["status"], "pass", result["findings"])
        self.assertEqual(result["source_hook_files"], 18)
        self.assertEqual(result["skill_wrappers"], 75)

    def test_audit_cli_is_machine_readable(self):
        process = subprocess.run([sys.executable, str(ROOT / "tools/ai/audit.py"), "--json"], cwd=ROOT,
                                 capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["status"], "pass")

    def test_unified_skills_command_lists_all_workflows(self):
        process = subprocess.run([sys.executable, str(ROOT / "tools/ai/studio.py"), "skills"], cwd=ROOT,
                                 capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("design-system:", process.stdout)
        self.assertIn("vertical-slice:", process.stdout)

    def test_unified_event_command_dispatches_without_claude(self):
        process = subprocess.run([sys.executable, str(ROOT / "tools/ai/studio.py"), "event", "Notification"], cwd=ROOT,
                                 capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("Notification", process.stdout)


if __name__ == "__main__":
    unittest.main()
