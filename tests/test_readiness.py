import subprocess
from types import SimpleNamespace
import tempfile
from pathlib import Path
import unittest

from firstwindow.hermes_agnes import HermesAgnesRoute
from firstwindow.readiness import build_readiness, probe_command, route_fingerprint, route_is_verified, setup_watch_expired


def route(*, ready=True, model="agnes-2.5-flash", base_url="https://apihub.agnes-ai.com/v1"):
    return HermesAgnesRoute(
        hermes_installed=True,
        provider_configured=True,
        selected=True,
        no_fallbacks=ready,
        ready=ready,
        model=model,
        base_url=base_url,
        key_env="AGNES_API_KEY",
        profile_home=r"C:\Hermes\profiles\firstwindowzero",
        reason="agnes-hermes-isolated-ready" if ready else "fallbacks-not-empty",
    )


class ReadinessTests(unittest.TestCase):
    def test_missing_hermes_recommends_install(self):
        report = build_readiness(
            agnes_free_confirmed=False,
            agnes_key_fingerprint="key-a",
            agnes_route=HermesAgnesRoute(
                False, False, False, False, False, None, None, None, None, "hermes-not-installed"
            ),
            hermes_installed=False,
            hermes_model={},
        )
        self.assertEqual(report.state, "blocked")
        self.assertEqual(report.action, "install-hermes")
        self.assertFalse(report.zero_cost_ready)

    def test_configured_agnes_profile_waits_for_free_confirmation(self):
        report = build_readiness(
            agnes_free_confirmed=False,
            agnes_key_fingerprint="key-a",
            agnes_route=route(),
            hermes_installed=True,
            hermes_model={"provider": "agnes", "default": "agnes-2.5-flash"},
        )
        self.assertFalse(report.zero_cost_ready)
        self.assertEqual(report.action, "confirm-agnes-free")
        self.assertTrue(report.agnes.configured)

    def test_confirmed_agnes_via_hermes_is_ready(self):
        report = build_readiness(
            agnes_free_confirmed=True,
            agnes_key_fingerprint="key-a",
            agnes_route=route(),
            hermes_installed=True,
            hermes_model={"provider": "agnes", "default": "agnes-2.5-flash"},
        )
        self.assertTrue(report.zero_cost_ready)
        self.assertEqual(report.ready_lane, "agnes-free")
        self.assertEqual(report.agnes.engine, "hermes")
        self.assertEqual(report.agnes.provider, "agnes")

    def test_agnes_profile_with_fallback_is_not_ready(self):
        report = build_readiness(
            agnes_free_confirmed=True,
            agnes_key_fingerprint="key-a",
            agnes_route=route(ready=False),
            hermes_installed=True,
            hermes_model={"provider": "agnes", "default": "agnes-2.5-flash"},
        )
        self.assertFalse(report.zero_cost_ready)
        self.assertEqual(report.action, "prepare-agnes-profile")

    def test_managed_local_hermes_is_ready(self):
        report = build_readiness(
            agnes_free_confirmed=False,
            agnes_key_fingerprint="key-a",
            agnes_route=route(ready=False),
            hermes_installed=True,
            hermes_model={"provider": "llamacpp", "default": "local-model"},
        )
        self.assertTrue(report.zero_cost_ready)
        self.assertEqual(report.ready_lane, "hermes-local")
        self.assertEqual(report.state, "ready")

    def test_route_execution_requires_exact_live_probe_fingerprint(self):
        ready = build_readiness(
            agnes_free_confirmed=True,
            agnes_key_fingerprint="key-a",
            agnes_route=route(),
            hermes_installed=True,
            hermes_model={},
        )
        proof = route_fingerprint(ready, "agnes-free")
        self.assertTrue(route_is_verified(ready, "agnes-free", "agnes-free", proof))
        self.assertFalse(route_is_verified(ready, "agnes-free", None, None))
        self.assertFalse(route_is_verified(ready, "agnes-free", "hermes-local", proof))

    def test_agnes_missing_key_blocks_cloud_lane_after_free_confirmation(self):
        report = build_readiness(
            agnes_free_confirmed=True,
            agnes_key_fingerprint=None,
            agnes_route=route(),
            hermes_installed=True,
            hermes_model={"provider": "agnes", "default": "agnes-2.5-flash"},
        )
        self.assertFalse(report.zero_cost_ready)
        self.assertFalse(report.agnes.credential_present)
        self.assertEqual(report.action, "configure-agnes-key")
        self.assertIsNone(route_fingerprint(report, "agnes-free"))

    def test_ready_local_lane_does_not_require_agnes_key(self):
        report = build_readiness(
            agnes_free_confirmed=False,
            agnes_key_fingerprint=None,
            agnes_route=route(),
            hermes_installed=True,
            hermes_model={"provider": "llamacpp", "default": "local-model"},
        )
        self.assertTrue(report.zero_cost_ready)
        self.assertEqual(report.ready_lane, "hermes-local")

    def test_agnes_key_change_invalidates_live_probe_fingerprint(self):
        first = build_readiness(
            agnes_free_confirmed=True,
            agnes_key_fingerprint="key-a",
            agnes_route=route(),
            hermes_installed=True,
            hermes_model={},
        )
        changed = build_readiness(
            agnes_free_confirmed=True,
            agnes_key_fingerprint="key-b",
            agnes_route=route(),
            hermes_installed=True,
            hermes_model={},
        )
        proof = route_fingerprint(first, "agnes-free")
        self.assertNotEqual(proof, route_fingerprint(changed, "agnes-free"))
        self.assertFalse(route_is_verified(changed, "agnes-free", "agnes-free", proof))

    def test_setup_watch_has_a_hard_stop(self):
        self.assertFalse(setup_watch_expired(199, 200))
        self.assertTrue(setup_watch_expired(200, 200))
        self.assertTrue(setup_watch_expired(201, 200))
        with self.assertRaises(ValueError):
            setup_watch_expired(0, 0)

    def test_route_fingerprint_invalidates_changed_agnes_route(self):
        ready = build_readiness(
            agnes_free_confirmed=True,
            agnes_key_fingerprint="key-a",
            agnes_route=route(),
            hermes_installed=True,
            hermes_model={"provider": "agnes", "default": "agnes-2.5-flash"},
        )
        changed = build_readiness(
            agnes_free_confirmed=True,
            agnes_key_fingerprint="key-a",
            agnes_route=route(model="agnes-other"),
            hermes_installed=True,
            hermes_model={"provider": "agnes", "default": "agnes-other"},
        )
        blocked = build_readiness(
            agnes_free_confirmed=False,
            agnes_key_fingerprint="key-a",
            agnes_route=route(),
            hermes_installed=True,
            hermes_model={"provider": "agnes", "default": "agnes-2.5-flash"},
        )
        proof = route_fingerprint(ready, "agnes-free")
        self.assertEqual(
            proof,
            ("agnes-free", "agnes", "agnes-2.5-flash", "https://apihub.agnes-ai.com/v1", "key-a"),
        )
        self.assertNotEqual(proof, route_fingerprint(changed, "agnes-free"))
        self.assertIsNone(route_fingerprint(blocked, "agnes-free"))

    def test_local_fingerprint_invalidates_changed_model(self):
        local_a = build_readiness(
            agnes_free_confirmed=False,
            agnes_key_fingerprint="key-a",
            agnes_route=route(ready=False),
            hermes_installed=True,
            hermes_model={"provider": "llamacpp", "default": "model-a"},
        )
        local_b = build_readiness(
            agnes_free_confirmed=False,
            agnes_key_fingerprint="key-a",
            agnes_route=route(ready=False),
            hermes_installed=True,
            hermes_model={"provider": "llamacpp", "default": "model-b"},
        )
        self.assertNotEqual(
            route_fingerprint(local_a, "hermes-local"),
            route_fingerprint(local_b, "hermes-local"),
        )

    def test_probe_command_reports_real_process_result(self):
        calls = []
        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(returncode=0, stdout="FIRSTWINDOW_READY\n", stderr="")
        with tempfile.TemporaryDirectory() as tmp:
            result = probe_command(["agent", "check"], Path(tmp), runner=runner, timeout=12)
        self.assertTrue(result.passed)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("FIRSTWINDOW_READY", result.output)
        self.assertEqual(calls[0][1]["timeout"], 12)

    def test_probe_requires_expected_marker_when_requested(self):
        def runner(command, **kwargs):
            return SimpleNamespace(returncode=0, stdout="agent exited cleanly\n", stderr="")
        with tempfile.TemporaryDirectory() as tmp:
            result = probe_command(
                ["agent", "check"],
                Path(tmp),
                runner=runner,
                expected_text="FIRSTWINDOW_READY",
            )
        self.assertFalse(result.passed)
        self.assertEqual(result.reason, "expected-output-missing")

    def test_probe_timeout_fails_closed(self):
        def runner(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        with tempfile.TemporaryDirectory() as tmp:
            result = probe_command(["agent"], Path(tmp), runner=runner, timeout=1)
        self.assertFalse(result.passed)
        self.assertEqual(result.reason, "timeout")


if __name__ == "__main__":
    unittest.main()
