from pathlib import Path
import json
import tempfile
import unittest

from firstwindow.runners import agnes_command, hermes_command


class RunnerTests(unittest.TestCase):
    def test_agnes_recipe_is_generated(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            command = agnes_command(project, "t1", "add a health endpoint")
            self.assertEqual(command[:3], ["agnes", "run", "--recipe"])
            self.assertEqual(json.loads(Path(command[3]).read_text())["prompt"], "add a health endpoint")

    def test_hermes_command_uses_custom_provider_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = list(hermes_command(Path(tmp), "t2", "fix bug", "qwen3.5:9b"))
            self.assertIn("--provider", command)
            self.assertIn("custom", command)
            self.assertIn("qwen3.5:9b", command)

    def test_hermes_managed_local_can_use_saved_provider_without_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = list(
                hermes_command(
                    Path(tmp),
                    "t3",
                    "fix bug",
                    "Qwen3-Coder",
                    provider=None,
                )
            )
            self.assertNotIn("--provider", command)
            self.assertIn("--model", command)
            self.assertIn("Qwen3-Coder", command)


if __name__ == "__main__":
    unittest.main()
