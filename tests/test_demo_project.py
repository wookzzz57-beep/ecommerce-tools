from pathlib import Path
import tempfile
import unittest

from firstwindow.demo_project import create_demo_project


class DemoProjectTests(unittest.TestCase):
    def test_create_demo_project_makes_beginner_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "firstwindow-demo"
            created = create_demo_project(target)
            self.assertEqual(created, target)
            self.assertTrue((target / "index.html").is_file())
            self.assertTrue((target / "README.md").is_file())
            self.assertIn("FirstWindow Demo", (target / "README.md").read_text(encoding="utf-8"))

    def test_demo_project_refuses_to_overwrite_nonempty_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "existing"
            target.mkdir()
            (target / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                create_demo_project(target)


if __name__ == "__main__":
    unittest.main()
