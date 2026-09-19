from pathlib import Path
import json
import tempfile
import unittest

from firstwindow.runners import agnes_command, hermes_command, project_env


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

    def test_project_env_overrides_stale_terminal_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            env = project_env(project, {"TERMINAL_CWD": r"C:\wrong", "HERMES_HOME": r"C:\profile"})
            self.assertEqual(Path(env["TERMINAL_CWD"]), project.resolve())
            self.assertEqual(env["HERMES_HOME"], r"C:\profile")

    def test_hermes_command_pins_project_directory_and_disables_cwd_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            command = list(hermes_command(project, "cwd", "touch fixture", "agnes-2.5-flash", provider="agnes"))
            self.assertIn("--in", command)
            self.assertEqual(Path(command[command.index("--in") + 1]), project)
            self.assertIn("--no-restore-cwd", command)

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

    def test_hermes_zero_cost_local_isolates_user_fallback_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = list(
                hermes_command(
                    Path(tmp),
                    "t4",
                    "verify local lane",
                    "Qwen3-Coder",
                    provider="llamacpp",
                    isolate_user_config=True,
                )
            )
            self.assertIn("--ignore-user-config", command)
            self.assertIn("--provider", command)
            self.assertEqual(command[command.index("--provider") + 1], "llamacpp")

    def test_unknown_cost_hermes_keeps_user_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = list(hermes_command(Path(tmp), "t5", "cloud task", "cloud-model", provider="custom"))
            self.assertNotIn("--ignore-user-config", command)


if __name__ == "__main__":
    unittest.main()
