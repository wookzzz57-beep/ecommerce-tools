import subprocess
from types import SimpleNamespace
import unittest

from firstwindow.bootstrap import install_command, run_installer_command, setup_actions
from firstwindow.windows_paths import runtime_path_candidates


class BootstrapTests(unittest.TestCase):
    def test_windows_install_commands_match_official_installers(self):
        self.assertEqual(
            install_command("windows", "agnes"),
            ["powershell", "-NoProfile", "-Command", "irm https://cos-agnes-code.agnes-ai.cn/cli-cn/release/download_cli.ps1 | iex"],
        )
        self.assertEqual(
            install_command("windows", "hermes"),
            ["powershell", "-NoProfile", "-Command", "iex (irm https://hermes-agent.nousresearch.com/install.ps1)"],
        )

    def test_installer_runner_reports_success(self):
        calls = []
        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(returncode=0)

        outcome = run_installer_command(
            ["installer", "--test"],
            timeout_seconds=12,
            creationflags=7,
            runner=runner,
        )
        self.assertEqual(outcome.exit_code, 0)
        self.assertFalse(outcome.timed_out)
        self.assertIsNone(outcome.error)
        self.assertEqual(calls[0][1]["timeout"], 12)
        self.assertEqual(calls[0][1]["creationflags"], 7)

    def test_installer_runner_preserves_nonzero_exit(self):
        def runner(command, **kwargs):
            return SimpleNamespace(returncode=7)

        outcome = run_installer_command(["installer"], runner=runner)
        self.assertEqual(outcome.exit_code, 7)
        self.assertFalse(outcome.timed_out)
        self.assertIsNone(outcome.error)

    def test_installer_runner_fails_closed_on_timeout(self):
        def runner(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        outcome = run_installer_command(["installer"], timeout_seconds=1, runner=runner)
        self.assertIsNone(outcome.exit_code)
        self.assertTrue(outcome.timed_out)
        self.assertEqual(outcome.error, "timeout")

    def test_installer_runner_reports_launcher_error(self):
        def runner(command, **kwargs):
            raise OSError("network launcher unavailable")

        outcome = run_installer_command(["installer"], runner=runner)
        self.assertIsNone(outcome.exit_code)
        self.assertFalse(outcome.timed_out)
        self.assertIn("network launcher unavailable", outcome.error or "")

    def test_setup_actions_only_include_missing_runtimes(self):
        actions = setup_actions(platform_name="windows", agnes_installed=False, hermes_installed=True)
        self.assertEqual([item.target for item in actions], ["agnes"])
        self.assertTrue(actions[0].requires_confirmation)

    def test_unknown_platform_is_rejected(self):
        with self.assertRaises(ValueError):
            install_command("plan9", "agnes")

    def test_windows_hermes_path_refresh_candidates_cover_current_and_legacy_layouts(self):
        paths = runtime_path_candidates(
            "windows",
            "hermes",
            {"LOCALAPPDATA": r"C:\Users\demo\AppData\Local"},
        )
        normalized = [str(path).replace("\\", "/").lower() for path in paths]
        self.assertTrue(any(path.endswith("/hermes/bin") for path in normalized))
        self.assertTrue(any(path.endswith("/hermes/hermes-agent/venv/scripts") for path in normalized))

    def test_windows_agnes_path_refresh_candidate_matches_official_installer(self):
        paths = runtime_path_candidates(
            "windows",
            "agnes",
            {"LOCALAPPDATA": r"C:\\Users\\demo\\AppData\\Local"},
        )
        normalized = [str(path).replace("\\", "/").lower() for path in paths]
        self.assertEqual(normalized, ["c:/users/demo/appdata/local/agnes/bin"])


if __name__ == "__main__":
    unittest.main()
