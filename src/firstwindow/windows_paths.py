from __future__ import annotations

import os
from pathlib import Path
import platform as platform_module
from typing import MutableMapping


def _platform_name(value: str | None = None) -> str:
    name = (value or platform_module.system()).strip().lower()
    return {"win32": "windows", "windows": "windows"}.get(name, name)


def runtime_path_candidates(
    platform_name: str,
    target: str,
    env: MutableMapping[str, str] | None = None,
) -> list[Path]:
    env = env if env is not None else os.environ
    if _platform_name(platform_name) != "windows":
        return []

    local_app_data = (env.get("LOCALAPPDATA") or "").strip()
    if not local_app_data:
        return []

    if target == "agnes":
        return [Path(local_app_data) / "Agnes" / "bin"]
    if target == "hermes":
        root = Path(local_app_data) / "hermes"
        return [root / "bin", root / "hermes-agent" / "venv" / "Scripts"]
    return []


def refresh_runtime_paths(
    platform_name: str,
    target: str,
    env: MutableMapping[str, str] | None = None,
) -> list[Path]:
    env = env if env is not None else os.environ
    entries = [entry for entry in env.get("PATH", "").split(os.pathsep) if entry]
    normalized = {os.path.normcase(os.path.normpath(entry)) for entry in entries}
    added: list[Path] = []

    for path in runtime_path_candidates(platform_name, target, env):
        if not path.is_dir():
            continue
        key = os.path.normcase(os.path.normpath(str(path)))
        if key in normalized:
            continue
        entries.insert(0, str(path))
        normalized.add(key)
        added.append(path)

    if added:
        env["PATH"] = os.pathsep.join(entries)
    return added
