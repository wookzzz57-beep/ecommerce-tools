from __future__ import annotations

from dataclasses import dataclass
import platform as platform_module


@dataclass(frozen=True)
class SetupAction:
    target: str
    label: str
    command: tuple[str, ...]
    requires_confirmation: bool = True


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
    actions: list[SetupAction] = []
    if not agnes_installed:
        actions.append(
            SetupAction(
                target="agnes",
                label="Install Agnes Code",
                command=tuple(install_command(_platform_name(platform_name), "agnes")),
            )
        )
    if not hermes_installed:
        actions.append(
            SetupAction(
                target="hermes",
                label="Install Hermes Agent",
                command=tuple(install_command(_platform_name(platform_name), "hermes")),
            )
        )
    return actions
