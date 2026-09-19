from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
from typing import Any, Mapping

from .hermes_agnes import HermesAgnesRoute
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
    profile_home: str | None = None


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUTHY


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def detect_lanes(
    env: Mapping[str, str] | None = None,
    *,
    hermes_model: Mapping[str, Any] | None = None,
    agnes_route: HermesAgnesRoute | None = None,
    agnes_credential_present: bool = True,
    agnes_capabilities: AgnesCapabilities | None = None,
) -> list[Lane]:
    env = os.environ if env is None else env
    hermes = command_exists("hermes")
    agnes_cli = command_exists("agnes")
    capabilities = agnes_capabilities or read_agnes_capabilities()
    agnes_cli_automation = bool(
        agnes_cli and capabilities.installed and capabilities.headless_recipe_ready
    )
    agnes_free = _truthy(env.get("FIRSTWINDOW_AGNES_FREE_CONFIRMED"))

    route = agnes_route
    agnes_api_ready = bool(
        hermes and route and route.ready and agnes_credential_present and agnes_free
    )

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

    if route and route.ready and not agnes_credential_present:
        agnes_reason = "Hermes isolated Agnes API profile is configured but its credential is missing."
    elif route and route.ready:
        agnes_reason = (
            "Hermes isolated Agnes API profile is ready and this account/key route is explicitly confirmed free."
            if agnes_free
            else "Hermes isolated Agnes API profile is ready; confirm that the current Agnes account/key route is free."
        )
    elif route:
        agnes_reason = f"Requires an isolated Hermes -> Agnes API profile ({route.reason})."
    else:
        agnes_reason = "Requires an isolated Hermes -> Agnes API profile."

    return [
        Lane(
            "agnes-free",
            "hermes",
            True,
            agnes_api_ready,
            agnes_reason,
            "agnes" if route else None,
            route.model if route else None,
            route.profile_home if route else None,
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
            "agnes-cli-configured",
            "agnes",
            False,
            agnes_cli_automation,
            (
                "Advanced direct Agnes CLI runner is available; cost is not guaranteed."
                if agnes_cli_automation
                else f"Direct Agnes CLI automation is unavailable ({capabilities.reason})."
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
