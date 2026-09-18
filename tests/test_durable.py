from pathlib import Path
import tempfile
import unittest
from firstwindow.durable import append_evidence, create_task, task_dir, verify_task

class DurableTests(unittest.TestCase):
    def test_task_requires_evidence_before_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "demo-1", "fix checkout", ["tests pass"])
            ok, failures = verify_task(project, "demo-1")
            self.assertFalse(ok)
            self.assertIn("evidence ledger empty", failures)
            append_evidence(project, "demo-1", "test", True, "unit tests pass")
            ok, failures = verify_task(project, "demo-1")
            self.assertTrue(ok)
            self.assertEqual(failures, [])

    def test_unsafe_task_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                task_dir(Path(tmp), "../escape")

if __name__ == "__main__":
    unittest.main()
