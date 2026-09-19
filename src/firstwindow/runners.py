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


def hermes_usage_path(project: Path, task_id: str) -> Path:
    return project / ".firstwindow" / "runtime" / f"{task_id}-hermes-usage.json"


def project_env(
    project: Path,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Pin Hermes file/terminal tools to the FirstWindow project root.

    Hermes <=0.21.1 one-shot mode can ignore process cwd/--in and resolve
    terminal tools from a persisted workspace. TERMINAL_CWD is the upstream
    compatibility pin and remains harmless on fixed releases.
    """
    result = dict(env or os.environ)
    result["TERMINAL_CWD"] = str(project.resolve())
    return result


def hermes_command(
    project: Path,
    task_id: str,
    task: str,
    model: str,
    *,
    provider: str | None = "custom",
    isolate_user_config: bool = False,
) -> Sequence[str]:
    runtime = project / ".firstwindow" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    usage = hermes_usage_path(project, task_id)

    command: list[str] = [
        "hermes",
        "--in",
        str(project),
        "--no-restore-cwd",
    ]
    if isolate_user_config:
        command.append("--ignore-user-config")
    command.extend(["-z", task])
    if provider:
        command.extend(["--provider", provider])
    command.extend(["--model", model, "--usage-file", str(usage)])
    return command


def run_command(
    command: Sequence[str],
    project: Path,
    *,
    dry_run: bool = False,
    env: dict[str, str] | None = None,
) -> int:
    if dry_run:
        print(json.dumps({"cwd": str(project), "command": list(command)}, ensure_ascii=False))
        return 0
    return int(subprocess.run(list(command), cwd=project, check=False, env=env).returncode)


def local_model_from_env() -> str:
    return os.environ.get("FIRSTWINDOW_LOCAL_MODEL", "").strip()
