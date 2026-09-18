import unittest

from firstwindow.bootstrap import install_command, setup_actions


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


if __name__ == "__main__":
    unittest.main()
