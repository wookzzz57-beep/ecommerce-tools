from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
import subprocess
from typing import Any, Callable, Mapping


_LOCAL_PROVIDERS = {"llamacpp", "llama.cpp", "llama-cpp"}


@dataclass(frozen=True)
class AgnesCapabilities:
    installed: bool
    version: str | None
    headless_recipe_ready: bool
    reason: str


def read_agnes_capabilities(
    *,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., Any] = subprocess.run,
) -> AgnesCapabilities:
    """Probe the installed Agnes CLI without authenticating or sending inference.

    FirstWindow needs a non-interactive recipe runner. Executable presence alone
    is not enough: some Agnes builds expose only the interactive surface.
    """
    command = which("agnes")
    if command is None:
        return AgnesCapabilities(False, None, False, "not-installed")

    version: str | None = None
    try:
        completed = runner(
            [command, "--version"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
        if int(getattr(completed, "returncode", 1)) == 0:
            raw = str(getattr(completed, "stdout", "") or "").strip()
            version = raw or None
    except (OSError, subprocess.SubprocessError):
        pass

    try:
        completed = runner(
            [command, "run", "--help"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
    except subprocess.TimeoutExpired:
        return AgnesCapabilities(True, version, False, "headless-probe-timeout")
    except (OSError, subprocess.SubprocessError):
        return AgnesCapabilities(True, version, False, "headless-probe-error")

    output = "\n".join(
        part for part in (
            str(getattr(completed, "stdout", "") or ""),
            str(getattr(completed, "stderr", "") or ""),
        ) if part
    )
    code = int(getattr(completed, "returncode", 1))
    ready = code == 0 and "--recipe" in output
    if ready:
        reason = "headless-recipe-ready"
    elif "not currently supported" in output.lower():
        reason = "headless-run-unsupported"
    else:
        reason = f"headless-help-exit-{code}"
    return AgnesCapabilities(True, version, ready, reason)


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
