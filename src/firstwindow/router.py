from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
from typing import Mapping

_TRUTHY = {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class Lane:
    name: str
    engine: str
    zero_cost: bool
    available: bool
    reason: str

def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUTHY

def command_exists(name: str) -> bool:
    return shutil.which(name) is not None

def detect_lanes(env: Mapping[str, str] | None = None) -> list[Lane]:
    env = env or os.environ
    agnes = command_exists("agnes")
    hermes = command_exists("hermes")
    ollama = command_exists("ollama")
    agnes_free = _truthy(env.get("FIRSTWINDOW_AGNES_FREE_CONFIRMED"))
    hermes_local = _truthy(env.get("FIRSTWINDOW_HERMES_LOCAL_CONFIRMED"))
    local_model = bool((env.get("FIRSTWINDOW_LOCAL_MODEL") or "").strip())
    return [
        Lane("agnes-free", "agnes", True, agnes and agnes_free,
             "Agnes detected; configured provider explicitly confirmed free." if agnes and agnes_free
             else "Requires Agnes plus FIRSTWINDOW_AGNES_FREE_CONFIRMED=1."),
        Lane("hermes-local", "hermes", True, hermes and ollama and hermes_local and local_model,
             "Hermes + Ollama detected; local endpoint/model explicitly confirmed." if hermes and ollama and hermes_local and local_model
             else "Requires Hermes, Ollama, FIRSTWINDOW_HERMES_LOCAL_CONFIRMED=1 and FIRSTWINDOW_LOCAL_MODEL."),
        Lane("agnes-configured", "agnes", False, agnes,
             "Uses the provider currently configured in Agnes; cost is not guaranteed to be $0."),
        Lane("hermes-configured", "hermes", False, hermes,
             "Uses the provider currently configured in Hermes; cost is not guaranteed to be $0."),
    ]

def choose_lane(lanes: list[Lane], *, zero_cost: bool = True, preferred: str | None = None) -> Lane:
    candidates = [lane for lane in lanes if lane.available and (lane.zero_cost or not zero_cost)]
    if preferred:
        for lane in candidates:
            if lane.name == preferred or lane.engine == preferred:
                return lane
        raise RuntimeError(f"Requested lane '{preferred}' is not available under the current guard.")
    if candidates:
        return candidates[0]
    if zero_cost:
        raise RuntimeError("No verified $0 lane is ready. Run 'firstwindow doctor' and explicitly confirm a free/local provider.")
    raise RuntimeError("No supported Agnes or Hermes runtime was detected.")
