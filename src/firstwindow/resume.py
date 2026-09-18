from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .durable import task_dir, verification_report


@dataclass(frozen=True)
class ResumableTask:
    task_id: str
    objective: str
    stage: str
    next_action: str
    updated_at: str


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _read_evidence(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            records.append(value)
    return records


def _acceptance(task: dict[str, Any]) -> list[dict[str, str]]:
    raw = task.get("acceptance")
    if not isinstance(raw, list):
        return []
    if task.get("schema_version") == 1:
        return [
            {"id": f"AC-{index:03d}", "text": str(item)}
            for index, item in enumerate(raw, start=1)
            if isinstance(item, str)
        ]
    items: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("id"), str) and isinstance(item.get("text"), str):
            items.append({"id": item["id"], "text": item["text"]})
    return items


def load_resume_context(project: Path, task_id: str) -> dict[str, Any]:
    root = task_dir(project, task_id)
    report = verification_report(project, task_id)
    if report.get("ok"):
        raise RuntimeError(f"task already verified complete: {task_id}")
    if report.get("mode") == "invalid":
        raise RuntimeError(f"task state is invalid and cannot be resumed safely: {task_id}")

    task = _read_object(root / "task.json")
    checkpoint = _read_object(root / "checkpoint.json")
    evidence = _read_evidence(root / "evidence.jsonl")
    criteria = _acceptance(task)

    status: dict[str, str] = {}
    for item in report.get("covered", []):
        status[item["id"]] = "covered"
    for item in report.get("uncovered", []):
        status[item["id"]] = "uncovered"
    for item in report.get("failed", []):
        status[item["id"]] = "failed"

    return {
        "task_id": task_id,
        "objective": str(task.get("objective") or ""),
        "stage": str(checkpoint.get("stage") or ""),
        "next_action": str(checkpoint.get("next_action") or ""),
        "updated_at": str(checkpoint.get("updated_at") or ""),
        "acceptance": [
            {"id": item["id"], "text": item["text"], "status": status.get(item["id"], "unknown")}
            for item in criteria
        ],
        "evidence": evidence[-20:],
    }


def discover_resumable_tasks(project: Path) -> list[ResumableTask]:
    root = project / ".firstwindow" / "tasks"
    if not root.is_dir():
        return []

    found: list[ResumableTask] = []
    for candidate in root.iterdir():
        if not candidate.is_dir():
            continue
        try:
            context = load_resume_context(project, candidate.name)
        except Exception:
            continue
        found.append(
            ResumableTask(
                task_id=context["task_id"],
                objective=context["objective"],
                stage=context["stage"],
                next_action=context["next_action"],
                updated_at=context["updated_at"],
            )
        )

    found.sort(key=lambda item: (item.updated_at, item.task_id), reverse=True)
    return found


def build_resume_prompt(context: dict[str, Any]) -> str:
    criteria_lines = []
    for item in context.get("acceptance", []):
        criteria_lines.append(f"- [{item['status']}] {item['id']}: {item['text']}")

    evidence_lines = []
    for record in context.get("evidence", []):
        refs = ",".join(record.get("criteria") or []) or "none"
        evidence_lines.append(
            f"- {record.get('kind', 'evidence')} pass={record.get('passed')} criteria={refs}: {record.get('detail', '')}"
        )

    return "\n".join(
        [
            f"Resume FirstWindow durable task {context['task_id']}.",
            "Repository durable state is canonical; hidden chat history is not.",
            "Do not replay completed work or repeat side effects already evidenced unless the checkpoint explicitly requires it.",
            "",
            f"Objective: {context['objective']}",
            f"Current stage: {context['stage']}",
            f"Next action: {context['next_action']}",
            "",
            "Acceptance status:",
            *(criteria_lines or ["- none"]),
            "",
            "Existing evidence:",
            *(evidence_lines or ["- none"]),
            "",
            "Continue from the checkpoint next action. Re-check only what is necessary for safety.",
            "Before claiming completion, record fresh evidence for every still-uncovered or failed acceptance criterion.",
        ]
    )
