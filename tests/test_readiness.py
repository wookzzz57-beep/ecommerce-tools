import subprocess
from types import SimpleNamespace
import tempfile
from pathlib import Path
import unittest

from firstwindow.readiness import build_readiness, probe_command, route_fingerprint, setup_watch_expired


class ReadinessTests(unittest.TestCase):
    def test_missing_runtimes_recommends_hermes_install(self):
        report = build_readiness(
            agnes_installed=False,
            agnes_free_confirmed=False,
            agnes_headless_ready=False,
            hermes_installed=False,
            hermes_model={},
        )
        self.assertEqual(report.state, "blocked")
        self.assertEqual(report.action, "install-hermes")
        self.assertFalse(report.zero_cost_ready)

    def test_cloud_configured_hermes_is_not_zero_cost_ready(self):
        report = build_readiness(
            agnes_installed=False,
            agnes_free_confirmed=False,
            agnes_headless_ready=False,
            hermes_installed=True,
            hermes_model={"provider": "agnes", "default": "agnes-2.5-flash"},
        )
        self.assertTrue(report.hermes.installed)
        self.assertTrue(report.hermes.configured)
        self.assertFalse(report.hermes.zero_cost_ready)
        self.assertEqual(report.action, "configure-hermes-local")

    def test_managed_local_hermes_is_ready(self):
        report = build_readiness(
            agnes_installed=False,
            agnes_free_confirmed=False,
            agnes_headless_ready=False,
            hermes_installed=True,
            hermes_model={"provider": "llamacpp", "default": "local-model"},
        )
        self.assertTrue(report.zero_cost_ready)
        self.assertEqual(report.ready_lane, "hermes-local")
        self.assertEqual(report.state, "ready")

    def test_explicitly_confirmed_agnes_is_ready(self):
        report = build_readiness(
            agnes_installed=True,
            agnes_free_confirmed=True,
            agnes_headless_ready=True,
            hermes_installed=False,
            hermes_model={},
        )
        self.assertTrue(report.zero_cost_ready)
        self.assertEqual(report.ready_lane, "agnes-free")

    def test_setup_watch_has_a_hard_stop(self):
        self.assertFalse(setup_watch_expired(199, 200))
        self.assertTrue(setup_watch_expired(200, 200))
        self.assertTrue(setup_watch_expired(201, 200))
        with self.assertRaises(ValueError):
            setup_watch_expired(0, 0)

    def test_route_fingerprint_invalidates_changed_or_blocked_route(self):
        local_a = build_readiness(
            agnes_installed=False,
            agnes_free_confirmed=False,
            agnes_headless_ready=False,
            hermes_installed=True,
            hermes_model={"provider": "llamacpp", "default": "model-a"},
        )
        local_b = build_readiness(
            agnes_installed=False,
            agnes_free_confirmed=False,
            agnes_headless_ready=False,
            hermes_installed=True,
            hermes_model={"provider": "llamacpp", "default": "model-b"},
        )
        blocked = build_readiness(
            agnes_installed=False,
            agnes_free_confirmed=False,
            agnes_headless_ready=False,
            hermes_installed=True,
            hermes_model={"provider": "agnes", "default": "cloud"},
        )
        proof = route_fingerprint(local_a, "hermes-local")
        self.assertIsNotNone(proof)
        self.assertNotEqual(proof, route_fingerprint(local_b, "hermes-local"))
        self.assertIsNone(route_fingerprint(blocked, "hermes-local"))

    def test_agnes_fingerprint_requires_current_free_confirmation(self):
        ready = build_readiness(
            agnes_installed=True,
            agnes_free_confirmed=True,
            agnes_headless_ready=True,
            hermes_installed=False,
            hermes_model={},
        )
        blocked = build_readiness(
            agnes_installed=True,
            agnes_free_confirmed=False,
            agnes_headless_ready=False,
            hermes_installed=False,
            hermes_model={},
        )
        self.assertEqual(route_fingerprint(ready, "agnes-free"), ("agnes-free", None, None))
        self.assertIsNone(route_fingerprint(blocked, "agnes-free"))

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

    def test_probe_accepts_expected_marker(self):
        def runner(command, **kwargs):
            return SimpleNamespace(returncode=0, stdout="FIRSTWINDOW_READY\n", stderr="")
        with tempfile.TemporaryDirectory() as tmp:
            result = probe_command(
                ["agent", "check"],
                Path(tmp),
                runner=runner,
                expected_text="FIRSTWINDOW_READY",
            )
        self.assertTrue(result.passed)

    def test_probe_timeout_fails_closed(self):
        def runner(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        with tempfile.TemporaryDirectory() as tmp:
            result = probe_command(["agent"], Path(tmp), runner=runner, timeout=1)
        self.assertFalse(result.passed)
        self.assertEqual(result.reason, "timeout")


if __name__ == "__main__":
    unittest.main()
