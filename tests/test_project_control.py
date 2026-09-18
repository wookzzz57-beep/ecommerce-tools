import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_project_state import validate_project_state


class ProjectControlTests(unittest.TestCase):
    def test_valid_state_passes(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3-control-and-reliability",
            "status": "active",
            "canonical_branch": "main",
            "current_release": "v0.2.0",
            "primary_objective": "Improve reliability without expanding runtime scope.",
            "active_engineering_issue": 4,
            "engineering_queue": [4, 5],
            "launch_track": [6],
            "wip_limit": 1,
            "resume_point": "Start issue #4 from a fresh branch.",
            "last_verified_main_sha": "abc123",
        }
        self.assertEqual(validate_project_state(state), [])

    def test_missing_resume_point_fails(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3",
            "status": "active",
            "canonical_branch": "main",
            "current_release": "v0.2.0",
            "primary_objective": "x",
            "active_engineering_issue": 4,
            "engineering_queue": [4],
            "launch_track": [6],
            "wip_limit": 1,
            "last_verified_main_sha": "abc123",
        }
        failures = validate_project_state(state)
        self.assertTrue(any("resume_point" in item for item in failures))

    def test_wip_above_one_fails(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3",
            "status": "active",
            "canonical_branch": "main",
            "current_release": "v0.2.0",
            "primary_objective": "x",
            "active_engineering_issue": 4,
            "engineering_queue": [4, 5],
            "launch_track": [6],
            "wip_limit": 2,
            "resume_point": "continue",
            "last_verified_main_sha": "abc123",
        }
        failures = validate_project_state(state)
        self.assertTrue(any("wip_limit" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
