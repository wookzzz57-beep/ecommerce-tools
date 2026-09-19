import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from firstwindow.hermes_agnes import (
    AGNES_KEY_ENV,
    AGNES_MODEL,
    HermesAgnesRoute,
    agnes_api_key_fingerprint,
    agnes_api_key_present,
    attest_hermes_usage,
    ensure_firstwindow_agnes_profile,
    parse_profile_path,
    read_hermes_agnes_route,
    save_agnes_api_key,
    scoped_env,
)


def done(code=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr)


class HermesAgnesTests(unittest.TestCase):
    def test_parse_profile_path(self):
        self.assertEqual(
            parse_profile_path("Profile: firstwindowzero\nPath:    C:\\Hermes\\profiles\\firstwindowzero\n"),
            r"C:\Hermes\profiles\firstwindowzero",
        )
        self.assertIsNone(parse_profile_path("Profile missing"))

    def test_isolated_route_requires_official_agnes_config_and_empty_fallbacks(self):
        responses = {
            "model": {"default": AGNES_MODEL, "provider": "agnes", "base_url": "https://apihub.agnes-ai.com/v1"},
            "providers.agnes": {
                "api": "https://apihub.agnes-ai.com/v1",
                "key_env": "AGNES_API_KEY",
                "transport": "chat_completions",
                "default_model": AGNES_MODEL,
            },
            "fallback_providers": [],
        }
        def runner(command, **kwargs):
            key = command[3]
            return done(stdout=json.dumps(responses[key]))

        route = read_hermes_agnes_route(
            r"C:\Hermes\profiles\firstwindowzero",
            which=lambda name: "hermes" if name == "hermes" else None,
            runner=runner,
        )
        self.assertTrue(route.ready)
        self.assertTrue(route.provider_configured)
        self.assertTrue(route.selected)
        self.assertTrue(route.no_fallbacks)
        self.assertEqual(route.model, AGNES_MODEL)

    def test_route_fails_closed_when_fallback_exists(self):
        responses = {
            "model": {"default": AGNES_MODEL, "provider": "agnes"},
            "providers.agnes": {
                "api": "https://apihub.agnes-ai.com/v1",
                "key_env": "AGNES_API_KEY",
                "transport": "chat_completions",
            },
            "fallback_providers": [{"provider": "deepseek", "model": "deepseek-v4-pro"}],
        }
        def runner(command, **kwargs):
            return done(stdout=json.dumps(responses[command[3]]))

        route = read_hermes_agnes_route(
            r"C:\Hermes\profiles\firstwindowzero",
            which=lambda _name: "hermes",
            runner=runner,
        )
        self.assertFalse(route.ready)
        self.assertEqual(route.reason, "fallbacks-not-empty")

    def test_usage_attestation_rejects_hidden_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.json"
            path.write_text(json.dumps({
                "completed": True,
                "failed": False,
                "api_calls": 1,
                "model": "deepseek-v4-pro",
                "provider": "deepseek",
            }), encoding="utf-8")
            result = attest_hermes_usage(path, expected_model=AGNES_MODEL)
        self.assertFalse(result.passed)
        self.assertEqual(result.reason, "unexpected-model")

    def test_usage_attestation_accepts_agnes_custom_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.json"
            path.write_text(json.dumps({
                "completed": True,
                "failed": False,
                "api_calls": 1,
                "model": AGNES_MODEL,
                "provider": "custom",
            }), encoding="utf-8")
            result = attest_hermes_usage(path, expected_model=AGNES_MODEL)
        self.assertTrue(result.passed)
        self.assertEqual(result.provider, "custom")

    def test_explicit_key_save_is_isolated_and_presence_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp)
            env_path = profile / ".env"
            env_path.write_text("# existing\nOPENAI_API_KEY=do-not-touch\n", encoding="utf-8")
            self.assertFalse(agnes_api_key_present(profile, {}))
            save_agnes_api_key(profile, "agnes-test-key-123")
            self.assertTrue(agnes_api_key_present(profile, {}))
            text = env_path.read_text(encoding="utf-8")
            self.assertIn("OPENAI_API_KEY=do-not-touch", text)
            self.assertIn("AGNES_API_KEY=agnes-test-key-123", text)

    def test_empty_env_mapping_does_not_inherit_process_agnes_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp)
            with patch.dict(os.environ, {AGNES_KEY_ENV: "process-secret"}, clear=False):
                self.assertFalse(agnes_api_key_present(profile, {}))
                self.assertIsNone(agnes_api_key_fingerprint(profile, {}))
                self.assertTrue(agnes_api_key_present(profile, None))
                self.assertIsNotNone(agnes_api_key_fingerprint(profile, None))

    def test_scoped_profile_env_removes_ambient_agnes_key(self):
        env = scoped_env(r"C:\\Hermes\\profiles\\firstwindowzero", {
            AGNES_KEY_ENV: "ambient-secret",
            "KEEP_ME": "yes",
        })
        self.assertNotIn(AGNES_KEY_ENV, env)
        self.assertEqual(env["KEEP_ME"], "yes")
        self.assertEqual(env["HERMES_HOME"], r"C:\\Hermes\\profiles\\firstwindowzero")

    def test_key_fingerprint_changes_without_exposing_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp)
            save_agnes_api_key(profile, "agnes-test-key-one")
            first = agnes_api_key_fingerprint(profile, {})
            save_agnes_api_key(profile, "agnes-test-key-two")
            second = agnes_api_key_fingerprint(profile, {})
            self.assertNotEqual(first, second)
            self.assertNotIn("agnes-test", first or "")
            self.assertNotIn("agnes-test", second or "")

    def test_key_save_rejects_multiline_or_whitespace_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                save_agnes_api_key(Path(tmp), "bad key")
            with self.assertRaises(ValueError):
                save_agnes_api_key(Path(tmp), "bad\nkey")

    def test_profile_setup_fails_closed_when_hermes_is_missing(self):
        result = ensure_firstwindow_agnes_profile(which=lambda _name: None)
        self.assertFalse(result.ready)
        self.assertEqual(result.reason, "hermes-not-installed")
        self.assertFalse(result.route.hermes_installed)

    def test_profile_setup_creates_blank_profile_and_never_passes_secret_value(self):
        calls = []
        show_count = 0
        profile_path = r"C:\Hermes\profiles\firstwindowzero"
        def runner(command, **kwargs):
            nonlocal show_count
            calls.append((list(command), dict(kwargs.get("env") or {})))
            if command[:3] == ["hermes", "profile", "show"]:
                show_count += 1
                if show_count == 1:
                    return done(code=1, stderr="missing")
                return done(stdout=f"Profile: firstwindowzero\nPath:    {profile_path}\n")
            if command[:3] == ["hermes", "profile", "create"]:
                return done(stdout="created")
            if command[:3] == ["hermes", "config", "set"]:
                return done(stdout="set")
            if command[:3] == ["hermes", "config", "get"]:
                key = command[3]
                values = {
                    "model": {"default": AGNES_MODEL, "provider": "agnes", "base_url": "https://apihub.agnes-ai.com/v1"},
                    "providers.agnes": {
                        "api": "https://apihub.agnes-ai.com/v1",
                        "key_env": "AGNES_API_KEY",
                        "transport": "chat_completions",
                    },
                    "fallback_providers": [],
                }
                return done(stdout=json.dumps(values[key]))
            return done()

        result = ensure_firstwindow_agnes_profile(
            runner=runner,
            which=lambda name: "hermes" if name == "hermes" else None,
        )
        self.assertTrue(result.ready)
        self.assertTrue(result.created)
        flattened = "\n".join(" ".join(command) for command, _env in calls)
        self.assertIn("profile create firstwindowzero --no-alias --no-skills", flattened)
        self.assertNotIn("--clone", flattened)
        self.assertNotIn("--clone-from", flattened)
        self.assertIn("config set fallback_providers []", flattened)
        self.assertIn("AGNES_API_KEY", flattened)
        self.assertNotIn("Bearer ", flattened)
        self.assertTrue(any(env.get("HERMES_HOME") == profile_path for _command, env in calls if env))


if __name__ == "__main__":
    unittest.main()
