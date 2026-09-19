from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BeginnerState:
    agnes_installed: bool
    agnes_free_confirmed: bool
    agnes_headless_ready: bool
    hermes_installed: bool
    hermes_local_ready: bool


def recommend_next_action(state: BeginnerState) -> str:
    if (state.agnes_installed and state.agnes_headless_ready and state.agnes_free_confirmed) or (
        state.hermes_installed and state.hermes_local_ready
    ):
        return "ready"
    if not state.agnes_installed and not state.hermes_installed:
        return "install"
    return "configure"
