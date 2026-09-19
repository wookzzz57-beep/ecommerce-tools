from pathlib import Path
import unittest


class ReleaseSurfaceTests(unittest.TestCase):
    def test_public_site_uses_latest_release_alias_not_stale_version_copy(self):
        html = Path("site/index.html").read_text(encoding="utf-8")
        self.assertIn("releases/latest", html)
        self.assertIn("Download latest Windows", html)
        self.assertNotIn("v0.3.0 Release", html)
        self.assertNotIn("Download v0.3.0", html)

    def test_public_site_matches_hermes_first_execution_architecture(self):
        html = Path("site/index.html").read_text(encoding="utf-8")
        app = Path("site/app.js").read_text(encoding="utf-8")
        self.assertIn("Hermes Agent", html)
        self.assertIn("Agnes API", html)
        self.assertIn("Hermes Agent", app)
        self.assertIn("Agnes API", app)
        self.assertNotIn("run Agnes Recipe", app)

    def test_readme_does_not_describe_released_v04_as_candidate(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        self.assertNotIn("v0.4 Windows candidate", readme)
        self.assertNotIn("released v0.3 package until v0.4", readme)
        self.assertIn("v0.4 Windows app", readme)


if __name__ == "__main__":
    unittest.main()
