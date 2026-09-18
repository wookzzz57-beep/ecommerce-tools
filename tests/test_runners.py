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

    def test_hermes_command_uses_custom_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = list(hermes_command(Path(tmp), "t2", "fix bug", "qwen3.5:9b"))
            self.assertIn("custom", command)
            self.assertIn("qwen3.5:9b", command)

if __name__ == "__main__":
    unittest.main()
