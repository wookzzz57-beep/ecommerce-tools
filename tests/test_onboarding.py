import unittest

from firstwindow.onboarding import BeginnerState, recommend_next_action


class OnboardingTests(unittest.TestCase):
    def test_ready_when_agnes_api_profile_is_confirmed_free(self):
        state = BeginnerState(
            agnes_api_ready=True,
            agnes_free_confirmed=True,
            hermes_installed=True,
            hermes_local_ready=False,
        )
        self.assertEqual(recommend_next_action(state), "ready")

    def test_agnes_profile_needs_free_confirmation(self):
        state = BeginnerState(
            agnes_api_ready=True,
            agnes_free_confirmed=False,
            hermes_installed=True,
            hermes_local_ready=False,
        )
        self.assertEqual(recommend_next_action(state), "confirm")

    def test_ready_when_hermes_local_is_available(self):
        state = BeginnerState(
            agnes_api_ready=False,
            agnes_free_confirmed=False,
            hermes_installed=True,
            hermes_local_ready=True,
        )
        self.assertEqual(recommend_next_action(state), "ready")

    def test_install_hermes_before_configuration(self):
        state = BeginnerState(
            agnes_api_ready=False,
            agnes_free_confirmed=False,
            hermes_installed=False,
            hermes_local_ready=False,
        )
        self.assertEqual(recommend_next_action(state), "install")

    def test_configure_when_hermes_exists_but_no_zero_cost_lane(self):
        state = BeginnerState(
            agnes_api_ready=False,
            agnes_free_confirmed=False,
            hermes_installed=True,
            hermes_local_ready=False,
        )
        self.assertEqual(recommend_next_action(state), "configure")


if __name__ == "__main__":
    unittest.main()
