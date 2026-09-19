import json
import unittest

from firstwindow.system_status import (
    AgnesCapabilities,
    hermes_local_ready,
    read_agnes_capabilities,
    parse_hermes_model_json,
    read_hermes_model,
)


class _Completed:
    returncode = 0
    stdout = '{"provider":"llamacpp","default":"Qwen3-Coder"}'


class SystemStatusTests(unittest.TestCase):
    def test_managed_llamacpp_is_verified_local(self):
        model = parse_hermes_model_json(json.dumps({"provider": "llamacpp", "default": "Qwen3-Coder"}))
        self.assertTrue(hermes_local_ready(model))
        self.assertEqual(model["provider"], "llamacpp")

    def test_cloud_provider_is_not_local(self):
        model = parse_hermes_model_json(json.dumps({"provider": "openrouter", "default": "qwen/qwen3"}))
        self.assertFalse(hermes_local_ready(model))

    def test_invalid_model_output_fails_closed(self):
        self.assertEqual(parse_hermes_model_json("not-json"), {})
        self.assertFalse(hermes_local_ready({}))

    def test_read_hermes_model_uses_non_secret_config_query(self):
        calls = []

        def fake_which(name):
            return "hermes" if name == "hermes" else None

        def fake_run(command, **kwargs):
            calls.append(command)
            return _Completed()

        model = read_hermes_model(which=fake_which, runner=fake_run)
        self.assertTrue(hermes_local_ready(model))
        self.assertEqual(calls[0], ["hermes", "config", "get", "model", "--json"])

    def test_agnes_headless_recipe_capability_requires_real_supported_help(self):
        calls = []
        def fake_which(name):
            return "agnes" if name == "agnes" else None
        def fake_run(command, **kwargs):
            calls.append(command)
            if "--version" in command:
                return type("Done", (), {"returncode": 0, "stdout": "agnes 1.99.0\n", "stderr": ""})()
            return type("Done", (), {"returncode": 0, "stdout": "Usage: agnes run --recipe FILE\n", "stderr": ""})()
        cap = read_agnes_capabilities(which=fake_which, runner=fake_run)
        self.assertTrue(cap.installed)
        self.assertTrue(cap.headless_recipe_ready)
        self.assertEqual(cap.reason, "headless-recipe-ready")
        self.assertEqual(len(calls), 2)

    def test_agnes_installed_but_unsupported_run_fails_closed(self):
        def fake_which(name):
            return "agnes" if name == "agnes" else None
        def fake_run(command, **kwargs):
            if "--version" in command:
                return type("Done", (), {"returncode": 0, "stdout": "agnes 1.62.5\n", "stderr": ""})()
            return type("Done", (), {
                "returncode": 2,
                "stdout": "",
                "stderr": "error: the subcommand 'run' is not currently supported\n",
            })()
        cap = read_agnes_capabilities(which=fake_which, runner=fake_run)
        self.assertTrue(cap.installed)
        self.assertFalse(cap.headless_recipe_ready)
        self.assertEqual(cap.reason, "headless-run-unsupported")

    def test_agnes_missing_is_not_capable(self):
        cap = read_agnes_capabilities(which=lambda _name: None)
        self.assertEqual(cap, AgnesCapabilities(False, None, False, "not-installed"))


if __name__ == "__main__":
    unittest.main()
