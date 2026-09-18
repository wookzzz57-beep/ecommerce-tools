import unittest

from firstwindow.bootstrap import install_command, setup_actions
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


if __name__ == "__main__":
    unittest.main()
