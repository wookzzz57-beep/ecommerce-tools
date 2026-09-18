import unittest
from unittest.mock import patch
from firstwindow.router import choose_lane, detect_lanes

class RouterTests(unittest.TestCase):
    @patch("firstwindow.router.command_exists")
    def test_zero_cost_prefers_confirmed_agnes(self, exists):
        exists.side_effect = lambda name: name in {"agnes", "hermes", "ollama"}
        env = {"FIRSTWINDOW_AGNES_FREE_CONFIRMED":"1","FIRSTWINDOW_HERMES_LOCAL_CONFIRMED":"1","FIRSTWINDOW_LOCAL_MODEL":"qwen3.5:9b"}
        self.assertEqual(choose_lane(detect_lanes(env), zero_cost=True).name, "agnes-free")

    @patch("firstwindow.router.command_exists", return_value=True)
    def test_zero_cost_blocks_unconfirmed_provider(self, _exists):
        with self.assertRaises(RuntimeError):
            choose_lane(detect_lanes({}), zero_cost=True)

    @patch("firstwindow.router.command_exists")
    def test_local_hermes_is_second_zero_cost_lane(self, exists):
        exists.side_effect = lambda name: name in {"hermes", "ollama"}
        env = {"FIRSTWINDOW_HERMES_LOCAL_CONFIRMED":"true","FIRSTWINDOW_LOCAL_MODEL":"qwen3.5:9b"}
        self.assertEqual(choose_lane(detect_lanes(env), zero_cost=True).name, "hermes-local")

if __name__ == "__main__":
    unittest.main()
