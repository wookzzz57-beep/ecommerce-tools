import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from firstwindow.cli import verify
from firstwindow.durable import append_evidence, create_task


class CliVerifyTests(unittest.TestCase):
    def test_verify_prints_covered_and_uncovered_criteria(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "cli-report", "ship endpoint", ["tests pass", "endpoint returns 200"])
            append_evidence(project, "cli-report", "test", True, "passed", criteria=["AC-001"])
            args = argparse.Namespace(project=project, task_id="cli-report")

            output = io.StringIO()
            with redirect_stdout(output):
                code = verify(args)

            text = output.getvalue()
            self.assertEqual(code, 1)
            self.assertIn("COVERED AC-001: tests pass", text)
            self.assertIn("UNCOVERED AC-002: endpoint returns 200", text)
            self.assertIn("NOT VERIFIED", text)


if __name__ == "__main__":
    unittest.main()
