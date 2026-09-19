from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
from typing import Any, Mapping

from .system_status import AgnesCapabilities, hermes_local_ready, read_agnes_capabilities

_TRUTHY = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Lane:
    name: str
    engine: str
    zero_cost: bool
    available: bool
    reason: str
    provider: str | None = None
    model: str | None = None


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUTHY


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def detect_lanes(
    env: Mapping[str, str] | None = None,
    *,
    hermes_model: Mapping[str, Any] | None = None,
    agnes_capabilities: AgnesCapabilities | None = None,
) -> list[Lane]:
    env = env or os.environ
    agnes = command_exists("agnes")
    hermes = command_exists("hermes")
    capabilities = agnes_capabilities or read_agnes_capabilities()
    agnes_automation = bool(agnes and capabilities.installed and capabilities.headless_recipe_ready)
    agnes_free = _truthy(env.get("FIRSTWINDOW_AGNES_FREE_CONFIRMED"))

    managed_local = hermes_local_ready(hermes_model or {})
    manual_local = (
        _truthy(env.get("FIRSTWINDOW_HERMES_LOCAL_CONFIRMED"))
        and bool((env.get("FIRSTWINDOW_LOCAL_MODEL") or "").strip())
    )
    hermes_zero_ready = hermes and (managed_local or manual_local)

    managed_model = ""
    if hermes_model:
        managed_model = str(
            hermes_model.get("default") or hermes_model.get("model") or ""
        ).strip()
    manual_model = (env.get("FIRSTWINDOW_LOCAL_MODEL") or "").strip()

    return [
        Lane(
            "agnes-free",
            "agnes",
            True,
            agnes_automation and agnes_free,
            (
                "Agnes headless recipe runner detected and its configured provider is explicitly confirmed free."
                if agnes_automation and agnes_free
                else (
                    f"Agnes is installed but automatic recipe execution is unavailable ({capabilities.reason})."
                    if agnes
                    else "Requires Agnes CLI, headless recipe support, and explicit free-provider confirmation."
                )
            ),
        ),
        Lane(
            "hermes-local",
            "hermes",
            True,
            hermes_zero_ready,
            (
                "Hermes managed Local Models runtime is selected."
                if hermes and managed_local
                else (
                    "Hermes local endpoint/model explicitly confirmed."
                    if hermes and manual_local
                    else "Requires Hermes with a selected managed Local Model."
                )
            ),
            "llamacpp" if managed_local else ("custom" if manual_local else None),
            managed_model if managed_local else (manual_model or None),
        ),
        Lane(
            "agnes-configured",
            "agnes",
            False,
            agnes_automation,
            (
                "Uses the provider configured in Agnes; cost is not guaranteed to be $0."
                if agnes_automation
                else f"Agnes automatic recipe execution is unavailable ({capabilities.reason})."
            ),
        ),
        Lane(
            "hermes-configured",
            "hermes",
            False,
            hermes,
            "Uses the provider configured in Hermes; cost is not guaranteed to be $0.",
        ),
    ]


def choose_lane(
    lanes: list[Lane],
    *,
    zero_cost: bool = True,
    preferred: str | None = None,
) -> Lane:
    candidates = [lane for lane in lanes if lane.available and (lane.zero_cost or not zero_cost)]
    if preferred:
        for lane in candidates:
            if lane.name == preferred or lane.engine == preferred:
                return lane
        raise RuntimeError(f"Requested lane '{preferred}' is not available under the current guard.")
    if candidates:
        return candidates[0]
    if zero_cost:
        raise RuntimeError(
            "No verified $0 lane is ready. Run 'firstwindow doctor' and complete the guided setup."
        )
    raise RuntimeError("No supported Agnes or Hermes runtime was detected.")
