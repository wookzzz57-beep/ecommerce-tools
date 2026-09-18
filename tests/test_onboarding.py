import unittest

from firstwindow.onboarding import BeginnerState, recommend_next_action


class OnboardingTests(unittest.TestCase):
    def test_ready_when_free_agnes_is_available(self):
        state = BeginnerState(agnes_installed=True, agnes_free_confirmed=True, hermes_installed=False, hermes_local_ready=False)
        self.assertEqual(recommend_next_action(state), "ready")

    def test_ready_when_hermes_local_is_available(self):
        state = BeginnerState(agnes_installed=False, agnes_free_confirmed=False, hermes_installed=True, hermes_local_ready=True)
        self.assertEqual(recommend_next_action(state), "ready")

    def test_install_runtime_before_configuration(self):
        state = BeginnerState(agnes_installed=False, agnes_free_confirmed=False, hermes_installed=False, hermes_local_ready=False)
        self.assertEqual(recommend_next_action(state), "install")

    def test_configure_when_runtime_exists_but_no_zero_cost_lane(self):
        state = BeginnerState(agnes_installed=True, agnes_free_confirmed=False, hermes_installed=True, hermes_local_ready=False)
        self.assertEqual(recommend_next_action(state), "configure")


if __name__ == "__main__":
    unittest.main()
