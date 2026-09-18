from pathlib import Path
import unittest

from firstwindow.release_policy import validate_windows_release_workflow


class ReleasePolicyTests(unittest.TestCase):
    def test_release_workflow_is_tag_driven_and_publishes_checksum(self):
        workflow = Path(".github/workflows/windows-build.yml").read_text(encoding="utf-8")
        failures = validate_windows_release_workflow(workflow)
        self.assertEqual(failures, [])

    def test_hardcoded_legacy_release_is_rejected(self):
        failures = validate_windows_release_workflow(
            "on:\n  push:\n    branches: [main]\nrun: gh release create v0.2.0 FirstWindow-Windows-x64.exe"
        )
        self.assertTrue(any("hard-coded" in item for item in failures))

    def test_main_push_release_mutation_is_rejected(self):
        failures = validate_windows_release_workflow(
            "on:\n  push:\n    branches: [main]\nif: github.ref == 'refs/heads/main'\nrun: gh release edit"
        )
        self.assertTrue(any("tag-driven" in item for item in failures))

    def test_missing_checksum_asset_is_rejected(self):
        failures = validate_windows_release_workflow(
            "on:\n  push:\n    tags: ['v*']\nrun: gh release create $TAG FirstWindow-Windows-x64.exe"
        )
        self.assertTrue(any("checksum" in item.lower() for item in failures))


if __name__ == "__main__":
    unittest.main()
