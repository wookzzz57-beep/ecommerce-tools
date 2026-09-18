import unittest

from scripts.check_project_state import validate_project_state


class ProjectControlTests(unittest.TestCase):
    def test_valid_active_engineering_state_passes(self):
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
            "last_verified_main_sha": "abc1234",
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
            "last_verified_main_sha": "abc1234",
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
            "last_verified_main_sha": "abc1234",
        }
        failures = validate_project_state(state)
        self.assertTrue(any("wip_limit" in item for item in failures))

    def test_released_state_allows_empty_engineering_and_launch(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3-released",
            "status": "released",
            "canonical_branch": "main",
            "current_release": "v0.3.0",
            "primary_objective": "Preserve the released baseline.",
            "active_engineering_issue": None,
            "engineering_queue": [],
            "launch_track": [],
            "wip_limit": 1,
            "resume_point": "Open a new issue before new implementation.",
            "last_verified_main_sha": "abc1234",
            "external_blockers": [],
        }
        self.assertEqual(validate_project_state(state), [])

    def test_released_state_rejects_active_queue(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3-released",
            "status": "released",
            "canonical_branch": "main",
            "current_release": "v0.3.0",
            "primary_objective": "Preserve the released baseline.",
            "active_engineering_issue": 6,
            "engineering_queue": [6],
            "launch_track": [],
            "wip_limit": 1,
            "resume_point": "Release complete.",
            "last_verified_main_sha": "abc1234",
            "external_blockers": [],
        }
        failures = validate_project_state(state)
        self.assertTrue(any("released state" in item for item in failures))

    def test_released_state_rejects_launch_track(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3-released",
            "status": "released",
            "canonical_branch": "main",
            "current_release": "v0.3.0",
            "primary_objective": "Preserve the released baseline.",
            "active_engineering_issue": None,
            "engineering_queue": [],
            "launch_track": [17],
            "wip_limit": 1,
            "resume_point": "Release complete.",
            "last_verified_main_sha": "abc1234",
            "external_blockers": [],
        }
        failures = validate_project_state(state)
        self.assertTrue(any("launch_track" in item for item in failures))

    def test_released_state_rejects_external_blockers(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3-released",
            "status": "released",
            "canonical_branch": "main",
            "current_release": "v0.3.0",
            "primary_objective": "Preserve the released baseline.",
            "active_engineering_issue": None,
            "engineering_queue": [],
            "launch_track": [],
            "wip_limit": 1,
            "resume_point": "Release complete.",
            "last_verified_main_sha": "abc1234",
            "external_blockers": ["release verification incomplete"],
        }
        failures = validate_project_state(state)
        self.assertTrue(any("external_blockers" in item for item in failures))

    def test_valid_post_release_state_passes_without_engineering_wip(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3-post-release-launch",
            "status": "post-release",
            "canonical_branch": "main",
            "current_release": "v0.3.0",
            "primary_objective": "Collect real launch and user evidence.",
            "active_engineering_issue": None,
            "engineering_queue": [],
            "launch_track": [17, 18],
            "launch_control": {
                "active_issue": 17,
                "experiment_wip_limit": 1,
                "product_baseline_frozen": True,
            },
            "wip_limit": 1,
            "resume_point": "Run the next scoped launch experiment.",
            "last_verified_main_sha": "abc1234",
            "external_blockers": [],
        }
        self.assertEqual(validate_project_state(state), [])

    def test_post_release_requires_launch_track(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3-post-release-launch",
            "status": "post-release",
            "canonical_branch": "main",
            "current_release": "v0.3.0",
            "primary_objective": "Collect real launch and user evidence.",
            "active_engineering_issue": None,
            "engineering_queue": [],
            "launch_track": [],
            "launch_control": {
                "active_issue": 17,
                "experiment_wip_limit": 1,
                "product_baseline_frozen": True,
            },
            "wip_limit": 1,
            "resume_point": "No active launch work.",
            "last_verified_main_sha": "abc1234",
            "external_blockers": [],
        }
        failures = validate_project_state(state)
        self.assertTrue(any("non-empty launch_track" in item for item in failures))

    def test_post_release_rejects_engineering_wip(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3-post-release-launch",
            "status": "post-release",
            "canonical_branch": "main",
            "current_release": "v0.3.0",
            "primary_objective": "Collect real launch and user evidence.",
            "active_engineering_issue": 11,
            "engineering_queue": [11],
            "launch_track": [17],
            "launch_control": {
                "active_issue": 17,
                "experiment_wip_limit": 1,
                "product_baseline_frozen": True,
            },
            "wip_limit": 1,
            "resume_point": "Do not mix launch and engineering state.",
            "last_verified_main_sha": "abc1234",
            "external_blockers": [],
        }
        failures = validate_project_state(state)
        self.assertTrue(any("post-release state" in item for item in failures))

    def test_post_release_active_launch_must_be_first(self):
        state = {
            "schema_version": 1,
            "project": "FirstWindow",
            "phase": "v0.3-post-release-launch",
            "status": "post-release",
            "canonical_branch": "main",
            "current_release": "v0.3.0",
            "primary_objective": "Collect real launch and user evidence.",
            "active_engineering_issue": None,
            "engineering_queue": [],
            "launch_track": [17, 18],
            "launch_control": {
                "active_issue": 18,
                "experiment_wip_limit": 1,
                "product_baseline_frozen": True,
            },
            "wip_limit": 1,
            "resume_point": "Resolve ambiguous active launch work.",
            "last_verified_main_sha": "abc1234",
            "external_blockers": [],
        }
        failures = validate_project_state(state)
        self.assertTrue(any("first in launch_track" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
