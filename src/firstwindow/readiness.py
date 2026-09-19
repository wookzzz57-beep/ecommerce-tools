from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping, Sequence

from .system_status import hermes_local_ready


@dataclass(frozen=True)
class EngineReadiness:
    engine: str
    installed: bool
    configured: bool
    zero_cost_ready: bool
    provider: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class ReadinessReport:
    state: str
    action: str
    zero_cost_ready: bool
    ready_lane: str | None
    agnes: EngineReadiness
    hermes: EngineReadiness


@dataclass(frozen=True)
class ProbeResult:
    passed: bool
    exit_code: int | None
    output: str
    reason: str


def build_readiness(
    *,
    agnes_installed: bool,
    agnes_free_confirmed: bool,
    hermes_installed: bool,
    hermes_model: Mapping[str, Any],
) -> ReadinessReport:
    provider = str(hermes_model.get("provider") or "").strip() or None
    model = str(hermes_model.get("default") or hermes_model.get("model") or "").strip() or None
    hermes_configured = bool(provider and model)
    hermes_zero = bool(hermes_installed and hermes_local_ready(hermes_model))
    agnes_zero = bool(agnes_installed and agnes_free_confirmed)

    agnes = EngineReadiness(
        engine="agnes",
        installed=agnes_installed,
        configured=agnes_installed,
        zero_cost_ready=agnes_zero,
    )
    hermes = EngineReadiness(
        engine="hermes",
        installed=hermes_installed,
        configured=hermes_configured,
        zero_cost_ready=hermes_zero,
        provider=provider,
        model=model,
    )

    if agnes_zero:
        return ReadinessReport("ready", "verify", True, "agnes-free", agnes, hermes)
    if hermes_zero:
        return ReadinessReport("ready", "verify", True, "hermes-local", agnes, hermes)
    if not hermes_installed:
        return ReadinessReport("blocked", "install-hermes", False, None, agnes, hermes)
    return ReadinessReport("blocked", "configure-hermes-local", False, None, agnes, hermes)


def probe_command(
    command: Sequence[str],
    project: Path,
    *,
    env: Mapping[str, str] | None = None,
    runner: Callable[..., Any] = subprocess.run,
    timeout: int = 180,
    expected_text: str | None = None,
) -> ProbeResult:
    try:
        completed = runner(
            list(command),
            cwd=project,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=None if env is None else dict(env),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        text = "\n".join(
            part for part in (str(getattr(exc, "stdout", "") or ""), str(getattr(exc, "stderr", "") or "")) if part
        )
        return ProbeResult(False, None, text[-4000:], "timeout")
    except (OSError, subprocess.SubprocessError) as exc:
        return ProbeResult(False, None, str(exc), "launcher-error")

    output = "\n".join(
        part for part in (
            str(getattr(completed, "stdout", "") or "").strip(),
            str(getattr(completed, "stderr", "") or "").strip(),
        ) if part
    )
    code = int(getattr(completed, "returncode", 1))
    tail = output[-4000:]
    if code != 0:
        return ProbeResult(False, code, tail, f"exit-{code}")
    if expected_text is not None and expected_text not in output:
        return ProbeResult(False, code, tail, "expected-output-missing")
    return ProbeResult(True, code, tail, "ok")
