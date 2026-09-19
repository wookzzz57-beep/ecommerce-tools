from pathlib import Path
import tempfile
import unittest

from firstwindow.durable import append_evidence, create_task, default_acceptance, task_dir, verify_task


class DurableTests(unittest.TestCase):
    def test_task_requires_evidence_before_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "demo-1", "fix checkout", ["tests pass"])
            ok, failures = verify_task(project, "demo-1")
            self.assertFalse(ok)
            self.assertIn("evidence ledger empty", failures)

            append_evidence(
                project,
                "demo-1",
                "test",
                True,
                "unit tests pass",
                criteria=["AC-001"],
            )
            ok, failures = verify_task(project, "demo-1")
            self.assertTrue(ok)
            self.assertEqual(failures, [])

    def test_default_task_is_not_verified_by_agent_exit_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "truthful-default", "Create output", default_acceptance())
            append_evidence(project, "truthful-default", "agent-exit", True, "exit 0", criteria=["AC-001"])
            ok, failures = verify_task(project, "truthful-default")
            self.assertFalse(ok)
            self.assertTrue(any("AC-002" in item and "uncovered" in item for item in failures))

    def test_unsafe_task_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                task_dir(Path(tmp), "../escape")


if __name__ == "__main__":
    unittest.main()
