import unittest

from firstwindow.distribution import (
    AGNES_DESKTOP_URL,
    HERMES_DESKTOP_URL,
    beginner_setup_action,
)


class DistributionTests(unittest.TestCase):
    def test_missing_hermes_prefers_official_desktop_page(self):
        action = beginner_setup_action("hermes")
        self.assertEqual(action.kind, "open_url")
        self.assertEqual(action.target, HERMES_DESKTOP_URL)
        self.assertTrue(action.requires_user_action)

    def test_missing_agnes_prefers_official_desktop_page(self):
        action = beginner_setup_action("agnes")
        self.assertEqual(action.kind, "open_url")
        self.assertEqual(action.target, AGNES_DESKTOP_URL)
        self.assertTrue(action.requires_user_action)

    def test_beginner_default_never_contains_remote_shell_command(self):
        for target in ("agnes", "hermes"):
            action = beginner_setup_action(target)
            self.assertNotIn("powershell", action.target.lower())
            self.assertNotIn("irm ", action.target.lower())
            self.assertNotIn("iex", action.target.lower())

    def test_unknown_target_fails_closed(self):
        with self.assertRaises(ValueError):
            beginner_setup_action("unknown")


if __name__ == "__main__":
    unittest.main()
