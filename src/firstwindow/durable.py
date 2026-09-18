from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

_TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def validate_task_id(task_id: str) -> str:
    if not _TASK_ID.fullmatch(task_id):
        raise ValueError("unsafe task_id")
    return task_id

def task_dir(project: Path, task_id: str) -> Path:
    validate_task_id(task_id)
    return project / ".firstwindow" / "tasks" / task_id

def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def create_task(project: Path, task_id: str, objective: str, acceptance: list[str]) -> Path:
    root = task_dir(project, task_id)
    if root.exists():
        raise FileExistsError(f"task already exists: {task_id}")
    if not objective.strip():
        raise ValueError("objective cannot be empty")
    if not acceptance or not all(item.strip() for item in acceptance):
        raise ValueError("at least one acceptance criterion is required")
    _atomic_json(root / "task.json", {
        "schema_version": 1, "task_id": task_id, "objective": objective.strip(),
        "acceptance": [item.strip() for item in acceptance], "created_at": now_iso()
    })
    write_checkpoint(project, task_id, "planned", "Dispatch to a verified lane.")
    return root

def write_checkpoint(project: Path, task_id: str, stage: str, next_action: str) -> None:
    _atomic_json(task_dir(project, task_id) / "checkpoint.json", {
        "schema_version": 1, "stage": stage, "next_action": next_action, "updated_at": now_iso()
    })

def append_evidence(project: Path, task_id: str, kind: str, passed: bool, detail: str) -> None:
    path = task_dir(project, task_id) / "evidence.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": now_iso(), "kind": kind, "passed": bool(passed), "detail": detail}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

def verify_task(project: Path, task_id: str) -> tuple[bool, list[str]]:
    root = task_dir(project, task_id)
    failures: list[str] = []
    try:
        task = json.loads((root / "task.json").read_text(encoding="utf-8"))
        checkpoint = json.loads((root / "checkpoint.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return False, [f"durable state unreadable: {exc}"]
    if not task.get("objective"):
        failures.append("objective missing")
    if not task.get("acceptance"):
        failures.append("acceptance criteria missing")
    if not checkpoint.get("next_action"):
        failures.append("checkpoint next_action missing")
    evidence = root / "evidence.jsonl"
    records = [json.loads(line) for line in evidence.read_text(encoding="utf-8").splitlines() if line.strip()] if evidence.exists() else []
    if not records:
        failures.append("evidence ledger empty")
    elif not any(bool(item.get("passed")) for item in records):
        failures.append("no passing evidence")
    return not failures, failures
