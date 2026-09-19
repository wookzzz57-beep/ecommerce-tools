from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Sequence

_TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

EXECUTION_ACCEPTANCE = "Agent process exits successfully through the verified route."
OUTCOME_ACCEPTANCE = "Requested task outcome is independently verified."


def default_acceptance() -> list[str]:
    """Separate transport success from actual task acceptance.

    The executor may prove AC-001 automatically. AC-002 deliberately remains
    uncovered until a distinct check/evidence record proves the requested
    outcome. This prevents `exit 0` or an agent saying "done" from becoming
    task-complete evidence.
    """
    return [EXECUTION_ACCEPTANCE, OUTCOME_ACCEPTANCE]


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


def _criterion_id(index: int) -> str:
    return f"AC-{index:03d}"


def create_task(project: Path, task_id: str, objective: str, acceptance: list[str]) -> Path:
    root = task_dir(project, task_id)
    if root.exists():
        raise FileExistsError(f"task already exists: {task_id}")
    if not objective.strip():
        raise ValueError("objective cannot be empty")
    if not acceptance or not all(isinstance(item, str) and item.strip() for item in acceptance):
        raise ValueError("at least one acceptance criterion is required")

    criteria = [
        {"id": _criterion_id(index), "text": item.strip()}
        for index, item in enumerate(acceptance, start=1)
    ]
    _atomic_json(
        root / "task.json",
        {
            "schema_version": 2,
            "task_id": task_id,
            "objective": objective.strip(),
            "acceptance": criteria,
            "created_at": now_iso(),
        },
    )
    write_checkpoint(project, task_id, "planned", "Dispatch to a verified lane.")
    return root


def write_checkpoint(project: Path, task_id: str, stage: str, next_action: str) -> None:
    _atomic_json(
        task_dir(project, task_id) / "checkpoint.json",
        {
            "schema_version": 1,
            "stage": stage,
            "next_action": next_action,
            "updated_at": now_iso(),
        },
    )


def append_evidence(
    project: Path,
    task_id: str,
    kind: str,
    passed: bool,
    detail: str,
    *,
    criteria: Sequence[str] | None = None,
) -> None:
    path = task_dir(project, task_id) / "evidence.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "timestamp": now_iso(),
        "kind": kind,
        "passed": bool(passed),
        "detail": detail,
    }
    if criteria is not None:
        if isinstance(criteria, (str, bytes)):
            raise ValueError("criteria must be a sequence of criterion IDs")
        refs: list[str] = []
        for criterion in criteria:
            if not isinstance(criterion, str) or not criterion.strip():
                raise ValueError("criterion IDs must be non-empty strings")
            value = criterion.strip()
            if value not in refs:
                refs.append(value)
        record["criteria"] = refs

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _read_evidence(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []

    records: list[dict[str, Any]] = []
    failures: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"evidence line {line_number} invalid JSON: {exc.msg}")
            continue
        if not isinstance(value, dict):
            failures.append(f"evidence line {line_number} must be a JSON object")
            continue
        records.append(value)
    return records, failures


def _base_report(schema_version: int | None, mode: str) -> dict[str, Any]:
    return {
        "ok": False,
        "schema_version": schema_version,
        "mode": mode,
        "covered": [],
        "uncovered": [],
        "failed": [],
        "failures": [],
    }


def _criterion_item(criterion: dict[str, str], record: dict[str, Any] | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"id": criterion["id"], "text": criterion["text"]}
    if record is not None:
        item["kind"] = record.get("kind")
        item["detail"] = record.get("detail")
        item["timestamp"] = record.get("timestamp")
    return item


def verification_report(project: Path, task_id: str) -> dict[str, Any]:
    root = task_dir(project, task_id)
    try:
        task = _read_json(root / "task.json")
        checkpoint = _read_json(root / "checkpoint.json")
    except Exception as exc:
        report = _base_report(None, "invalid")
        report["failures"].append(f"durable state unreadable: {exc}")
        return report

    schema_version = task.get("schema_version")
    mode = "legacy" if schema_version == 1 else "criteria" if schema_version == 2 else "invalid"
    report = _base_report(schema_version if isinstance(schema_version, int) else None, mode)
    failures: list[str] = report["failures"]

    if not task.get("objective"):
        failures.append("objective missing")
    if not checkpoint.get("next_action"):
        failures.append("checkpoint next_action missing")

    records, ledger_failures = _read_evidence(root / "evidence.jsonl")
    failures.extend(ledger_failures)

    if schema_version == 1:
        acceptance = task.get("acceptance")
        if not isinstance(acceptance, list) or not acceptance or not all(
            isinstance(item, str) and item.strip() for item in acceptance
        ):
            failures.append("acceptance criteria missing")
        if not records:
            failures.append("evidence ledger empty")
        elif not any(bool(item.get("passed")) for item in records):
            failures.append("no passing evidence")
        report["ok"] = not failures
        return report

    if schema_version != 2:
        failures.append(f"unsupported task schema_version: {schema_version}")
        return report

    raw_criteria = task.get("acceptance")
    if not isinstance(raw_criteria, list) or not raw_criteria:
        failures.append("acceptance criteria missing")
        return report

    criteria: list[dict[str, str]] = []
    known_ids: set[str] = set()
    for index, item in enumerate(raw_criteria, start=1):
        if not isinstance(item, dict):
            failures.append(f"acceptance criterion {index} must be an object")
            continue
        criterion_id = item.get("id")
        text = item.get("text")
        if not isinstance(criterion_id, str) or not criterion_id.strip():
            failures.append(f"acceptance criterion {index} id missing")
            continue
        if not isinstance(text, str) or not text.strip():
            failures.append(f"acceptance criterion {criterion_id} text missing")
            continue
        criterion_id = criterion_id.strip()
        if criterion_id in known_ids:
            failures.append(f"duplicate acceptance criterion id: {criterion_id}")
            continue
        known_ids.add(criterion_id)
        criteria.append({"id": criterion_id, "text": text.strip()})

    if not criteria:
        return report

    if not records:
        failures.append("evidence ledger empty")

    latest: dict[str, dict[str, Any]] = {}
    unknown_refs: set[str] = set()

    for line_number, record in enumerate(records, start=1):
        refs = record.get("criteria")
        if refs is None:
            continue
        if not isinstance(refs, list) or not all(
            isinstance(ref, str) and ref.strip() for ref in refs
        ):
            failures.append(f"evidence record {line_number} criteria must be a list of non-empty IDs")
            continue
        if not isinstance(record.get("passed"), bool):
            failures.append(f"evidence record {line_number} passed must be boolean")
            continue
        for ref in refs:
            criterion_id = ref.strip()
            if criterion_id not in known_ids:
                unknown_refs.add(criterion_id)
                continue
            latest[criterion_id] = record

    for criterion_id in sorted(unknown_refs):
        failures.append(f"unknown criterion reference: {criterion_id}")

    for criterion in criteria:
        record = latest.get(criterion["id"])
        if record is None:
            report["uncovered"].append(_criterion_item(criterion))
            failures.append(f"criterion uncovered: {criterion['id']} {criterion['text']}")
        elif record["passed"]:
            report["covered"].append(_criterion_item(criterion, record))
        else:
            report["failed"].append(_criterion_item(criterion, record))
            failures.append(f"criterion failed: {criterion['id']} {criterion['text']}")

    report["ok"] = not failures
    return report


def verify_task(project: Path, task_id: str) -> tuple[bool, list[str]]:
    report = verification_report(project, task_id)
    return bool(report["ok"]), list(report["failures"])
