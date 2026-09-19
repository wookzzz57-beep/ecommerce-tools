import unittest
from unittest.mock import patch

from firstwindow.hermes_agnes import HermesAgnesRoute
from firstwindow.router import choose_lane, detect_lanes
from firstwindow.system_status import AgnesCapabilities


def api_route(*, ready=True, fallbacks=False):
    return HermesAgnesRoute(
        hermes_installed=True,
        provider_configured=True,
        selected=True,
        no_fallbacks=not fallbacks,
        ready=ready and not fallbacks,
        model="agnes-2.5-flash",
        base_url="https://apihub.agnes-ai.com/v1",
        key_env="AGNES_API_KEY",
        profile_home=r"C:\Hermes\profiles\firstwindowzero",
        reason="agnes-hermes-isolated-ready" if ready and not fallbacks else "fallbacks-not-empty",
    )


class RouterTests(unittest.TestCase):
    @patch("firstwindow.router.command_exists")
    def test_zero_cost_prefers_confirmed_agnes_via_hermes(self, exists):
        exists.side_effect = lambda name: name == "hermes"
        env = {"FIRSTWINDOW_AGNES_FREE_CONFIRMED": "1"}
        lane = choose_lane(
            detect_lanes(
                env,
                agnes_route=api_route(),
                agnes_capabilities=AgnesCapabilities(False, None, False, "not-installed"),
            ),
            zero_cost=True,
        )
        self.assertEqual(lane.name, "agnes-free")
        self.assertEqual(lane.engine, "hermes")
        self.assertEqual(lane.provider, "agnes")
        self.assertEqual(lane.model, "agnes-2.5-flash")
        self.assertTrue(lane.profile_home)

    @patch("firstwindow.router.command_exists", return_value=True)
    def test_agnes_api_requires_explicit_free_confirmation(self, _exists):
        with patch.dict("os.environ", {"FIRSTWINDOW_AGNES_FREE_CONFIRMED": "1"}, clear=False):
            with self.assertRaises(RuntimeError):
                choose_lane(
                    detect_lanes(
                        {},
                        agnes_route=api_route(),
                        agnes_capabilities=AgnesCapabilities(False, None, False, "not-installed"),
                    ),
                    zero_cost=True,
                    preferred="agnes-free",
                )

    @patch("firstwindow.router.command_exists", return_value=True)
    def test_agnes_api_blocks_profile_with_fallbacks(self, _exists):
        env = {"FIRSTWINDOW_AGNES_FREE_CONFIRMED": "1"}
        with self.assertRaises(RuntimeError):
            choose_lane(
                detect_lanes(
                    env,
                    agnes_route=api_route(ready=False, fallbacks=True),
                    agnes_capabilities=AgnesCapabilities(False, None, False, "not-installed"),
                ),
                zero_cost=True,
                preferred="agnes-free",
            )

    @patch("firstwindow.router.command_exists")
    def test_local_hermes_is_second_zero_cost_lane(self, exists):
        exists.side_effect = lambda name: name == "hermes"
        env = {
            "FIRSTWINDOW_HERMES_LOCAL_CONFIRMED": "true",
            "FIRSTWINDOW_LOCAL_MODEL": "qwen3.5:9b",
        }
        lane = choose_lane(
            detect_lanes(
                env,
                agnes_route=None,
                agnes_capabilities=AgnesCapabilities(False, None, False, "not-installed"),
            ),
            zero_cost=True,
        )
        self.assertEqual(lane.name, "hermes-local")

    @patch("firstwindow.router.command_exists")
    def test_managed_hermes_local_uses_explicit_llamacpp_provider(self, exists):
        exists.side_effect = lambda name: name == "hermes"
        lanes = detect_lanes(
            {},
            hermes_model={"provider": "llamacpp", "default": "Qwen3-Coder"},
            agnes_route=None,
            agnes_capabilities=AgnesCapabilities(False, None, False, "not-installed"),
        )
        lane = choose_lane(lanes, zero_cost=True, preferred="hermes-local")
        self.assertEqual(lane.provider, "llamacpp")
        self.assertEqual(lane.model, "Qwen3-Coder")


if __name__ == "__main__":
    unittest.main()
