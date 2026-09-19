from __future__ import annotations

from dataclasses import dataclass
import platform as platform_module
import subprocess
from typing import Any, Callable, Sequence


INSTALLER_TIMEOUT_SECONDS = 600


@dataclass(frozen=True)
class SetupAction:
    target: str
    label: str
    command: tuple[str, ...]
    requires_confirmation: bool = True


@dataclass(frozen=True)
class InstallerOutcome:
    exit_code: int | None
    timed_out: bool
    error: str | None = None


def run_installer_command(
    command: Sequence[str],
    *,
    timeout_seconds: int = INSTALLER_TIMEOUT_SECONDS,
    creationflags: int = 0,
    runner: Callable[..., Any] = subprocess.run,
) -> InstallerOutcome:
    """Run one allowlisted installer with a hard upper bound.

    FirstWindow must never leave the beginner GUI waiting forever on a network
    installer. A timeout is a truthful blocked state, not a successful install.
    """
    try:
        completed = runner(
            list(command),
            check=False,
            timeout=timeout_seconds,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired:
        return InstallerOutcome(exit_code=None, timed_out=True, error="timeout")
    except (OSError, subprocess.SubprocessError) as exc:
        return InstallerOutcome(exit_code=None, timed_out=False, error=str(exc))
    return InstallerOutcome(exit_code=int(getattr(completed, "returncode", 1)), timed_out=False)


def _platform_name(value: str | None = None) -> str:
    name = (value or platform_module.system()).strip().lower()
    aliases = {
        "win32": "windows",
        "windows": "windows",
        "darwin": "macos",
        "macos": "macos",
        "linux": "linux",
    }
    return aliases.get(name, name)


def install_command(platform_name: str, target: str) -> list[str]:
    system = _platform_name(platform_name)
    if target not in {"agnes", "hermes"}:
        raise ValueError(f"unsupported setup target: {target}")

    if system == "windows":
        scripts = {
            "agnes": "irm https://cos-agnes-code.agnes-ai.cn/cli-cn/release/download_cli.ps1 | iex",
            "hermes": "iex (irm https://hermes-agent.nousresearch.com/install.ps1)",
        }
        return ["powershell", "-NoProfile", "-Command", scripts[target]]

    if system in {"linux", "macos"}:
        scripts = {
            "agnes": "curl -fsSL https://cos-agnes-code.agnes-ai.cn/cli-cn/release/download_cli.sh | bash",
            "hermes": "curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash",
        }
        return ["bash", "-lc", scripts[target]]

    raise ValueError(f"unsupported platform: {platform_name}")


def setup_actions(
    *,
    platform_name: str | None = None,
    agnes_installed: bool,
    hermes_installed: bool,
) -> list[SetupAction]:
    """Return beginner-path prerequisites.

    Hermes is the only required agent runtime. Agnes CLI is intentionally not
    part of this list: the primary cloud lane is Agnes API configured inside
    Hermes, while direct Agnes CLI remains an explicit advanced fallback.
    """
    del agnes_installed  # retained for API compatibility with older callers
    actions: list[SetupAction] = []
    if not hermes_installed:
        actions.append(
            SetupAction(
                target="hermes",
                label="Install Hermes Agent",
                command=tuple(install_command(_platform_name(platform_name), "hermes")),
            )
        )
    return actions
