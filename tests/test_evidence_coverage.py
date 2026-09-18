from pathlib import Path
import json
import tempfile
import unittest

from firstwindow.durable import append_evidence, create_task, task_dir, verification_report


class EvidenceCoverageTests(unittest.TestCase):
    def test_new_task_uses_v2_stable_criterion_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            root = create_task(project, "v2-create", "ship endpoint", ["tests pass", "endpoint returns 200"])
            task = json.loads((root / "task.json").read_text(encoding="utf-8"))
            self.assertEqual(task["schema_version"], 2)
            self.assertEqual(
                task["acceptance"],
                [
                    {"id": "AC-001", "text": "tests pass"},
                    {"id": "AC-002", "text": "endpoint returns 200"},
                ],
            )

    def test_partial_coverage_reports_uncovered_criterion(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "partial", "ship endpoint", ["tests pass", "endpoint returns 200"])
            append_evidence(project, "partial", "test", True, "unit tests passed", criteria=["AC-001"])
            report = verification_report(project, "partial")
            self.assertFalse(report["ok"])
            self.assertEqual([item["id"] for item in report["covered"]], ["AC-001"])
            self.assertEqual([item["id"] for item in report["uncovered"]], ["AC-002"])

    def test_all_criteria_covered_by_passing_evidence_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "complete", "ship endpoint", ["tests pass", "endpoint returns 200"])
            append_evidence(project, "complete", "test", True, "unit tests passed", criteria=["AC-001"])
            append_evidence(project, "complete", "probe", True, "GET /health -> 200", criteria=["AC-002"])
            report = verification_report(project, "complete")
            self.assertTrue(report["ok"])
            self.assertEqual([item["id"] for item in report["covered"]], ["AC-001", "AC-002"])
            self.assertEqual(report["uncovered"], [])
            self.assertEqual(report["failed"], [])

    def test_latest_result_for_criterion_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "latest", "keep tests green", ["tests pass"])
            append_evidence(project, "latest", "test", True, "first run passed", criteria=["AC-001"])
            append_evidence(project, "latest", "test", False, "regression failed", criteria=["AC-001"])
            report = verification_report(project, "latest")
            self.assertFalse(report["ok"])
            self.assertEqual([item["id"] for item in report["failed"]], ["AC-001"])

    def test_unknown_criterion_reference_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            create_task(project, "unknown", "keep tests green", ["tests pass"])
            append_evidence(project, "unknown", "test", True, "passed", criteria=["AC-999"])
            report = verification_report(project, "unknown")
            self.assertFalse(report["ok"])
            self.assertTrue(any("unknown criterion reference: AC-999" in item for item in report["failures"]))

    def test_malformed_criterion_reference_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            root = create_task(project, "malformed", "keep tests green", ["tests pass"])
            (root / "evidence.jsonl").write_text(
                json.dumps({
                    "timestamp": "x",
                    "kind": "test",
                    "passed": True,
                    "detail": "bad criteria shape",
                    "criteria": "AC-001",
                }) + "\n",
                encoding="utf-8",
            )
            report = verification_report(project, "malformed")
            self.assertFalse(report["ok"])
            self.assertTrue(any("criteria must be a list" in item for item in report["failures"]))

    def test_v1_task_keeps_legacy_verification_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            root = task_dir(project, "legacy")
            root.mkdir(parents=True)
            (root / "task.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "task_id": "legacy",
                    "objective": "legacy task",
                    "acceptance": ["tests pass"],
                    "created_at": "2026-01-01T00:00:00+00:00",
                }),
                encoding="utf-8",
            )
            (root / "checkpoint.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "stage": "agent-finished",
                    "next_action": "verify",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }),
                encoding="utf-8",
            )
            (root / "evidence.jsonl").write_text(
                json.dumps({"timestamp": "x", "kind": "test", "passed": True, "detail": "legacy pass"}) + "\n",
                encoding="utf-8",
            )
            report = verification_report(project, "legacy")
            self.assertTrue(report["ok"])
            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["mode"], "legacy")

    def test_future_task_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            root = task_dir(project, "future")
            root.mkdir(parents=True)
            (root / "task.json").write_text(
                json.dumps({
                    "schema_version": 99,
                    "task_id": "future",
                    "objective": "future task",
                    "acceptance": [{"id": "AC-001", "text": "x"}],
                }),
                encoding="utf-8",
            )
            (root / "checkpoint.json").write_text(
                json.dumps({"schema_version": 1, "stage": "planned", "next_action": "verify"}),
                encoding="utf-8",
            )
            report = verification_report(project, "future")
            self.assertFalse(report["ok"])
            self.assertTrue(any("unsupported task schema_version: 99" in item for item in report["failures"]))


if __name__ == "__main__":
    unittest.main()
