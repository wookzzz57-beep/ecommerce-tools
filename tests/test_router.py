import unittest
from unittest.mock import patch
from firstwindow.router import choose_lane, detect_lanes
from firstwindow.system_status import AgnesCapabilities

class RouterTests(unittest.TestCase):
    @patch("firstwindow.router.command_exists")
    def test_zero_cost_prefers_confirmed_agnes(self, exists):
        exists.side_effect = lambda name: name in {"agnes", "hermes", "ollama"}
        env = {"FIRSTWINDOW_AGNES_FREE_CONFIRMED":"1","FIRSTWINDOW_HERMES_LOCAL_CONFIRMED":"1","FIRSTWINDOW_LOCAL_MODEL":"qwen3.5:9b"}
        self.assertEqual(choose_lane(detect_lanes(env, agnes_capabilities=AgnesCapabilities(True, "agnes 1", True, "headless-recipe-ready")), zero_cost=True).name, "agnes-free")

    @patch("firstwindow.router.command_exists", return_value=True)
    def test_zero_cost_blocks_unconfirmed_provider(self, _exists):
        with self.assertRaises(RuntimeError):
            choose_lane(detect_lanes({}, agnes_capabilities=AgnesCapabilities(True, "agnes 1", False, "headless-run-unsupported")), zero_cost=True)

    @patch("firstwindow.router.command_exists")
    def test_local_hermes_is_second_zero_cost_lane(self, exists):
        exists.side_effect = lambda name: name in {"hermes", "ollama"}
        env = {"FIRSTWINDOW_HERMES_LOCAL_CONFIRMED":"true","FIRSTWINDOW_LOCAL_MODEL":"qwen3.5:9b"}
        self.assertEqual(choose_lane(detect_lanes(env, agnes_capabilities=AgnesCapabilities(False, None, False, "not-installed")), zero_cost=True).name, "hermes-local")

    @patch("firstwindow.router.command_exists", return_value=True)
    def test_confirmed_agnes_is_blocked_without_headless_recipe_support(self, _exists):
        env = {"FIRSTWINDOW_AGNES_FREE_CONFIRMED": "1"}
        lanes = detect_lanes(
            env,
            agnes_capabilities=AgnesCapabilities(True, "agnes 1.62.5", False, "headless-run-unsupported"),
        )
        with self.assertRaises(RuntimeError):
            choose_lane(lanes, zero_cost=True, preferred="agnes-free")

    @patch("firstwindow.router.command_exists")
    def test_managed_hermes_local_uses_explicit_llamacpp_provider(self, exists):
        exists.side_effect = lambda name: name == "hermes"
        lanes = detect_lanes(
            {},
            hermes_model={"provider": "llamacpp", "default": "Qwen3-Coder"},
            agnes_capabilities=AgnesCapabilities(False, None, False, "not-installed"),
        )
        lane = choose_lane(lanes, zero_cost=True, preferred="hermes-local")
        self.assertEqual(lane.provider, "llamacpp")
        self.assertEqual(lane.model, "Qwen3-Coder")

if __name__ == "__main__":
    unittest.main()
