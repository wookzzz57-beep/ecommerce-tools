import json
import unittest

from firstwindow.system_status import (
    hermes_local_ready,
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


if __name__ == "__main__":
    unittest.main()
