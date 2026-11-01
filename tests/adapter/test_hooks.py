"""Offline tests for the Codex event-compatible hook dispatcher."""
import json
from pathlib import Path
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ai"))
import hooks


class HookDispatcherTests(unittest.TestCase):
    def test_force_push_is_blocked_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            result, code = hooks.dispatch("PreToolUse", Path(directory), {
                "tool_name": "Bash", "tool_input": {"command": "git push origin main --force"}
            })
        self.assertEqual(code, 2)
        self.assertEqual(result["decision"], "block")

    def test_write_outside_project_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            result, code = hooks.dispatch("PreToolUse", Path(directory), {
                "tool_name": "Write", "tool_input": {"file_path": str(Path(directory).parent / "outside.md")}
            })
        self.assertEqual(code, 2)
        self.assertEqual(result["decision"], "block")

    def test_compaction_writes_recovery_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, code = hooks.dispatch("PreCompact", root, {"source": "test"})
            checkpoint = root / result["checkpoint"]
            self.assertEqual(code, 0)
            self.assertTrue(checkpoint.exists())
            self.assertIn("Codex Studio Checkpoint", checkpoint.read_text(encoding="utf-8"))
            self.assertTrue((root / "production/session-logs/compaction-log.txt").exists())

    def test_instruction_event_preserves_payload_as_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, code = hooks.dispatch("InstructionsLoaded", root, {"file_path": "ai/rules/example.md", "reason": "read"})
            line = (root / "production/session-logs/instructions-loaded.log").read_text(encoding="utf-8")
            record = json.loads(line)
            self.assertEqual(code, 0)
            self.assertTrue(result["logged"])
            self.assertEqual(record["file_path"], "ai/rules/example.md")


if __name__ == "__main__":
    unittest.main()
