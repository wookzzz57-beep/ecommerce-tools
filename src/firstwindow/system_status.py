from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Callable, Mapping


_LOCAL_PROVIDERS = {"llamacpp", "llama.cpp", "llama-cpp"}


def parse_hermes_model_json(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return {}

    if not isinstance(value, dict):
        return {}

    nested = value.get("value")
    if isinstance(nested, dict):
        value = nested

    return dict(value)


def hermes_local_ready(model: Mapping[str, Any]) -> bool:
    provider = str(model.get("provider") or "").strip().lower()
    model_name = str(model.get("default") or model.get("model") or "").strip()
    return provider in _LOCAL_PROVIDERS and bool(model_name)


def read_hermes_model(
    *,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    if which("hermes") is None:
        return {}

    try:
        completed = runner(
            ["hermes", "config", "get", "model", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return {}

    if getattr(completed, "returncode", 1) != 0:
        return {}

    return parse_hermes_model_json(getattr(completed, "stdout", ""))
