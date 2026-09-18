from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Sequence


def agnes_command(project: Path, task_id: str, task: str) -> Sequence[str]:
    runtime = project / ".firstwindow" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    recipe = runtime / f"{task_id}-agnes.json"
    recipe.write_text(
        json.dumps(
            {
                "title": f"FirstWindow task {task_id}",
                "description": "Run a FirstWindow coding task with explicit verification.",
                "instructions": (
                    "Work only inside the current project. Respect AGENTS.md. "
                    "Run relevant tests/build checks before claiming completion and report concrete evidence."
                ),
                "prompt": task,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return ["agnes", "run", "--recipe", str(recipe)]


def hermes_command(
    project: Path,
    task_id: str,
    task: str,
    model: str,
    *,
    provider: str = "custom",
) -> Sequence[str]:
    runtime = project / ".firstwindow" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    usage = runtime / f"{task_id}-hermes-usage.json"
    return [
        "hermes",
        "-z",
        task,
        "--provider",
        provider,
        "--model",
        model,
        "--usage-file",
        str(usage),
    ]


def run_command(command: Sequence[str], project: Path, *, dry_run: bool = False) -> int:
    if dry_run:
        print(json.dumps({"cwd": str(project), "command": list(command)}, ensure_ascii=False))
        return 0
    return int(subprocess.run(list(command), cwd=project, check=False).returncode)


def local_model_from_env() -> str:
    return os.environ.get("FIRSTWINDOW_LOCAL_MODEL", "").strip()
