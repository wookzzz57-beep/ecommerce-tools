import json
import unittest

from firstwindow.system_status import hermes_local_ready, parse_hermes_model_json


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


if __name__ == "__main__":
    unittest.main()
