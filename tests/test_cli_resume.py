import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from firstwindow.cli import resume, tasks
from firstwindow.durable import create_task, write_checkpoint
from firstwindow.router import Lane


class CliResumeTests(unittest.TestCase):
    def test_tasks_lists_resumable_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "resume-1", "Fix checkout", ["Agent process exits successfully."])
            write_checkpoint(project, "resume-1", "agent-failed", "Continue from failing checkout test.")
            args = argparse.Namespace(project=project)

            output = io.StringIO()
            with redirect_stdout(output):
                code = tasks(args)

            self.assertEqual(code, 0)
            text = output.getvalue()
            self.assertIn("resume-1", text)
            self.assertIn("agent-failed", text)
            self.assertIn("Continue from failing checkout test", text)

    def test_resume_dry_run_uses_existing_task_id_without_recreating_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "resume-2", "Fix checkout", ["Agent process exits successfully."])
            write_checkpoint(project, "resume-2", "agent-failed", "Continue from failing checkout test.")
            args = argparse.Namespace(
                project=project,
                task_id="resume-2",
                engine=None,
                allow_unknown_cost=False,
                model=None,
                dry_run=True,
            )
            lane = Lane(
                name="agnes-free",
                engine="agnes",
                zero_cost=True,
                available=True,
                reason="test",
            )

            output = io.StringIO()
            with patch("firstwindow.cli._lanes", return_value=[lane]), redirect_stdout(output):
                code = resume(args)

            self.assertEqual(code, 0)
            text = output.getvalue()
            self.assertIn("task_id=resume-2", text)
            self.assertIn("resume=true", text)
            self.assertTrue((project / ".firstwindow" / "tasks" / "resume-2" / "task.json").is_file())


if __name__ == "__main__":
    unittest.main()
